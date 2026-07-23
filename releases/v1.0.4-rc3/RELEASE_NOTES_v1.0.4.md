# Release notes: v1.0.4-rc3

This release candidate adds manuscript-matched E3/E5 reconstructed no-taper
artifacts prepared after v1.0.3.

## Added

- Reconstructed E3 no-taper manifest, metrics, station-leakage summary table,
  and manuscript Table 10 fragment.
- Reconstructed E5 no-taper manifest, metrics, selected-checkpoint summary table,
  and manuscript Table 12 fragment.
- Sanitized public configurations and manifests with relative identifiers.
- Public rebuild and validation scripts for Tables 10 and 12.
- Table 10 displays the evaluator-side source-aware row as `Idealized Wiener`
  rather than the legacy oracle-Wiener display label.
- Current public-facing interpretation text replaces the abandoned
  oracle-based comparison framing with report-card and role-specific wording.
- The misnamed duplicate `tables/table10_reconstructed_no_taper_candidate.tex`
  is excluded from this release candidate.

## Scientific boundary

These artifacts are new no-taper reconstructions, not historical
sample-identical reruns of the originally submitted tapered E3/E5 diagnostics.
They preserve the intended scoring track: descriptive diagnostics only, no
cross-regime primary ranking. The reconstructed diagnostics preserved the
qualitative signs and zero-exclusion conclusions of the submitted tapered
diagnostics; this supports, but does not prove, the expectation that
target-shaping effects were largely common-mode within these shared-target
contrasts.

## Publication status

This is a local release candidate. GitHub tag creation, GitHub release
publication, and Zenodo new-version deposition have not been performed by this
script.
