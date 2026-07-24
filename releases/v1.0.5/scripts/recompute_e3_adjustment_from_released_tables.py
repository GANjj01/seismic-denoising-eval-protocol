"""Recompute the released E3 adjustment/matching closure from package tables.

This is the package-portable entry point for v1.0.5. It uses only files that
are included in the formal release package: the released no-taper E3 per-case
metrics, released covariate tables, and frozen analysis configuration. It does
not read raw waveforms, sample tensors, model weights, or any workstation path.
"""

from __future__ import annotations

import argparse
import csv
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np


METRICS = ("output_vs_clean_snr", "amp_ratio_clean", "corr_z", "background_suppression_db")
COVARIATES = (
    "target_snr_db",
    "log10_noise_rms_injection_10s",
    "dominant_freq_hz",
    "spectral_slope_1_20",
    "log10_high_low_bandpower_ratio",
    "frame_rms_cv_4s",
)
STATION_COVARIATES = (
    "noise_rms_full_mean",
    "dominant_freq_hz_mean",
    "spectral_slope_1_20_mean",
    "frame_rms_cv_4s_mean",
)
BOOTSTRAP_SEED = 20260611
BOOTSTRAP_REPLICATES = 1000
MATCHING_CALIPER = 2.5


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = []
        for row in rows:
            for key in row:
                if key not in fieldnames:
                    fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def f(value: Any) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return math.nan
    return out if math.isfinite(out) else math.nan


def finite(values: list[Any] | np.ndarray) -> np.ndarray:
    arr = np.asarray(values, dtype=float)
    return arr[np.isfinite(arr)]


def stable_seed(seed: int, method: str, metric: str, suffix: str = "") -> int:
    text = f"{method}|{metric}|{suffix}"
    return seed + sum((i + 1) * ord(ch) for i, ch in enumerate(text))


def zero_excluded(low: float, high: float) -> bool:
    return math.isfinite(low) and math.isfinite(high) and ((low > 0.0) or (high < 0.0))


def direction(value: float) -> str:
    if not math.isfinite(value):
        return "nan"
    return "positive" if value > 0 else "negative" if value < 0 else "zero"


def tex_escape(value: Any) -> str:
    text = str(value)
    for old, new in [("\\", r"\textbackslash{}"), ("_", r"\_"), ("%", r"\%"), ("&", r"\&")]:
        text = text.replace(old, new)
    return text


def fmt(value: Any, digits: int = 3) -> str:
    num = f(value)
    if not math.isfinite(num):
        return ""
    return f"{num:+.{digits}f}"


def interval(row: dict[str, Any]) -> str:
    return f"[{fmt(row.get('ci95_low'))}, {fmt(row.get('ci95_high'))}]"


def load_outcomes(package_root: Path) -> list[dict[str, Any]]:
    cov_rows = read_csv(package_root / "e3_no_taper_confounding_closure" / "data" / "e3_no_taper_case_covariates.csv")
    cov_lookup = {row["case_id"]: row for row in cov_rows}
    out = []
    for row in read_csv(package_root / "source_metrics" / "e3_detail_wide.csv"):
        cov = cov_lookup.get(row["case_id"])
        if cov is None:
            continue
        item: dict[str, Any] = dict(row)
        item["station_noise"] = cov["station_noise"]
        for name in COVARIATES:
            item[name] = cov[name]
        out.append(item)
    return out


def station_means(rows: list[dict[str, Any]], method: str, metric: str) -> dict[tuple[str, str], float]:
    grouped: dict[tuple[str, str], list[float]] = defaultdict(list)
    for row in rows:
        if row["method"] != method:
            continue
        value = f(row[metric])
        if math.isfinite(value):
            grouped[(row["group"], row["station_noise"])].append(value)
    return {key: float(np.mean(values)) for key, values in grouped.items() if values}


