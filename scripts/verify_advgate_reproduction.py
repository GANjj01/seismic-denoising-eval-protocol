"""Verify AdvGate public API and manuscript-reproduction mapping."""

from __future__ import annotations

import builtins
import inspect
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import numpy as np

from blindspot_eval_protocol import baselines


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def synthetic_trace() -> np.ndarray:
    x = np.zeros((2000, 3), dtype=np.float32)
    x[:, 0] = 0.1 * np.sin(np.arange(2000) / 17.0)
    x[1200:1240, 0] += 10.0
    return x


def simulate_missing_obspy(x: np.ndarray) -> None:
    original_import = builtins.__import__

    def guarded_import(name, *args, **kwargs):
        if name.startswith("obspy"):
            raise ImportError("simulated missing ObsPy")
        return original_import(name, *args, **kwargs)

    try:
        builtins.__import__ = guarded_import
        quantile = baselines.adv_gate_quantile(x, energy_threshold_quantile=0.90)
        alias = baselines.adv_gate(x, energy_threshold_quantile=0.90)
        require(np.array_equal(alias, quantile), "adv_gate alias changed under missing-ObsPy simulation")
        try:
            baselines.adv_gate_sta_lta(x, fs=100.0)
        except RuntimeError as exc:
            require("ObsPy" in str(exc), "missing-ObsPy error message should name ObsPy")
        else:
            raise AssertionError("adv_gate_sta_lta should fail clearly when ObsPy is unavailable")
    finally:
        builtins.__import__ = original_import


def main() -> None:
    legacy = ROOT / "legacy_scripts" / "adversarial_baselines_eval.py"
    legacy_text = legacy.read_text(encoding="utf-8")

    require(hasattr(baselines, "adv_gate_sta_lta"), "missing adv_gate_sta_lta")
    require(hasattr(baselines, "adv_gate_quantile"), "missing adv_gate_quantile")
    require(baselines.adv_gate is not baselines.adv_gate_sta_lta, "adv_gate should not silently point to STA/LTA")
    require("classic_sta_lta" in inspect.getsource(baselines.adv_gate_sta_lta), "STA/LTA function does not reference classic_sta_lta")
    require('"AdvGate": adv_gate_sta_lta(x)' in legacy_text, "legacy paper script does not map AdvGate to adv_gate_sta_lta")

    x = synthetic_trace()
    quantile = baselines.adv_gate_quantile(x, energy_threshold_quantile=0.90)
    alias = baselines.adv_gate(x, energy_threshold_quantile=0.90)

    require(np.array_equal(alias, quantile), "adv_gate alias should match adv_gate_quantile")
    require(quantile.shape == x.shape, "quantile output shape changed")
    require(quantile.dtype == x.dtype, "quantile output dtype changed")
    require(np.count_nonzero(quantile) > 0, "quantile gate removed the fixed burst unexpectedly")

    simulate_missing_obspy(x)

    try:
        sta_lta = baselines.adv_gate_sta_lta(x, fs=100.0, sta_s=0.5, lta_s=10.0, tau=2.5)
    except RuntimeError as exc:
        require("ObsPy" in str(exc), "STA/LTA failure should mention ObsPy")
        print("ObsPy unavailable; STA/LTA runtime check skipped after clear optional-dependency error.")
    else:
        require(sta_lta.shape == x.shape, "STA/LTA output shape changed")
        require(sta_lta.dtype == x.dtype, "STA/LTA output dtype changed")
        require(np.count_nonzero(sta_lta) > 0, "STA/LTA gate removed the fixed burst unexpectedly")
        require(not np.array_equal(sta_lta, quantile), "STA/LTA and quantile gates should remain distinguishable")
        print("ObsPy available; STA/LTA runtime check passed.")

    print("AdvGate reproduction verification passed.")


if __name__ == "__main__":
    main()
