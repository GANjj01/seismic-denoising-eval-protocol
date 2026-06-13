"""Polarization/covariance rescoring for oracle-free continuous outputs.

This script rebuilds the deterministic 816-case oracle-free evaluation and
adds target-property metrics on the already-defined P+10 s, three-component
event window. It does not train models; it reruns inference only to recover the
waveform arrays needed for the additional scoring functions.
"""

from __future__ import annotations

import argparse
import csv
import math
import os
import random
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import torch

from external_final_eval import (
    FS,
    P_IDX,
    TARGET_LEN,
    bandpass_filter,
    denoise_waveform,
    filter_station_files,
    load_3c_mseed,
    load_models,
    make_template,
    parse_checkpoint_specs,
    station_from_name,
    write_csv,
)
from oracle_free_continuous_eval import (
    CONTINUOUS_LEN,
    EVENT_SIGNAL_LEN,
    blind_noise_psd,
    exact_noise_psd,
    inject_template,
    make_continuous_noise,
    spectral_wiener,
)


PROJECT_ROOT = Path(
    os.environ.get(
        "SEISMIC_TRAINING_WORKSPACE",
        str(Path(__file__).resolve().parents[2] / "training_workspace_placeholder"),
    )
)
EVENT_METRIC_LEN = int(10.0 * FS)


def demean_window(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=np.float64)
    return x - x.mean(axis=0, keepdims=True)


def covariance_shape(window: np.ndarray, eps: float = 1e-12) -> tuple[np.ndarray, float]:
    w = demean_window(window)
    cov = (w.T @ w) / max(len(w), 1)
    trace = float(np.trace(cov))
    return cov / max(trace, eps), trace


def polarization_attrs(window: np.ndarray, eps: float = 1e-12):
    w = demean_window(window)
    cov = (w.T @ w) / max(len(w), 1)
    vals, vecs = np.linalg.eigh(cov)
    order = np.argsort(vals)[::-1]
    vals = np.maximum(vals[order], 0.0)
    vecs = vecs[:, order]
    l1, l2, l3 = vals
    rect = 1.0 - (l2 + l3) / max(2.0 * l1, eps)
    plan = 1.0 - (2.0 * l3) / max(l1 + l2, eps)
    return float(rect), float(plan), vecs[:, 0], float(np.trace(cov))


def principal_angle_deg(a: np.ndarray, b: np.ndarray) -> float:
    dot = float(abs(np.dot(a, b)) / max(np.linalg.norm(a) * np.linalg.norm(b), 1e-12))
    dot = min(1.0, max(0.0, dot))
    return float(math.degrees(math.acos(dot)))


def component_corr(output: np.ndarray, clean: np.ndarray, component: int, max_lag_s: float = 1.0) -> float:
    y = output[:, component].astype(np.float64)
    c = clean[:, component].astype(np.float64)
    y = y - y.mean()
    c = c - c.mean()
    max_lag = int(max_lag_s * FS)
    best = -1.0
    for lag in range(-max_lag, max_lag + 1):
        if lag < 0:
            yy = y[-lag:]
            cc = c[: len(c) + lag]
        elif lag > 0:
            yy = y[: len(y) - lag]
            cc = c[lag:]
        else:
            yy = y
            cc = c
        denom = float(np.linalg.norm(yy) * np.linalg.norm(cc))
        if denom <= 1e-12:
            corr = 0.0
        else:
            corr = float(np.dot(yy, cc) / denom)
        if corr > best:
            best = corr
    return best


def metric_window(trace: np.ndarray, onset: int) -> np.ndarray:
    event_crop = trace[onset - P_IDX:onset - P_IDX + TARGET_LEN]
    if len(event_crop) != TARGET_LEN:
        raise ValueError("Event crop is outside the continuous trace")
    return event_crop[P_IDX:P_IDX + EVENT_METRIC_LEN]


def wiener_blind(x: np.ndarray) -> np.ndarray:
    freqs, psd = blind_noise_psd(x)
    return spectral_wiener(x, psd, freqs)


def wiener_oracle(x: np.ndarray, exact_noise: np.ndarray) -> np.ndarray:
    freqs, psd = exact_noise_psd(exact_noise)
    return spectral_wiener(x, psd, freqs)


