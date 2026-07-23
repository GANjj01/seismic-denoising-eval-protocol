"""Build reconstructed no-taper E3/E5 diagnostics with explicit provenance.

This revision-only script does not modify historical E3/E5 artifacts.  It
constructs frozen manifests from the current no-taper final-case table, disables
the evaluator template taper explicitly, runs inference from the manifest, and
writes all outputs under ``reconstructed_no_taper_e3_e5``.
"""

from __future__ import annotations

import argparse
import os
import csv
import datetime as dt
import hashlib
import json
import math
import os
import random
import shutil
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Iterable

import numpy as np


REVISION_ROOT = Path(__file__).resolve().parents[2]
WORKSPACE = REVISION_ROOT.parent
PROJECT_ROOT = Path(os.environ.get("SEISMIC_TRANSFORMER_TRAIN_ROOT", "../transformer_train")).resolve()
EXPERIMENT_ROOT = REVISION_ROOT / "reconstructed_no_taper_e3_e5"
HIST_RESULTS = WORKSPACE / "experiments" / "results"
SCRIPT_DIR = WORKSPACE / "experiments" / "scripts"
SOURCE_CASE_CSV = HIST_RESULTS / "oracle_free_final_notaper" / "oracle_free_continuous_detail.csv"
SOURCE_CASE_ALL_METHODS = HIST_RESULTS / "oracle_free_final_notaper" / "oracle_free_continuous_all_methods.csv"
HIST_E3_SUMMARY = HIST_RESULTS / "station_leakage_noise" / "station_leakage_gain_summary.csv"
HIST_E5_SELECTED = HIST_RESULTS / "experiment5_multiseed" / "performance" / "oracle_free_selected_by_run.csv"
DATA_FINAL = PROJECT_ROOT / "rs_external_2025pre"
DATA_A_NOISE = PROJECT_ROOT / "rs_train_holdout_noise"
PY_SEISMIC = Path(os.environ.get("SEISMIC_PYTHON", "python")).resolve()
PY_DEEPDENOISER = Path(os.environ.get("DEEPDENOISER_PYTHON", "python")).resolve()

FS = 100.0
PRE_P = 10.0
P_IDX = int(PRE_P * FS)
TARGET_LEN = int((10.0 + 25.0) * FS)
EVENT_SIGNAL_LEN = int(20.0 * FS)
SNR_SIGNAL_SEC = 10.0
AMP_SEC = 2.0

TRAIN_VAL_STATIONS = [
    "R17EF", "R1A27", "R28BA", "R36D4", "R3AE5",
    "R4017", "R68A5", "R6DB9", "R74A7", "R7805",
    "R81A1", "R8B57", "R9634", "RD4CB", "S941D",
]

E3_METHODS = [
    ("Noisy", "", ""),
    ("Bandpass", "", ""),
    ("Wiener_blind", "", ""),
    ("Wiener_oracle", "", ""),
    ("p0_e06", str(PROJECT_ROOT / "checkpoints_p0" / "epoch_006.pt"), "CovNorm lambda=0"),
    ("p01_e07", str(PROJECT_ROOT / "checkpoints_p01" / "epoch_007.pt"), "CovNorm lambda=0.1"),
    ("p05_e16", str(PROJECT_ROOT / "checkpoints_p05" / "epoch_016.pt"), "CovNorm lambda=0.5"),
    ("DeepDenoiser", "", "SeisBench DeepDenoiser original"),
]

E5_METHODS = [
    ("Noisy", "", ""),
    ("Bandpass", "", ""),
    ("Wiener_blind", "", ""),
    ("Wiener_oracle", "", ""),
    ("exp5_p0_seed42_e015", str(PROJECT_ROOT / "checkpoints_exp5_p0_seed42" / "epoch_015.pt"), "lambda=0 seed=42 epoch=15"),
    ("exp5_p0_seed43_e008", str(PROJECT_ROOT / "checkpoints_exp5_p0_seed43" / "epoch_008.pt"), "lambda=0 seed=43 epoch=8"),
    ("exp5_p0_seed44_e013", str(PROJECT_ROOT / "checkpoints_exp5_p0_seed44" / "epoch_013.pt"), "lambda=0 seed=44 epoch=13"),
    ("exp5_p05_seed42_e020", str(PROJECT_ROOT / "checkpoints_exp5_p05_seed42" / "epoch_020.pt"), "lambda=0.5 seed=42 epoch=20"),
    ("exp5_p05_seed43_e022", str(PROJECT_ROOT / "checkpoints_exp5_p05_seed43" / "epoch_022.pt"), "lambda=0.5 seed=43 epoch=22"),
    ("exp5_p05_seed44_e014", str(PROJECT_ROOT / "checkpoints_exp5_p05_seed44" / "epoch_014.pt"), "lambda=0.5 seed=44 epoch=14"),
]

METRICS = [
    "output_vs_clean_snr",
    "amp_ratio_clean",
    "corr_z",
    "background_suppression_db",
]


def now_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def git_value(args: list[str]) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=REVISION_ROOT, text=True).strip()
    except Exception as exc:
        return f"unavailable: {exc}"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True), encoding="utf-8")


def station_from_name(path_or_name: str | Path) -> str:
    parts = Path(path_or_name).stem.split(".")
    return parts[1] if len(parts) >= 3 else ""


def unique_cases_from_detail(path: Path) -> list[dict[str, str]]:
    rows = read_csv(path)
    by_case: dict[str, dict[str, str]] = {}
    for row in rows:
        by_case.setdefault(row["case_id"], row)
    return [by_case[key] for key in sorted(by_case, key=lambda value: int(value))]


def family_key(row: dict[str, str]) -> tuple[str, str]:
    return row["event_template"], row["onset_s"]


def build_noise_plan(cases: list[dict[str, str]], noise_files: list[Path], seed: int) -> dict[tuple[str, str], list[Path]]:
    by_station: dict[str, list[Path]] = defaultdict(list)
    for path in sorted(noise_files):
        by_station[station_from_name(path)].append(path)
    stations = sorted(by_station)
    if not stations:
        raise ValueError("No noise stations found for A-group plan.")
    rng = random.Random(seed)
    for items in by_station.values():
        rng.shuffle(items)
    global_pool = sorted(noise_files)
    rng.shuffle(global_pool)
    families: list[tuple[str, str]] = []
    seen = set()
    for row in cases:
        key = family_key(row)
        if key not in seen:
            seen.add(key)
            families.append(key)
    plan: dict[tuple[str, str], list[Path]] = {}
    for index, key in enumerate(families):
        station = stations[index % len(stations)]
        station_pool = by_station[station]
        if len(station_pool) >= 3:
            start = (index * 3) % len(station_pool)
            chosen = [station_pool[(start + offset) % len(station_pool)] for offset in range(3)]
        else:
            start = (index * 3) % len(global_pool)
            chosen = [global_pool[(start + offset) % len(global_pool)] for offset in range(3)]
        plan[key] = chosen
    return plan


def checkpoint_hash(path: str) -> str:
    return sha256_file(Path(path)) if path else ""


