"""Adversarial diagnostic baselines for metric-failure demonstrations.

These baselines are deliberately constructed, parameter-fixed transforms.  They
are not intended as competitive denoisers; they show how single metrics can be
Goodharted by methods that discard waveform information.
"""

from __future__ import annotations

import argparse
import csv
import os
import random
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from obspy.signal.trigger import classic_sta_lta

from external_final_eval import (
    FS,
    P_IDX,
    TARGET_LEN,
    bandpass_filter,
    clean_amp_ratio,
    compute_amp_ratio,
    compute_delay_z,
    compute_snr_z,
    filter_station_files,
    load_3c_mseed,
    make_template,
    output_vs_clean_snr,
    psd_suppression,
    rms,
    station_from_name,
    summarize as summarize_real,
    write_csv,
)
from oracle_free_continuous_eval import (
    CONTINUOUS_LEN,
    EVENT_SIGNAL_LEN,
    background_suppression,
    event_metrics,
    inject_template,
    make_continuous_noise,
    summarize as summarize_continuous,
)


WORKSPACE = Path(__file__).resolve().parents[2]
RESULTS = WORKSPACE / "experiments" / "results"
DEFAULT_TRAINING_WORKSPACE = Path(
    os.environ.get("SEISMIC_TRAINING_WORKSPACE", str(WORKSPACE / "training_workspace_placeholder"))
)
ART = WORKSPACE / "paper" / "artifacts"
METHODS = ("AdvGate", "AdvShrink", "AdvScale")


def robust_mad(x: np.ndarray, axis=0) -> np.ndarray:
    med = np.median(x, axis=axis, keepdims=True)
    return np.median(np.abs(x - med), axis=axis, keepdims=True) + 1e-12


def adv_gate(x: np.ndarray, sta_s: float = 0.5, lta_s: float = 10.0, tau: float = 2.5) -> np.ndarray:
    energy = np.linalg.norm(x.astype(np.float64), axis=1)
    cft = classic_sta_lta(energy, int(sta_s * FS), int(lta_s * FS))
    gate = (cft > tau).astype(np.float32)[:, None]
    return (x * gate).astype(np.float32)


def adv_shrink(x: np.ndarray, tau: float = 3.0) -> np.ndarray:
    threshold = tau * robust_mad(x, axis=0)
    return (np.sign(x) * np.maximum(np.abs(x) - threshold, 0.0)).astype(np.float32)


def adv_scale(x: np.ndarray, scale: float = 0.01) -> np.ndarray:
    return (scale * x).astype(np.float32)


def adversarial_outputs(x: np.ndarray) -> dict[str, np.ndarray]:
    return {
        "AdvGate": adv_gate(x),
        "AdvShrink": adv_shrink(x),
        "AdvScale": adv_scale(x),
    }


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def prefixed_rows(protocol: str, rows: list[dict]) -> list[dict]:
    out = []
    for row in rows:
        record = {"protocol": protocol}
        record.update(row)
        out.append(record)
    return out


def eval_real(data_dir: Path, out_dir: Path, exclude_stations, max_events: int) -> tuple[list[dict], list[dict]]:
    event_files = filter_station_files(
        sorted((data_dir / "events").glob("*.mseed")),
        exclude_stations=exclude_stations,
    )
    if max_events:
        event_files = event_files[:max_events]

    rows = []
    for idx, path in enumerate(event_files, 1):
        raw = load_3c_mseed(path, TARGET_LEN)
        snr_raw = compute_snr_z(raw)
        for method, den in adversarial_outputs(raw).items():
            delay = compute_delay_z(den)
            record = {
                "event_id": path.stem,
                "station": station_from_name(path),
                "file": str(path),
                "method": method,
                "snr_raw": snr_raw,
                "snr": compute_snr_z(den),
                "snr_gain": compute_snr_z(den) - snr_raw,
                "amp_ratio": compute_amp_ratio(raw, den),
                "delay_s": "" if delay is None else delay,
            }
            record.update(psd_suppression(raw, den))
            rows.append(record)
        print(f"[adv real {idx}/{len(event_files)}] {path.name}")

    summary = summarize_real(
        rows,
        "method",
        ["snr_gain", "amp_ratio", "delay_s", "psd_1_5", "psd_5_10", "psd_10_20"],
    )
    write_csv(out_dir / "adversarial_real_events_detail.csv", rows)
    write_csv(out_dir / "adversarial_real_events_summary.csv", summary)
    return rows, summary