def score_output(
    output: np.ndarray,
    clean: np.ndarray,
    mixture: np.ndarray,
    onset: int,
    identity_scores: dict[str, float],
    trace_gate: float,
) -> dict[str, float | int]:
    y_win = metric_window(output, onset)
    c_win = metric_window(clean, onset)
    x_win = metric_window(mixture, onset)

    c_shape, clean_trace = covariance_shape(c_win)
    y_shape, output_trace = covariance_shape(y_win)
    x_shape, mixture_trace = covariance_shape(x_win)

    gated = int(clean_trace < trace_gate)
    d_clean = float(np.linalg.norm(y_shape - c_shape, ord="fro"))
    d_noisy = float(np.linalg.norm(y_shape - x_shape, ord="fro"))

    y_rect, y_plan, y_axis, _ = polarization_attrs(y_win)
    c_rect, c_plan, c_axis, _ = polarization_attrs(c_win)
    theta = principal_angle_deg(y_axis, c_axis)

    return {
        "d_cov_clean": d_clean,
        "d_cov_noisy": d_noisy,
        "d_cov_gain_vs_identity": identity_scores["d_cov_clean"] - d_clean,
        "theta_deg": theta,
        "theta_reduction_vs_identity": identity_scores["theta_deg"] - theta,
        "rectilinearity_abs_error": abs(y_rect - c_rect),
        "planarity_abs_error": abs(y_plan - c_plan),
        "corr_z": component_corr(y_win, c_win, 0),
        "corr_n": component_corr(y_win, c_win, 1),
        "corr_e": component_corr(y_win, c_win, 2),
        "clean_trace": clean_trace,
        "output_trace": output_trace,
        "mixture_trace": mixture_trace,
        "trace_gate_flag": gated,
    }


def mean(values):
    vals = [float(v) for v in values if np.isfinite(float(v))]
    return float(np.mean(vals)) if vals else float("nan")


