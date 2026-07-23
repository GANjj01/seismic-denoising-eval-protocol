# Oracle terminology cleanup

Date: 2026-07-24

## Cleanup decision

The project no longer uses an oracle/non-oracle interpretive frame in current
public-facing scientific text. The deployable signal-processing baseline is
`Wiener-blind`; the evaluator-side clean/noise decomposition row is
`Idealized Wiener (source-aware diagnostic)` or `Idealized Wiener` in compact
tables.

## Replacements

- Table 10 caption:
  - old: `excluded from the principal non-oracle interpretation`
  - new: `excluded from the principal report-card interpretation`
- E3 Results:
  - old: `principal non-oracle methods`
  - new: `principal report-card methods`
- Reviewer 2, Comment 11 response:
  - old: `principal non-oracle methods`
  - new: `principal report-card methods`
- v1.0.4 README:
  - uses `principal report-card interpretation`.
- v1.0.4 release notes:
  - refers to `oracle-based comparison framing`, not the abandoned slash-form
    wording.

## Boundaries

- No E3/E5 metrics, manifests, checkpoint references, bootstrap outputs, or
  scientific values were modified.
- Frozen internal identifiers such as `Wiener_oracle` in metrics and manifests
  are retained where they are part of immutable provenance; public display text
  maps that identifier to `Idealized Wiener`.
- Historical audit files may quote banned phrases only in migration records or
  banned-term lists.