def eval_continuous(
    data_dir: Path,
    out_dir: Path,
    exclude_stations,
    snr_levels: list[float],
    seed: int,
    max_events: int,
) -> tuple[list[dict], list[dict], dict]:
    events = filter_station_files(
        sorted((data_dir / "events").glob("*.mseed")),
        exclude_stations=exclude_stations,
    )
    noises = filter_station_files(
        sorted((data_dir / "mixed").glob("*.mseed")),
        exclude_stations=exclude_stations,
    )
    if max_events:
        events = events[:max_events]

    noises_by_station = defaultdict(list)
    for path in noises:
        noises_by_station[station_from_name(path)].append(path)

    rng = random.Random(seed)
    rows = []
    example = {}
    case_id = 0
    for event_index, event_path in enumerate(events, 1):
        station = station_from_name(event_path)
        candidates = noises_by_station.get(station, noises)
        if len(candidates) < 3:
            candidates = noises
        chosen = rng.sample(candidates, 3)
        noise = make_continuous_noise(chosen)
        template = make_template(load_3c_mseed(event_path, TARGET_LEN))
        onset = rng.randint(int(18 * FS), int(62 * FS))

        for target_snr in snr_levels:
            case_id += 1
            mixture, clean = inject_template(noise, template, onset, target_snr)
            outputs = adversarial_outputs(mixture)
            if not example and float(target_snr) == 0.0:
                example = {
                    "mixture": mixture,
                    "clean": clean,
                    "advgate": outputs["AdvGate"],
                    "onset": onset,
                    "event_path": event_path,
                    "target_snr": target_snr,
                }
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
        print(f"[adv continuous {event_index}/{len(events)}] cases={case_id} {event_path.name}")

    summary = summarize_continuous(rows)
    write_csv(out_dir / "adversarial_oracle_free_detail.csv", rows)
    write_csv(out_dir / "adversarial_oracle_free_summary.csv", summary)
    return rows, summary, example


def build_cache_and_report(out_dir: Path, real_rows, continuous_rows, real_summary, continuous_summary):
    cache = prefixed_rows("real_event", real_rows) + prefixed_rows("oracle_free_continuous", continuous_rows)
    write_csv(out_dir / "adversarial_baselines_cache.csv", cache)

    real_lookup = {
        row["method"]: row for row in read_csv(RESULTS / "final_balanced_real" / "external_real_events_summary.csv")
    }
    for row in real_summary:
        real_lookup[row["method"]] = row
    oracle_lookup = {
        row["method"]: row for row in read_csv(RESULTS / "oracle_free_final" / "oracle_free_revised_summary.csv")
    }
    for row in continuous_summary:
        oracle_lookup[row["method"]] = row

    order = [
        "AdvGate", "AdvShrink", "AdvScale", "DeepDenoiser", "Wiener",
        "Wiener_blind", "p0_e06", "p01_e07", "p05_e16",
    ]
    report = []
    for method in order:
        real = real_lookup.get(method, {})
        oracle = oracle_lookup.get(method, {})
        if not real and not oracle:
            continue
        report.append({
            "method": method,
            "real_event_apparent_snr_gain_mean": real.get("snr_gain_mean", ""),
            "real_event_amp_ratio_mean": real.get("amp_ratio_mean", ""),
            "continuous_output_clean_snr_mean": oracle.get("output_vs_clean_snr_mean", ""),
            "continuous_corr_z_mean": oracle.get("corr_z_mean", ""),
            "continuous_amp_ratio_median": oracle.get("amp_ratio_clean_median", ""),
            "continuous_background_suppression_mean": oracle.get("background_suppression_db_mean", ""),
        })
    write_csv(out_dir / "adversarial_report_card.csv", report)
    return report


