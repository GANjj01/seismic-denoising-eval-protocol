"""Validate the v1.0.4-rc3 E3/E5 release-candidate archive."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def assert_equal(label: str, got, expected, errors: list[str]) -> None:
    if got != expected:
        errors.append(f"{label}: expected {expected!r}, got {got!r}")


def assert_close(label: str, got: float, expected: float, tol: float, errors: list[str]) -> None:
    if abs(got - expected) > tol:
        errors.append(f"{label}: expected {expected}, got {got}")


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    errors: list[str] = []

    forbidden = ["C:\\Users\\Administrator", "D:\\anacona", "Documents\\seismic denoiser", "Desktop\\transformer_train"]
    scanned = []
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in {".md", ".csv", ".json", ".yml", ".yaml", ".ps1", ".sh", ".py", ".txt", ".tex"}:
            text = path.read_text(encoding="utf-8", errors="replace")
            scanned.append(str(path.relative_to(root)))
            for marker in forbidden:
                if marker in text:
                    errors.append(f"path pollution: {path.relative_to(root)} contains {marker}")

    banned_phrases = [
        "Wiener-oracle",
        "Wiener oracle",
        "oracle Wiener",
        "principal non-oracle",
        "non-oracle",
        "non-oracle methods",
        "non-oracle interpretation",
    ]
    allowlisted_fragments = [
        "release_sync/ORACLE_TERMINOLOGY_OCCURRENCE_MAP.md",
        "release_sync/ORACLE_TERMINOLOGY_CLEANUP.md",
        "release_sync/VERIFIER_BANNED_TERM_POLICY.md",
        "release_sync/TERMINOLOGY_AUDIT.md",
        "release_sync/PRE_RELEASE_PATCH_CHANGELOG.md",
        "scripts/verify_release_artifacts.py",
    ]
    terminology_hits = []
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in {".md", ".txt", ".tex", ".py", ".yml", ".yaml", ".json"}:
            continue
        rel = path.relative_to(root).as_posix()
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        for lineno, line in enumerate(lines, start=1):
            low = line.lower()
            for phrase in banned_phrases:
                if phrase.lower() in low:
                    allowlisted = any(rel == item for item in allowlisted_fragments)
                    status = "allowlisted" if allowlisted else "forbidden"
                    terminology_hits.append({
                        "file": rel,
                        "line": lineno,
                        "matched_phrase": phrase,
                        "status": status,
                    })
                    if not allowlisted:
                        errors.append(f"forbidden terminology: {rel}:{lineno}: {phrase}")

    e3_manifest = read_csv(root / "manifests" / "e3_no_taper_manifest.csv")
    e5_manifest = read_csv(root / "manifests" / "e5_no_taper_manifest.csv")
    assert_equal("E3 manifest rows", len(e3_manifest), 13056, errors)
    assert_equal("E5 manifest rows", len(e5_manifest), 8160, errors)
    assert_equal("E3 unique cases", len({r["case_id"] for r in e3_manifest}), 1632, errors)
    assert_equal("E5 unique cases", len({r["case_id"] for r in e5_manifest}), 816, errors)
    assert_equal("E3 failures", sum(1 for r in e3_manifest if r.get("failure")), 0, errors)
    assert_equal("E5 failures", sum(1 for r in e5_manifest if r.get("failure")), 0, errors)
    assert_equal("E3 no taper", {r["taper_applied"] for r in e3_manifest}, {"false"}, errors)
    assert_equal("E5 no taper", {r["taper_applied"] for r in e5_manifest}, {"false"}, errors)

    e3_metrics = read_csv(root / "metrics" / "e3_per_case_metrics.csv")
    e5_metrics = read_csv(root / "metrics" / "e5_per_case_metrics.csv")
    assert_equal("E3 metric rows", len(e3_metrics), 65280, errors)
    assert_equal("E5 metric rows", len(e5_metrics), 40800, errors)

    e3_table = read_csv(root / "tables" / "e3_reconstructed_no_taper_table.csv")
    e5_table = read_csv(root / "tables" / "e5_reconstructed_no_taper_table.csv")
    assert_equal("E3 table rows", len(e3_table), 32, errors)
    assert_equal("E5 table rows", len(e5_table), 3, errors)
    for row in e3_table:
        if row["method"] == "DeepDenoiser" and row["metric"] == "output_vs_clean_snr":
            assert_close("E3 DeepDenoiser clean-SNR", float(row["station_leakage_gain_A_minus_B"]), 0.5733203596061571, 1e-12, errors)
        if row["method"] == "Wiener_blind" and row["metric"] == "output_vs_clean_snr":
            assert_close("E3 Wiener-blind clean-SNR", float(row["station_leakage_gain_A_minus_B"]), 0.5580491799099447, 1e-12, errors)
    for row in e5_table:
        if row["seed"] == "42":
            assert_close("E5 seed42 clean-SNR delta", float(row["clean_snr_db_delta_lambda05_minus_lambda0"]), -0.4622854147687133, 1e-12, errors)
            assert_close("E5 seed42 amp delta", float(row["amp_ratio_delta_lambda05_minus_lambda0"]), 0.439289768692106, 1e-12, errors)
            assert_close("E5 seed42 corr delta", float(row["corr_z_delta_lambda05_minus_lambda0"]), 0.02533947298366951, 1e-12, errors)

    rebuild_dir = root / "_validation_rebuild"
    rebuild_dir.mkdir(exist_ok=True)
    subprocess.run([sys.executable, str(root / "scripts" / "rebuild_e3_e5_tables.py"), "--root", str(root), "--out", "_validation_rebuild"], check=True)
    for name in ["table10_e3_reconstructed_no_taper.tex", "table12_e5_reconstructed_no_taper.tex"]:
        expected = (root / "manuscript" / "generated_tables" / name).read_text(encoding="utf-8").strip()
        got = (rebuild_dir / name).read_text(encoding="utf-8").strip()
        if got != expected:
            errors.append(f"rebuilt fragment mismatch: {name}")
    table10_text = (root / "manuscript" / "generated_tables" / "table10_e3_reconstructed_no_taper.tex").read_text(encoding="utf-8")
    legacy_label = "Wiener" + "-oracle"
    if legacy_label in table10_text:
        errors.append("Table 10 fragment still contains the legacy oracle-Wiener display label")
    if "Idealized Wiener" not in table10_text:
        errors.append("Table 10 fragment is missing Idealized Wiener")
    readme = (root / "README.md").read_text(encoding="utf-8")
    if "source-aware sensitivity diagnostic" not in readme:
        errors.append("README missing Idealized Wiener source-aware role note")
    if "unprocessed-input sanity control" not in readme:
        errors.append("README missing Noisy sanity-control note")
    if (root / "tables" / "table10_reconstructed_no_taper_candidate.tex").exists():
        errors.append("misnamed table10_reconstructed_no_taper_candidate.tex is present")
    candidate = (root / "MANUSCRIPT_RELEASE_UPDATE_CANDIDATE.md").read_text(encoding="utf-8")
    if "supports, but does not prove" not in candidate:
        errors.append("release-update candidate missing support-not-proof wording")

    checksums = root / "PUBLIC_SHA256SUMS.txt"
    if checksums.exists():
        for line in checksums.read_text(encoding="utf-8-sig").splitlines():
            if not line.strip() or line.startswith("#"):
                continue
            digest, rel = line.split(None, 1)
            rel = rel.strip()
            if rel == "PUBLIC_SHA256SUMS.txt":
                continue
            path = root / rel
            if not path.exists():
                errors.append(f"checksum target missing: {rel}")
            elif sha256_file(path) != digest:
                errors.append(f"checksum mismatch: {rel}")

    report = {
        "status": "pass" if not errors else "fail",
        "errors": errors,
        "scanned_text_files": len(scanned),
        "terminology_hits": terminology_hits,
        "current_public_forbidden_terminology_hits": sum(1 for item in terminology_hits if item["status"] == "forbidden"),
        "historical_allowlisted_terminology_hits": sum(1 for item in terminology_hits if item["status"] == "allowlisted"),
        "e3_manifest_rows": len(e3_manifest),
        "e5_manifest_rows": len(e5_manifest),
        "e3_unique_cases": len({r["case_id"] for r in e3_manifest}),
        "e5_unique_cases": len({r["case_id"] for r in e5_manifest}),
    }
    (root / "RC3_VALIDATION_REPORT.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
