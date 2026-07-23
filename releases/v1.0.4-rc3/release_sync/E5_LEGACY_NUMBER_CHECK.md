# E5 legacy number check

Date: 2026-07-24

## Current formal reconstructed no-taper values

- Seed 42: clean-SNR delta `-0.462`, amplitude-ratio delta `+0.439`,
  correlation delta `+0.025`.
- Seed 43: clean-SNR delta `-0.063`, amplitude-ratio delta `-0.044`,
  correlation delta `-0.017`.
- Seed 44: clean-SNR delta `-0.088`, amplitude-ratio delta `+0.048`,
  correlation delta `+0.032`.
- Current median amplitude-ratio delta: `+0.048`.

Numeric source:

- `reconstructed_no_taper_e3_e5/tables/e5_reconstructed_no_taper_table.csv`
- `manuscript/generated_tables/table12_e5_reconstructed_no_taper.tex`

## Allowed legacy values

- `+0.453` appears only as the historical tapered seed-42 amplitude-ratio delta
  in `comparison/e5_new_notaper_vs_historical_tapered.md` and earlier audit
  prose that explicitly labels it as historical.
- `+0.0529` or rounded `+0.053` appears only in old unused fragments or the
  historical tapered-versus-new no-taper comparison.

## Not allowed

The legacy values must not appear as current values in:

- current manuscript Results;
- current manuscript Discussion;
- response letter;
- cover letter;
- Table 12;
- public release notes current-result summary.

## Verification

The current manuscript and response report `+0.439` for seed 42 and `+0.048` as
the median/seed-44 no-taper amplitude-ratio value. The current manuscript and
response contain zero `+0.453` and zero `+0.0529` occurrences after this patch.
