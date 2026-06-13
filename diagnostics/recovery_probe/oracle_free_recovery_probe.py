"""Oracle recovery probe for calibrating oracle-free report-card sensitivity.

This script rebuilds the deterministic 816-case oracle-free evaluation and
scores synthetic outputs with a known fraction of the injected noise removed:

    y_r = clean + (1 - r) * (mixture - clean)

where r is the recovery fraction. It does not train or run neural models. The
goal is to show that the report-card metrics can register a controlled success
when one exists.
"""

from __future__ import annotations

import argparse
import random
from collections import defaultdict
from pathlib import Path

import numpy as np

from external_final_eval import (
    FS,
    P_IDX,
    TARGET_LEN,
    best_lag_and_corr,
    clean_amp_ratio,
    filter_station_files,
    load_3c_mseed,
    make_template,
    output_vs_clean_snr,
    station_from_name,
    write_csv,
)
from oracle_free_continuous_eval import (
    EVENT_SIGNAL_LEN,
    background_suppression,
    inject_template,
    make_continuous_noise,
)


def safe_std(values):
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    return float(values.std(ddof=1)) if values.size > 1 else 0.0


def event_metrics_with_gain(output: np.ndarray, identity: np.ndarray, clean: np.ndarray, onset: int):
    shifted_output = output[onset - P_IDX:onset - P_IDX + TARGET_LEN]
    shifted_identity = identity[onset - P_IDX:onset - P_IDX + TARGET_LEN]
    shifted_clean = clean[onset - P_IDX:onset - P_IDX + TARGET_LEN]
    if len(shifted_output) != TARGET_LEN:
        raise ValueError("Event crop is outside the continuous trace")
    lag, corr = best_lag_and_corr(shifted_output, shifted_clean)
    snr_abs = output_vs_clean_snr(shifted_output, shifted_clean)
    identity_snr_abs = output_vs_clean_snr(shifted_identity, shifted_clean)
    return {
        "clean_snr_abs": snr_abs,
        "identity_clean_snr_abs": identity_snr_abs,
        "clean_snr_gain_vs_identity": snr_abs - identity_snr_abs,
        "amp_ratio_clean": clean_amp_ratio(shifted_output, shifted_clean),
        "lag_s": lag,
        "corr_z": corr,
    }


def summarize(rows):
    metrics = (
        "clean_snr_gain_vs_identity",
        "clean_snr_abs",
        "amp_ratio_clean",
        "lag_s",
        "corr_z",
        "background_suppression_db",
    )
    groups = defaultdict(list)
    for row in rows:
        groups[row["method"]].append(row)
    summary = []
    for method, items in sorted(groups.items(), key=lambda kv: float(kv[1][0]["recovery_fraction"])):
        record = {
            "method": method,
            "recovery_fraction": float(items[0]["recovery_fraction"]),
            "n": len(items),
        }
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


