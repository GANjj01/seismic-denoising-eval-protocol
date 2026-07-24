# Final E3 No-Taper Confounding Closure

- Generated UTC: 2026-07-23T23:53:25+00:00
- Git HEAD: `3a57199d02e46cfce92b8f7ec604560eec9da563`
- Source manifest: `reconstructed_no_taper_e3_e5/manifests/e3_no_taper_manifest.csv`
- Source metric table: `reconstructed_no_taper_e3_e5/metrics/e3_detail_wide.csv`
- Case covariates generated: 1632
- Covariate failures: 0
- Station covariate rows: 48
- Matched station pairs retained: 15
- Direction-consistent unadjusted/regression/matched outcomes: 30/32
- Direction-consistent non-sanity-control outcomes: 30/31
- Zero-exclusion consistency across unadjusted/regression/matched outcomes: 29/32

## Balance Before/After Matching

- noise_rms_full_mean: SMD -0.182 before, +0.555 after.
- dominant_freq_hz_mean: SMD -0.479 before, -0.037 after.
- spectral_slope_1_20_mean: SMD -0.431 before, -0.059 after.
- frame_rms_cv_4s_mean: SMD +0.082 before, +0.066 after.

The prespecified greedy 1:1 station matching retained all 15 familiar stations
and 15 of 33 unseen stations, forming 15 matched pairs. Matching did not
improve the worst-case covariate balance: the maximum absolute SMD increased
from 0.479 before matching to 0.555 after matching because of residual
imbalance in noise RMS. Matched estimates are therefore interpreted as a
limited-overlap secondary sensitivity analysis rather than definitive
deconfounded effects, and they are reported separately from the
regression-adjusted sensitivity estimates.

## Interpretation Boundary

The no-taper closure replaces the earlier tapered-only confounding provenance for the reconstructed E3 diagnostic. It remains a post-hoc sensitivity analysis for the A/B station-domain design, not a causal estimate of station memorization.

Rows graded as suggestive:
- DeepDenoiser / background_suppression_db: direction_consistent=False.
- Noisy / output_vs_clean_snr: direction_consistent=False.
