# Terminology audit

Date: 2026-07-24

## Current policy

- `Wiener-blind`: deployable blind signal-processing baseline.
- `Idealized Wiener (source-aware diagnostic)`: evaluator-side clean/noise
  decomposition diagnostic. In space-constrained tables, display as
  `Idealized Wiener` and define the source-aware role in the caption or note.
- `Noisy`: unprocessed-input sanity control.

## Manuscript-facing changes

- Table 10 display name changed from the legacy oracle-Wiener display label to
  `Idealized Wiener`.
- Table 10 caption now states:
  - `The Noisy row is the unprocessed-input sanity control; zero-valued gain contrasts are expected by construction where applicable.`
  - `The Idealized Wiener row uses evaluator-side source decomposition and is included only as a source-aware sensitivity diagnostic; it is not a deployable baseline and is excluded from the principal report-card interpretation.`
- Baseline-role table now uses `Idealized Wiener (source-aware diagnostic)`.
- Supplementary component-correlation table display label changed to
  `Idealized Wiener`.

## Frozen internal identifiers

The frozen CSV, manifest, and metric files still contain internal method IDs such
as `Wiener_oracle`. These files were not edited, consistent with the no-rerun and
no-metric-modification boundary. Public LaTeX tables and explanatory text map
that internal identifier to `Idealized Wiener`.

## Verification target

- Current manuscript and rc2 public display tables should contain zero
  occurrences of the legacy oracle-Wiener display label.
- `Idealized Wiener` must be accompanied by the source-aware diagnostic boundary
  in manuscript Table 10 or package README/release notes.

## Banned-term migration record

| Banned public-facing phrase | Replacement | Allowed context |
| --- | --- | --- |
| `principal non-oracle interpretation` | `principal report-card interpretation` | quoted banned-term list or migration record only |
| `principal non-oracle methods` | `principal report-card methods` | quoted banned-term list or migration record only |
| `non-oracle methods` | role-specific wording such as `principal report-card methods`, `deployable-baseline comparison`, or `source-aware diagnostic` | quoted banned-term list or migration record only |
| `non-oracle interpretation` | `principal report-card interpretation` | quoted banned-term list or migration record only |