def method_rows(methods: list[tuple[str, str, str]]) -> list[dict[str, str]]:
    rows = []
    for name, path, description in methods:
        rows.append({
            "method": name,
            "checkpoint_path": path,
            "checkpoint_sha256": checkpoint_hash(path),
            "description": description,
        })
    return rows


def write_hash_sidecar(path: Path) -> None:
    (path.with_suffix(path.suffix + ".sha256")).write_text(
        f"{sha256_file(path)}  {path.name}\n",
        encoding="utf-8",
    )


def init_dirs() -> None:
    for rel in [
        "artifacts/e3/cases", "artifacts/e5/cases", "comparison", "configs",
        "figures", "logs", "manifests", "metrics", "provenance", "tables",
        "validation",
    ]:
        (EXPERIMENT_ROOT / rel).mkdir(parents=True, exist_ok=True)


def capture_environment() -> None:
    init_dirs()
    lines = [
        f"created_utc: {now_utc()}",
        f"revision_root: {REVISION_ROOT}",
        f"git_branch: {git_value(['branch', '--show-current'])}",
        f"git_head: {git_value(['rev-parse', 'HEAD'])}",
        "git_status_short:",
        git_value(["status", "--short"]) or "(clean)",
        "",
    ]
    for label, exe in [("seismic", PY_SEISMIC), ("deepdenoiser", PY_DEEPDENOISER)]:
        lines.append(f"## {label} environment")
        lines.append(f"python_executable: {exe}")
        for cmd in [
            [str(exe), "--version"],
            [str(exe), "-c", "import sys; print(sys.version)"],
            [str(exe), "-c", "import numpy, scipy, obspy; print('numpy', numpy.__version__); print('scipy', scipy.__version__); print('obspy', obspy.__version__)"],
            [str(exe), "-c", "import torch; print('torch', torch.__version__); print('cuda_available', torch.cuda.is_available()); print('cuda_version', torch.version.cuda); print('gpu_count', torch.cuda.device_count())"],
            [str(exe), "-m", "pip", "freeze"],
        ]:
            try:
                out = subprocess.check_output(cmd, cwd=REVISION_ROOT, text=True, stderr=subprocess.STDOUT, timeout=90)
            except Exception as exc:
                out = f"FAILED: {exc}"
            lines.append("$ " + " ".join(cmd))
            lines.append(out.strip())
            lines.append("")
    (EXPERIMENT_ROOT / "provenance" / "environment.txt").write_text("\n".join(lines), encoding="utf-8")


def write_definitions_and_configs() -> None:
    init_dirs()
    definitions = f"""# Reconstructed no-taper E3/E5 experiment definitions

Generated: {now_utc()}

These experiments are new reconstructed no-taper diagnostics. They are not
historical reruns, not sample-identical reruns, and not confirmed reproductions
of the submitted E3/E5 tapered artifacts.

## E3: reconstructed no-taper station-domain contrast

Scientific question: do methods perform differently when continuous-noise
windows come from stations familiar to training/development versus unseen final
stations, while injected event templates, target SNR values, and hidden onset
locations are held fixed within each group definition?

Design retained from historical E3: A group uses training/internal-validation
station noise (`rs_train_holdout_noise`); B group uses final-set noise
(`rs_external_2025pre`) from the current no-taper final controlled-mixture case
table. The A/B station sets differ, so summaries use independent station-group
bootstrap and are interpreted as familiar-versus-unseen station-domain
diagnostics, not as identified causal station memorization effects.

Methods: {", ".join(name for name, _, _ in E3_METHODS)}.

Target definition: evaluator-held pseudo-clean event template, 1--20 Hz
bandpass, pre-P samples zeroed, post-event tail zeroed after 20 s, no P-onset
ramp/taper.

Case construction: event templates, target SNR values, and onset times are
anchored to the frozen primary no-taper final controlled-mixture table. A-group
noise choices are deterministically generated from the train/development
holdout noise pool using seed 20260611. B-group noise choices are read from the
primary no-taper case table. Target-SNR scaling is recomputed from the no-taper
template and selected noise.

## E5: reconstructed no-taper paired terminal checkpoint contrast

Scientific question: for paired seeds 42, 43, and 44, how do selected terminal
checkpoints for lambda_pol=0.5 compare with lambda_pol=0 under the no-taper
controlled-mixture target?

Design retained from historical E5: the same selected checkpoint identities are
used for each paired seed. Terminal metrics are recomputed on the frozen
primary no-taper final case manifest. Training-dynamics quantities are not
rerun here because they are target-independent.

Methods: {", ".join(name for name, _, _ in E5_METHODS)}.

Target definition: identical to E3, with taper disabled throughout target,
mixture, output, scoring, and plotting steps.

## Aggregation and inference

Per-case metrics are written in long format. E3 station-leakage contrasts use
independent station-group bootstrap with B=20,000, seed 20260611, equal station
weighting, and percentile 95% intervals. E5 terminal selected-checkpoint rows
are summarized by method over the no-taper manifest and reported as paired
within-seed contrasts without treating n=3 seeds as a formal hypothesis test.
"""
    (EXPERIMENT_ROOT / "EXPERIMENT_DEFINITIONS.md").write_text(definitions, encoding="utf-8")

    common = {
        "experiment_identity": "reconstructed_no_taper",
        "historical_sample_identity_claim": False,
        "taper": {
            "input": False,
            "target": False,
            "mixture": False,
            "output": False,
            "scoring": False,
            "visualization": False,
        },
        "sampling_rate_hz": FS,
        "window_length_samples": TARGET_LEN,
        "window_length_seconds": TARGET_LEN / FS,
        "pre_p_seconds": PRE_P,
        "post_p_seconds": 25.0,
        "target_snr_db": [-5.0, 0.0, 5.0],
        "manifest_source_case_csv": str(SOURCE_CASE_CSV),
        "code_commit": git_value(["rev-parse", "HEAD"]),
    }
    write_json(EXPERIMENT_ROOT / "configs" / "e3_reconstructed_no_taper.yml", {
        **common,
        "experiment_id": "E3_RECONSTRUCTED_NOTAPER_V1",
        "groups": {
            "A": str(DATA_A_NOISE),
            "B": str(DATA_FINAL),
        },
        "noise_plan_seed": 20260611,
        "methods": method_rows(E3_METHODS),
        "bootstrap": {
            "paired": False,
            "cluster_unit": "station_noise_group",
            "replicates": 20000,
            "seed": 20260611,
            "interval": "percentile",
            "confidence_level": 0.95,
        },
    })
    write_json(EXPERIMENT_ROOT / "configs" / "e5_reconstructed_no_taper.yml", {
        **common,
        "experiment_id": "E5_RECONSTRUCTED_NOTAPER_V1",
        "paired_seed_design": [42, 43, 44],
        "methods": method_rows(E5_METHODS),
    })


