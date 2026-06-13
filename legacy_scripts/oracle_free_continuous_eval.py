"""Oracle-free continuous-noise synthetic evaluation.

Earthquake templates are injected at hidden random times into 90 s continuous
noise assembled from held-out Raspberry Shake noise windows.  Neural models,
band-pass filtering, and the blind Wiener baseline receive only the mixture.
The blind Wiener estimate uses low-energy frames selected from the full trace;
it is not given the event onset.  An oracle Wiener result that sees the true
noise realization is reported separately as an upper-bound diagnostic.
"""

from __future__ import annotations

import argparse
import csv
import math
import os
import random
from collections import defaultdict
from pathlib import Path

import numpy as np
import torch
from scipy import signal as scipy_signal

from external_final_eval import (
    FS,
    P_IDX,
    SNR_SIGNAL_SEC,
    TARGET_LEN,
    bandpass_filter,
    best_lag_and_corr,
    clean_amp_ratio,
    denoise_waveform,
    filter_station_files,
    load_3c_mseed,
    load_models,
    make_template,
    output_vs_clean_snr,
    parse_checkpoint_specs,
    rms,
    station_from_name,
    write_csv,
)


PROJECT_ROOT = Path(
    os.environ.get(
        "SEISMIC_TRAINING_WORKSPACE",
        str(Path(__file__).resolve().parents[2] / "training_workspace_placeholder"),
    )
)
CONTINUOUS_SEC = 90.0
CONTINUOUS_LEN = int(CONTINUOUS_SEC * FS)
EVENT_SIGNAL_LEN = int(20.0 * FS)
FRAME_LEN = int(4.0 * FS)
FRAME_HOP = int(2.0 * FS)


def safe_std(values):
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    return float(values.std(ddof=1)) if values.size > 1 else 0.0


def make_continuous_noise(paths: list[Path]) -> np.ndarray:
    chunks = [bandpass_filter(load_3c_mseed(path, TARGET_LEN)) for path in paths]
    stream = np.concatenate(chunks, axis=0)
    stream -= np.median(stream, axis=0, keepdims=True)
    if len(stream) < CONTINUOUS_LEN:
        repeats = int(np.ceil(CONTINUOUS_LEN / len(stream)))
        stream = np.tile(stream, (repeats, 1))
    return stream[:CONTINUOUS_LEN].astype(np.float32)


def inject_template(
    noise: np.ndarray,
    template: np.ndarray,
    onset: int,
    target_snr_db: float,
) -> tuple[np.ndarray, np.ndarray]:
    event = template[P_IDX:P_IDX + EVENT_SIGNAL_LEN].copy()
    event_rms = rms(event[: int(SNR_SIGNAL_SEC * FS)])
    noise_seg = noise[onset:onset + int(SNR_SIGNAL_SEC * FS)]
    scale = event_rms / ((10 ** (target_snr_db / 20.0)) * (rms(noise_seg) + 1e-12))
    scaled_noise = noise * scale
    clean = np.zeros_like(scaled_noise, dtype=np.float32)
    end = min(len(clean), onset + len(event))
    clean[onset:end] = event[: end - onset]
    return (scaled_noise + clean).astype(np.float32), clean


def spectral_wiener(x: np.ndarray, noise_psd: np.ndarray, freqs: np.ndarray) -> np.ndarray:
    output = np.zeros_like(x, dtype=np.float32)
    for component in range(3):
        sig = x[:, component]
        f_total, total_psd = scipy_signal.welch(
            sig, fs=FS, nperseg=min(512, len(sig))
        )
        pn = np.interp(f_total, freqs, noise_psd[:, component])
        gain = np.maximum(1.0 - pn / (total_psd + 1e-12), 0.0)
        fft_freqs = np.fft.rfftfreq(len(sig), 1.0 / FS)
        gain_fft = np.interp(fft_freqs, f_total, gain)
        output[:, component] = np.fft.irfft(
            np.fft.rfft(sig) * gain_fft, n=len(sig)
        ).astype(np.float32)
    return output


def blind_noise_psd(x: np.ndarray, low_fraction: float = 0.30):
    starts = list(range(0, len(x) - FRAME_LEN + 1, FRAME_HOP))
    frames = np.stack([x[start:start + FRAME_LEN] for start in starts])
    energy = np.mean(frames.astype(np.float64) ** 2, axis=(1, 2))
    count = max(3, int(math.ceil(low_fraction * len(frames))))
    selected = frames[np.argsort(energy)[:count]]
    spectra = []
    for frame in selected:
        per_component = []
        for component in range(3):
            freqs, psd = scipy_signal.welch(
                frame[:, component], fs=FS, nperseg=min(256, FRAME_LEN)
            )
            per_component.append(psd)
        spectra.append(np.stack(per_component, axis=1))
    return freqs, np.median(np.stack(spectra), axis=0)


def exact_noise_psd(noise: np.ndarray):
    values = []
    for component in range(3):
        freqs, psd = scipy_signal.welch(
            noise[:, component], fs=FS, nperseg=min(512, len(noise))
        )
        values.append(psd)
    return freqs, np.stack(values, axis=1)


def wiener_blind(x: np.ndarray) -> np.ndarray:
    freqs, psd = blind_noise_psd(x)
    return spectral_wiener(x, psd, freqs)


