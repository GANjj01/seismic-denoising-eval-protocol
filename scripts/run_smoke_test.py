from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from blindspot_eval_protocol.report_card import main as report_card_main


def main() -> int:
    input_csv = ROOT / "per_case_metrics" / "oracle_free_816_all_methods.csv"
    output_csv = ROOT / "smoke_outputs" / "oracle_free_report_card_smoke.csv"
    return report_card_main(["--input", str(input_csv), "--output", str(output_csv)])


if __name__ == "__main__":
    raise SystemExit(main())