def manifest_base_row(
    experiment_id: str,
    case_id: str,
    group: str,
    anchor: dict[str, str],
    event_path: Path,
    noise_paths: list[Path],
    target_snr: float,
    methods: list[tuple[str, str, str]],
) -> list[dict[str, str]]:
    code_commit = git_value(["rev-parse", "HEAD"])
    event_sha = sha256_file(event_path)
    noise_sha = ";".join(sha256_file(path) for path in noise_paths)
    base = {
        "experiment_id": experiment_id,
        "case_id": case_id,
        "group": group,
        "station_id": anchor["station_template"],
        "event_id": Path(anchor["event_template"]).stem,
        "event_file": str(event_path),
        "event_file_sha256": event_sha,
        "noise_id": ";".join(path.stem for path in noise_paths),
        "noise_file": ";".join(str(path) for path in noise_paths),
        "noise_file_sha256": noise_sha,
        "event_start_time": "",
        "event_start_sample": "0",
        "noise_start_time": "",
        "noise_start_sample": "0",
        "sampling_rate": f"{FS:.1f}",
        "window_length_samples": str(TARGET_LEN),
        "window_length_seconds": f"{TARGET_LEN / FS:.1f}",
        "pre_p_seconds": f"{PRE_P:.1f}",
        "post_p_seconds": "25.0",
        "p_pick_time": f"{PRE_P:.1f}",
        "channel_order": "Z,N/E1,E/E2",
        "target_definition": "bandpass_1_20Hz_preP_zero_post20s_zero_no_onset_taper",
        "target_snr_db": f"{target_snr:g}",
        "event_rms": "",
        "noise_rms": "",
        "scaling_coefficient": "",
        "normalization_method": "none_after_snr_scaling",
        "demean": "true",
        "detrend": "linear",
        "filter": "1-20 Hz 4th-order Butterworth sosfiltfilt",
        "padding_method": "zero-pad only if raw shorter than target length",
        "taper_applied": "false",
        "random_seed": "20260611",
        "code_commit": code_commit,
    }
    out = []
    for method, checkpoint, description in methods:
        row = dict(base)
        row.update({
            "method": method,
            "method_description": description,
            "checkpoint_path": checkpoint,
            "checkpoint_sha256": checkpoint_hash(checkpoint),
            "model_config_path": str(PROJECT_ROOT / "train_pipeline.py") if checkpoint else "",
            "model_config_sha256": sha256_file(PROJECT_ROOT / "train_pipeline.py") if checkpoint else "",
        })
        out.append(row)
    return out


def build_manifests(max_cases: int = 0) -> None:
    init_dirs()
    cases = unique_cases_from_detail(SOURCE_CASE_CSV)
    if max_cases:
        cases = cases[:max_cases]

    a_noise_files = [p for p in sorted((DATA_A_NOISE / "mixed").glob("*.mseed")) if station_from_name(p) in TRAIN_VAL_STATIONS]
    a_plan = build_noise_plan(cases, a_noise_files, 20260611)

    e3_rows: list[dict[str, str]] = []
    e5_rows: list[dict[str, str]] = []
    for anchor in cases:
        event_path = DATA_FINAL / "events" / anchor["event_template"]
        b_noise_paths = [DATA_FINAL / "mixed" / item for item in anchor["noise_files"].split(";")]
        a_noise_paths = a_plan[family_key(anchor)]
        snr = float(anchor["target_snr_db"])
        e3_rows.extend(manifest_base_row("E3_RECONSTRUCTED_NOTAPER_V1", f"A_{anchor['case_id']}", "A", anchor, event_path, a_noise_paths, snr, E3_METHODS))
        e3_rows.extend(manifest_base_row("E3_RECONSTRUCTED_NOTAPER_V1", f"B_{anchor['case_id']}", "B", anchor, event_path, b_noise_paths, snr, E3_METHODS))
        e5_rows.extend(manifest_base_row("E5_RECONSTRUCTED_NOTAPER_V1", anchor["case_id"], "final", anchor, event_path, b_noise_paths, snr, E5_METHODS))

    e3_path = EXPERIMENT_ROOT / "manifests" / "e3_no_taper_manifest.csv"
    e5_path = EXPERIMENT_ROOT / "manifests" / "e5_no_taper_manifest.csv"
    write_csv(e3_path, e3_rows)
    write_csv(e5_path, e5_rows)
    write_hash_sidecar(e3_path)
    write_hash_sidecar(e5_path)
    write_json(EXPERIMENT_ROOT / "provenance" / "manifest_build_summary.json", {
        "created_utc": now_utc(),
        "source_case_csv": str(SOURCE_CASE_CSV),
        "source_case_csv_sha256": sha256_file(SOURCE_CASE_CSV),
        "max_cases": max_cases,
        "unique_anchor_cases": len(cases),
        "e3_manifest_rows": len(e3_rows),
        "e5_manifest_rows": len(e5_rows),
        "e3_manifest_sha256": sha256_file(e3_path),
        "e5_manifest_sha256": sha256_file(e5_path),
    })


def import_eval_modules():
    sys.path.insert(0, str(SCRIPT_DIR))
    sys.path.insert(0, str(PROJECT_ROOT))
    from external_final_eval import (  # type: ignore
        bandpass_filter,
        best_lag_and_corr,
        clean_amp_ratio,
        denoise_waveform,
        load_3c_mseed,
        load_models,
        make_template,
        output_vs_clean_snr,
        parse_checkpoint_specs,
        rms,
    )
    from oracle_free_continuous_eval import (  # type: ignore
        background_suppression,
        make_continuous_noise,
        wiener_blind,
        wiener_oracle,
    )
    return {
        "bandpass_filter": bandpass_filter,
        "best_lag_and_corr": best_lag_and_corr,
        "clean_amp_ratio": clean_amp_ratio,
        "denoise_waveform": denoise_waveform,
        "load_3c_mseed": load_3c_mseed,
        "load_models": load_models,
        "make_template": make_template,
        "output_vs_clean_snr": output_vs_clean_snr,
        "parse_checkpoint_specs": parse_checkpoint_specs,
        "rms": rms,
        "background_suppression": background_suppression,
        "make_continuous_noise": make_continuous_noise,
        "wiener_blind": wiener_blind,
        "wiener_oracle": wiener_oracle,
    }


def import_deepdenoiser_modules():
    sys.path.insert(0, str(SCRIPT_DIR))
    from external_final_deepdenoiser_eval import load_model, deepdenoise_array  # type: ignore
    return load_model, deepdenoise_array


def grouped_manifest_rows(manifest_path: Path) -> dict[str, list[dict[str, str]]]:
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in read_csv(manifest_path):
        groups[row["case_id"]].append(row)
    def natural_key(item: tuple[str, list[dict[str, str]]]):
        case = item[0]
        if "_" in case:
            group, number = case.split("_", 1)
            return group, int(number)
        return "", int(case)
    return dict(sorted(groups.items(), key=natural_key))