def plot_example(example: dict, out_path: Path):
    if not example:
        return
    onset = int(example["onset"])
    start = max(0, onset - int(5 * FS))
    end = min(CONTINUOUS_LEN, onset + EVENT_SIGNAL_LEN)
    t = (np.arange(start, end) - onset) / FS
    rows = [
        ("Noisy input", example["mixture"][start:end, 0]),
        ("AdvGate output", example["advgate"][start:end, 0]),
        ("Clean template", example["clean"][start:end, 0]),
    ]
    fig, axes = plt.subplots(3, 1, figsize=(10.8, 6.6), sharex=True)
    for ax, (label, wave) in zip(axes, rows):
        ax.plot(t, wave, color="#2F4858", linewidth=0.8)
        ax.axvline(0, color="#D1495B", linestyle="--", linewidth=1.0)
        ax.set_ylabel(label)
        ax.grid(alpha=0.16)
    raw_crop = example["mixture"][onset - P_IDX:onset - P_IDX + TARGET_LEN]
    gate_crop = example["advgate"][onset - P_IDX:onset - P_IDX + TARGET_LEN]
    clean_crop = example["clean"][onset - P_IDX:onset - P_IDX + TARGET_LEN]
    apparent_gain = compute_snr_z(gate_crop) - compute_snr_z(raw_crop)
    clean_snr = output_vs_clean_snr(gate_crop, clean_crop)
    corr = event_metrics(example["advgate"], example["clean"], onset)["corr_z"]
    fig.suptitle(
        "AdvGate diagnostic: high apparent SNR from an information-destroying gate",
        fontsize=12,
    )
    axes[0].set_title(
        f"{example['event_path'].name}, target {example['target_snr']:+.0f} dB | "
        f"apparent SNR gain {apparent_gain:+.1f} dB, clean-SNR {clean_snr:+.2f} dB, corr {corr:.2f}",
        fontsize=9,
    )
    axes[-1].set_xlabel("Time from hidden event onset (s)")
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=220)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_dir", type=Path, default=DEFAULT_TRAINING_WORKSPACE / "rs_external_2025pre")
    parser.add_argument("--out_dir", type=Path, default=RESULTS / "adversarial_baselines")
    parser.add_argument("--exclude_stations", nargs="+", default=["R3E8B", "R57B0", "R6468", "R6995", "RF4CA"])
    parser.add_argument("--snr_levels", nargs="+", type=float, default=[-5.0, 0.0, 5.0])
    parser.add_argument("--seed", type=int, default=20260611)
    parser.add_argument("--max_events", type=int, default=0)
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    real_rows, real_summary = eval_real(args.data_dir, args.out_dir, args.exclude_stations, args.max_events)
    continuous_rows, continuous_summary, example = eval_continuous(
        args.data_dir,
        args.out_dir,
        args.exclude_stations,
        args.snr_levels,
        args.seed,
        args.max_events,
    )
    report = build_cache_and_report(args.out_dir, real_rows, continuous_rows, real_summary, continuous_summary)
    plot_example(example, ART / "figure_advgate_diagnostic_waveform.png")

    print(f"Wrote {args.out_dir / 'adversarial_baselines_cache.csv'}")
    print(f"Wrote {args.out_dir / 'adversarial_report_card.csv'}")
    print(f"Wrote {ART / 'figure_advgate_diagnostic_waveform.png'}")
    for row in report:
        print(
            f"{row['method']:14s} real_snr={row['real_event_apparent_snr_gain_mean']} "
            f"clean_snr={row['continuous_output_clean_snr_mean']} "
            f"corr={row['continuous_corr_z_mean']}"
        )


if __name__ == "__main__":
    main()
