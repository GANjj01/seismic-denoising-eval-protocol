"""Small baseline transforms for protocol diagnostics.

The NumPy implementations mirror the paper's identity and adversarial baselines.
They are intentionally simple: these are report-card controls, not competitive
denoisers.
"""

from __future__ import annotations

try:
    import numpy as np
except Exception:  # pragma: no cover - lets docs import without NumPy.
    np = None


def identity(x):
    """No-op baseline: output equals input."""
    return x.copy() if hasattr(x, "copy") else x


def adv_scale(x, scale: float = 0.01):
    """Global amplitude shrink; SNR ratio is unchanged but background drops."""
    return x * scale


def adv_shrink(x, tau: float = 3.0):
    """Coordinatewise soft-thresholding with a robust MAD threshold."""
    if np is None:
        raise RuntimeError("adv_shrink requires NumPy")
    med = np.median(x, axis=0, keepdims=True)
    mad = np.median(np.abs(x - med), axis=0, keepdims=True) + 1e-12
    threshold = tau * mad
    return (np.sign(x) * np.maximum(np.abs(x) - threshold, 0.0)).astype(x.dtype, copy=False)


def adv_gate_quantile(x, energy_threshold_quantile: float = 0.90):
    """Dependency-light quantile energy gate for smoke tests.

    The manuscript's AdvGate uses STA/LTA.  This dependency-light variant keeps
    only high-energy samples and demonstrates the same metric-failure mode.
    """
    if np is None:
        raise RuntimeError("adv_gate requires NumPy")
    energy = np.linalg.norm(x.astype(float), axis=-1)
    threshold = np.quantile(energy, energy_threshold_quantile)
    gate = (energy >= threshold).astype(x.dtype)
    while gate.ndim < x.ndim:
        gate = gate[..., None]
    return x * gate


def adv_gate_sta_lta(x, fs: float, sta_s: float = 0.5, lta_s: float = 10.0, tau: float = 2.5):
    """Manuscript-exact STA/LTA AdvGate used for Table 4 and Figure 5.

    This implementation requires ObsPy.  It gates samples using
    ``obspy.signal.trigger.classic_sta_lta`` applied to the three-component
    energy trace, matching the paper-era legacy evaluation script.
    """
    if np is None:
        raise RuntimeError("adv_gate_sta_lta requires NumPy")
    try:
        from obspy.signal.trigger import classic_sta_lta
    except Exception as exc:  # pragma: no cover - optional dependency path.
        raise RuntimeError("adv_gate_sta_lta requires ObsPy") from exc
    energy = np.linalg.norm(x.astype(float), axis=-1)
    cft = classic_sta_lta(energy, int(sta_s * fs), int(lta_s * fs))
    gate = (cft > tau).astype(x.dtype)
    while gate.ndim < x.ndim:
        gate = gate[..., None]
    return (x * gate).astype(x.dtype, copy=False)


def adv_gate(x, energy_threshold_quantile: float = 0.90):
    """Backward-compatible alias for the dependency-light quantile gate.

    Use ``adv_gate_sta_lta`` for manuscript Table 4/Figure 5 reproduction.
    """
    return adv_gate_quantile(x, energy_threshold_quantile=energy_threshold_quantile)


BASELINES = {
    "Identity": identity,
    "AdvScale": adv_scale,
    "AdvShrink": adv_shrink,
    "AdvGate": adv_gate,
    "AdvGateQuantile": adv_gate_quantile,
}