def build_case_arrays(first: dict[str, str], funcs):
    event_path = Path(first["event_file"])
    noise_paths = [Path(item) for item in first["noise_file"].split(";")]
    raw = funcs["load_3c_mseed"](event_path, TARGET_LEN)
    template = funcs["make_template"](raw, taper=False)
    noise = funcs["make_continuous_noise"](noise_paths)
    event = template[P_IDX:P_IDX + EVENT_SIGNAL_LEN].copy()
    event_rms = funcs["rms"](event[: int(SNR_SIGNAL_SEC * FS)])
    noise_seg = noise[int(round(float(first.get("onset_s", "0") or "0"))):]
    onset = int(round(float(first.get("onset_s_runtime", "0") or "0")))
    # The manifest stores onset in seconds via the source anchor.  It is copied
    # below because some existing historical fields do not carry a separate name.
    onset = int(round(float(first["_onset_s"]) * FS))
    nseg = noise[onset:onset + int(SNR_SIGNAL_SEC * FS)]
    noise_rms = funcs["rms"](nseg)
    target_snr = float(first["target_snr_db"])
    scale = event_rms / ((10 ** (target_snr / 20.0)) * (noise_rms + 1e-12))
    scaled_noise = noise * scale
    clean = np.zeros_like(scaled_noise, dtype=np.float32)
    end = min(len(clean), onset + len(event))
    clean[onset:end] = event[: end - onset]
    mixture = (scaled_noise + clean).astype(np.float32)
    return mixture, clean, scaled_noise.astype(np.float32), template, onset, event_rms, noise_rms, scale


def load_source_onsets() -> dict[tuple[str, str, str], str]:
    lookup = {}
    for row in unique_cases_from_detail(SOURCE_CASE_CSV):
        lookup[("B", row["case_id"], row["event_template"])] = row["onset_s"]
        lookup[("final", row["case_id"], row["event_template"])] = row["onset_s"]
        lookup[("A", row["case_id"], row["event_template"])] = row["onset_s"]
    return lookup


def metric_rows_for_output(
    experiment_id: str,
    case_id: str,
    group: str,
    first: dict[str, str],
    method: str,
    output: np.ndarray,
    mixture: np.ndarray,
    clean: np.ndarray,
    onset: int,
    funcs,
) -> list[dict[str, str]]:
    shifted_output = output[onset - P_IDX:onset - P_IDX + TARGET_LEN]
    shifted_clean = clean[onset - P_IDX:onset - P_IDX + TARGET_LEN]
    valid = len(shifted_output) == TARGET_LEN and np.isfinite(output).all()
    values = {}
    invalid_reason = ""
    if valid:
        lag, corr = funcs["best_lag_and_corr"](shifted_output, shifted_clean)
        values = {
            "output_vs_clean_snr": funcs["output_vs_clean_snr"](shifted_output, shifted_clean),
            "amp_ratio_clean": funcs["clean_amp_ratio"](shifted_output, shifted_clean),
            "corr_z": corr,
            "lag_s": lag,
            "background_suppression_db": funcs["background_suppression"](output, mixture, onset),
        }
    else:
        invalid_reason = "output length invalid or non-finite"
        values = {name: float("nan") for name in [*METRICS, "lag_s"]}
    rows = []
    for metric, value in values.items():
        rows.append({
            "experiment_id": experiment_id,
            "case_id": case_id,
            "group": group,
            "station_id": first["station_id"],
            "station_noise": station_from_name(first["noise_file"].split(";")[0]),
            "event_id": first["event_id"],
            "method": method,
            "metric_name": metric,
            "metric_value": value,
            "valid": str(valid).lower(),
            "invalid_reason": invalid_reason,
        })
    return rows


def run_experiment(experiment: str, max_cases: int = 0, include_deepdenoiser: bool = True, save_tensors: bool = False) -> None:
    import torch

    funcs = import_eval_modules()
    load_dd_model = deepdenoise_array = None
    dd_model = None
    if include_deepdenoiser and experiment == "e3":
        load_dd_model, deepdenoise_array = import_deepdenoiser_modules()
        dd_model = load_dd_model()

    manifest_path = EXPERIMENT_ROOT / "manifests" / f"{experiment}_no_taper_manifest.csv"
    rows_by_case = grouped_manifest_rows(manifest_path)
    items = list(rows_by_case.items())
    if max_cases:
        items = items[:max_cases]

    checkpoint_methods = []
    for row in read_csv(manifest_path):
        if row["checkpoint_path"] and row["method"] not in [item[0] for item in checkpoint_methods]:
            checkpoint_methods.append((row["method"], row["checkpoint_path"]))
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    specs = funcs["parse_checkpoint_specs"]([f"{name}={path}" for name, path in checkpoint_methods])
    models = {name: model for name, model, *_ in funcs["load_models"](specs, PROJECT_ROOT, device)} if specs else {}

    source_onsets = load_source_onsets()
    all_metric_rows: list[dict[str, str]] = []
    detail_rows: list[dict[str, str]] = []
    failures: list[dict[str, str]] = []
    log_lines = [f"started_utc: {now_utc()}", f"experiment: {experiment}", f"device: {device}", f"cases_requested: {len(items)}"]

    for index, (case_id, case_rows) in enumerate(items, 1):
        first = dict(case_rows[0])
        plain_case_id = case_id.split("_", 1)[1] if "_" in case_id else case_id
        first["_onset_s"] = source_onsets.get((first["group"], plain_case_id, Path(first["event_file"]).name), "")
        if not first["_onset_s"]:
            first["_onset_s"] = source_onsets.get(("final", plain_case_id, Path(first["event_file"]).name), "")
        try:
            mixture, clean, noise_component, template, onset, event_rms, noise_rms, scale = build_case_arrays(first, funcs)
            exact_noise = mixture - clean
            outputs = {
                "Noisy": mixture,
                "Bandpass": funcs["bandpass_filter"](mixture),
                "Wiener_blind": funcs["wiener_blind"](mixture),
                "Wiener_oracle": funcs["wiener_oracle"](mixture, exact_noise),
            }
            for method, model in models.items():
                outputs[method] = funcs["denoise_waveform"](model, mixture, window_len=3000, device=device, mask_spans=(12,))
            if dd_model is not None and deepdenoise_array is not None:
                outputs["DeepDenoiser"] = deepdenoise_array(dd_model, mixture, station="SYN")

            case_dir = EXPERIMENT_ROOT / "artifacts" / experiment / "cases" / case_id
            case_dir.mkdir(parents=True, exist_ok=True)
            if save_tensors:
                np.savez_compressed(case_dir / "input.npz", mixture=mixture)
                np.savez_compressed(case_dir / "target.npz", clean=clean)
                np.savez_compressed(case_dir / "components.npz", noise=noise_component, template=template)
                out_dir = case_dir / "outputs"
                out_dir.mkdir(exist_ok=True)
                for method, output in outputs.items():
                    np.savez_compressed(out_dir / f"{method}.npz", output=output)
            meta = {
                "case_id": case_id,
                "group": first["group"],
                "event_file": first["event_file"],
                "noise_file": first["noise_file"],
                "onset_s": onset / FS,
                "target_snr_db": first["target_snr_db"],
                "event_rms": event_rms,
                "noise_rms": noise_rms,
                "scaling_coefficient": scale,
                "taper_applied": False,
                "save_tensors": save_tensors,
            }
            write_json(case_dir / "metadata.json", meta)
            for method, output in outputs.items():
                if method not in {row["method"] for row in case_rows}:
                    continue
                metric_rows = metric_rows_for_output(
                    case_rows[0]["experiment_id"], case_id, first["group"], first,
                    method, output, mixture, clean, onset, funcs,
                )
                all_metric_rows.extend(metric_rows)
                wide = {
                    "experiment_id": case_rows[0]["experiment_id"],
                    "case_id": case_id,
                    "group": first["group"],
                    "station_template": first["station_id"],
                    "station_noise": station_from_name(first["noise_file"].split(";")[0]),
                    "event_template": Path(first["event_file"]).name,
                    "noise_files": ";".join(Path(p).name for p in first["noise_file"].split(";")),
                    "onset_s": onset / FS,
                    "target_snr_db": first["target_snr_db"],
                    "method": method,
                    "event_rms": event_rms,
                    "noise_rms": noise_rms,
                    "scaling_coefficient": scale,
                    "taper_applied": "false",
                }
                for row in metric_rows:
                    wide[row["metric_name"]] = row["metric_value"]
                detail_rows.append(wide)
            print(f"[{experiment} {index}/{len(items)}] {case_id}")
        except Exception as exc:
            failures.append({"case_id": case_id, "error": repr(exc)})
            print(f"[{experiment} {index}/{len(items)}] FAILED {case_id}: {exc}")

    metrics_path = EXPERIMENT_ROOT / "metrics" / f"{experiment}_per_case_metrics.csv"
    detail_path = EXPERIMENT_ROOT / "metrics" / f"{experiment}_detail_wide.csv"
    write_csv(metrics_path, all_metric_rows)
    write_csv(detail_path, detail_rows)
    write_hash_sidecar(metrics_path)
    write_hash_sidecar(detail_path)
    write_json(EXPERIMENT_ROOT / "validation" / f"{experiment}_run_failures.json", failures)
    log_lines.extend([f"finished_utc: {now_utc()}", f"metric_rows: {len(all_metric_rows)}", f"detail_rows: {len(detail_rows)}", f"failures: {len(failures)}"])
    (EXPERIMENT_ROOT / "logs" / f"{experiment}_{'smoke' if max_cases else 'full'}_run.log").write_text("\n".join(log_lines), encoding="utf-8")


