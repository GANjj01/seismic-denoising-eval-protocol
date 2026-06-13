"""Metric definitions used by the blind-spot denoising report card.

The full paper implementation computes these metrics on 3C NumPy arrays.  This
module keeps the formula-level utilities small and dependency-light so a new
baseline can reuse the same semantics without importing training code.
"""

from __future__ import annotations

import math
from typing import Iterable


EPS = 1e-12


def rms(values: Iterable[float]) -> float:
    vals = [float(v) for v in values]
    if not vals:
        return 0.0
    return math.sqrt(sum(v * v for v in vals) / len(vals))


def db_ratio(numerator: float, denominator: float, eps: float = EPS) -> float:
    return 20.0 * math.log10((float(numerator) + eps) / (float(denominator) + eps))


def clean_snr(output_minus_clean: Iterable[float], clean: Iterable[float]) -> float:
    """Absolute clean SNR: 20 log10(rms(clean) / rms(output - clean))."""
    return db_ratio(rms(clean), rms(output_minus_clean))


def clean_snr_gain(output_minus_clean: Iterable[float], input_minus_clean: Iterable[float], clean: Iterable[float]) -> float:
    """Reported continuous metric: clean SNR(output) - clean SNR(input)."""
    return clean_snr(output_minus_clean, clean) - clean_snr(input_minus_clean, clean)


def amplitude_ratio(output_window: Iterable[float], clean_window: Iterable[float]) -> float:
    return (rms(output_window) + EPS) / (rms(clean_window) + EPS)


def background_suppression(input_background: Iterable[float], output_background: Iterable[float]) -> float:
    return db_ratio(rms(input_background), rms(output_background))
