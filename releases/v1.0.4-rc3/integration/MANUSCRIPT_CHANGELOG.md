# Manuscript Changelog

Scope: E3/E5 manuscript integration of the completed reconstructed no-taper experiments.

## Changed Files

| File | Change |
| --- | --- |
| `manuscript/BlindSpot_evaluation_framework_AIIG_elsarticle.tex` | Updated Methods scoring tracks; replaced E3 and E5 current-result wording with reconstructed no-taper shared-target diagnostics; updated Table 10 and Table 12 inputs/captions; added Discussion and Limitations boundary language. |
| `manuscript/generated_tables/table10_e3_reconstructed_no_taper.tex` | New manuscript Table 10 fragment generated from `reconstructed_no_taper_e3_e5/tables/e3_reconstructed_no_taper_table.csv`. |
| `manuscript/generated_tables/table12_e5_reconstructed_no_taper.tex` | New manuscript Table 12 fragment generated from `reconstructed_no_taper_e3_e5/tables/e5_reconstructed_no_taper_table.csv`. |
| `manuscript/generated_tables/table_analysis_timeline.tex` | Supplementary timeline updated so E3/E5 are current reconstructed no-taper diagnostics; historical tapered E3 confounding/matching rows are provenance sensitivity. |

## Final Manuscript Wording Boundaries

- E3/E5 are `reconstructed no-taper shared-target diagnostics`.
- They are not primary report-card rankings.
- They are not historical sample-identical reruns of the submitted tapered E3/E5 experiments.
- Historical tapered E3/E5 artifacts remain provenance only.
- Differences between historical tapered and reconstructed no-taper values cannot be attributed to taper removal alone.

## Table Mapping

| Revised table | Label | Current fragment | Numeric source |
| --- | --- | --- | --- |
| Table 10 | `tab:e3_leakage` | `manuscript/generated_tables/table10_e3_reconstructed_no_taper.tex` | `reconstructed_no_taper_e3_e5/tables/e3_reconstructed_no_taper_table.csv` |
| Table 12 | `tab:e5_performance` | `manuscript/generated_tables/table12_e5_reconstructed_no_taper.tex` | `reconstructed_no_taper_e3_e5/tables/e5_reconstructed_no_taper_table.csv` |

## Numeric Anchors Inserted

E3 clean-SNR A--B leakage gain:

- DeepDenoiser: +0.573 dB [0.143, 1.048]
- Wiener-blind: +0.558 dB [0.084, 1.084]
- `lambda_pol=0`: -0.230 dB [-0.470, -0.011]
- `lambda_pol=0.1`: -0.186 dB [-0.392, -0.001]
- `lambda_pol=0.5`: -0.211 dB [-0.439, -0.005]

E5 `lambda_pol=0.5 - lambda_pol=0` terminal contrasts:

- Seed 42: clean-SNR -0.462 dB, amplitude ratio +0.439, correlation +0.025
- Seed 43: clean-SNR -0.063 dB, amplitude ratio -0.044, correlation -0.017
- Seed 44: clean-SNR -0.088 dB, amplitude ratio +0.048, correlation +0.032

## Historical Files Preserved

The older fragments `manuscript/generated_tables/table08_station_leakage_diagnostic.tex` and `manuscript/generated_tables/table10_e5_terminal_differences.tex` were not overwritten or deleted. They are no longer referenced by the main manuscript table inputs for revised Tables 10 and 12.