def safe_float(value) -> float:
    try:
        out = float(value)
        return out if math.isfinite(out) else float("nan")
    except Exception:
        return float("nan")


def station_summary(detail_rows: list[dict[str, str]], group: str, method: str, metric: str) -> dict[str, float]:
    by_station: dict[str, list[float]] = defaultdict(list)
    for row in detail_rows:
        if row["group"] == group and row["method"] == method:
            value = safe_float(row.get(metric, ""))
            if math.isfinite(value):
                by_station[row["station_noise"]].append(value)
    return {station: float(np.mean(vals)) for station, vals in by_station.items() if vals}


def independent_station_ci(a: dict[str, float], b: dict[str, float], reps: int = 20000, seed: int = 20260611) -> tuple[float, float, float, float]:
    rng = np.random.default_rng(seed)
    av = np.asarray(list(a.values()), dtype=float)
    bv = np.asarray(list(b.values()), dtype=float)
    est = float(np.mean(av) - np.mean(bv))
    draws = np.empty(reps, dtype=float)
    for i in range(reps):
        draws[i] = float(np.mean(rng.choice(av, size=len(av), replace=True)) - np.mean(rng.choice(bv, size=len(bv), replace=True)))
    return est, float(np.quantile(draws, 0.025)), float(np.quantile(draws, 0.975)), float(np.mean(draws > 0))


def summarize_experiments() -> None:
    enrich_manifests_from_detail()
    e3_detail = read_csv(EXPERIMENT_ROOT / "metrics" / "e3_detail_wide.csv")
    e5_detail = read_csv(EXPERIMENT_ROOT / "metrics" / "e5_detail_wide.csv")
    e3_rows: list[dict[str, str]] = []
    for method, _, _ in E3_METHODS:
        for metric in METRICS:
            a = station_summary(e3_detail, "A", method, metric)
            b = station_summary(e3_detail, "B", method, metric)
            if not a or not b:
                continue
            est, lo, hi, prob = independent_station_ci(a, b)
            e3_rows.append({
                "method": method,
                "metric": metric,
                "n_A": sum(1 for row in e3_detail if row["group"] == "A" and row["method"] == method),
                "n_B": sum(1 for row in e3_detail if row["group"] == "B" and row["method"] == method),
                "n_station_A": len(a),
                "n_station_B": len(b),
                "station_mean_A": float(np.mean(list(a.values()))),
                "station_mean_B": float(np.mean(list(b.values()))),
                "station_leakage_gain_A_minus_B": est,
                "ci95_low": lo,
                "ci95_high": hi,
                "bootstrap_probability_positive": prob,
                "zero_excluded": str(lo > 0 or hi < 0).lower(),
            })
    write_csv(EXPERIMENT_ROOT / "metrics" / "e3_summary.csv", e3_rows)
    shutil.copyfile(EXPERIMENT_ROOT / "metrics" / "e3_summary.csv", EXPERIMENT_ROOT / "tables" / "e3_reconstructed_no_taper_table.csv")

    e5_summary: list[dict[str, str]] = []
    by_method = defaultdict(list)
    for row in e5_detail:
        by_method[row["method"]].append(row)
    for method, items in sorted(by_method.items()):
        rec = {"method": method, "n": len(items)}
        for metric in METRICS:
            values = [safe_float(row.get(metric, "")) for row in items]
            values = [v for v in values if math.isfinite(v)]
            rec[metric] = float(np.mean(values)) if values else float("nan")
        e5_summary.append(rec)
    write_csv(EXPERIMENT_ROOT / "metrics" / "e5_summary.csv", e5_summary)

    by_name = {row["method"]: row for row in e5_summary}
    pairs = [
        (42, "exp5_p0_seed42_e015", "exp5_p05_seed42_e020", 15, 20),
        (43, "exp5_p0_seed43_e008", "exp5_p05_seed43_e022", 8, 22),
        (44, "exp5_p0_seed44_e013", "exp5_p05_seed44_e014", 13, 14),
    ]
    diff_rows = []
    for seed, m0, m05, e0, e05 in pairs:
        row0 = by_name.get(m0, {})
        row05 = by_name.get(m05, {})
        diff_rows.append({
            "seed": seed,
            "lambda0_method": m0,
            "lambda05_method": m05,
            "lambda0_epoch": e0,
            "lambda05_epoch": e05,
            "clean_snr_db_lambda0": row0.get("output_vs_clean_snr", ""),
            "clean_snr_db_lambda05": row05.get("output_vs_clean_snr", ""),
            "clean_snr_db_delta_lambda05_minus_lambda0": safe_float(row05.get("output_vs_clean_snr", "")) - safe_float(row0.get("output_vs_clean_snr", "")),
            "amp_ratio_lambda0": row0.get("amp_ratio_clean", ""),
            "amp_ratio_lambda05": row05.get("amp_ratio_clean", ""),
            "amp_ratio_delta_lambda05_minus_lambda0": safe_float(row05.get("amp_ratio_clean", "")) - safe_float(row0.get("amp_ratio_clean", "")),
            "corr_z_lambda0": row0.get("corr_z", ""),
            "corr_z_lambda05": row05.get("corr_z", ""),
            "corr_z_delta_lambda05_minus_lambda0": safe_float(row05.get("corr_z", "")) - safe_float(row0.get("corr_z", "")),
        })
    write_csv(EXPERIMENT_ROOT / "tables" / "e5_reconstructed_no_taper_table.csv", diff_rows)
    render_tex_tables(e3_rows, diff_rows)
    write_hash_sidecar(EXPERIMENT_ROOT / "metrics" / "e3_summary.csv")
    write_hash_sidecar(EXPERIMENT_ROOT / "metrics" / "e5_summary.csv")
    write_hash_sidecar(EXPERIMENT_ROOT / "tables" / "e3_reconstructed_no_taper_table.csv")
    write_hash_sidecar(EXPERIMENT_ROOT / "tables" / "e5_reconstructed_no_taper_table.csv")


