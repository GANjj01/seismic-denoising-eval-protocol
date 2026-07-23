# E3 reconstructed no-taper versus historical tapered diagnostic

Generated: 2026-07-23T17:30:43+00:00

The reconstructed no-taper analysis is not asserted to be sample-identical to the submitted tapered diagnostic; differences cannot be attributed exclusively to taper removal.

| Method | Metric | Historical tapered A-B | Reconstructed no-taper A-B | Difference | New CI | New zero-excluded |
|---|---:|---:|---:|---:|---:|---:|
| Noisy | output_vs_clean_snr | -0.000 | +0.000 | +0.000 | [-0.000, +0.000] | false |
| Noisy | amp_ratio_clean | +0.348 | +0.303 | -0.044 | [-0.234, +0.859] | false |
| Noisy | corr_z | +0.020 | +0.019 | -0.000 | [-0.040, +0.078] | false |
| Noisy | background_suppression_db | +0.000 | +0.000 | -0.000 | [-0.000, +0.000] | false |
| Bandpass | output_vs_clean_snr | +0.230 | +0.231 | +0.000 | [-0.294, +0.981] | false |
| Bandpass | amp_ratio_clean | +0.196 | +0.165 | -0.031 | [-0.273, +0.604] | false |
| Bandpass | corr_z | +0.035 | +0.034 | -0.000 | [-0.022, +0.088] | false |
| Bandpass | background_suppression_db | +0.076 | +0.076 | -0.000 | [-0.423, +0.723] | false |
| Wiener_blind | output_vs_clean_snr | +0.560 | +0.558 | -0.002 | [+0.084, +1.084] | true |
| Wiener_blind | amp_ratio_clean | +0.310 | +0.282 | -0.027 | [-0.131, +0.696] | false |
| Wiener_blind | corr_z | +0.043 | +0.043 | -0.000 | [-0.014, +0.098] | false |
| Wiener_blind | background_suppression_db | +0.264 | +0.263 | -0.001 | [-0.423, +0.981] | false |
| Wiener_oracle | output_vs_clean_snr | +2.357 | +2.353 | -0.004 | [+1.444, +3.269] | true |
| Wiener_oracle | amp_ratio_clean | +0.124 | +0.124 | +0.000 | [+0.047, +0.202] | true |
| Wiener_oracle | corr_z | +0.066 | +0.066 | -0.000 | [+0.026, +0.106] | true |
| Wiener_oracle | background_suppression_db | +0.576 | +0.556 | -0.021 | [-0.570, +1.662] | false |
| p0_e06 | output_vs_clean_snr | -0.228 | -0.230 | -0.002 | [-0.470, -0.011] | true |
| p0_e06 | amp_ratio_clean | +0.094 | +0.081 | -0.013 | [-0.258, +0.429] | false |
| p0_e06 | corr_z | -0.011 | -0.011 | +0.001 | [-0.063, +0.040] | false |
| p0_e06 | background_suppression_db | -0.590 | -0.589 | +0.000 | [-1.371, +0.149] | false |
| p01_e07 | output_vs_clean_snr | -0.183 | -0.186 | -0.002 | [-0.392, -0.001] | true |
| p01_e07 | amp_ratio_clean | +0.173 | +0.154 | -0.019 | [-0.182, +0.489] | false |
| p01_e07 | corr_z | -0.011 | -0.010 | +0.001 | [-0.060, +0.038] | false |
| p01_e07 | background_suppression_db | -0.471 | -0.471 | +0.001 | [-1.151, +0.172] | false |
| p05_e16 | output_vs_clean_snr | -0.210 | -0.211 | -0.001 | [-0.439, -0.005] | true |
| p05_e16 | amp_ratio_clean | +0.215 | +0.191 | -0.024 | [-0.120, +0.515] | false |
| p05_e16 | corr_z | -0.019 | -0.019 | +0.001 | [-0.071, +0.033] | false |
| p05_e16 | background_suppression_db | -0.376 | -0.374 | +0.002 | [-1.131, +0.348] | false |
| DeepDenoiser | output_vs_clean_snr | +0.624 | +0.573 | -0.051 | [+0.143, +1.048] | true |
| DeepDenoiser | amp_ratio_clean | +0.154 | +0.145 | -0.009 | [+0.060, +0.239] | true |
| DeepDenoiser | corr_z | +0.051 | +0.046 | -0.005 | [-0.009, +0.100] | false |
| DeepDenoiser | background_suppression_db | -0.919 | -0.914 | +0.005 | [-3.650, +1.793] | false |

Qualitative reading: use this as an auxiliary station-domain diagnostic. The new reconstruction preserves the A/B scientific frame but does not prove a historical sample-identical no-taper replay.
