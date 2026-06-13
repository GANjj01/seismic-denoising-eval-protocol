"""Experiment 8: matched 3C Noise2Void U-Net baseline.

This script adds a self-supervised 1D U-Net baseline without changing the
existing CovNorm/Transformer training code.  It reuses the current project data
split, optimizer conventions, loss scale, and final evaluation metrics.

Typical flow:

  python n2v_unet_baseline.py train --mask_variant sync
  python n2v_unet_baseline.py eval-development --mask_variant sync
  python n2v_unet_baseline.py select --mask_variant sync
  python n2v_unet_baseline.py eval-final-real --mask_variant sync
  python n2v_unet_baseline.py eval-oracle-free --mask_variant sync
  python n2v_unet_baseline.py report-card --mask_variant sync
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import random
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from tqdm import tqdm


PROJECT_ROOT = Path(
    os.environ.get(
        "SEISMIC_TRAINING_WORKSPACE",
        str(Path(__file__).resolve().parents[2] / "training_workspace_placeholder"),
    )
)
WORKSPACE = Path(__file__).resolve().parents[2]
RESULTS = WORKSPACE / "experiments" / "results"
DEFAULT_DATA_DIR = PROJECT_ROOT / "rs_data"
DEFAULT_EXTERNAL_DIR = PROJECT_ROOT / "rs_external_2025pre"
DEFAULT_INDEX_FILE = PROJECT_ROOT / "data_index.json"
DEFAULT_EXCLUDE_DEV_STATIONS = ["R3E8B", "R57B0", "R6468", "R6995", "RF4CA"]

sys.path.append(str(PROJECT_ROOT))
from train_pipeline import MiniSEEDIndexer, build_dataloaders, load_mseed_3c

from external_final_eval import (
    FS,
    P_IDX,
    TARGET_LEN,
    bandpass_filter,
    compute_amp_ratio,
    compute_delay_z,
    compute_snr_z,
    filter_station_files,
    load_3c_mseed,
    psd_suppression,
    station_from_name,
    summarize as summarize_real,
    wiener_baseline,
    write_csv,
)
from oracle_free_continuous_eval import (
    background_suppression,
    event_metrics,
    inject_template,
    make_continuous_noise,
    make_template,
    summarize as summarize_continuous,
    wiener_blind,
    wiener_oracle,
)


class ConvScale(nn.Module):
    """Single-convolution U-Net scale, sized to stay close to 0.8 M params."""

    def __init__(self, in_ch: int, out_ch: int, kernel_size: int = 7):
        super().__init__()
        pad = kernel_size // 2
        groups = min(8, out_ch)
        while out_ch % groups != 0:
            groups -= 1
        self.net = nn.Sequential(
            nn.Conv1d(in_ch, out_ch, kernel_size, padding=pad),
            nn.GroupNorm(groups, out_ch),
            nn.SiLU(),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class N2VUNet1D(nn.Module):
    """1D U-Net for 3 x 3000 Z/N/E windows.

    The four encoder scales use channels 32 -> 64 -> 128 -> 256 with kernel 7.
    Upsampling uses interpolation plus convolution rather than transposed
    convolution so the parameter count remains matched to the Transformer.
    """

    def __init__(self, in_channels: int = 3, channels=(32, 64, 128, 256), kernel_size: int = 7):
        super().__init__()
        c1, c2, c3, c4 = channels
        self.enc1 = ConvScale(in_channels, c1, kernel_size)
        self.enc2 = ConvScale(c1, c2, kernel_size)
        self.enc3 = ConvScale(c2, c3, kernel_size)
        self.enc4 = ConvScale(c3, c4, kernel_size)
        self.dec3 = ConvScale(c4 + c3, c3, kernel_size)
        self.dec2 = ConvScale(c3 + c2, c2, kernel_size)
        self.dec1 = ConvScale(c2 + c1, c1, kernel_size)
        self.out = nn.Conv1d(c1, in_channels, kernel_size, padding=kernel_size // 2)

    def forward(self, x: torch.Tensor, blind_spot_mask: torch.Tensor | None = None) -> torch.Tensor:
        # N2V inference is a full-image single forward pass.  The argument is
        # accepted only to keep checkpoint probes from failing; it is not used
        # and this model is never evaluated through Transformer blind-pass code.
        x = x.transpose(1, 2)  # [B, C, T]
        e1 = self.enc1(x)
        e2 = self.enc2(F.max_pool1d(e1, 2))
        e3 = self.enc3(F.max_pool1d(e2, 2))
        e4 = self.enc4(F.max_pool1d(e3, 2))

        d3 = F.interpolate(e4, size=e3.shape[-1], mode="linear", align_corners=False)
        d3 = self.dec3(torch.cat([d3, e3], dim=1))
        d2 = F.interpolate(d3, size=e2.shape[-1], mode="linear", align_corners=False)
        d2 = self.dec2(torch.cat([d2, e2], dim=1))
        d1 = F.interpolate(d2, size=e1.shape[-1], mode="linear", align_corners=False)
        d1 = self.dec1(torch.cat([d1, e1], dim=1))
        return self.out(d1).transpose(1, 2)


class N2VMasker:
    """Noise2Void random-value replacement masker.

    point: independent [time, component] points are masked.
    sync: the same time samples are masked across Z/N/E.
    """

    def __init__(
        self,
        mask_fraction: float = 0.015,
        variant: str = "sync",
        neighbor_radius: int = 5,
        seed: int = 42,
    ):
        if variant not in {"point", "sync"}:
            raise ValueError("variant must be 'point' or 'sync'")
        self.mask_fraction = float(mask_fraction)
        self.variant = variant
        self.neighbor_radius = int(neighbor_radius)
        self.seed = int(seed)
        self._generators: dict[str, torch.Generator] = {}

    def _generator_for(self, device: torch.device) -> torch.Generator:
        key = str(device)
        if key not in self._generators:
            gen = torch.Generator(device=device)
            gen.manual_seed(self.seed)
            self._generators[key] = gen
        return self._generators[key]

    def __call__(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        b, t, c = x.shape
        device = x.device
        gen = self._generator_for(device)
        if self.variant == "sync":
            time_mask = torch.rand((b, t), generator=gen, device=device) < self.mask_fraction
            # Guarantee at least one supervised time per window.
            missing = ~time_mask.any(dim=1)
            if missing.any():
                idx = torch.randint(0, t, (int(missing.sum()),), generator=gen, device=device)
                rows = torch.nonzero(missing, as_tuple=False).flatten()
                time_mask[rows, idx] = True
            mask = time_mask[:, :, None].expand(-1, -1, c)
        else:
            mask = torch.rand((b, t, c), generator=gen, device=device) < self.mask_fraction
            missing = ~mask.view(b, -1).any(dim=1)
            if missing.any():
                flat_idx = torch.randint(0, t * c, (int(missing.sum()),), generator=gen, device=device)
                rows = torch.nonzero(missing, as_tuple=False).flatten()
                mask[rows, flat_idx // c, flat_idx % c] = True

        radius = max(1, self.neighbor_radius)
        raw_offsets = torch.randint(0, 2 * radius, (b, t), generator=gen, device=device)
        offsets = raw_offsets - radius
        offsets = offsets + (offsets >= 0).long()
        src_t = (torch.arange(t, device=device)[None, :] + offsets).clamp(0, t - 1)
        src = x.gather(1, src_t[:, :, None].expand(-1, -1, c))
        corrupted = torch.where(mask, src, x)
        return corrupted, mask


class N2VLoss(nn.Module):
    def __init__(self, beta: float = 1.0):
        super().__init__()
        self.beta = float(beta)

    def forward(self, pred: torch.Tensor, target: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
        if mask.any():
            return F.smooth_l1_loss(pred[mask], target[mask], beta=self.beta)
        return F.smooth_l1_loss(pred, target, beta=self.beta)


def per_window_component_mad_normalize(x: torch.Tensor, eps: float = 1e-6) -> tuple[torch.Tensor, torch.Tensor]:
    """Normalize each sample and component by median absolute amplitude.

    This makes the N2V baseline use the same loss scale convention as the main
    model instead of letting a few high-amplitude windows dominate optimization.
    """
    scale = x.abs().median(dim=1, keepdim=True).values.clamp_min(eps)
    return x / scale, scale


class N2VEventReconEvaluator:
    def __init__(
        self,
        event_files,
        masker: N2VMasker,
        window_len: int,
        device: torch.device,
        n_windows: int = 32,
    ):
        self.masker = masker
        self.window_len = int(window_len)
        self.device = device
        self.windows = []
        for path in list(event_files)[: max(1, n_windows)]:
            for seg in load_mseed_3c(path, 100.0):
                if len(seg) >= self.window_len:
                    self.windows.append(torch.from_numpy(seg[: self.window_len].astype(np.float32)))
                    break
            if len(self.windows) >= n_windows:
                break

    def __len__(self) -> int:
        return len(self.windows)

    @torch.no_grad()
    def evaluate(self, model: nn.Module) -> float:
        if not self.windows:
            return float("nan")
        model.eval()
        losses = []
        for x_cpu in self.windows:
            x = x_cpu[None].to(self.device)
            x, _ = per_window_component_mad_normalize(x)
            x_corr, mask = self.masker(x)
            pred = model(x_corr)
            losses.append(float(((pred - x).pow(2)[mask]).mean().detach().cpu()))
        return float(np.mean(losses))


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def parameter_count(model: nn.Module) -> int:
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


def build_optimizer(model: nn.Module, lr: float, weight_decay: float) -> torch.optim.Optimizer:
    decay_params, no_decay_params = [], []
    for name, p in model.named_parameters():
        if not p.requires_grad:
            continue
        if p.ndim >= 2:
            decay_params.append(p)
        else:
            no_decay_params.append(p)
    return torch.optim.AdamW(
        [
            {"params": decay_params, "weight_decay": weight_decay},
            {"params": no_decay_params, "weight_decay": 0.0},
        ],
        lr=lr,
    )


def save_checkpoint(path: Path, model: nn.Module, epoch: int, val_loss: float, event_recon: float, args) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "epoch": epoch,
            "val_loss": val_loss,
            "event_recon": event_recon,
            "model": model.state_dict(),
            "architecture": "N2VUNet1D",
            "mask_variant": args.mask_variant,
            "mask_fraction": args.mask_fraction,
            "neighbor_radius": args.neighbor_radius,
            "loss": "SmoothL1",
            "smooth_l1_beta": args.smooth_l1_beta,
            "normalization": "per-window per-component MAD before masking/loss",
            "train_seed": args.seed,
            "mask_seed": args.seed,
            "dataloader_seed": args.seed,
            "inference_protocol": "N2V full-image single forward per sliding window; no blind-pass masking",
            "channels": [32, 64, 128, 256],
            "kernel_size": 7,
        },
        path,
    )


def load_n2v_model(checkpoint: Path, device: torch.device) -> tuple[N2VUNet1D, dict]:
    ckpt = torch.load(checkpoint, map_location=device)
    model = N2VUNet1D(
        channels=tuple(ckpt.get("channels", [32, 64, 128, 256])),
        kernel_size=int(ckpt.get("kernel_size", 7)),
    ).to(device)
    model.load_state_dict(ckpt["model"])
    model.eval()
    return model, ckpt


def train(args) -> None:
    set_seed(args.seed)
    device = torch.device("cuda" if torch.cuda.is_available() and not args.cpu else "cpu")
    print(f"Device: {device}")
    model = N2VUNet1D().to(device)
    print(f"N2V U-Net parameters: {parameter_count(model) / 1e6:.3f} M")
    print(
        "N2V protocol: "
        f"mask_variant={args.mask_variant}, mask_fraction={100 * args.mask_fraction:.2f}%, "
        "training input/loss space=per-window per-component MAD-normalized, "
        "inference=full-image forward with MAD rescale"
    )

    indexer = MiniSEEDIndexer(str(args.data_dir), str(args.index_file))
    index = indexer.load()
    event_index = normalize_event_index(args.event_index or Path(args.data_dir) / "event_index.json", Path(args.data_dir), Path(args.save_dir))
    train_loader, val_loader, val_event = build_dataloaders(
        index,
        window_len=args.window_len,
        batch_size=args.batch_size,
        num_workers=args.num_workers,
        seed=args.seed,
        event_index_file=str(event_index),
        p_event=args.p_event,
        steps_per_epoch=args.steps_per_epoch,
        val_steps=args.val_steps,
        cache_size=args.cache_size,
    )

    masker = N2VMasker(args.mask_fraction, args.mask_variant, args.neighbor_radius, args.seed)
    criterion = N2VLoss(beta=args.smooth_l1_beta)
    evaluator = N2VEventReconEvaluator(
        val_event, masker=masker, window_len=args.window_len,
        device=device, n_windows=args.eval_windows,
    )
    optimizer = build_optimizer(model, args.lr, args.weight_decay)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer, T_max=args.epochs, eta_min=args.lr * 0.01
    )
    use_amp = device.type == "cuda"
    amp_dtype = torch.bfloat16 if use_amp and torch.cuda.get_device_capability(device)[0] >= 8 else torch.float16
    scaler = torch.cuda.amp.GradScaler() if use_amp and amp_dtype == torch.float16 else None

    save_dir = Path(args.save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)
    history = []
    best_metric = float("inf")
    best_epoch = 0
    for epoch in range(1, args.epochs + 1):
        t0 = time.time()
        model.train()
        train_losses = []
        mask_fracs = []
        gnorms = []
        n_nan = 0
        for batch in tqdm(train_loader, desc=f"train {epoch:03d}", ncols=80, leave=False):
            x = batch.to(device)
            x, _ = per_window_component_mad_normalize(x)
            x_corr, mask = masker(x)
            with torch.amp.autocast("cuda", enabled=use_amp, dtype=amp_dtype):
                pred = model(x_corr)
                loss = criterion(pred, x, mask)
            if not torch.isfinite(loss):
                n_nan += 1
            optimizer.zero_grad()
            if scaler is not None:
                scaler.scale(loss).backward()
                scaler.unscale_(optimizer)
                gnorm = torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                scaler.step(optimizer)
                scaler.update()
            else:
                loss.backward()
                gnorm = torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                optimizer.step()
            train_losses.append(float(loss.detach().cpu()))
            mask_fracs.append(float(mask.float().mean().detach().cpu()))
            if math.isfinite(float(gnorm)):
                gnorms.append(float(gnorm))

        model.eval()
        val_losses = []
        with torch.no_grad():
            for batch in val_loader:
                x = batch.to(device)
                x, _ = per_window_component_mad_normalize(x)
                x_corr, mask = masker(x)
                pred = model(x_corr)
                val_losses.append(float(criterion(pred, x, mask).detach().cpu()))
        scheduler.step()
        val_loss = float(np.mean(val_losses))
        event_recon = evaluator.evaluate(model) if len(evaluator) else val_loss
        row = {
            "epoch": epoch,
            "train_loss": float(np.mean(train_losses)),
            "val_loss": val_loss,
            "event_recon": event_recon,
            "lr": scheduler.get_last_lr()[0],
            "mask_fraction": float(np.mean(mask_fracs)),
            "gnorm_mean": float(np.mean(gnorms)) if gnorms else 0.0,
            "gnorm_max": float(np.max(gnorms)) if gnorms else 0.0,
            "n_nan": n_nan,
            "seconds": time.time() - t0,
        }
        history.append(row)
        print(
            f"epoch {epoch:03d}/{args.epochs} train={row['train_loss']:.5f} "
            f"val={val_loss:.5f} event_recon={event_recon:.5f} "
            f"mask={100 * row['mask_fraction']:.2f}% "
            f"gnorm_mean={row['gnorm_mean']:.2f} "
            f"gnorm_max={row['gnorm_max']:.2f} NaN={n_nan} {row['seconds']:.0f}s"
        )
        save_checkpoint(save_dir / f"epoch_{epoch:03d}.pt", model, epoch, val_loss, event_recon, args)
        if event_recon < best_metric:
            best_metric = event_recon
            best_epoch = epoch
            save_checkpoint(save_dir / "best.pt", model, epoch, val_loss, event_recon, args)
            print(f"  saved best.pt at epoch {epoch} event_recon={event_recon:.5f}")
        if epoch - best_epoch > args.early_stop:
            print(f"early stop after {args.early_stop} epochs without event-recon improvement")
            break

    write_csv(save_dir / "history.csv", history)
    with (save_dir / "history.json").open("w", encoding="utf-8") as handle:
        json.dump(history, handle, indent=2)
    print(f"Training complete. Best epoch={best_epoch}, event_recon={best_metric:.5f}")


def normalize_event_index(event_index: str | Path, data_dir: Path, save_dir: Path) -> Path:
    """Return an event_index JSON whose file fields are absolute paths.

    The current project event_index stores paths relative to transformer_train
    when the original trainer is launched there.  This baseline is launched from
    experiments/scripts, so we materialize a resolved copy next to checkpoints.
    """
    event_index = Path(event_index)
    if not event_index.exists():
        return event_index
    records = json.loads(event_index.read_text(encoding="utf-8"))
    fixed = []
    for record in records:
        item = dict(record)
        file_value = item.get("file")
        if file_value:
            path = Path(file_value)
            if not path.is_absolute():
                candidates = [
                    PROJECT_ROOT / path,
                    data_dir / path,
                    data_dir / path.name,
                    data_dir / "events" / path.name,
                ]
                for candidate in candidates:
                    if candidate.exists():
                        item["file"] = str(candidate.resolve())
                        break
        fixed.append(item)
    save_dir.mkdir(parents=True, exist_ok=True)
    out = save_dir / "event_index.absolute.json"
    out.write_text(json.dumps(fixed, indent=2), encoding="utf-8")
    return out


@torch.no_grad()
def denoise_waveform_n2v(
    model: nn.Module,
    waveform: np.ndarray,
    window_len: int = 3000,
    overlap: int = 500,
    device: torch.device | None = None,
) -> np.ndarray:
    """Full-image N2V inference: one prediction per sliding window."""
    device = device or torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.eval()
    waveform = np.asarray(waveform, dtype=np.float32)
    t = len(waveform)
    mad = np.array([np.median(np.abs(waveform[:, i])) + 1e-6 for i in range(3)], dtype=np.float32)
    norm = waveform / mad[None, :]
    stride = window_len - overlap
    starts = list(range(0, max(1, t - window_len + 1), stride))
    if not starts or starts[-1] + window_len < t:
        starts.append(max(0, t - window_len))
    hann = np.hanning(window_len).astype(np.float32)
    out = np.zeros_like(norm)
    wsum = np.zeros(t, dtype=np.float32)
    use_amp = device.type == "cuda"
    amp_dtype = torch.bfloat16 if use_amp and torch.cuda.get_device_capability(device)[0] >= 8 else torch.float16
    for start in starts:
        end = min(start + window_len, t)
        length = end - start
        chunk = np.zeros((window_len, 3), dtype=np.float32)
        chunk[:length] = norm[start:end]
        if np.abs(chunk).max() < 1e-10:
            continue
        x = torch.from_numpy(chunk[None]).to(device)
        with torch.amp.autocast("cuda", enabled=use_amp, dtype=amp_dtype):
            pred = model(x).squeeze(0).float().cpu().numpy()
        out[start:end] += pred[:length] * hann[:length, None]
        wsum[start:end] += hann[:length]
    out = out / np.maximum(wsum, 1e-8)[:, None]
    return out * mad[None, :]


def parse_checkpoint_specs(items: list[str]) -> list[tuple[str, Path]]:
    specs = []
    for item in items:
        if "=" in item:
            name, path = item.split("=", 1)
        else:
            path = item
            name = Path(path).stem
        specs.append((name, Path(path)))
    return specs


def default_checkpoint_specs(args) -> list[tuple[str, Path]]:
    if args.checkpoint:
        return parse_checkpoint_specs(args.checkpoint)
    selected = Path(args.results_dir) / "selected_checkpoint.json"
    if selected.exists():
        data = json.loads(selected.read_text(encoding="utf-8"))
        return [(data["method"], Path(data["checkpoint"]))]
    best = Path(args.save_dir) / "best.pt"
    return [(f"n2v_{args.mask_variant}_best", best)]


def eval_real(args) -> None:
    device = torch.device("cuda" if torch.cuda.is_available() and not args.cpu else "cpu")
    models = []
    for name, checkpoint in default_checkpoint_specs(args):
        model, ckpt = load_n2v_model(checkpoint, device)
        models.append((name, model, checkpoint, ckpt))
        print(f"Loaded {name}: {checkpoint} epoch={ckpt.get('epoch')}")
    event_files = filter_station_files(
        sorted((Path(args.external_dir) / "events").glob("*.mseed")),
        args.include_stations,
        args.exclude_stations,
    )
    if args.max_events:
        event_files = event_files[: args.max_events]
    rows = []
    for idx, path in enumerate(event_files, 1):
        print(f"[n2v real {idx}/{len(event_files)}] {path.name}")
        try:
            raw = load_3c_mseed(path, TARGET_LEN)
        except Exception as exc:
            print(f"  skip: {exc}")
            continue
        waves = {
            "Raw": raw,
            "Identity": raw.copy(),
            "Bandpass": bandpass_filter(raw),
            "Wiener": wiener_baseline(raw, P_IDX),
        }
        for name, model, _, _ in models:
            waves[name] = denoise_waveform_n2v(model, raw, window_len=args.window_len, device=device)
        snr_raw = compute_snr_z(raw)
        for method, den in waves.items():
            delay = compute_delay_z(den)
            rec = {
                "event_id": path.stem,
                "station": station_from_name(path),
                "file": str(path),
                "method": method,
                "snr_raw": snr_raw,
                "snr": compute_snr_z(den),
                "snr_gain": compute_snr_z(den) - snr_raw,
                "amp_ratio": 1.0 if method == "Raw" else compute_amp_ratio(raw, den),
                "delay_s": "" if delay is None else delay,
            }
            if method != "Raw":
                rec.update(psd_suppression(raw, den))
            rows.append(rec)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    summary = summarize_real(
        rows, "method", ["snr_gain", "amp_ratio", "delay_s", "psd_1_5", "psd_5_10", "psd_10_20"]
    )
    write_csv(out_dir / "external_real_events_detail.csv", rows)
    write_csv(out_dir / "external_real_events_summary.csv", summary)
    print(f"Wrote {out_dir / 'external_real_events_summary.csv'}")


def eval_oracle_free(args) -> None:
    device = torch.device("cuda" if torch.cuda.is_available() and not args.cpu else "cpu")
    models = []
    for name, checkpoint in default_checkpoint_specs(args):
        model, ckpt = load_n2v_model(checkpoint, device)
        models.append((name, model, checkpoint, ckpt))
        print(f"Loaded {name}: {checkpoint} epoch={ckpt.get('epoch')}")
    events = filter_station_files(
        sorted((Path(args.external_dir) / "events").glob("*.mseed")),
        None,
        args.exclude_stations,
    )
    noises = filter_station_files(
        sorted((Path(args.external_dir) / "mixed").glob("*.mseed")),
        None,
        args.exclude_stations,
    )
    if args.max_events:
        events = events[: args.max_events]
    noises_by_station = defaultdict(list)
    for path in noises:
        noises_by_station[station_from_name(path)].append(path)
    rng = random.Random(args.seed)
    rows = []
    case_id = 0
    for event_index, event_path in enumerate(events, 1):
        station = station_from_name(event_path)
        candidates = noises_by_station.get(station, noises)
        if len(candidates) < 3:
            candidates = noises
        chosen = rng.sample(candidates, 3)
        noise = make_continuous_noise(chosen)
        template = make_template(load_3c_mseed(event_path, TARGET_LEN), taper=not args.no_template_taper)
        onset = rng.randint(int(18 * FS), int(62 * FS))
        for target_snr in args.snr_levels:
            case_id += 1
            mixture, clean = inject_template(noise, template, onset, target_snr)
            exact_noise = mixture - clean
            outputs = {
                "Noisy": mixture,
                "Identity": mixture.copy(),
                "Bandpass": bandpass_filter(mixture),
                "Wiener_blind": wiener_blind(mixture),
                "Wiener_oracle": wiener_oracle(mixture, exact_noise),
            }
            for name, model, _, _ in models:
                outputs[name] = denoise_waveform_n2v(
                    model, mixture, window_len=args.window_len, device=device
                )
            for method, output in outputs.items():
                record = {
                    "case_id": case_id,
                    "event_template": event_path.name,
                    "station_template": station,
                    "noise_files": ";".join(path.name for path in chosen),
                    "station_noise": station_from_name(chosen[0]),
                    "onset_s": onset / FS,
                    "target_snr_db": target_snr,
                    "method": method,
                    "background_suppression_db": background_suppression(output, mixture, onset),
                }
                record.update(event_metrics(output, clean, onset))
                rows.append(record)
        print(f"[n2v continuous {event_index}/{len(events)}] cases={case_id} {event_path.name}")
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    summary = summarize_continuous(rows)
    write_csv(out_dir / "oracle_free_continuous_detail.csv", rows)
    write_csv(out_dir / "oracle_free_continuous_summary.csv", summary)
    write_csv(out_dir / "oracle_free_revised_summary.csv", summary)
    print(f"Wrote {out_dir / 'oracle_free_revised_summary.csv'}")


def select_checkpoint(args) -> None:
    dev_dir = Path(args.development_dir)
    if "development" not in dev_dir.name.lower() and not args.allow_non_development_selection:
        raise RuntimeError(
            f"Refusing to select from non-development directory: {dev_dir}. "
            "Pass --allow_non_development_selection only for smoke/debug runs."
        )
    summary_path = dev_dir / "external_real_events_summary.csv"
    rows = read_csv(summary_path)
    candidates = [
        row for row in rows
        if row["method"].startswith(f"n2v_{args.mask_variant}_e")
        and row.get("snr_gain_mean", "") != ""
    ]
    if not candidates:
        raise RuntimeError(f"No n2v_{args.mask_variant}_e* rows found in {summary_path}")
    best_snr = max(float(row["snr_gain_mean"]) for row in candidates)
    retained = [row for row in candidates if float(row["snr_gain_mean"]) >= best_snr - args.snr_tolerance_db]
    selected = max(retained, key=lambda row: float(row["amp_ratio_mean"]))
    epoch_text = selected["method"].rsplit("_e", 1)[-1]
    checkpoint = Path(args.save_dir) / f"epoch_{int(epoch_text):03d}.pt"
    record = {
        "method": selected["method"],
        "checkpoint": str(checkpoint),
        "selection_rule": f"within {args.snr_tolerance_db:g} dB of best development SNR gain, maximize amp_ratio_mean",
        "best_snr_gain_mean": best_snr,
        "selected_snr_gain_mean": selected["snr_gain_mean"],
        "selected_amp_ratio_mean": selected["amp_ratio_mean"],
    }
    results_dir = Path(args.results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)
    write_csv(results_dir / "checkpoint_selection.csv", [record])
    (results_dir / "selected_checkpoint.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    print(json.dumps(record, indent=2))


def read_csv(path: Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def lookup_rows(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    return {row["method"]: row for row in read_csv(path)}


def report_card(args) -> None:
    n2v_real = lookup_rows(Path(args.real_dir) / "external_real_events_summary.csv")
    n2v_oracle = lookup_rows(Path(args.oracle_dir) / "oracle_free_revised_summary.csv")
    real_lookup = lookup_rows(RESULTS / "final_balanced_real" / "external_real_events_summary.csv")
    oracle_lookup = lookup_rows(RESULTS / "oracle_free_final" / "oracle_free_revised_summary.csv")
    adv = lookup_rows(RESULTS / "adversarial_baselines" / "adversarial_report_card.csv")
    deep_real = lookup_rows(RESULTS / "final_external_results" / "external_real_events_deepdenoiser_summary.csv")
    real_lookup.update(deep_real)
    report_methods = lambda name: name == "Identity" or name.startswith("n2v_")
    real_lookup.update({name: row for name, row in n2v_real.items() if report_methods(name)})
    oracle_lookup.update({name: row for name, row in n2v_oracle.items() if report_methods(name)})

    order = [
        "AdvGate", "AdvShrink", "AdvScale",
        "Identity", "Bandpass", "Wiener", "Wiener_blind", "Wiener_oracle",
        "DeepDenoiser", "p0_e06", "p01_e07", "p05_e16",
    ] + sorted([name for name in set(n2v_real) | set(n2v_oracle) if name.startswith("n2v_")])
    rows = []
    for method in order:
        real = real_lookup.get(method, {})
        oracle = oracle_lookup.get(method, {})
        adv_row = adv.get(method, {})
        if not real and not oracle and not adv_row:
            continue
        rows.append({
            "method": method,
            "real_event_apparent_snr_gain_mean": real.get("snr_gain_mean", adv_row.get("real_event_apparent_snr_gain_mean", "")),
            "real_event_amp_ratio_mean": real.get("amp_ratio_mean", adv_row.get("real_event_amp_ratio_mean", "")),
            "continuous_output_clean_snr_mean": oracle.get("output_vs_clean_snr_mean", adv_row.get("continuous_output_clean_snr_mean", "")),
            "continuous_corr_z_mean": oracle.get("corr_z_mean", adv_row.get("continuous_corr_z_mean", "")),
            "continuous_amp_ratio_median": oracle.get("amp_ratio_clean_median", adv_row.get("continuous_amp_ratio_median", "")),
            "continuous_background_suppression_mean": oracle.get("background_suppression_db_mean", adv_row.get("continuous_background_suppression_mean", "")),
        })
    out_dir = Path(args.results_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    write_csv(out_dir / "n2v_unet_report_card.csv", rows)
    print(f"Wrote {out_dir / 'n2v_unet_report_card.csv'}")


def add_common_paths(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--external_dir", type=Path, default=DEFAULT_EXTERNAL_DIR)
    parser.add_argument("--exclude_stations", nargs="+", default=DEFAULT_EXCLUDE_DEV_STATIONS)
    parser.add_argument("--include_stations", nargs="+", default=None)
    parser.add_argument("--cpu", action="store_true")
    parser.add_argument("--window_len", type=int, default=3000)
    parser.add_argument("--mask_variant", choices=["sync", "point"], default="sync")
    parser.add_argument("--save_dir", type=Path, default=RESULTS / "n2v_unet_sync_mask" / "checkpoints")
    parser.add_argument("--results_dir", type=Path, default=RESULTS / "n2v_unet_sync_mask")
    parser.add_argument("--checkpoint", action="append", help="NAME=PATH; defaults to selected checkpoint or best.pt")
    parser.add_argument("--max_events", type=int, default=0)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_train = sub.add_parser("train")
    p_train.add_argument("--data_dir", type=Path, default=DEFAULT_DATA_DIR)
    p_train.add_argument("--index_file", type=Path, default=DEFAULT_INDEX_FILE)
    p_train.add_argument("--event_index", type=str, default=None)
    p_train.add_argument("--save_dir", type=Path, default=RESULTS / "n2v_unet_sync_mask" / "checkpoints")
    p_train.add_argument("--mask_variant", choices=["sync", "point"], default="sync")
    p_train.add_argument("--mask_fraction", type=float, default=0.015)
    p_train.add_argument("--neighbor_radius", type=int, default=5)
    p_train.add_argument("--window_len", type=int, default=3000)
    p_train.add_argument("--batch_size", type=int, default=16)
    p_train.add_argument("--epochs", type=int, default=30)
    p_train.add_argument("--early_stop", type=int, default=30)
    p_train.add_argument("--lr", type=float, default=1e-4)
    p_train.add_argument("--weight_decay", type=float, default=1e-2)
    p_train.add_argument("--smooth_l1_beta", type=float, default=1.0)
    p_train.add_argument("--num_workers", type=int, default=0)
    p_train.add_argument("--seed", type=int, default=42)
    p_train.add_argument("--p_event", type=float, default=0.5)
    p_train.add_argument("--steps_per_epoch", type=int, default=3000)
    p_train.add_argument("--val_steps", type=int, default=500)
    p_train.add_argument("--cache_size", type=int, default=2000)
    p_train.add_argument("--eval_windows", type=int, default=32)
    p_train.add_argument("--cpu", action="store_true")
    p_train.set_defaults(func=train)

    p_dev = sub.add_parser("eval-development")
    add_common_paths(p_dev)
    p_dev.add_argument("--out_dir", type=Path, default=RESULTS / "n2v_unet_sync_mask" / "development_25_all_epochs")
    p_dev.set_defaults(
        func=eval_real,
        include_stations=DEFAULT_EXCLUDE_DEV_STATIONS,
        exclude_stations=[],
    )

    p_select = sub.add_parser("select")
    p_select.add_argument("--mask_variant", choices=["sync", "point"], default="sync")
    p_select.add_argument("--save_dir", type=Path, default=RESULTS / "n2v_unet_sync_mask" / "checkpoints")
    p_select.add_argument("--development_dir", type=Path, default=RESULTS / "n2v_unet_sync_mask" / "development_25_all_epochs")
    p_select.add_argument("--results_dir", type=Path, default=RESULTS / "n2v_unet_sync_mask")
    p_select.add_argument("--snr_tolerance_db", type=float, default=2.0)
    p_select.add_argument("--allow_non_development_selection", action="store_true")
    p_select.set_defaults(func=select_checkpoint)

    p_real = sub.add_parser("eval-final-real")
    add_common_paths(p_real)
    p_real.add_argument("--out_dir", type=Path, default=RESULTS / "n2v_unet_sync_mask" / "final_balanced_real")
    p_real.set_defaults(func=eval_real)

    p_oracle = sub.add_parser("eval-oracle-free")
    add_common_paths(p_oracle)
    p_oracle.add_argument("--out_dir", type=Path, default=RESULTS / "n2v_unet_sync_mask" / "oracle_free_final")
    p_oracle.add_argument("--snr_levels", nargs="+", type=float, default=[-5, 0, 5])
    p_oracle.add_argument("--seed", type=int, default=20260611)
    p_oracle.add_argument("--no_template_taper", action="store_true")
    p_oracle.set_defaults(func=eval_oracle_free)

    p_report = sub.add_parser("report-card")
    p_report.add_argument("--results_dir", type=Path, default=RESULTS / "n2v_unet_sync_mask")
    p_report.add_argument("--real_dir", type=Path, default=RESULTS / "n2v_unet_sync_mask" / "final_balanced_real")
    p_report.add_argument("--oracle_dir", type=Path, default=RESULTS / "n2v_unet_sync_mask" / "oracle_free_final")
    p_report.add_argument("--mask_variant", choices=["sync", "point"], default="sync")
    p_report.set_defaults(func=report_card)

    args = parser.parse_args()
    if args.command in {"eval-development", "eval-final-real", "eval-oracle-free"} and not args.checkpoint:
        # Evaluate all epoch checkpoints during development; final runs use the
        # selected checkpoint if available, otherwise best.pt.
        if args.command == "eval-development":
            ckpts = sorted(Path(args.save_dir).glob("epoch_*.pt"))
            args.checkpoint = [
                f"n2v_{args.mask_variant}_e{int(p.stem.split('_')[-1]):02d}={p}" for p in ckpts
            ]
            if not args.checkpoint:
                raise FileNotFoundError(f"No epoch_*.pt checkpoints found in {args.save_dir}")
    args.func(args)


if __name__ == "__main__":
    main()