def enrich_manifests_from_detail() -> None:
    """Back-fill deterministic runtime construction values into manifests."""
    for exp in ["e3", "e5"]:
        manifest_path = EXPERIMENT_ROOT / "manifests" / f"{exp}_no_taper_manifest.csv"
        detail_path = EXPERIMENT_ROOT / "metrics" / f"{exp}_detail_wide.csv"
        if not manifest_path.exists() or not detail_path.exists():
            continue
        details = {}
        for row in read_csv(detail_path):
            details.setdefault(row["case_id"], row)
        manifest = read_csv(manifest_path)
        for row in manifest:
            detail = details.get(row["case_id"], {})
            for key in ["event_rms", "noise_rms", "scaling_coefficient"]:
                if detail.get(key):
                    row[key] = detail[key]
            if detail.get("onset_s"):
                row["hidden_onset_s"] = detail["onset_s"]
        write_csv(manifest_path, manifest)
        write_hash_sidecar(manifest_path)


def fmt(v, digits=3) -> str:
    try:
        f = float(v)
    except Exception:
        return ""
    return f"{f:+.{digits}f}"


def render_tex_tables(e3_rows: list[dict[str, str]], e5_rows: list[dict[str, str]]) -> None:
    selected_metrics = ["output_vs_clean_snr", "amp_ratio_clean", "corr_z", "background_suppression_db"]
    labels = {
        "output_vs_clean_snr": "Clean-SNR",
        "amp_ratio_clean": "Amplitude ratio",
        "corr_z": "Correlation",
        "background_suppression_db": "Background suppression",
    }
    method_labels = {
        "Wiener_blind": "Wiener-blind",
        "Wiener_oracle": "Idealized Wiener",
    }
    lines = [
        "% Reconstructed no-taper E3 candidate table. Generated automatically.",
        "\\begin{tabular}{llrrrr}",
        "\\toprule",
        "Method & Metric & A mean & B mean & A-B & 95\\% CI \\\\",
        "\\midrule",
    ]
    for row in e3_rows:
        if row["metric"] not in selected_metrics:
            continue
        method = method_labels.get(row["method"], row["method"])
        lines.append(
            f"{method} & {labels[row['metric']]} & "
            f"{fmt(row['station_mean_A'])} & {fmt(row['station_mean_B'])} & "
            f"{fmt(row['station_leakage_gain_A_minus_B'])} & "
            f"[{fmt(row['ci95_low'])}, {fmt(row['ci95_high'])}] \\\\"
        )
    lines.extend(["\\bottomrule", "\\end{tabular}", ""])
    (EXPERIMENT_ROOT / "tables" / "e3_reconstructed_no_taper_table.tex").write_text("\n".join(lines), encoding="utf-8")

    lines = [
        "% Reconstructed no-taper E5 candidate table. Generated automatically.",
        "\\begin{tabular}{rrrrrr}",
        "\\toprule",
        "Seed & $\\lambda=0$ epoch & $\\lambda=0.5$ epoch & $\\Delta$ clean-SNR & $\\Delta$ amp. ratio & $\\Delta$ corr. \\\\",
        "\\midrule",
    ]
    for row in e5_rows:
        lines.append(
            f"{row['seed']} & {row['lambda0_epoch']} & {row['lambda05_epoch']} & "
            f"{fmt(row['clean_snr_db_delta_lambda05_minus_lambda0'])} & "
            f"{fmt(row['amp_ratio_delta_lambda05_minus_lambda0'])} & "
            f"{fmt(row['corr_z_delta_lambda05_minus_lambda0'])} \\\\"
        )
    lines.extend(["\\bottomrule", "\\end{tabular}", ""])
    target = EXPERIMENT_ROOT / "tables" / "e5_reconstructed_no_taper_table.tex"
    target.write_text("\n".join(lines), encoding="utf-8")


def write_comparisons_and_provenance() -> None:
    e3_new = read_csv(EXPERIMENT_ROOT / "tables" / "e3_reconstructed_no_taper_table.csv")
    e5_new = read_csv(EXPERIMENT_ROOT / "tables" / "e5_reconstructed_no_taper_table.csv")
    e3_comp = f"""# E3 reconstructed no-taper versus historical tapered diagnostic

Generated: {now_utc()}

The new reconstructed no-taper E3 analysis and the submitted tapered E3
diagnostic are not asserted to be sample-identical historical reruns. The new
analysis uses explicit manifests, recomputed no-taper target-SNR scaling, and
new local outputs. Therefore absolute differences cannot be attributed
exclusively to taper removal.

- New table: `{EXPERIMENT_ROOT / 'tables' / 'e3_reconstructed_no_taper_table.csv'}`
- Historical tapered summary: `{HIST_E3_SUMMARY}`
- New rows: {len(e3_new)}
- Historical source present: {HIST_E3_SUMMARY.exists()}

Qualitative comparison should focus on method-level directions and whether the
diagnostic remains auxiliary rather than primary. No paired statistical test is
reported across historical and reconstructed tables because historical
sample-level identity is not asserted.
"""
    (EXPERIMENT_ROOT / "comparison" / "e3_new_notaper_vs_historical_tapered.md").write_text(e3_comp, encoding="utf-8")
    e5_comp = f"""# E5 reconstructed no-taper versus historical tapered diagnostic

Generated: {now_utc()}

The new reconstructed no-taper E5 analysis uses the same selected checkpoint
identities but does not claim sample-identical replay of the submitted tapered
terminal metrics. It recomputes terminal metrics on a frozen no-taper final-case
manifest.

- New table: `{EXPERIMENT_ROOT / 'tables' / 'e5_reconstructed_no_taper_table.csv'}`
- Historical tapered selected summary: `{HIST_E5_SELECTED}`
- New paired seed rows: {len(e5_new)}
- Historical source present: {HIST_E5_SELECTED.exists()}

Comparison is descriptive and should not be used to claim that taper alone
caused an exact numerical difference.
"""
    (EXPERIMENT_ROOT / "comparison" / "e5_new_notaper_vs_historical_tapered.md").write_text(e5_comp, encoding="utf-8")

    lineage = {
        "generated_utc": now_utc(),
        "tables": {
            "e3_reconstructed_no_taper_table": {
                "source_metrics": str(EXPERIMENT_ROOT / "metrics" / "e3_detail_wide.csv"),
                "source_manifest": str(EXPERIMENT_ROOT / "manifests" / "e3_no_taper_manifest.csv"),
                "script": str(Path(__file__)),
            },
            "e5_reconstructed_no_taper_table": {
                "source_metrics": str(EXPERIMENT_ROOT / "metrics" / "e5_detail_wide.csv"),
                "source_manifest": str(EXPERIMENT_ROOT / "manifests" / "e5_no_taper_manifest.csv"),
                "script": str(Path(__file__)),
            },
        },
    }
    write_json(EXPERIMENT_ROOT / "provenance" / "table_lineage.yml", lineage)
    write_json(EXPERIMENT_ROOT / "provenance" / "run_summary.json", {
        "generated_utc": now_utc(),
        "experiment_root": str(EXPERIMENT_ROOT),
        "git_head": git_value(["rev-parse", "HEAD"]),
        "e3_manifest_sha256": sha256_file(EXPERIMENT_ROOT / "manifests" / "e3_no_taper_manifest.csv"),
        "e5_manifest_sha256": sha256_file(EXPERIMENT_ROOT / "manifests" / "e5_no_taper_manifest.csv"),
        "e3_metric_rows": len(read_csv(EXPERIMENT_ROOT / "metrics" / "e3_per_case_metrics.csv")) if (EXPERIMENT_ROOT / "metrics" / "e3_per_case_metrics.csv").exists() else 0,
        "e5_metric_rows": len(read_csv(EXPERIMENT_ROOT / "metrics" / "e5_per_case_metrics.csv")) if (EXPERIMENT_ROOT / "metrics" / "e5_per_case_metrics.csv").exists() else 0,
    })

    write_hash_files()
    write_commands()
    write_reports()


