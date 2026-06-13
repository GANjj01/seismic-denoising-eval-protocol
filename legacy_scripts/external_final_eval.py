"""
Batch external evaluation for station-disjoint Raspberry Shake windows.

Modes
-----
real:
  Evaluate external event windows downloaded by Parallel_download.py.
  Event windows are assumed to be PRE_P=10 s, POST_P=25 s.

synthetic:
  Build an in-band synthetic-injection diagnostic from external event templates
  and external real-noise windows. Both template and noise are restricted to
  1-20 Hz before mixing, so simple frequency separation is not enough.

Examples
--------
python external_batch_eval.py real --data_dir ./rs_external_2025pre --out_dir ./external_eval_results
python external_batch_eval.py synthetic --data_dir ./rs_external_2025pre --out_dir ./external_eval_results --noise_per_event 4
"""

import argparse
import csv
import math
import os
import random
import sys
from pathlib import Path

import numpy as np
import torch
from obspy import Stream, read as obspy_read
from obspy.signal.trigger import classic_sta_lta, trigger_onset
from scipy import signal as scipy_signal

PROJECT_ROOT = Path(
    os.environ.get(
        "SEISMIC_TRAINING_WORKSPACE",
        str(Path(__file__).resolve().parents[2] / "training_workspace_placeholder"),
    )
)
WORKSPACE = Path(__file__).resolve().parents[2]
RESULTS_ROOT = WORKSPACE / "experiments" / "results"
sys.path.append(str(PROJECT_ROOT))
from train_pipeline import SeismicDenoiserV2, denoise_waveform


FS = 100.0
PRE_P = 10.0
POST_P = 25.0
P_IDX = int(PRE_P * FS)
TARGET_LEN = int((PRE_P + POST_P) * FS)
SNR_SIGNAL_SEC = 10.0
AMP_SEC = 2.0
DETECT_TOL_SEC = 2.0
FREQ_BANDS = [
    (1, 5, "psd_1_5"),
    (5, 10, "psd_5_10"),
    (10, 20, "psd_10_20"),
]


DEFAULT_CHECKPOINTS = [
    ("p0_ep09", "checkpoints_p0/epoch_009.pt"),
    ("p05_ep09", "checkpoints_p05/epoch_009.pt"),
    ("p05_ep14", "checkpoints_p05/epoch_014.pt"),
    ("p05_ep20", "checkpoints_p05/epoch_020.pt"),
]


def parse_checkpoint_specs(items):
    specs = []
    for item in items:
        if "=" in item:
            name, path = item.split("=", 1)
        else:
            path = item
            name = Path(path).stem
        specs.append((name, path))
    return specs


def station_from_name(path):
    parts = Path(path).stem.split(".")
    return parts[1] if len(parts) >= 3 else ""


def filter_station_files(paths, include_stations=None, exclude_stations=None):
    include = set(include_stations or [])
    exclude = set(exclude_stations or [])
    return [
        path for path in paths
        if (not include or station_from_name(path) in include)
        and station_from_name(path) not in exclude
    ]


def rms(x):
    x = np.asarray(x, dtype=np.float64)
    return float(np.sqrt(np.mean(x * x))) if x.size else 0.0


def safe_std(x):
    return float(np.std(x)) if len(x) > 1 else 0.0


def load_3c_mseed(path, target_len=None):
    st = obspy_read(str(path))
    st.detrend("demean")
    st.detrend("linear")
    for tr in st:
        if abs(float(tr.stats.sampling_rate) - FS) > 0.1:
            tr.resample(FS)

    def pick(suffixes):
        s = Stream()
        for tr in st:
            ch = tr.stats.channel[-1].upper()
            if ch in suffixes:
                s += tr
        if len(s) == 0:
            return None
        s.merge(method=1, fill_value=0)
        return s[0]

    z = pick({"Z"})
    n = pick({"N", "1"})
    e = pick({"E", "2"})
    if z is None or n is None or e is None:
        raise ValueError(f"missing 3C in {path}")

    start = max(z.stats.starttime, n.stats.starttime, e.stats.starttime)
    end = min(z.stats.endtime, n.stats.endtime, e.stats.endtime)
    for tr in (z, n, e):
        tr.trim(start, end, pad=True, fill_value=0)

    length = min(len(z.data), len(n.data), len(e.data))
    x = np.stack([z.data[:length], n.data[:length], e.data[:length]], axis=-1).astype(np.float32)
    if target_len is not None:
        if len(x) >= target_len:
            x = x[:target_len]
        else:
            pad = np.zeros((target_len - len(x), 3), dtype=np.float32)
            x = np.concatenate([x, pad], axis=0)
    return x