def wiener_oracle(x: np.ndarray, exact_noise: np.ndarray) -> np.ndarray:
    freqs, psd = exact_noise_psd(exact_noise)
    return spectral_wiener(x, psd, freqs)


def event_metrics(output: np.ndarray, clean: np.ndarray, onset: int):
    shifted_output = output[onset - P_IDX:onset - P_IDX + TARGET_LEN]
    shifted_clean = clean[onset - P_IDX:onset - P_IDX + TARGET_LEN]
    if len(shifted_output) != TARGET_LEN:
        raise ValueError("Event crop is outside the continuous trace")
    lag, corr = best_lag_and_corr(shifted_output, shifted_clean)
    return {
        "output_vs_clean_snr": output_vs_clean_snr(shifted_output, shifted_clean),
        "amp_ratio_clean": clean_amp_ratio(shifted_output, shifted_clean),
        "lag_s": lag,
        "corr_z": corr,
    }


def background_suppression(output: np.ndarray, mixture: np.ndarray, onset: int) -> float:
    mask = np.ones(len(output), dtype=bool)
    margin = int(2.0 * FS)
    mask[max(0, onset - margin):min(len(mask), onset + EVENT_SIGNAL_LEN + margin)] = False
    return float(20 * np.log10(rms(mixture[mask]) / (rms(output[mask]) + 1e-12)))


def summarize(rows):
    metrics = (
        "output_vs_clean_snr", "amp_ratio_clean", "lag_s", "corr_z",
        "background_suppression_db",
    )
    groups = defaultdict(list)
    for row in rows:
        groups[row["method"]].append(row)
    summary = []
    for method, items in sorted(groups.items()):
        record = {"method": method, "n": len(items)}
        for metric in metrics:
            values = np.asarray([float(item[metric]) for item in items], dtype=float)
            values = values[np.isfinite(values)]
            record[f"{metric}_mean"] = float(values.mean())
            record[f"{metric}_std"] = safe_std(values)
            record[f"{metric}_median"] = float(np.median(values))
            record[f"{metric}_q25"] = float(np.quantile(values, 0.25))
            record[f"{metric}_q75"] = float(np.quantile(values, 0.75))
        amp = np.asarray([float(item["amp_ratio_clean"]) for item in items])
        record["amp_in_0p8_1p2_fraction"] = float(np.mean((amp >= 0.8) & (amp <= 1.2)))
        summary.append(record)
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_dir", type=Path, required=True)
    parser.add_argument("--out_dir", type=Path, required=True)
    parser.add_argument("--checkpoint", dest="checkpoints", action="append", required=True)
    parser.add_argument("--exclude_stations", nargs="+", default=[])
    parser.add_argument("--snr_levels", nargs="+", type=float, default=[-5, 0, 5])
    parser.add_argument("--seed", type=int, default=20260611)
    parser.add_argument("--max_events", type=int, default=0)
    parser.add_argument("--cpu", action="store_true")
    parser.add_argument("--no_template_taper", action="store_true")
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    device = torch.device("cuda" if torch.cuda.is_available() and not args.cpu else "cpu")
    specs = parse_checkpoint_specs(args.checkpoints)
    models = load_models(specs, PROJECT_ROOT, device)

    events = filter_station_files(
        sorted((args.data_dir / "events").glob("*.mseed")),
        exclude_stations=args.exclude_stations,
    )
    noises = filter_station_files(
        sorted((args.data_dir / "mixed").glob("*.mseed")),
        exclude_stations=args.exclude_stations,
    )
    if args.max_events:
        events = events[:args.max_events]
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
        template = make_template(
            load_3c_mseed(event_path, TARGET_LEN),
            taper=not args.no_template_taper,
        )
        onset = rng.randint(int(18 * FS), int(62 * FS))

        for target_snr in args.snr_levels:
            case_id += 1
            mixture, clean = inject_template(noise, template, onset, target_snr)
            exact_noise = mixture - clean
            outputs = {
                "Noisy": mixture,
                "Bandpass": bandpass_filter(mixture),
                "Wiener_blind": wiener_blind(mixture),
                "Wiener_oracle": wiener_oracle(mixture, exact_noise),
            }
            for name, model, _, _, _ in models:
                outputs[name] = denoise_waveform(
                    model, mixture, window_len=3000, device=device, mask_spans=(12,)
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
                    "background_suppression_db": background_suppression(
                        output, mixture, onset
                    ),
                }
                record.update(event_metrics(output, clean, onset))
                rows.append(record)
        print(f"[continuous {event_index}/{len(events)}] cases={case_id} {event_path.name}")

    detail_path = args.out_dir / "oracle_free_continuous_detail.csv"
    summary_path = args.out_dir / "oracle_free_continuous_summary.csv"
    write_csv(detail_path, rows)
    summary = summarize(rows)
    write_csv(summary_path, summary)
    print(f"Wrote {detail_path}")
    print(f"Wrote {summary_path}")
    for row in summary:
        print(
            f"{row['method']:14s} n={row['n']} "
            f"SNR={row['output_vs_clean_snr_mean']:+.3f} "
            f"amp_med={row['amp_ratio_clean_median']:.3f} "
            f"corr={row['corr_z_mean']:.3f} "
            f"bg={row['background_suppression_db_mean']:+.3f}"
        )


if __name__ == "__main__":
    main()
