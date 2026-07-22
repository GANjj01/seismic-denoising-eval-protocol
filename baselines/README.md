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
- `adv_gate_sta_lta`: manuscript-exact STA/LTA AdvGate implementation. This
  optional path requires ObsPy.
- `adv_gate_quantile`: dependency-light quantile energy-gating diagnostic for
  smoke tests and interface checks.
- `adv_gate`: backward-compatible alias for `adv_gate_quantile`.

The paper-era STA/LTA AdvGate implementation is included for provenance in
`legacy_scripts/adversarial_baselines_eval.py`, where the `AdvGate` row maps to
`adv_gate_sta_lta`. Use `blindspot_eval_protocol.baselines.adv_gate_sta_lta`
when reproducing the manuscript-era AdvGate result. Use `adv_gate_quantile` or
the compatibility alias `adv_gate` for dependency-light smoke tests.

Install the optional manuscript dependency set before running the STA/LTA path:

```bash
pip install .[manuscript]
```