def bandpass_filter(x, low=1.0, high=20.0):
    y = np.zeros_like(x, dtype=np.float32)
    sos = scipy_signal.butter(4, [low, high], btype="bandpass", fs=FS, output="sos")
    for i in range(3):
        y[:, i] = scipy_signal.sosfiltfilt(sos, x[:, i]).astype(np.float32)
    return y


def wiener_baseline(x, noise_len):
    y = np.zeros_like(x, dtype=np.float32)
    noise = x[:noise_len]
    for i in range(3):
        sig = x[:, i]
        nperseg = min(128, max(noise_len // 2, 8))
        f, pn = scipy_signal.welch(noise[:, i], fs=FS, nperseg=nperseg)
        _, px = scipy_signal.welch(sig, fs=FS, nperseg=nperseg)
        gain = np.maximum(1 - pn / (px + 1e-12), 0)
        f_fft = np.fft.rfftfreq(len(sig), 1 / FS)
        gain_i = np.interp(f_fft, f, gain)
        y[:, i] = np.fft.irfft(np.fft.rfft(sig) * gain_i, n=len(sig)).astype(np.float32)
    return y


def compute_snr_z(x, p=P_IDX):
    noise = x[:p, 0]
    sig = x[p:p + int(SNR_SIGNAL_SEC * FS), 0]
    if len(noise) < 10 or len(sig) < 10:
        return float("nan")
    return float(20 * np.log10(rms(sig) / (rms(noise) + 1e-12)))


def compute_amp_ratio(raw, den, p=P_IDX):
    seg = slice(p, p + int(AMP_SEC * FS))
    r = np.percentile(np.abs(raw[seg, 0]), 95)
    d = np.percentile(np.abs(den[seg, 0]), 95)
    return float(d / (r + 1e-12))


def compute_delay_z(x, p=P_IDX):
    sta_s, lta_s = int(0.5 * FS), int(5.0 * FS)
    try:
        cft = classic_sta_lta(x[:, 0].astype(np.float64), sta_s, lta_s)
        trig = trigger_onset(cft, 2.0, 1.0)
    except Exception:
        return None
    tol = int(DETECT_TOL_SEC * FS)
    starts = [int(t[0]) for t in trig if abs(int(t[0]) - p) <= tol]
    if not starts:
        return None
    best = min(starts, key=lambda v: abs(v - p))
    return float((best - p) / FS)


def psd_suppression(raw, den, p=P_IDX):
    out = {}
    if p < 64:
        return {name: float("nan") for _, _, name in FREQ_BANDS}
    for fmin, fmax, name in FREQ_BANDS:
        vals = []
        for c in range(3):
            nperseg = min(256, p // 2)
            f, pr = scipy_signal.welch(raw[:p, c], fs=FS, nperseg=nperseg)
            _, pd = scipy_signal.welch(den[:p, c], fs=FS, nperseg=nperseg)
            mask = (f >= fmin) & (f <= fmax)
            if np.any(mask):
                vals.append(10 * np.log10((np.mean(pr[mask]) + 1e-12) /
                                          (np.mean(pd[mask]) + 1e-12)))
        out[name] = float(np.mean(vals)) if vals else float("nan")
    return out


def load_models(checkpoint_specs, root, device, d_model=128, num_layers=4):
    models = []
    for name, rel_path in checkpoint_specs:
        path = Path(rel_path)
        if not path.is_absolute():
            path = root / path
        ckpt = torch.load(path, map_location=device)
        model = SeismicDenoiserV2(
            d_model=d_model, num_layers=num_layers, num_heads=8,
            dropout=0.0, max_len=3000,
        ).to(device)
        model.load_state_dict(ckpt["model"])
        model.eval()
        models.append((name, model, path, ckpt.get("epoch"), ckpt.get("event_recon")))
        print(f"Loaded {name}: {path} epoch={ckpt.get('epoch')} event_recon={ckpt.get('event_recon')}")
    return models


def summarize(rows, group_key, metrics):
    groups = {}
    for row in rows:
        groups.setdefault(row[group_key], []).append(row)
    out = []
    for key, items in sorted(groups.items()):
        rec = {group_key: key, "n": len(items)}
        for metric in metrics:
            vals = []
            for item in items:
                v = item.get(metric, "")
                if v in ("", None):
                    continue
                try:
                    fv = float(v)
                except Exception:
                    continue
                if math.isfinite(fv):
                    vals.append(fv)
            rec[f"{metric}_mean"] = float(np.mean(vals)) if vals else float("nan")
            rec[f"{metric}_std"] = safe_std(vals) if vals else float("nan")
        out.append(rec)
    return out


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    keys = list(rows[0].keys())
    for row in rows[1:]:
        for key in row.keys():
            if key not in keys:
                keys.append(key)
    with open(path, "w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)


def eval_real(args):
    root = PROJECT_ROOT
    data_dir = Path(args.data_dir)
    if not data_dir.is_absolute():
        data_dir = root / data_dir
    out_dir = Path(args.out_dir)
    if not out_dir.is_absolute():
        out_dir = RESULTS_ROOT / out_dir

    device = torch.device("cuda" if torch.cuda.is_available() and not args.cpu else "cpu")
    print(f"Device: {device}")
    ckpts = parse_checkpoint_specs(args.checkpoints or [f"{n}={p}" for n, p in DEFAULT_CHECKPOINTS])
    models = load_models(ckpts, root, device, args.d_model, args.num_layers)

    event_files = filter_station_files(
        sorted((data_dir / "events").glob("*.mseed")),
        args.include_stations,
        args.exclude_stations,
    )
    if args.max_events:
        event_files = event_files[:args.max_events]
    print(f"External real events: {len(event_files)}")

    rows = []
    for idx, path in enumerate(event_files, 1):
        sta = station_from_name(path)
        event_id = path.stem
        print(f"[real {idx}/{len(event_files)}] {event_id}")
        try:
            raw = load_3c_mseed(path, TARGET_LEN)
        except Exception as ex:
            print(f"  skip: {ex}")
            continue

        waves = {
            "Raw": raw,
            "Bandpass": bandpass_filter(raw),
            "Wiener": wiener_baseline(raw, P_IDX),
        }
        for name, model, _, _, _ in models:
            waves[name] = denoise_waveform(model, raw, window_len=3000, device=device)

        snr_raw = compute_snr_z(raw)
        for method, den in waves.items():
            snr = compute_snr_z(den)
            delay = compute_delay_z(den)
            rec = {
                "event_id": event_id,
                "station": sta,
                "file": str(path),
                "method": method,
                "snr_raw": snr_raw,
                "snr": snr,
                "snr_gain": snr - snr_raw,
                "amp_ratio": 1.0 if method == "Raw" else compute_amp_ratio(raw, den),
                "delay_s": "" if delay is None else delay,
            }
            if method != "Raw":
                rec.update(psd_suppression(raw, den))
            rows.append(rec)

    summary = summarize(rows, "method", ["snr_gain", "amp_ratio", "delay_s", "psd_1_5", "psd_5_10", "psd_10_20"])
    write_csv(out_dir / "external_real_events_detail.csv", rows)
    write_csv(out_dir / "external_real_events_summary.csv", summary)
    print(f"\nWrote {out_dir / 'external_real_events_detail.csv'}")
    print(f"Wrote {out_dir / 'external_real_events_summary.csv'}")
    print_summary(summary, ["snr_gain", "amp_ratio", "delay_s"])


def make_template(event, taper=True):
    clean = bandpass_filter(event)
    clean[:P_IDX] = 0.0
    taper_len = int(0.5 * FS)
    if taper and taper_len > 1:
        ramp = np.linspace(0, 1, taper_len, dtype=np.float32)[:, None]
        clean[P_IDX:P_IDX + taper_len] *= ramp
    # Remove very late low-level tail from the pseudo-clean template.
    end = min(len(clean), P_IDX + int(20 * FS))
    clean[end:] = 0.0
    return clean.astype(np.float32)


def scale_noise_to_snr(clean, noise, target_snr_db):
    sig = clean[P_IDX:P_IDX + int(SNR_SIGNAL_SEC * FS)]
    nseg = noise[P_IDX:P_IDX + int(SNR_SIGNAL_SEC * FS)]
    scale = rms(sig) / ((10 ** (target_snr_db / 20.0)) * (rms(nseg) + 1e-12))
    return noise * scale


def best_lag_and_corr(output, clean, p=P_IDX):
    a = output[p:p + int(SNR_SIGNAL_SEC * FS), 0].astype(np.float64)
    b = clean[p:p + int(SNR_SIGNAL_SEC * FS), 0].astype(np.float64)
    if len(a) < 10 or len(b) < 10:
        return float("nan"), float("nan")
    a0 = a - np.mean(a)
    b0 = b - np.mean(b)
    corr_full = scipy_signal.correlate(a0, b0, mode="full")
    lags = scipy_signal.correlation_lags(len(a0), len(b0), mode="full")
    keep = np.abs(lags) <= int(1.0 * FS)
    if not np.any(keep):
        return float("nan"), float("nan")
    k = np.argmax(corr_full[keep])
    lag = lags[keep][k]
    denom = np.linalg.norm(a0) * np.linalg.norm(b0) + 1e-12
    corr = corr_full[keep][k] / denom
    return float(lag / FS), float(corr)


def output_vs_clean_snr(output, clean):
    seg = slice(P_IDX, P_IDX + int(SNR_SIGNAL_SEC * FS))
    err = output[seg] - clean[seg]
    return float(20 * np.log10(rms(clean[seg]) / (rms(err) + 1e-12)))


def clean_amp_ratio(output, clean):
    seg = slice(P_IDX, P_IDX + int(AMP_SEC * FS))
    a = np.percentile(np.abs(output[seg, 0]), 95)
    b = np.percentile(np.abs(clean[seg, 0]), 95)
    return float(a / (b + 1e-12))


def eval_synthetic(args):
    root = PROJECT_ROOT
    data_dir = Path(args.data_dir)
    if not data_dir.is_absolute():
        data_dir = root / data_dir
    out_dir = Path(args.out_dir)
    if not out_dir.is_absolute():
        out_dir = RESULTS_ROOT / out_dir

    device = torch.device("cuda" if torch.cuda.is_available() and not args.cpu else "cpu")
    print(f"Device: {device}")
    ckpts = parse_checkpoint_specs(args.checkpoints or [f"{n}={p}" for n, p in DEFAULT_CHECKPOINTS])
    models = load_models(ckpts, root, device, args.d_model, args.num_layers)

    event_files = filter_station_files(
        sorted((data_dir / "events").glob("*.mseed")),
        args.include_stations,
        args.exclude_stations,
    )
    noise_files = filter_station_files(
        sorted((data_dir / "mixed").glob("*.mseed")),
        args.include_stations,
        args.exclude_stations,
    )
    if args.max_events:
        event_files = event_files[:args.max_events]
    rng = random.Random(args.seed)
    rng.shuffle(noise_files)

    rows = []
    case_idx = 0
    for eidx, event_path in enumerate(event_files, 1):
        try:
            template = make_template(load_3c_mseed(event_path, TARGET_LEN))
        except Exception as ex:
            print(f"skip template {event_path.name}: {ex}")
            continue
        if rms(template[P_IDX:P_IDX + int(SNR_SIGNAL_SEC * FS)]) <= 1e-12:
            print(f"skip weak template {event_path.name}")
            continue

        selected_noise = [noise_files[(eidx * args.noise_per_event + j) % len(noise_files)]
                          for j in range(args.noise_per_event)]
        for noise_path in selected_noise:
            try:
                noise = bandpass_filter(load_3c_mseed(noise_path, TARGET_LEN))
            except Exception as ex:
                print(f"skip noise {noise_path.name}: {ex}")
                continue
            noise[:P_IDX] -= np.mean(noise[:P_IDX], axis=0, keepdims=True)

            for target_snr in args.snr_levels:
                case_idx += 1
                scaled_noise = scale_noise_to_snr(template, noise, target_snr)
                noisy = (template + scaled_noise).astype(np.float32)
                waves = {
                    "Noisy": noisy,
                    "Bandpass": bandpass_filter(noisy),
                    "Wiener": wiener_baseline(noisy, P_IDX),
                }
                for name, model, _, _, _ in models:
                    waves[name] = denoise_waveform(model, noisy, window_len=3000, device=device)

                for method, out in waves.items():
                    lag, corr = best_lag_and_corr(out, template)
                    rows.append({
                        "case_id": case_idx,
                        "event_template": event_path.name,
                        "noise_file": noise_path.name,
                        "station_template": station_from_name(event_path),
                        "station_noise": station_from_name(noise_path),
                        "target_snr_db": target_snr,
                        "method": method,
                        "output_vs_clean_snr": output_vs_clean_snr(out, template),
                        "amp_ratio_clean": clean_amp_ratio(out, template),
                        "lag_s": lag,
                        "corr_z": corr,
                    })
        print(f"[synthetic] templates {eidx}/{len(event_files)} cases={case_idx}")

    summary = summarize(rows, "method", ["output_vs_clean_snr", "amp_ratio_clean", "lag_s", "corr_z"])
    write_csv(out_dir / "external_synthetic_inband_detail.csv", rows)
    write_csv(out_dir / "external_synthetic_inband_summary.csv", summary)
    print(f"\nWrote {out_dir / 'external_synthetic_inband_detail.csv'}")
    print(f"Wrote {out_dir / 'external_synthetic_inband_summary.csv'}")
    print_summary(summary, ["output_vs_clean_snr", "amp_ratio_clean", "lag_s", "corr_z"])


def add_transient_noise(noise, rng, strength=1.0):
    """Add short in-band burst noise after P to break the stationary-noise assumption."""
    out = noise.copy()
    start_min = P_IDX + int(0.5 * FS)
    start_max = min(len(out) - int(0.5 * FS), P_IDX + int(8.0 * FS))
    if start_max <= start_min:
        return out
    start = rng.randint(start_min, start_max)
    dur = rng.randint(int(0.15 * FS), int(0.8 * FS))
    end = min(len(out), start + dur)
    t = np.arange(end - start, dtype=np.float32) / FS
    freq = rng.uniform(3.0, 18.0)
    phase = rng.uniform(0, 2 * np.pi)
    env = scipy_signal.windows.tukey(end - start, alpha=0.6).astype(np.float32)
    carrier = np.sin(2 * np.pi * freq * t + phase).astype(np.float32)
    amp_ref = np.percentile(np.abs(noise[P_IDX:P_IDX + int(SNR_SIGNAL_SEC * FS), 0]), 95) + 1e-12
    burst = strength * amp_ref * carrier * env
    comp_weights = np.asarray([1.0, rng.uniform(0.3, 0.9), rng.uniform(0.3, 0.9)], dtype=np.float32)
    out[start:end] += burst[:, None] * comp_weights[None, :]
    return out


def eval_synthetic_nonstationary(args):
    root = PROJECT_ROOT
    data_dir = Path(args.data_dir)
    if not data_dir.is_absolute():
        data_dir = root / data_dir
    out_dir = Path(args.out_dir)
    if not out_dir.is_absolute():
        out_dir = RESULTS_ROOT / out_dir

    device = torch.device("cuda" if torch.cuda.is_available() and not args.cpu else "cpu")
    print(f"Device: {device}")
    ckpts = parse_checkpoint_specs(args.checkpoints or [f"{n}={p}" for n, p in DEFAULT_CHECKPOINTS])
    models = load_models(ckpts, root, device, args.d_model, args.num_layers)

    event_files = filter_station_files(
        sorted((data_dir / "events").glob("*.mseed")),
        args.include_stations,
        args.exclude_stations,
    )
    noise_files = filter_station_files(
        sorted((data_dir / "mixed").glob("*.mseed")),
        args.include_stations,
        args.exclude_stations,
    )
    if args.max_events:
        event_files = event_files[:args.max_events]
    rng = random.Random(args.seed)
    rng.shuffle(noise_files)

    rows = []
    case_idx = 0
    for eidx, event_path in enumerate(event_files, 1):
        try:
            template = make_template(load_3c_mseed(event_path, TARGET_LEN))
        except Exception as ex:
            print(f"skip template {event_path.name}: {ex}")
            continue
        if rms(template[P_IDX:P_IDX + int(SNR_SIGNAL_SEC * FS)]) <= 1e-12:
            print(f"skip weak template {event_path.name}")
            continue

        for j in range(args.noise_per_event):
            pre_path = noise_files[(eidx * args.noise_per_event + j) % len(noise_files)]
            post_path = noise_files[(eidx * args.noise_per_event + j + len(noise_files) // 3) % len(noise_files)]
            try:
                pre_noise = bandpass_filter(load_3c_mseed(pre_path, TARGET_LEN))
                post_noise = bandpass_filter(load_3c_mseed(post_path, TARGET_LEN))
            except Exception as ex:
                print(f"skip noise pair {pre_path.name}, {post_path.name}: {ex}")
                continue

            noise = np.zeros_like(template, dtype=np.float32)
            noise[:P_IDX] = pre_noise[:P_IDX]
            noise[P_IDX:] = post_noise[P_IDX:]
            noise = add_transient_noise(noise, rng, strength=args.transient_strength)
            noise[:P_IDX] -= np.mean(noise[:P_IDX], axis=0, keepdims=True)

            for target_snr in args.snr_levels:
                case_idx += 1
                scaled_noise = scale_noise_to_snr(template, noise, target_snr)
                noisy = (template + scaled_noise).astype(np.float32)
                waves = {
                    "Noisy": noisy,
                    "Bandpass": bandpass_filter(noisy),
                    "Wiener": wiener_baseline(noisy, P_IDX),
                }
                for name, model, _, _, _ in models:
                    waves[name] = denoise_waveform(model, noisy, window_len=3000, device=device)

                for method, out in waves.items():
                    lag, corr = best_lag_and_corr(out, template)
                    rows.append({
                        "case_id": case_idx,
                        "event_template": event_path.name,
                        "pre_noise_file": pre_path.name,
                        "post_noise_file": post_path.name,
                        "station_template": station_from_name(event_path),
                        "station_pre_noise": station_from_name(pre_path),
                        "station_post_noise": station_from_name(post_path),
                        "target_snr_db": target_snr,
                        "method": method,
                        "output_vs_clean_snr": output_vs_clean_snr(out, template),
                        "amp_ratio_clean": clean_amp_ratio(out, template),
                        "lag_s": lag,
                        "corr_z": corr,
                    })
        print(f"[synthetic_nonstationary] templates {eidx}/{len(event_files)} cases={case_idx}")

    summary = summarize(rows, "method", ["output_vs_clean_snr", "amp_ratio_clean", "lag_s", "corr_z"])
    write_csv(out_dir / "external_synthetic_nonstationary_detail.csv", rows)
    write_csv(out_dir / "external_synthetic_nonstationary_summary.csv", summary)
    print(f"\nWrote {out_dir / 'external_synthetic_nonstationary_detail.csv'}")
    print(f"Wrote {out_dir / 'external_synthetic_nonstationary_summary.csv'}")
    print_summary(summary, ["output_vs_clean_snr", "amp_ratio_clean", "lag_s", "corr_z"])


def print_summary(summary, metrics):
    if not summary:
        return
    print("\nSummary:")
    header = ["method", "n"]
    for m in metrics:
        header.extend([f"{m}_mean", f"{m}_std"])
    print("\t".join(header))
    for row in summary:
        vals = [str(row.get("method", "")), str(row.get("n", ""))]
        for m in metrics:
            vals.append(f"{row.get(m + '_mean', float('nan')):.3f}")
            vals.append(f"{row.get(m + '_std', float('nan')):.3f}")
        print("\t".join(vals))


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="mode", required=True)

    def add_common(p):
        p.add_argument("--data_dir", default="./rs_external_2025pre")
        p.add_argument("--out_dir", default="./external_eval_results")
        p.add_argument("--checkpoint", dest="checkpoints", action="append",
                       help="name=path. Can be repeated. Default: p0 ep9, p05 ep9/14/20")
        p.add_argument("--d_model", type=int, default=128)
        p.add_argument("--num_layers", type=int, default=4)
        p.add_argument("--max_events", type=int, default=0)
        p.add_argument("--cpu", action="store_true")
        p.add_argument("--include_stations", nargs="+", default=None)
        p.add_argument("--exclude_stations", nargs="+", default=None)

    p_real = sub.add_parser("real")
    add_common(p_real)

    p_syn = sub.add_parser("synthetic")
    add_common(p_syn)
    p_syn.add_argument("--noise_per_event", type=int, default=4)
    p_syn.add_argument("--snr_levels", type=float, nargs="+", default=[-5.0, 0.0, 5.0])
    p_syn.add_argument("--seed", type=int, default=20260609)

    p_hard = sub.add_parser("synthetic_nonstationary")
    add_common(p_hard)
    p_hard.add_argument("--noise_per_event", type=int, default=4)
    p_hard.add_argument("--snr_levels", type=float, nargs="+", default=[-5.0, 0.0, 5.0])
    p_hard.add_argument("--seed", type=int, default=20260609)
    p_hard.add_argument("--transient_strength", type=float, default=1.0)

    args = parser.parse_args()
    if args.mode == "real":
        eval_real(args)
    elif args.mode == "synthetic":
        eval_synthetic(args)
    elif args.mode == "synthetic_nonstationary":
        eval_synthetic_nonstationary(args)


if __name__ == "__main__":
    main()