def summarize_by_snr(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[(row["method"], row["target_snr_db"])].append(row)
    out = []
    for (method, snr), items in sorted(
        groups.items(),
        key=lambda kv: (float(kv[1][0]["recovery_fraction"]), float(kv[0][1])),
    ):
        out.append({
            "method": method,
            "recovery_fraction": float(items[0]["recovery_fraction"]),
            "target_snr_db": snr,
            "n": len(items),
            "clean_snr_gain_vs_identity_mean": float(np.mean([float(i["clean_snr_gain_vs_identity"]) for i in items])),
            "corr_z_mean": float(np.mean([float(i["corr_z"]) for i in items])),
            "amp_ratio_clean_median": float(np.median([float(i["amp_ratio_clean"]) for i in items])),
            "background_suppression_db_mean": float(np.mean([float(i["background_suppression_db"]) for i in items])),
        })
    return out


def station_bootstrap(values_by_station, n_boot=5000, seed=20260614):
    rng = np.random.default_rng(seed)
    stations = sorted(values_by_station)
    station_means = np.asarray([np.mean(values_by_station[s]) for s in stations], dtype=float)
    observed = float(np.mean(station_means))
    boots = []
    for _ in range(n_boot):
        idx = rng.integers(0, len(station_means), size=len(station_means))
        boots.append(float(np.mean(station_means[idx])))
    lo, hi = np.quantile(boots, [0.025, 0.975])
    return observed, float(lo), float(hi), len(stations)


def bootstrap_vs_identity(rows):
    metrics = (
        "clean_snr_gain_vs_identity",
        "corr_z",
        "amp_ratio_clean",
        "background_suppression_db",
    )
    methods = sorted(
        {row["method"] for row in rows if float(row["recovery_fraction"]) > 0.0},
        key=lambda m: next(float(row["recovery_fraction"]) for row in rows if row["method"] == m),
    )
    identity_by_case = {}
    for row in rows:
        if row["method"] == "Identity":
            identity_by_case[row["case_id"]] = row
    out = []
    for method in methods:
        for metric in metrics:
            values = defaultdict(list)
            for row in rows:
                if row["method"] != method:
                    continue
                identity = identity_by_case[row["case_id"]]
                if metric == "clean_snr_gain_vs_identity":
                    diff = float(row[metric])
                elif metric == "background_suppression_db":
                    diff = float(row[metric])
                else:
                    diff = float(row[metric]) - float(identity[metric])
                values[str(row["station_template"])].append(diff)
            mean, lo, hi, nsta = station_bootstrap(values)
            out.append({
                "method": method,
                "recovery_fraction": next(float(row["recovery_fraction"]) for row in rows if row["method"] == method),
                "metric": metric,
                "mean": mean,
                "ci_low": lo,
                "ci_high": hi,
                "n_stations": nsta,
            })
    return out


def monotonic_checks(summary):
    ordered = sorted(summary, key=lambda row: float(row["recovery_fraction"]))
    metrics = [
        "clean_snr_gain_vs_identity_mean",
        "corr_z_mean",
        "background_suppression_db_mean",
    ]
    rows = []
    for metric in metrics:
        values = [float(row[metric]) for row in ordered]
        diffs = np.diff(values)
        rows.append({
            "metric": metric,
            "ordered_methods": ";".join(str(row["method"]) for row in ordered),
            "values": ";".join(f"{value:.6g}" for value in values),
            "nondecreasing": bool(np.all(diffs >= -1e-9)),
        })
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_dir", type=Path, required=True)
    parser.add_argument("--out_dir", type=Path, required=True)
    parser.add_argument("--exclude_stations", nargs="+", default=[])
    parser.add_argument("--snr_levels", nargs="+", type=float, default=[-5, 0, 5])
    parser.add_argument("--seed", type=int, default=20260611)
    parser.add_argument("--recovery_fractions", nargs="+", type=float, default=[0.30, 0.50, 0.70, 0.90])
    parser.add_argument("--max_events", type=int, default=0)
    parser.add_argument("--no_template_taper", action="store_true")
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
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

    fractions = [0.0] + sorted({float(v) for v in args.recovery_fractions})
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
            noise_residual = mixture - clean
            outputs = {}
            for fraction in fractions:
                if fraction == 0.0:
                    method = "Identity"
                else:
                    method = f"OracleRecovery{int(round(100 * fraction)):02d}"
                outputs[method] = (clean + (1.0 - fraction) * noise_residual).astype(np.float32)

            for method, output in outputs.items():
                fraction = 0.0 if method == "Identity" else float(method.replace("OracleRecovery", "")) / 100.0
                record = {
                    "case_id": case_id,
                    "event_template": event_path.name,
                    "station_template": station,
                    "noise_files": ";".join(path.name for path in chosen),
                    "station_noise": station_from_name(chosen[0]),
                    "onset_s": onset / FS,
                    "target_snr_db": target_snr,
                    "method": method,
                    "recovery_fraction": fraction,
                    "background_suppression_db": background_suppression(output, mixture, onset),
                }
                record.update(event_metrics_with_gain(output, mixture, clean, onset))
                rows.append(record)
        print(f"[recovery-probe {event_index}/{len(events)}] cases={case_id} {event_path.name}")

    detail = args.out_dir / "recovery_probe_detail.csv"
    summary = args.out_dir / "recovery_probe_summary.csv"
    by_snr = args.out_dir / "recovery_probe_by_snr.csv"
    boot = args.out_dir / "recovery_probe_station_bootstrap_vs_identity.csv"
    checks = args.out_dir / "recovery_probe_monotonic_checks.csv"
    write_csv(detail, rows)
    summary_rows = summarize(rows)
    write_csv(summary, summary_rows)
    write_csv(by_snr, summarize_by_snr(rows))
    write_csv(boot, bootstrap_vs_identity(rows))
    write_csv(checks, monotonic_checks(summary_rows))
    print(f"Wrote {detail}")
    print(f"Wrote {summary}")
    for row in summary_rows:
        print(
            f"{row['method']:18s} r={row['recovery_fraction']:.2f} "
            f"gain={row['clean_snr_gain_vs_identity_mean']:+.3f} "
            f"corr={row['corr_z_mean']:.3f} "
            f"amp_med={row['amp_ratio_clean_median']:.3f} "
            f"bg={row['background_suppression_db_mean']:+.3f}"
        )


if __name__ == "__main__":
    main()