def independent_station_bootstrap(a: np.ndarray, b: np.ndarray, n_boot: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    draws = np.empty(n_boot, dtype=float)
    for i in range(n_boot):
        aa = rng.choice(a, size=a.size, replace=True)
        bb = rng.choice(b, size=b.size, replace=True)
        draws[i] = float(np.mean(aa) - np.mean(bb))
    return draws


def unadjusted_results(rows: list[dict[str, Any]], n_boot: int = 20000) -> list[dict[str, Any]]:
    methods = sorted({row["method"] for row in rows})
    out = []
    for method in methods:
        for metric in METRICS:
            means = station_means(rows, method, metric)
            a = np.asarray([v for (g, _), v in means.items() if g == "A"], dtype=float)
            b = np.asarray([v for (g, _), v in means.items() if g == "B"], dtype=float)
            if not a.size or not b.size:
                continue
            boot = independent_station_bootstrap(a, b, n_boot, BOOTSTRAP_SEED)
            estimate = float(np.mean(a) - np.mean(b))
            low = float(np.quantile(boot, 0.025))
            high = float(np.quantile(boot, 0.975))
            out.append({
                "method": method,
                "metric": metric,
                "n_A": int(sum(1 for row in rows if row["method"] == method and row["group"] == "A")),
                "n_B": int(sum(1 for row in rows if row["method"] == method and row["group"] == "B")),
                "n_station_A": int(a.size),
                "n_station_B": int(b.size),
                "station_mean_A": float(np.mean(a)),
                "station_mean_B": float(np.mean(b)),
                "unadjusted_A_minus_B": estimate,
                "ci95_low": low,
                "ci95_high": high,
                "bootstrap_replicates": n_boot,
                "bootstrap_seed": BOOTSTRAP_SEED,
                "direction": direction(estimate),
                "zero_excluded": zero_excluded(low, high),
            })
    return out


def design(rows: list[dict[str, Any]]) -> tuple[np.ndarray, list[str]]:
    columns = ["intercept", "group_A"]
    cols = [np.ones(len(rows)), np.asarray([1.0 if row["group"] == "A" else 0.0 for row in rows])]
    for name in COVARIATES:
        values = np.asarray([f(row[name]) for row in rows], dtype=float)
        mean = np.nanmean(values)
        sd = np.nanstd(values)
        cols.append((values - mean) / (sd + 1e-12))
        columns.append(f"z_{name}")
    return np.column_stack(cols), columns


def fit_ols(rows: list[dict[str, Any]], metric: str) -> tuple[float, np.ndarray, list[str], dict[str, Any]]:
    y = np.asarray([f(row[metric]) for row in rows], dtype=float)
    x, columns = design(rows)
    keep = np.isfinite(y) & np.all(np.isfinite(x), axis=1)
    diag = {"n_rows": len(rows), "n_kept": int(keep.sum()), "n_parameters": int(x.shape[1]), "rank": "", "condition_number": ""}
    if keep.sum() <= x.shape[1]:
        return math.nan, np.full(x.shape[1], np.nan), columns, diag
    beta, *_ = np.linalg.lstsq(x[keep], y[keep], rcond=None)
    diag["rank"] = int(np.linalg.matrix_rank(x[keep]))
    diag["condition_number"] = float(np.linalg.cond(x[keep]))
    return float(beta[1]), beta, columns, diag


def regression_bootstrap(rows: list[dict[str, Any]], metric: str, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    by_group_station: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_group_station[(row["group"], row["station_noise"])].append(row)
    stations = {group: sorted(st for g, st in by_group_station if g == group) for group in ("A", "B")}
    draws = []
    for _ in range(BOOTSTRAP_REPLICATES):
        sample = []
        for group in ("A", "B"):
            picked = rng.choice(stations[group], size=len(stations[group]), replace=True)
            for station in picked:
                sample.extend(by_group_station[(group, str(station))])
        draws.append(fit_ols(sample, metric)[0])
    return np.asarray(draws, dtype=float)


def regression_results(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    results = []
    coeffs = []
    diagnostics = []
    for method in sorted({row["method"] for row in rows}):
        subset = [row for row in rows if row["method"] == method]
        for metric in METRICS:
            estimate, beta, columns, diag = fit_ols(subset, metric)
            seed = stable_seed(BOOTSTRAP_SEED, method, metric, "regression")
            boot = regression_bootstrap(subset, metric, seed)
            boot = boot[np.isfinite(boot)]
            low = float(np.quantile(boot, 0.025)) if boot.size else math.nan
            high = float(np.quantile(boot, 0.975)) if boot.size else math.nan
            results.append({
                "method": method,
                "metric": metric,
                "adjusted_A_minus_B": estimate,
                "ci95_low": low,
                "ci95_high": high,
                "bootstrap_replicates": BOOTSTRAP_REPLICATES,
                "bootstrap_seed": seed,
                "bootstrap_finite_replicates": int(boot.size),
                "direction": direction(estimate),
                "zero_excluded": zero_excluded(low, high),
                "model": "outcome ~ group_A + standardized_covariates",
                "covariates": ";".join(COVARIATES),
            })
            for name, value in zip(columns, beta):
                coeffs.append({"method": method, "metric": metric, "coefficient": name, "value": float(value)})
            diagnostics.append({
                "method": method,
                "metric": metric,
                **diag,
                "n_station_A": len({row["station_noise"] for row in subset if row["group"] == "A"}),
                "n_station_B": len({row["station_noise"] for row in subset if row["group"] == "B"}),
                "bootstrap_finite_replicates": int(boot.size),
            })
    return results, coeffs, diagnostics


def balance(rows: list[dict[str, Any]], stations: set[tuple[str, str]] | None = None) -> list[dict[str, Any]]:
    if stations is not None:
        rows = [row for row in rows if (row["group"], row["station_noise"]) in stations]
    out = []
    for cov in STATION_COVARIATES:
        a = finite([row[cov] for row in rows if row["group"] == "A"])
        b = finite([row[cov] for row in rows if row["group"] == "B"])
        pooled = math.sqrt(((a.var(ddof=1) if a.size > 1 else 0.0) + (b.var(ddof=1) if b.size > 1 else 0.0)) / 2.0)
        smd = float((a.mean() - b.mean()) / (pooled + 1e-12)) if a.size and b.size else math.nan
        out.append({
            "covariate": cov,
            "n_station_A": int(a.size),
            "n_station_B": int(b.size),
            "mean_A": float(a.mean()) if a.size else math.nan,
            "mean_B": float(b.mean()) if b.size else math.nan,
            "median_A": float(np.median(a)) if a.size else math.nan,
            "median_B": float(np.median(b)) if b.size else math.nan,
            "sd_A": float(a.std(ddof=1)) if a.size > 1 else 0.0,
            "sd_B": float(b.std(ddof=1)) if b.size > 1 else 0.0,
            "standardized_mean_difference_A_minus_B": smd,
        })
    return out


def standardized_vectors(rows: list[dict[str, Any]]) -> dict[tuple[str, str], np.ndarray]:
    values = {cov: np.asarray([f(row[cov]) for row in rows], dtype=float) for cov in STATION_COVARIATES}
    means = {cov: float(np.nanmean(arr)) for cov, arr in values.items()}
    sds = {cov: float(np.nanstd(arr)) + 1e-12 for cov, arr in values.items()}
    return {
        (row["group"], row["station_noise"]): np.asarray([(f(row[cov]) - means[cov]) / sds[cov] for cov in STATION_COVARIATES], dtype=float)
        for row in rows
    }


def match_stations(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    vecs = standardized_vectors(rows)
    a_keys = sorted(key for key in vecs if key[0] == "A")
    b_available = set(key for key in vecs if key[0] == "B")
    pairs = []
    for a_key in a_keys:
        candidates = []
        for b_key in b_available:
            dist = float(np.linalg.norm(vecs[a_key] - vecs[b_key]))
            candidates.append((dist, b_key))
        candidates.sort(key=lambda item: (item[0], item[1][1]))
        if candidates and candidates[0][0] <= MATCHING_CALIPER:
            dist, b_key = candidates[0]
            b_available.remove(b_key)
            pairs.append({
                "pair_id": len(pairs) + 1,
                "station_A": a_key[1],
                "station_B": b_key[1],
                "distance": dist,
                "caliper": MATCHING_CALIPER,
                "replacement": "false",
                "tie_break": "lowest_distance_then_station_name",
            })
    return pairs


def matched_results(rows: list[dict[str, Any]], pairs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for method in sorted({row["method"] for row in rows}):
        for metric in METRICS:
            means = station_means(rows, method, metric)
            diffs = []
            for pair in pairs:
                a = means.get(("A", pair["station_A"]))
                b = means.get(("B", pair["station_B"]))
                if a is not None and b is not None:
                    diffs.append(a - b)
            arr = np.asarray(diffs, dtype=float)
            if arr.size == 0:
                continue
            seed = stable_seed(BOOTSTRAP_SEED, method, metric, "matched")
            rng = np.random.default_rng(seed)
            boot = rng.choice(arr, size=(BOOTSTRAP_REPLICATES, arr.size), replace=True).mean(axis=1)
            estimate = float(arr.mean())
            low = float(np.quantile(boot, 0.025))
            high = float(np.quantile(boot, 0.975))
            out.append({
                "method": method,
                "metric": metric,
                "n_pairs": int(arr.size),
                "matched_A_minus_B": estimate,
                "ci95_low": low,
                "ci95_high": high,
                "bootstrap_replicates": BOOTSTRAP_REPLICATES,
                "bootstrap_seed": seed,
                "direction": direction(estimate),
                "zero_excluded": zero_excluded(low, high),
            })
    return out


def direction_audit(unadjusted: list[dict[str, Any]], regression: list[dict[str, Any]], matched: list[dict[str, Any]], n_pairs: int, n_a_stations: int) -> list[dict[str, Any]]:
    reg_lookup = {(row["method"], row["metric"]): row for row in regression}
    match_lookup = {(row["method"], row["metric"]): row for row in matched}
    out = []
    for row in unadjusted:
        key = (row["method"], row["metric"])
        reg = reg_lookup.get(key, {})
        mat = match_lookup.get(key, {})
        estimates = [f(row["unadjusted_A_minus_B"]), f(reg.get("adjusted_A_minus_B")), f(mat.get("matched_A_minus_B"))]
        dirs = [direction(value) for value in estimates if math.isfinite(value)]
        zeros = [row.get("zero_excluded"), reg.get("zero_excluded"), mat.get("zero_excluded")]
        direction_consistent = len(set(dirs)) == 1
        zero_exclusion_consistent = len(set(str(z).lower() for z in zeros if z != "")) == 1
        grade = "qualified_consistent"
        if not direction_consistent or n_pairs < 0.7 * n_a_stations:
            grade = "suggestive"
        out.append({
            "method": row["method"],
            "metric": row["metric"],
            "unadjusted_A_minus_B": row["unadjusted_A_minus_B"],
            "unadjusted_ci95_low": row["ci95_low"],
            "unadjusted_ci95_high": row["ci95_high"],
            "regression_adjusted_A_minus_B": reg.get("adjusted_A_minus_B", ""),
            "regression_ci95_low": reg.get("ci95_low", ""),
            "regression_ci95_high": reg.get("ci95_high", ""),
            "matched_A_minus_B": mat.get("matched_A_minus_B", ""),
            "matched_ci95_low": mat.get("ci95_low", ""),
            "matched_ci95_high": mat.get("ci95_high", ""),
            "unadjusted_direction": direction(f(row["unadjusted_A_minus_B"])),
            "regression_direction": direction(f(reg.get("adjusted_A_minus_B"))),
            "matched_direction": direction(f(mat.get("matched_A_minus_B"))),
            "direction_consistent": direction_consistent,
            "zero_exclusion_consistent": zero_exclusion_consistent,
            "interpretation_grade": grade,
        })
    return out


def write_tables(table_dir: Path, balance_rows: list[dict[str, Any]], regression: list[dict[str, Any]], matched: list[dict[str, Any]], pairs: list[dict[str, Any]], direction_rows: list[dict[str, Any]]) -> None:
    table_dir.mkdir(parents=True, exist_ok=True)

    balance_lines = [r"\begin{tabular}{lrrrrrrr}", r"\toprule", r"Covariate & Pre mean A & Pre mean B & Pre med. A & Pre med. B & Pre SMD & Post SMD & Pairs \\", r"\midrule"]
    for row in balance_rows:
        balance_lines.append(
            f"{tex_escape(row['covariate'])} & {f(row['mean_A_before']):.3g} & {f(row['mean_B_before']):.3g} & "
            f"{f(row['median_A_before']):.3g} & {f(row['median_B_before']):.3g} & {fmt(row['before_smd'])} & "
            f"{fmt(row['after_smd'])} & {row['n_pairs_after']} \\\\"
        )
    balance_lines += [r"\bottomrule", r"\end{tabular}"]
    (table_dir / "e3_no_taper_balance_before_after_table.tex").write_text("\n".join(balance_lines) + "\n", encoding="utf-8")

    compact_balance = [{"covariate": row["covariate"], "before_smd": row["before_smd"], "after_smd": row["after_smd"], "n_pairs_after": row["n_pairs_after"]} for row in balance_rows]
    write_csv(table_dir / "e3_no_taper_confounding_balance_table.csv", compact_balance)
    compact_lines = ["% Generated by rebuild_e3_no_taper_confounding_closure.py"]
    for row in compact_balance:
        compact_lines.append(f"{row['covariate']} & {float(row['before_smd']):+.3f} & {float(row['after_smd']):+.3f} & {row['n_pairs_after']} \\\\")
    (table_dir / "e3_no_taper_confounding_balance_table.tex").write_text("\n".join(compact_lines) + "\n", encoding="utf-8")

    reg_lines = [r"\begin{tabular}{llllr}", r"\toprule", r"Method & Metric & Adjusted A--B & 95\% CI & Excludes 0 \\", r"\midrule"]
    for row in regression:
        reg_lines.append(f"{tex_escape(row['method'])} & {tex_escape(row['metric'])} & {fmt(row['adjusted_A_minus_B'])} & {interval(row)} & {str(row['zero_excluded']).lower()} \\\\")
    reg_lines += [r"\bottomrule", r"\end{tabular}"]
    (table_dir / "e3_no_taper_regression_adjusted_table.tex").write_text("\n".join(reg_lines) + "\n", encoding="utf-8")

    matched_lines = [r"\begin{tabular}{llllrr}", r"\toprule", r"Method & Metric & Matched A--B & 95\% CI & Pairs & Excludes 0 \\", r"\midrule"]
    for row in matched:
        matched_lines.append(f"{tex_escape(row['method'])} & {tex_escape(row['metric'])} & {fmt(row['matched_A_minus_B'])} & {interval(row)} & {row['n_pairs']} & {str(row['zero_excluded']).lower()} \\\\")
    matched_lines += [r"\bottomrule", r"\end{tabular}"]
    (table_dir / "e3_no_taper_matched_table.tex").write_text("\n".join(matched_lines) + "\n", encoding="utf-8")

    pair_lines = [r"\begin{tabular}{rllr}", r"\toprule", r"Pair & A station & B station & Distance \\", r"\midrule"]
    for idx, row in enumerate(pairs, 1):
        pair_lines.append(f"{idx} & {tex_escape(row['station_A'])} & {tex_escape(row['station_B'])} & {f(row['distance']):.3f} \\\\")
    pair_lines += [r"\bottomrule", r"\end{tabular}"]
    (table_dir / "e3_no_taper_matching_pairs_table.tex").write_text("\n".join(pair_lines) + "\n", encoding="utf-8")

    direction_lines = [r"\begin{tabular}{llllll}", r"\toprule", r"Method & Metric & Unadjusted & Adjusted & Matched & Grade \\", r"\midrule"]
    for row in direction_rows:
        direction_lines.append(
            f"{tex_escape(row['method'])} & {tex_escape(row['metric'])} & {row['unadjusted_direction']} & "
            f"{row['regression_direction']} & {row['matched_direction']} & {tex_escape(row['interpretation_grade'])} \\\\"
        )
    direction_lines += [r"\bottomrule", r"\end{tabular}"]
    (table_dir / "e3_no_taper_direction_audit_table.tex").write_text("\n".join(direction_lines) + "\n", encoding="utf-8")

    summary = []
    for metric in METRICS:
        metric_rows = [row for row in direction_rows if row["metric"] == metric]
        summary.append({
            "metric": metric,
            "n_rows": len(metric_rows),
            "direction_consistent": sum(str(row["direction_consistent"]).lower() == "true" for row in metric_rows),
            "zero_exclusion_consistent": sum(str(row["zero_exclusion_consistent"]).lower() == "true" for row in metric_rows),
        })
    write_csv(table_dir / "e3_no_taper_direction_summary.csv", summary)


def recompute(package_root: Path, output_dir: Path) -> None:
    package_root = package_root.resolve()
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    outcome_rows = load_outcomes(package_root)
    station_rows = read_csv(package_root / "e3_no_taper_confounding_closure" / "data" / "e3_no_taper_station_covariates.csv")
    unadjusted = unadjusted_results(outcome_rows)
    regression, coeffs, diagnostics = regression_results(outcome_rows)
    before = balance(station_rows)
    pairs = match_stations(station_rows)
    matched_station_set = {("A", p["station_A"]) for p in pairs} | {("B", p["station_B"]) for p in pairs}
    after = balance(station_rows, matched_station_set)
    after_lookup = {row["covariate"]: row for row in after}
    balance_joined = []
    for row in before:
        aft = after_lookup[row["covariate"]]
        before_smd = f(row["standardized_mean_difference_A_minus_B"])
        after_smd = f(aft["standardized_mean_difference_A_minus_B"])
        balance_joined.append({
            "covariate": row["covariate"],
            "mean_A_before": row["mean_A"],
            "mean_B_before": row["mean_B"],
            "median_A_before": row["median_A"],
            "median_B_before": row["median_B"],
            "before_smd": before_smd,
            "mean_A_after": aft["mean_A"],
            "mean_B_after": aft["mean_B"],
            "median_A_after": aft["median_A"],
            "median_B_after": aft["median_B"],
            "after_smd": after_smd,
            "absolute_smd_reduction": abs(before_smd) - abs(after_smd),
            "residual_absolute_smd": abs(after_smd),
            "n_station_A_before": row["n_station_A"],
            "n_station_B_before": row["n_station_B"],
            "n_station_A_after": aft["n_station_A"],
            "n_station_B_after": aft["n_station_B"],
            "n_pairs_after": len(pairs),
        })
    matched = matched_results(outcome_rows, pairs)
    direction_rows = direction_audit(unadjusted, regression, matched, len(pairs), len({r["station_noise"] for r in station_rows if r["group"] == "A"}))

    results = output_dir / "results"
    tables = output_dir / "tables"
    write_csv(results / "e3_unadjusted_results.csv", unadjusted)
    write_csv(results / "e3_regression_adjusted_results.csv", regression)
    write_csv(results / "e3_matched_results.csv", matched)
    write_csv(results / "e3_balance_before_after.csv", balance_joined)
    write_csv(results / "e3_matching_pairs.csv", pairs)
    write_csv(results / "e3_model_coefficients.csv", coeffs)
    write_csv(results / "e3_model_diagnostics.csv", diagnostics)
    write_csv(results / "e3_direction_and_zero_exclusion_audit.csv", direction_rows)
    write_tables(tables, balance_joined, regression, matched, pairs, direction_rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-root", required=True, help="Path to extracted seismic-denoising-eval-protocol_v1.0.5 package root")
    parser.add_argument("--output-dir", required=True, help="Temporary output directory for recomputed CSV/TEX files")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    package_root = Path(args.package_root)
    output_dir = Path(args.output_dir)
    if not (package_root / "source_metrics" / "e3_detail_wide.csv").exists():
        raise SystemExit(f"Missing package source metrics under {package_root}")
    recompute(package_root, output_dir)
    print(f"PASS: recomputed E3 adjustment artifacts under {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
