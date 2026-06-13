"""Thin adapter sketch for evaluating SeisBench denoisers in the report card.

The protocol needs only one contract: a method receives a three-component
mixture array and returns a three-component output array with the same shape.
SeisBench models can be wrapped behind this contract and then scored by the
same final-real and oracle-free evaluators.
"""

from __future__ import annotations


class SeisBenchDenoiserAdapter:
    """Wrap a SeisBench model as a protocol denoiser.

    This class is intentionally thin because SeisBench model families differ in
    preprocessing expectations.  Keep all resampling, filtering, channel order,
    and normalization explicit in the caller or subclass.
    """

    def __init__(self, model, preprocess=None, postprocess=None):
        self.model = model
        self.preprocess = preprocess or (lambda x: x)
        self.postprocess = postprocess or (lambda y: y)

    def __call__(self, waveform_3c):
        prepared = self.preprocess(waveform_3c)
        prediction = self.model(prepared)
        return self.postprocess(prediction)
