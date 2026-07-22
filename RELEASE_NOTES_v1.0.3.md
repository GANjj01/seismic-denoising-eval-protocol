# v1.0.3 Release Notes

This release updates the evaluation-protocol artifacts for:

> A Reproducible Evaluation Protocol for Self-Supervised Three-Component
> Blind-Spot Seismic Denoising

## User-Visible Updates

- Updates README and citation metadata for the v1.0.3 artifact set.
- Records the empirical scope as Raspberry Shake AM single-station
  three-component evaluation rather than instrument-independent validation.
- Clarifies that legacy `oracle_free` filenames correspond to controlled
  reference-based mixture evaluation with evaluator-held pseudo-clean
  references in the revised manuscript terminology.
- Clarifies the AdvGate provenance boundary: manuscript-era results used the
  archived STA/LTA implementation, while the reusable package keeps a
  dependency-light quantile-energy `adv_gate` variant for smoke tests and
  interface checks.
- Adds explicit public AdvGate entry points:
  `adv_gate_sta_lta`, `adv_gate_quantile`, and the compatibility alias
  `adv_gate`.
- Updates package metadata, license metadata, and checksum records.
- Replaces local checkpoint paths in released training provenance with neutral
  `<TRAINING_WORKSPACE>/...` placeholders.

## Compatibility

No breaking Python package API change is intended. The public API name
`adv_gate` is retained. Legacy filenames are not renamed.