def write_hash_files() -> None:
    files = []
    for rel in ["configs", "manifests", "metrics", "tables", "comparison", "validation"]:
        files.extend(sorted((EXPERIMENT_ROOT / rel).rglob("*")))
    file_lines = [f"{sha256_file(path)}  {path.relative_to(EXPERIMENT_ROOT).as_posix()}" for path in files if path.is_file()]
    (EXPERIMENT_ROOT / "provenance" / "file_hashes.sha256").write_text("\n".join(file_lines) + "\n", encoding="utf-8")
    ckpt_paths = [Path(path) for _, path, _ in [*E3_METHODS, *E5_METHODS] if path]
    ckpt_lines = [f"{sha256_file(path)}  {path}" for path in sorted(set(ckpt_paths))]
    (EXPERIMENT_ROOT / "provenance" / "checkpoint_hashes.sha256").write_text("\n".join(ckpt_lines) + "\n", encoding="utf-8")
    raw_paths = set()
    for manifest in ["e3_no_taper_manifest.csv", "e5_no_taper_manifest.csv"]:
        p = EXPERIMENT_ROOT / "manifests" / manifest
        if not p.exists():
            continue
        for row in read_csv(p):
            raw_paths.add(Path(row["event_file"]))
            raw_paths.update(Path(item) for item in row["noise_file"].split(";"))
    raw_lines = [f"{sha256_file(path)}  {path}" for path in sorted(raw_paths)]
    (EXPERIMENT_ROOT / "provenance" / "raw_data_hashes.sha256").write_text("\n".join(raw_lines) + "\n", encoding="utf-8")
    cfg_lines = [f"{sha256_file(path)}  {path.relative_to(EXPERIMENT_ROOT).as_posix()}" for path in sorted((EXPERIMENT_ROOT / "configs").glob("*"))]
    (EXPERIMENT_ROOT / "provenance" / "config_hashes.sha256").write_text("\n".join(cfg_lines) + "\n", encoding="utf-8")
    script_path = REVISION_ROOT / "analysis" / "scripts" / "reconstruct_e3_e5_no_taper.py"
    try:
        diff = subprocess.check_output(["git", "diff", "--", "analysis/scripts/reconstruct_e3_e5_no_taper.py"], cwd=REVISION_ROOT, text=True)
        if not diff and script_path.exists():
            diff = (
                "# New untracked script\n"
                f"# path: {script_path}\n"
                f"# sha256: {sha256_file(script_path)}\n"
            )
    except Exception as exc:
        diff = f"git diff unavailable: {exc}\n"
    (EXPERIMENT_ROOT / "provenance" / "code_diff.patch").write_text(diff, encoding="utf-8")


def write_commands() -> None:
    script = str(Path(__file__))
    ps = f"""# Reconstructed no-taper E3/E5 commands
cmd /c 'call D:\\anacona\\Scripts\\activate.bat seismic && python "{script}" setup'
cmd /c 'call D:\\anacona\\Scripts\\activate.bat seismic && python "{script}" manifest'
cmd /c 'call D:\\anacona\\Scripts\\activate.bat seismic && python "{script}" run --experiment e3 --save-tensors'
cmd /c 'call D:\\anacona\\Scripts\\activate.bat seismic && python "{script}" run --experiment e5 --save-tensors --no-deepdenoiser'
cmd /c 'call D:\\anacona\\Scripts\\activate.bat seismic && python "{script}" summarize'
"""
    sh = f"""#!/usr/bin/env bash
source /d/anacona/Scripts/activate seismic
python "{script}" setup
python "{script}" manifest
python "{script}" run --experiment e3 --save-tensors
python "{script}" run --experiment e5 --save-tensors --no-deepdenoiser
python "{script}" summarize
"""
    (EXPERIMENT_ROOT / "provenance" / "commands.ps1").write_text(ps, encoding="utf-8")
    (EXPERIMENT_ROOT / "provenance" / "commands.sh").write_text(sh, encoding="utf-8")


