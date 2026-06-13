# Baseline Controls

The reusable baseline transforms live in:

```text
src/blindspot_eval_protocol/baselines.py
```

Included controls:

- `Identity`: output equals input; required for detecting pass-through models.
- `AdvScale`: global shrink, useful for showing that background suppression can
  be gamed without improving waveform recovery.
- `AdvShrink`: soft-thresholding diagnostic.
- `AdvGate`: energy-gating diagnostic.

The paper-era STA/LTA AdvGate implementation is kept in the internal archive.
The anonymous release keeps only the dependency-light baseline controls used by
the smoke-testable report-card interface.
