"""Dependency-light report-card summarizer.

Input is a per-case CSV with the columns produced by the oracle-free evaluator:
case_id, station_template, method, output_vs_clean_snr, corr_z,
amp_ratio_clean, and background_suppression_db.  If a Noisy or Identity row is
present for each case, clean-SNR gain is computed relative to that row.
"""

from __future__ import annotations

import argparse
import csv
import statistics
from collections import defaultdict
from pathlib import Path


REQUIRED = {
    "case_id",
    "station_template",
    "method",
    "output_vs_clean_snr",
    "corr_z",
    "amp_ratio_clean",
    "background_suppression_db",
}


def _float(row: dict[str, str], key: str) -> float:
    value = row.get(key, "")
    return float(value) if value not in ("", None) else float("nan")


def summarize(rows: list[dict[str, str]], baseline_methods: tuple[str, ...] = ("Noisy", "Identity")) -> list[dict[str, object]]:
    by_case: dict[str, dict[str, dict[str, str]]] = defaultdict(dict)
    for row in rows:
        by_case[row["case_id"]][row["method"]] = row

    methods = sorted({row["method"] for row in rows})
    out = []
    for method in methods:
        if method in baseline_methods:
            continue
        snr_gains = []
        corr = []
        amp = []
        bg = []
        stations = set()
        for case_id, case_rows in by_case.items():
            if method not in case_rows:
                continue
            baseline = next((case_rows[b] for b in baseline_methods if b in case_rows), None)
            if baseline is None:
                continue
            row = case_rows[method]
            snr_gains.append(_float(row, "output_vs_clean_snr") - _float(baseline, "output_vs_clean_snr"))
            corr.append(_float(row, "corr_z"))
            amp.append(_float(row, "amp_ratio_clean"))
            bg.append(_float(row, "background_suppression_db"))
            stations.add(row["station_template"])
        if snr_gains:
            out.append({
                "method": method,
                "n_cases": len(snr_gains),
                "n_stations": len(stations),
                "clean_snr_gain_mean": statistics.fmean(snr_gains),
                "corr_z_mean": statistics.fmean(corr),
                "amp_ratio_median": statistics.median(amp),
                "background_suppression_mean": statistics.fmean(bg),
            })
    return out


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        missing = REQUIRED.difference(reader.fieldnames or [])
        if missing:
            raise SystemExit(f"Missing required columns: {sorted(missing)}")
        return list(reader)


def write_rows(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise SystemExit("No report-card rows were produced")
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="Per-case oracle-free metrics CSV")
    parser.add_argument("--output", required=True, type=Path, help="Summary report-card CSV")
    args = parser.parse_args(argv)
    rows = summarize(read_rows(args.input))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_rows(args.output, rows)
    print(f"wrote {args.output} ({len(rows)} methods)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