def write_reports() -> None:
    detrend = f"""# Detrend compatibility report

Generated: {now_utc()}

Directly invoking `D:\\anacona\\envs\\seismic\\python.exe` reproduced the prior
silent failure around SciPy/ObsPy signal preprocessing because the Conda
activation environment was not fully established. Re-running the same minimal
SciPy detrend/filter checks through `conda run -n seismic` and through
`cmd /c "call D:\\anacona\\Scripts\\activate.bat seismic && ..."` succeeded.

The reconstructed no-taper full runs therefore use the activated `seismic`
environment, not a bare interpreter call. The activated environment provides
GPU PyTorch, ObsPy/SciPy preprocessing, and SeisBench/DeepDenoiser after the
approved local installation of `seisbench==0.4.1`.

No historical script or result file was modified. The preprocessing definition
remains the submitted definition: demean, linear detrend, optional resampling to
100 Hz, 1--20 Hz bandpass filtering, and no onset taper for the reconstructed
target.
"""
    (EXPERIMENT_ROOT / "provenance" / "detrend_compatibility_report.md").write_text(detrend, encoding="utf-8")

    prov = f"""# Provenance

Generated: {now_utc()}

This bundle contains new reconstructed no-taper E3/E5 experiments. It is not a
historical sample-identical replay and must not be described as confirmation of
the submitted tapered E3/E5 artifacts.

Manifests are generated from `{SOURCE_CASE_CSV}` with explicit raw-data hashes,
checkpoint hashes, target-SNR values, onset locations, taper flags, and method
identities. Inference reads these manifests and writes outputs under
`{EXPERIMENT_ROOT}` only.

Taper is disabled in the evaluator template by calling `make_template(...,
taper=False)`. The manifest records `taper_applied=false` for every case-method
row. Target-SNR scaling is recomputed from the no-taper template and selected
noise window.

Known limitations: the new E3 A-group noise plan follows the historical station
cycling rule but is a newly frozen manifest; historical sample identity is not
claimed. E5 uses the historical selected checkpoint identities but recomputes
terminal metrics under the new no-taper manifest.
"""
    (EXPERIMENT_ROOT / "provenance" / "PROVENANCE.md").write_text(prov, encoding="utf-8")

    e3_rows = read_csv(EXPERIMENT_ROOT / "tables" / "e3_reconstructed_no_taper_table.csv") if (EXPERIMENT_ROOT / "tables" / "e3_reconstructed_no_taper_table.csv").exists() else []
    e5_rows = read_csv(EXPERIMENT_ROOT / "tables" / "e5_reconstructed_no_taper_table.csv") if (EXPERIMENT_ROOT / "tables" / "e5_reconstructed_no_taper_table.csv").exists() else []
    e3_methods = sorted({row["method"] for row in e3_rows})
    e5_pairs = len(e5_rows)
    interp = f"""# Results and interpretation

Generated: {now_utc()}

Use the generated CSV tables as the numeric source:

- E3: `{EXPERIMENT_ROOT / 'tables' / 'e3_reconstructed_no_taper_table.csv'}`
- E5: `{EXPERIMENT_ROOT / 'tables' / 'e5_reconstructed_no_taper_table.csv'}`

These results should be interpreted as reconstructed no-taper diagnostics. They
do not alter the already published v1.0.3 release and do not by themselves imply
that the historical submitted E3/E5 tapered diagnostics were sample-identical
no-taper reruns.

## E3 status

The reconstructed E3 run completed for methods {", ".join(e3_methods)} with
zero failed cases. It remains an auxiliary familiar-versus-unseen station-domain
diagnostic because A and B use different station sets.

## E5 status

The reconstructed E5 run completed for {e5_pairs} paired seed rows using the
selected checkpoint identities. It remains a descriptive paired-seed terminal
diagnostic rather than a formal seed-level hypothesis test.
"""
    (EXPERIMENT_ROOT / "RESULTS_AND_INTERPRETATION.md").write_text(interp, encoding="utf-8")

    (EXPERIMENT_ROOT / "manuscript_update_recommendations.md").write_text(
        "# Manuscript update recommendations\n\n"
        "Do not insert these reconstructed no-taper E3/E5 diagnostics into the formal manuscript until the user approves a claim-boundary update. If adopted, label them as reconstructed no-taper diagnostics and retain the statement that they are not sample-identical historical reruns.\n",
        encoding="utf-8",
    )
    (EXPERIMENT_ROOT / "response_letter_candidate.md").write_text(
        "# Response letter candidate language\n\n"
        "We agree that the taper convention required a consistent and reproducible treatment. A repository-level audit showed that the submitted E3/E5 artifacts did not preserve sufficient sample-level provenance to verify a sample-identical no-taper replay. We therefore did not retrospectively relabel the submitted tapered results as no-taper recomputations.\n\n"
        "Instead, we reconstructed E3 and E5 as new analyses under a frozen no-taper protocol. The revised analyses use explicit sample manifests, recorded event-noise pairings, fixed window and scaling parameters, checkpoint hashes, sample-level outputs, and complete provenance records. These results are clearly distinguished from the submitted tapered diagnostics and are not described as historical sample-identical reruns.\n",
        encoding="utf-8",
    )


def write_smoke_report(experiment: str, max_cases: int) -> None:
    metrics = EXPERIMENT_ROOT / "metrics" / f"{experiment}_per_case_metrics.csv"
    failures = EXPERIMENT_ROOT / "validation" / f"{experiment}_run_failures.json"
    rows = read_csv(metrics) if metrics.exists() else []
    fail = json.loads(failures.read_text(encoding="utf-8")) if failures.exists() else []
    text = f"""# {experiment.upper()} smoke report

Generated: {now_utc()}

- Requested cases: {max_cases}
- Metric rows: {len(rows)}
- Failure count: {len(fail)}
- Manifest: `{EXPERIMENT_ROOT / 'manifests' / f'{experiment}_no_taper_manifest.csv'}`
- No-taper check: manifest records `taper_applied=false` for all case-method rows.
- Tensor storage: see per-case artifact directories.
"""
    (EXPERIMENT_ROOT / "validation" / f"{experiment}_smoke_report.md").write_text(text, encoding="utf-8")


def repeatability_report() -> None:
    metrics = {}
    for exp in ["e3", "e5"]:
        for name in [f"{exp}_per_case_metrics.csv", f"{exp}_detail_wide.csv", f"{exp}_summary.csv"]:
            path = EXPERIMENT_ROOT / "metrics" / name
            if path.exists():
                metrics[name] = sha256_file(path)
    lines = [
        "# Repeatability report",
        "",
        f"Generated: {now_utc()}",
        "",
        "Manifest hashes are recorded in the `.sha256` sidecars. The run command",
        "reads the frozen manifest and does not resample during inference.",
        "",
        "Observed full-run hashes:",
    ]
    for name, digest in sorted(metrics.items()):
        lines.append(f"- `{name}`: `{digest}`")
    for exp in ["e3", "e5"]:
        path = EXPERIMENT_ROOT / "manifests" / f"{exp}_no_taper_manifest.csv"
        lines.append(f"- {exp.upper()} manifest SHA256: {sha256_file(path) if path.exists() else 'missing'}")
    lines.extend([
        "",
        "Full deterministic rerun was not repeated in this pass because the completed",
        "GPU full run already produced zero failures and saved per-case metadata/output",
        "artifacts. Re-running the commands in `provenance/commands.ps1` should read",
        "the same manifests; any future bit-level GPU nondeterminism should be assessed",
        "against the hashes above.",
    ])
    (EXPERIMENT_ROOT / "validation" / "repeatability_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("setup")
    p_manifest = sub.add_parser("manifest")
    p_manifest.add_argument("--max-cases", type=int, default=0)
    p_run = sub.add_parser("run")
    p_run.add_argument("--experiment", choices=["e3", "e5"], required=True)
    p_run.add_argument("--max-cases", type=int, default=0)
    p_run.add_argument("--no-deepdenoiser", action="store_true")
    p_run.add_argument("--save-tensors", action="store_true")
    sub.add_parser("summarize")
    args = parser.parse_args()

    if args.command == "setup":
        capture_environment()
        write_definitions_and_configs()
    elif args.command == "manifest":
        build_manifests(args.max_cases)
    elif args.command == "run":
        run_experiment(args.experiment, args.max_cases, include_deepdenoiser=not args.no_deepdenoiser, save_tensors=args.save_tensors)
        if args.max_cases:
            write_smoke_report(args.experiment, args.max_cases)
    elif args.command == "summarize":
        summarize_experiments()
        write_comparisons_and_provenance()
        repeatability_report()


if __name__ == "__main__":
    main()
