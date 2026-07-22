# v1.0.3 Revision Release Notes

Status: prepared locally; pending authorized push, tag, GitHub release, Zenodo
new version, and public access verification.

This revision release updates the existing public repository for the major
revision of:

> A Reproducible Evaluation Protocol for Self-Supervised Three-Component
> Blind-Spot Seismic Denoising

## Main Updates

- Updates README and citation metadata from the earlier release-candidate
  language to the v1.0.3 revision-release candidate.
- Records the empirical scope as Raspberry Shake AM single-station
  three-component evaluation rather than instrument-independent validation.
- Clarifies that legacy `oracle_free` filenames correspond to controlled
  reference-based mixture evaluation with evaluator-held pseudo-clean
  references in the revised manuscript terminology.
- Clarifies the AdvGate provenance boundary: manuscript-era results used the
  archived STA/LTA implementation, while the reusable package keeps a
  dependency-light quantile-energy `adv_gate` variant for smoke tests and
  interface checks.
- Keeps historical releases intact and prepares a new versioned release rather
  than modifying old tags or old Zenodo files.

## Archiving Plan

The project already has a Zenodo concept DOI:

```text
10.5281/zenodo.20681569
```

Stage 8B should create a new Zenodo version under the existing record and then
replace the pending DOI/status fields with the exact v1.0.3 version DOI.

## Compatibility

No breaking Python package API change is intended. The public API name
`adv_gate` is retained. Legacy filenames are not renamed.
