"""Rebuild manuscript Table 10 and Table 12 fragments from released CSVs."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


METHOD_LABELS = {
    "Noisy": "Noisy",
    "Bandpass": "Band-pass",
    "DeepDenoiser": "DeepDenoiser",
    "Wiener_blind": "Wiener-blind",
    "Wiener_oracle": "Idealized Wiener",
    "p0_e06": r"$\lpol=0$",
    "p01_e07": r"$\lpol=0.1$",
    "p05_e16": r"$\lpol=0.5$",
}
ORDER = ["Noisy", "Bandpass", "DeepDenoiser", "Wiener_blind", "Wiener_oracle", "p0_e06", "p01_e07", "p05_e16"]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def signed(value: float, digits: int = 3) -> str:
    return f"{value:+.{digits}f}"


def ci(row: dict[str, str]) -> str:
    return f"{signed(float(row['station_leakage_gain_A_minus_B']))} [{signed(float(row['ci95_low']))}, {signed(float(row['ci95_high']))}]"


def build_table10(root: Path, out_dir: Path) -> Path:
    rows = read_csv(root / "tables" / "e3_reconstructed_no_taper_table.csv")
    keyed = {(r["method"], r["metric"]): r for r in rows}
    lines = [
        r"\begin{tabular}{lcc}",
        r"\toprule",
        r"Method & Clean-SNR A--B (dB) & Background suppression A--B (dB) \\",
        r"\midrule",
    ]
    for method in ORDER:
        clean = ci(keyed[(method, "output_vs_clean_snr")])
        bg = ci(keyed[(method, "background_suppression_db")])
        lines.append(f"{METHOD_LABELS[method]} & {clean} & {bg} \\\\")
    lines.extend([r"\bottomrule", r"\end{tabular}"])
    out = out_dir / "table10_e3_reconstructed_no_taper.tex"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out


def build_table12(root: Path, out_dir: Path) -> Path:
    rows = read_csv(root / "tables" / "e5_reconstructed_no_taper_table.csv")
    lines = [
        r"\begin{tabular}{rrrrrr}",
        r"\toprule",
        r"Seed & $\lambda=0$ epoch & $\lambda=0.5$ epoch & $\Delta$ clean-SNR & $\Delta$ amp. ratio & $\Delta$ corr. \\",
        r"\midrule",
    ]
    for row in rows:
        lines.append(
            f"{row['seed']} & {row['lambda0_epoch']} & {row['lambda05_epoch']} & "
            f"{signed(float(row['clean_snr_db_delta_lambda05_minus_lambda0']))} & "
            f"{signed(float(row['amp_ratio_delta_lambda05_minus_lambda0']))} & "
            f"{signed(float(row['corr_z_delta_lambda05_minus_lambda0']))} \\\\"
        )
    lines.extend([r"\bottomrule", r"\end{tabular}"])
    out = out_dir / "table12_e5_reconstructed_no_taper.tex"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".", help="Release-candidate root")
    parser.add_argument("--out", default="generated_tables", help="Output directory relative to root")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    out_dir = (root / args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    table10 = build_table10(root, out_dir)
    table12 = build_table12(root, out_dir)
    print(f"wrote {table10.relative_to(root)}")
    print(f"wrote {table12.relative_to(root)}")


if __name__ == "__main__":
    main()
