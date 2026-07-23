# Legacy value audit for E5 amplitude delta

Scope: public-release synchronization check for the reconstructed no-taper E3/E5
artifacts.

## Decision

The current manuscript value for the seed-42 E5 amplitude-ratio delta is
`+0.439`, matching `reconstructed_no_taper_e3_e5/tables/e5_reconstructed_no_taper_table.csv`
(`0.439289768692106`, rounded to three decimals).

## Repairs made

- `manuscript/BlindSpot_evaluation_framework_AIIG_elsarticle.tex`: the current
  Discussion narrative was corrected from `+0.453 amplitude ratio` to
  `+0.439 amplitude ratio`.
- The E5 Results paragraph now says the reconstructed summaries are prepared
  for inclusion in a manuscript-matched versioned archive rather than already
  included in the v1.0.3 revision artifacts.

## Intentionally retained legacy occurrences

- `reconstructed_no_taper_e3_e5/comparison/e5_new_notaper_vs_historical_tapered.md`
  retains `+0.453 | +0.439 | -0.014` as the historical tapered-versus-new
  no-taper comparison.
- `manuscript/generated_tables/table10_e5_terminal_differences.tex` retains
  `+0.4532` as an older unreferenced historical fragment. The current manuscript
  uses `table12_e5_reconstructed_no_taper.tex`.

## Current identity assertions

- E3 identity: `reconstructed_no_taper_shared_target_diagnostic`.
- E3 cases: 1,632; method-case manifest rows: 13,056; failures: 0.
- E3 manuscript table: Table 10.
- E3 `primary_ranking`: false.
- E3 `historical_sample_identical_rerun`: false.
- E5 identity: `reconstructed_no_taper_shared_target_diagnostic`.
- E5 cases: 816; method-case manifest rows: 8,160; failures: 0.
- E5 manuscript table: Table 12.
- E5 `primary_ranking`: false.
- E5 `historical_sample_identical_rerun`: false.