def summarize(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    metrics = [
        "d_cov_clean",
        "d_cov_noisy",
        "d_cov_gain_vs_identity",
        "theta_deg",
        "theta_reduction_vs_identity",
        "rectilinearity_abs_error",
        "planarity_abs_error",
        "corr_z",
        "corr_n",
        "corr_e",
    ]
    groups = defaultdict(list)
    for row in rows:
        groups[row["method"]].append(row)
    out = []
    for method, items in sorted(groups.items()):
        rec = {"method": method, "n": len(items)}
        for metric in metrics:
            vals = np.asarray([float(item[metric]) for item in items], dtype=float)
            rec[f"{metric}_mean"] = float(np.mean(vals))
            rec[f"{metric}_median"] = float(np.median(vals))
            rec[f"{metric}_q25"] = float(np.quantile(vals, 0.25))
            rec[f"{metric}_q75"] = float(np.quantile(vals, 0.75))
        rec["trace_gate_count"] = int(sum(int(item["trace_gate_flag"]) for item in items))
        out.append(rec)
    return out


def summarize_by_snr(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    groups = defaultdict(list)
    for row in rows:
        groups[(row["method"], row["target_snr_db"])].append(row)
    out = []
    for (method, snr), items in sorted(groups.items(), key=lambda kv: (str(kv[0][0]), float(kv[0][1]))):
        out.append({
            "method": method,
            "target_snr_db": snr,
            "n": len(items),
            "d_cov_gain_vs_identity_mean": mean(item["d_cov_gain_vs_identity"] for item in items),
            "theta_reduction_vs_identity_mean": mean(item["theta_reduction_vs_identity"] for item in items),
            "d_cov_clean_mean": mean(item["d_cov_clean"] for item in items),
            "theta_deg_mean": mean(item["theta_deg"] for item in items),
            "corr_n_mean": mean(item["corr_n"] for item in items),
            "corr_e_mean": mean(item["corr_e"] for item in items),
        })
    return out


def station_bootstrap(values_by_station: dict[str, list[float]], n_boot=5000, seed=20260614):
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


def bootstrap_tables(rows: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    methods = sorted({row["method"] for row in rows if row["method"] != "Identity"})
    vs_identity = []
    for method in methods:
        for metric in ["d_cov_gain_vs_identity", "theta_reduction_vs_identity"]:
            values = defaultdict(list)
            for row in rows:
                if row["method"] == method:
                    values[str(row["station_template"])].append(float(row[metric]))
            obs, lo, hi, nsta = station_bootstrap(values)
            vs_identity.append({
                "method": method,
                "metric": metric,
                "mean": obs,
                "ci_low": lo,
                "ci_high": hi,
                "n_stations": nsta,
            })

    by_case = defaultdict(dict)
    for row in rows:
        key = (row["case_id"], row["station_template"], row["target_snr_db"])
        by_case[key][row["method"]] = row
    paired = []
    pairs = [("p01_e07", "p0_e06"), ("p05_e16", "p0_e06")]
    for method, base in pairs:
        for metric in ["d_cov_gain_vs_identity", "theta_reduction_vs_identity", "d_cov_clean", "theta_deg"]:
            values = defaultdict(list)
            for key, md in by_case.items():
                if method in md and base in md:
                    station = str(key[1])
                    values[station].append(float(md[method][metric]) - float(md[base][metric]))
            obs, lo, hi, nsta = station_bootstrap(values)
            paired.append({
                "contrast": f"{method}-{base}",
                "metric": metric,
                "mean": obs,
                "ci_low": lo,
                "ci_high": hi,
                "n_stations": nsta,
            })
    return vs_identity, paired


def mechanism_plot(rows: list[dict[str, object]], out_path: Path):
    methods = ["p0_e06", "p05_e16"]
    metrics = [("d_cov_noisy", "to noisy mixture"), ("d_cov_clean", "to clean template")]
    fig, axes = plt.subplots(1, 2, figsize=(8.0, 3.4), dpi=220, sharey=False)
    colors = ["#4c78a8", "#e45756"]
    for ax, (metric, title) in zip(axes, metrics):
        means, lows, highs = [], [], []
        for method in methods:
            values = defaultdict(list)
            for row in rows:
                if row["method"] == method:
                    values[str(row["station_template"])].append(float(row[metric]))
            obs, lo, hi, _ = station_bootstrap(values)
            means.append(obs)
            lows.append(obs - lo)
            highs.append(hi - obs)
        x = np.arange(len(methods))
        ax.bar(x, means, color=colors, width=0.62)
        ax.errorbar(x, means, yerr=[lows, highs], fmt="none", ecolor="#222222", elinewidth=1.0, capsize=3)
        ax.set_xticks(x, [r"$\lambda=0$", r"$\lambda=0.5$"])
        ax.set_title(title)
        ax.set_ylabel(r"$D_{\mathrm{cov}}$")
        ax.grid(axis="y", alpha=0.25)
    fig.suptitle("Covariance-shape distance of CovNorm outputs", y=1.04, fontsize=10)
    fig.tight_layout()
    fig.savefig(out_path, bbox_inches="tight", dpi=220)
    plt.close(fig)


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
    parser.add_argument("--trace_gate", type=float, default=0.001)
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
        template = make_template(load_3c_mseed(event_path, TARGET_LEN), taper=not args.no_template_taper)
        onset = rng.randint(int(18 * FS), int(62 * FS))

        for target_snr in args.snr_levels:
            case_id += 1
            mixture, clean = inject_template(noise, template, onset, target_snr)
            exact_noise = mixture - clean
            outputs = {
                "Identity": mixture,
                "Bandpass": bandpass_filter(mixture),
                "Wiener_blind": wiener_blind(mixture),
                "Wiener_oracle": wiener_oracle(mixture, exact_noise),
            }
            for name, model, _, _, _ in models:
                outputs[name] = denoise_waveform(model, mixture, window_len=3000, device=device, mask_spans=(12,))

            identity_scores = score_output(mixture, clean, mixture, onset, {"d_cov_clean": 0.0, "theta_deg": 0.0}, args.trace_gate)
            identity_scores["d_cov_gain_vs_identity"] = 0.0
            identity_scores["theta_reduction_vs_identity"] = 0.0

            for method, output in outputs.items():
                scores = identity_scores if method == "Identity" else score_output(
                    output, clean, mixture, onset, identity_scores, args.trace_gate
                )
                record = {
                    "case_id": case_id,
                    "event_template": event_path.name,
                    "station_template": station,
                    "noise_files": ";".join(path.name for path in chosen),
                    "station_noise": station_from_name(chosen[0]),
                    "onset_s": onset / FS,
                    "target_snr_db": target_snr,
                    "method": method,
                }
                record.update(scores)
                rows.append(record)
        print(f"[polar {event_index}/{len(events)}] cases={case_id} {event_path.name}")

    write_csv(args.out_dir / "polarization_rescore_detail.csv", rows)
    write_csv(args.out_dir / "polarization_rescore_summary.csv", summarize(rows))
    write_csv(args.out_dir / "polarization_rescore_by_snr.csv", summarize_by_snr(rows))
    vs_identity, paired = bootstrap_tables(rows)
    write_csv(args.out_dir / "polarization_station_bootstrap_vs_identity.csv", vs_identity)
    write_csv(args.out_dir / "polarization_covnorm_pair_bootstrap.csv", paired)
    mechanism_plot(rows, args.out_dir / "covnorm_dcov_noisy_vs_clean.png")
    print(f"Wrote outputs to {args.out_dir}")


if __name__ == "__main__":
    main()
