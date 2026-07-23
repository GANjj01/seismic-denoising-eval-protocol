# Pre-release patch changelog

Date: 2026-07-24

## Scope

This patch addresses terminology, provenance, and file-integrity issues before a
future public v1.0.4 release. It does not rerun E3/E5, reselect checkpoints,
modify frozen manifests, modify per-case metrics, change numerical table values,
commit, push, create a GitHub release, or publish a Zenodo version.

## Changes

- Table 10 public display label changed from the legacy oracle-Wiener display
  label to `Idealized Wiener`.
- Table 10 caption now defines both the Noisy row and Idealized Wiener row.
- The abandoned oracle/non-oracle framing was removed from current public-facing
  interpretation text and replaced with report-card and role-specific wording.
- Baseline-role wording now separates `Wiener-blind` from
  `Idealized Wiener (source-aware diagnostic)`.
- E3 Results now explicitly separates the reconstructed no-taper Table 10 chain
  from the submitted tapered spectral-balance/regression/matching confounding
  audit.
- Discussion and response wording now state that reconstructed E3/E5 preserved
  qualitative signs and zero-exclusion conclusions, with the limitation
  `supports, but does not prove`.
- The duplicate misnamed E5 candidate file
  `tables/table10_reconstructed_no_taper_candidate.tex` was deleted and removed
  from provenance file hashes.
- The v1.0.4 staging script now produces rc2 instead of overwriting rc1.

## Unchanged

- E3/E5 manifests.
- E3/E5 per-case metrics.
- E3/E5 frozen CSV summaries.
- Current E3 and E5 scientific values.
- v1.0.3 public release.
- `submitted_original`.
