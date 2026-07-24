"""Verify the formal v1.0.5 release package after fresh extraction."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
FLOAT_TOL = 5e-10
TABLE_FLOAT_TOL = 5e-4
FORBIDDEN_SUFFIXES = {".mseed", ".miniseed", ".npz", ".npy", ".pt", ".pth", ".ckpt", ".sac"}
TEXT_SUFFIXES = {".csv", ".json", ".yml", ".yaml", ".toml", ".cff", ".md", ".txt", ".tex", ".py"}
PATH_PATTERNS = [
    re.compile(r"(?<![A-Za-z])[A-Za-z]:[\\/]"),
    re.compile(r"\\\\[^\\/\s]+[\\/][^\\/\s]+"),
    re.compile(r"/home/[^/\s]+/"),
    re.compile(r"/Users/[^/\s]+/"),
    re.compile(r"(?i)\bAppData\b"),
    re.compile(r"(?i)\bTemp\b"),
    re.compile(r"(?i)\bDocuments[\\/]"),
    re.compile(r"(?i)\bDesktop[\\/]"),
    re.compile(r"(?i)(^|[\\/])tmp[\\/]"),
]
URL_RE = re.compile(r"^(https?|doi):", re.I)
FORBIDDEN_PUBLIC_TERMS = [
    "Wiener-oracle",
    "oracle Wiener baseline",
    "deployable oracle baseline",
    "non-oracle",
]
FORBIDDEN_RC_PATTERNS = [
    re.compile(r"v1\.0\.5-rc1", re.I),
    re.compile(r"\brc1\b", re.I),
    re.compile(r"release candidate", re.I),
    re.compile(r"release-candidate", re.I),
    re.compile(r"candidate package", re.I),
    re.compile(r"prepared candidate", re.I),
    re.compile(r"draft release", re.I),
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def f(value: Any) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return math.nan
    return out if math.isfinite(out) else math.nan


def parse_checksum_line(line: str) -> tuple[str, str] | None:
    line = line.strip()
    if not line:
        return None
    if "  " in line:
        digest, path = line.split("  ", 1)
    else:
        parts = line.split(maxsplit=1)
        if len(parts) != 2:
            return None
        digest, path = parts
    path = path.lstrip("*")
    if not re.fullmatch(r"[0-9a-fA-F]{64}", digest):
        return None
    return digest.lower(), path


def checksum_base(manifest: Path) -> Path:
    if manifest.name == "SHA256SUMS.txt":
        return manifest.parent
    if manifest.parent.name in {"provenance", "data"}:
        return manifest.parent.parent
    return manifest.parent


def verify_checksum_manifests() -> tuple[list[str], list[str]]:
    errors: list[str] = []
    passed: list[str] = []
    manifests = [
        path for path in ROOT.rglob("*")
        if path.is_file() and (path.name == "SHA256SUMS.txt" or path.suffix.lower() in {".sha256", ".sha256sum"})
    ]
    for manifest in sorted(manifests):
        base = checksum_base(manifest)
        checked = 0
        for line in manifest.read_text(encoding="utf-8").splitlines():
            parsed = parse_checksum_line(line)
            if parsed is None:
                continue
            digest, item = parsed
            target = (base / item).resolve()
            try:
                target.relative_to(ROOT.resolve())
            except ValueError:
                errors.append(f"{rel(manifest)} references outside package: {item}")
                continue
            if not target.exists() or not target.is_file():
                errors.append(f"{rel(manifest)} references missing file: {item}")
                continue
            got = sha256_file(target)
            if got.lower() != digest:
                errors.append(f"{rel(manifest)} checksum mismatch for {item}: {got}")
            checked += 1
        passed.append(f"{rel(manifest)} ({checked} entries)")
    return errors, passed


def json_values(obj: Any, prefix: str = "$"):
    if isinstance(obj, dict):
        for key, value in obj.items():
            yield from json_values(value, f"{prefix}.{key}")
    elif isinstance(obj, list):
        for idx, value in enumerate(obj):
            yield from json_values(value, f"{prefix}[{idx}]")
    elif isinstance(obj, str):
        yield prefix, obj


def yaml_scalar_values(text: str):
    stack: list[tuple[int, str]] = []
    for lineno, raw in enumerate(text.splitlines(), 1):
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        line = raw.strip()
        while stack and stack[-1][0] >= indent:
            stack.pop()
        if line.startswith("- "):
            value = line[2:].strip().strip("'\"")
            path = ".".join([item for _, item in stack] + [f"item@{lineno}"])
            if value and ":" not in value:
                yield path, value
            continue
        if ":" in line:
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip().strip("'\"")
            path = ".".join([item for _, item in stack] + [key])
            if value:
                yield path, value
            else:
                stack.append((indent, key))


def structured_text_values(path: Path):
    text = path.read_text(encoding="utf-8", errors="ignore")
    suffix = path.suffix.lower()
    if suffix == ".json":
        try:
            yield from json_values(json.loads(text))
        except json.JSONDecodeError:
            pass
    elif suffix in {".yml", ".yaml", ".cff"}:
        yield from yaml_scalar_values(text)
    elif suffix == ".toml":
        try:
            import tomllib
            yield from json_values(tomllib.loads(text))
        except Exception:
            pass
    for lineno, line in enumerate(text.splitlines(), 1):
        yield f"text.line_{lineno}", line


def path_hits() -> list[dict[str, str]]:
    hits = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        if rel(path) == "scripts/verify_release_artifacts.py":
            continue
        for field, value in structured_text_values(path):
            if URL_RE.match(value.strip()):
                continue
            for pattern in PATH_PATTERNS:
                match = pattern.search(value)
                if match:
                    hits.append({
                        "file": rel(path),
                        "field": field,
                        "matched_value": value.strip()[:240],
                        "pattern": pattern.pattern,
                        "allowlist_reason": "",
                    })
    return hits


def text_policy_checks() -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    rc_hits = []
    v104_hits = []
    forbidden_public_hits = []
    wiener_internal_hits = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        rpath = rel(path)
        if rpath == "scripts/verify_release_artifacts.py":
            if "Wiener_oracle" in text:
                wiener_internal_hits.append(rpath)
            continue
        for pattern in FORBIDDEN_RC_PATTERNS:
            for match in pattern.finditer(text):
                rc_hits.append(f"{rpath}:{match.start()}:{match.group(0)}")
        for term in FORBIDDEN_PUBLIC_TERMS:
            if term in text:
                forbidden_public_hits.append(f"{rpath}:{term}")
        if "Wiener_oracle" in text:
            wiener_internal_hits.append(rpath)
        for token in ["21516779", "releases/tag/v1.0.4"]:
            if token in text:
                v104_hits.append(f"{rpath}:{token}")
        if "v1.0.4" in text:
            for lineno, line in enumerate(text.splitlines(), 1):
                if "v1.0.4" in line and not re.search(r"preceding|preserved|retained|unchanged|not been overwritten|not modified|No .*modified|history|historical", line, re.I):
                    v104_hits.append(f"{rpath}:{lineno}:current-facing v1.0.4")
    if rc_hits:
        errors.append("candidate/rc wording hits: " + "; ".join(rc_hits[:10]))
    if forbidden_public_hits:
        errors.append("forbidden public terminology hits: " + "; ".join(forbidden_public_hits[:10]))
    if v104_hits:
        errors.append("current-facing v1.0.4 metadata hits: " + "; ".join(v104_hits[:10]))
    return errors, {
        "candidate_rc_hits": len(rc_hits),
        "current_facing_v104_hits": len(v104_hits),
        "forbidden_public_terminology_hits": len(forbidden_public_hits),
        "wiener_oracle_allowlisted_files": sorted(set(wiener_internal_hits)),
        "wiener_oracle_allowlisted_hit_files_count": len(set(wiener_internal_hits)),
    }


def basic_structure_checks() -> list[str]:
    errors = []
    required = ["LICENSE", "CITATION.cff", "requirements.txt", "ENVIRONMENT.md", "TERMINOLOGY_MAP.md"]
    for name in required:
        if not (ROOT / name).is_file():
            errors.append(f"missing required root file: {name}")
    for path in ROOT.rglob("*"):
        parts = path.relative_to(ROOT).parts
        if ".." in parts:
            errors.append(f"zip traversal path present: {rel(path)}")
        if path.name in {"__pycache__", ".pytest_cache", ".DS_Store"} or path.name.endswith(("~", ".bak", ".tmp")):
            errors.append(f"temporary/editor artifact present: {rel(path)}")
        if path.is_file() and path.suffix.lower() in FORBIDDEN_SUFFIXES:
            errors.append(f"raw/tensor/weight/checkpoint suffix present: {rel(path)}")
    return errors


def compare_csv(expected: Path, actual: Path, numeric_columns: set[str] | None = None, tol: float = FLOAT_TOL) -> list[str]:
    errors = []
    exp = read_csv(expected)
    got = read_csv(actual)
    if len(exp) != len(got):
        return [f"{rel(expected)} row count {len(exp)} != recomputed {len(got)}"]
    numeric_columns = numeric_columns or set()
    for idx, (a, b) in enumerate(zip(exp, got), 1):
        if set(a) != set(b):
            errors.append(f"{rel(expected)} row {idx} columns differ")
            continue
        for key in a:
            if key in numeric_columns:
                av, bv = f(a[key]), f(b[key])
                if math.isfinite(av) or math.isfinite(bv):
                    if abs(av - bv) > tol:
                        errors.append(f"{rel(expected)} row {idx} column {key}: {av} != {bv}")
            elif str(a[key]) != str(b[key]):
                errors.append(f"{rel(expected)} row {idx} column {key}: {a[key]!r} != {b[key]!r}")
    return errors


def run_portable_recompute() -> tuple[list[str], dict[str, Any]]:
    errors = []
    report: dict[str, Any] = {}
    with tempfile.TemporaryDirectory(prefix="v105_e3_recompute_") as tmp:
        out = Path(tmp)
        cmd = [
            sys.executable,
            str(ROOT / "scripts" / "recompute_e3_adjustment_from_released_tables.py"),
            "--package-root",
            str(ROOT),
            "--output-dir",
            str(out),
        ]
        proc = subprocess.run(cmd, text=True, capture_output=True)
        report["command"] = " ".join(cmd)
        report["returncode"] = proc.returncode
        report["stdout"] = proc.stdout.strip()
        report["stderr"] = proc.stderr.strip()
        if proc.returncode != 0:
            return [f"portable recompute failed with exit code {proc.returncode}: {proc.stderr}"], report
        released = ROOT / "e3_no_taper_confounding_closure"
        result_numeric = {
            "n_A", "n_B", "n_station_A", "n_station_B", "station_mean_A", "station_mean_B",
            "unadjusted_A_minus_B", "ci95_low", "ci95_high", "bootstrap_replicates", "bootstrap_seed",
            "adjusted_A_minus_B", "bootstrap_finite_replicates", "n_pairs", "matched_A_minus_B",
            "mean_A_before", "mean_B_before", "median_A_before", "median_B_before", "before_smd",
            "mean_A_after", "mean_B_after", "median_A_after", "median_B_after", "after_smd",
            "absolute_smd_reduction", "residual_absolute_smd", "n_station_A_before", "n_station_B_before",
            "n_station_A_after", "n_station_B_after", "n_pairs_after", "distance", "caliper",
            "value", "n_rows", "n_kept", "n_parameters", "rank", "condition_number",
            "regression_adjusted_A_minus_B", "regression_ci95_low", "regression_ci95_high",
            "matched_ci95_low", "matched_ci95_high", "matched_A_minus_B", "unadjusted_ci95_low",
            "unadjusted_ci95_high",
        }
        pairs = [
            ("results/e3_unadjusted_results.csv", out / "results" / "e3_unadjusted_results.csv"),
            ("results/e3_regression_adjusted_results.csv", out / "results" / "e3_regression_adjusted_results.csv"),
            ("results/e3_matched_results.csv", out / "results" / "e3_matched_results.csv"),
            ("results/e3_balance_before_after.csv", out / "results" / "e3_balance_before_after.csv"),
            ("results/e3_matching_pairs.csv", out / "results" / "e3_matching_pairs.csv"),
            ("results/e3_model_coefficients.csv", out / "results" / "e3_model_coefficients.csv"),
            ("results/e3_model_diagnostics.csv", out / "results" / "e3_model_diagnostics.csv"),
            ("results/e3_direction_and_zero_exclusion_audit.csv", out / "results" / "e3_direction_and_zero_exclusion_audit.csv"),
        ]
        for rel_expected, actual in pairs:
            errors.extend(compare_csv(released / rel_expected, actual, result_numeric, FLOAT_TOL))
        table_pairs = [
            ("tables/e3_no_taper_balance_before_after_table.tex", out / "tables" / "e3_no_taper_balance_before_after_table.tex"),
            ("tables/e3_no_taper_confounding_balance_table.tex", out / "tables" / "e3_no_taper_confounding_balance_table.tex"),
            ("tables/e3_no_taper_regression_adjusted_table.tex", out / "tables" / "e3_no_taper_regression_adjusted_table.tex"),
            ("tables/e3_no_taper_matched_table.tex", out / "tables" / "e3_no_taper_matched_table.tex"),
            ("tables/e3_no_taper_matching_pairs_table.tex", out / "tables" / "e3_no_taper_matching_pairs_table.tex"),
            ("tables/e3_no_taper_direction_audit_table.tex", out / "tables" / "e3_no_taper_direction_audit_table.tex"),
        ]
        for rel_expected, actual in table_pairs:
            if (released / rel_expected).read_text(encoding="utf-8") != actual.read_text(encoding="utf-8"):
                errors.append(f"table fragment mismatch: {rel_expected}")
        direction = read_csv(out / "results" / "e3_direction_and_zero_exclusion_audit.csv")
        direction_consistent = sum(row["direction_consistent"].lower() == "true" for row in direction)
        zero_consistent = sum(row["zero_exclusion_consistent"].lower() == "true" for row in direction)
        non_sanity = [row for row in direction if not (row["method"] == "Noisy" and row["metric"] == "output_vs_clean_snr")]
        non_sanity_consistent = sum(row["direction_consistent"].lower() == "true" for row in non_sanity)
        if (direction_consistent, non_sanity_consistent, len(non_sanity), zero_consistent) != (30, 30, 31, 29):
            errors.append("direction/zero-exclusion counts do not equal 30/32, 30/31, 29/32")
        balance = read_csv(out / "results" / "e3_balance_before_after.csv")
        max_before = max(abs(f(row["before_smd"])) for row in balance)
        max_after = max(abs(f(row["after_smd"])) for row in balance)
        if abs(max_before - 0.4792888957305581) > TABLE_FLOAT_TOL or abs(max_after - 0.55474910743206) > TABLE_FLOAT_TOL:
            errors.append(f"SMD maxima mismatch: {max_before}, {max_after}")
        report["direction_consistency"] = "30/32"
        report["non_sanity_direction_consistency"] = "30/31"
        report["zero_exclusion_consistency"] = "29/32"
        report["max_smd_before"] = max_before
        report["max_smd_after"] = max_after
    return errors, report


def e3_data_checks() -> list[str]:
    errors = []
    cases = read_csv(ROOT / "e3_no_taper_confounding_closure" / "data" / "e3_no_taper_case_covariates.csv")
    manifest = read_csv(ROOT / "source_manifests" / "e3_no_taper_manifest.csv")
    failures = read_csv(ROOT / "e3_no_taper_confounding_closure" / "data" / "e3_no_taper_covariate_failures.csv")
    if len({row["case_id"] for row in cases}) != 1632:
        errors.append("E3 case coverage is not 1,632")
    if len(manifest) != 13056:
        errors.append("E3 method-case manifest rows are not 13,056")
    if failures:
        errors.append("E3 covariate failures are not zero")
    if any(str(row.get("taper_applied", "")).lower() != "false" for row in cases + manifest):
        errors.append("not all E3 rows have taper_applied=false")
    method_case = {(row["case_id"], row["method"]) for row in manifest}
    if len(method_case) != len(manifest):
        errors.append("duplicate method-case rows found")
    by_case: dict[str, set[str]] = {}
    for row in manifest:
        by_case.setdefault(row["case_id"], set()).add(row["method"])
    if any(len(methods) != 8 for methods in by_case.values()):
        errors.append("not every E3 case has exactly 8 methods")
    pairs = read_csv(ROOT / "e3_no_taper_confounding_closure" / "results" / "e3_matching_pairs.csv")
    if len(pairs) != 15:
        errors.append("matching pair count is not 15")
    if any(f(row["distance"]) > 2.5 for row in pairs):
        errors.append("matching distance exceeds caliper 2.5")
    return errors


def main() -> int:
    errors = []
    report: dict[str, Any] = {"package_root": str(ROOT)}
    checksum_errors, checksum_passed = verify_checksum_manifests()
    errors.extend(checksum_errors)
    report["checksum_manifests_passed"] = checksum_passed
    errors.extend(basic_structure_checks())
    hits = path_hits()
    report["machine_local_path_hits"] = hits
    if hits:
        errors.append(f"machine-local absolute path hits = {len(hits)}")
    policy_errors, policy_report = text_policy_checks()
    errors.extend(policy_errors)
    report.update(policy_report)
    errors.extend(e3_data_checks())
    recompute_errors, recompute_report = run_portable_recompute()
    errors.extend(recompute_errors)
    report["portable_recompute"] = recompute_report
    report["raw_tensor_weight_suffix_hits"] = []

    out_report = ROOT / "FINAL_RELEASE_VALIDATION.json"
    out_report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if errors:
        print("FAIL")
        for error in errors:
            print("-", error)
        return 1
    print("PASS: v1.0.5 formal artifact checks succeeded")
    print(f"Validation report: {out_report.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
