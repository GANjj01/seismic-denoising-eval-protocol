# E3 analysis chain map

| Value/claim | Analysis chain | Taper status | Current role | Manuscript location |
| ----------- | -------------- | ------------ | ------------ | ------------------- |
| E3 uses 1,632 cases | Reconstructed no-taper frozen manifest | no-taper; `taper_applied=false` | Current Table 10 provenance | Section E3, manifest paragraph |
| E3 uses 13,056 method-case rows | Reconstructed no-taper frozen manifest | no-taper; `taper_applied=false` | Current Table 10 provenance | Section E3, manifest paragraph |
| E3 zero failed cases | Reconstructed no-taper frozen manifest | no-taper; `taper_applied=false` | Current Table 10 provenance | Section E3, manifest paragraph |
| DeepDenoiser clean-SNR A--B +0.573 [0.143, 1.048] | Reconstructed no-taper Table 10 unadjusted A--B station-domain contrast | no-taper | Current diagnostic result; not a primary ranking | Section E3 result paragraph; Table 10 |
| Wiener-blind clean-SNR A--B +0.558 [0.084, 1.084] | Reconstructed no-taper Table 10 unadjusted A--B station-domain contrast | no-taper | Current deployable blind-baseline diagnostic result | Section E3 result paragraph; Table 10 |
| `\lambda_{\mathrm{pol}}=0` clean-SNR A--B -0.230 [-0.470, -0.011] | Reconstructed no-taper Table 10 unadjusted A--B station-domain contrast | no-taper | Current self-supervised diagnostic result | Section E3 result paragraph; Table 10 |
| `\lambda_{\mathrm{pol}}=0.1` clean-SNR A--B -0.186 [-0.392, -0.001] | Reconstructed no-taper Table 10 unadjusted A--B station-domain contrast | no-taper | Current self-supervised diagnostic result | Section E3 result paragraph; Table 10 |
| `\lambda_{\mathrm{pol}}=0.5` clean-SNR A--B -0.211 [-0.439, -0.005] | Reconstructed no-taper Table 10 unadjusted A--B station-domain contrast | no-taper | Current self-supervised diagnostic result | Section E3 result paragraph; Table 10 |
| Background-suppression intervals for principal report-card methods span zero | Reconstructed no-taper Table 10 unadjusted A--B station-domain contrast | no-taper | Current diagnostic interpretation | Section E3 result paragraph; Table 10 |
| Spectral slope SMD about -0.415 | Submitted tapered confounding audit | submitted tapered | Design-provenance context only | Section E3 provenance paragraph |
| Dominant-frequency SMD about -0.395 | Submitted tapered confounding audit | submitted tapered | Design-provenance context only | Section E3 provenance paragraph |
| High/low bandpower SMD about -0.392 | Submitted tapered confounding audit | submitted tapered | Design-provenance context only | Section E3 provenance paragraph |
| 29 of 32 directional agreement | Submitted tapered confounding audit across unadjusted, regression-adjusted, and matched analyses | submitted tapered | Design-provenance context only; not recomputed for Table 10 | Section E3 provenance paragraph |
| 14/15 A stations retained | Submitted tapered station-matching audit | submitted tapered | Design-provenance context only | Section E3 provenance paragraph |
| 14/33 B stations retained | Submitted tapered station-matching audit | submitted tapered | Design-provenance context only | Section E3 provenance paragraph |
| Residual noise-RMS SMD 0.169 | Submitted tapered station-matching audit | submitted tapered | Residual imbalance caveat | Section E3 provenance paragraph |
| Earlier adjusted DeepDenoiser +0.714 | Submitted tapered regression-adjusted confounding audit | submitted tapered | Historical design-provenance value if cited; not recomputed for Table 10 | Not cited in current manuscript after this patch |
| Earlier adjusted Wiener-blind +0.590 | Submitted tapered regression-adjusted confounding audit | submitted tapered | Historical design-provenance value if cited; not recomputed for Table 10 | Not cited in current manuscript after this patch |

Boundary statement inserted in the manuscript:

> The following spectral-balance, regression-adjustment, and station-matching results derive from the submitted tapered confounding audit and are retained only as design-provenance context; they were not recomputed as part of the reconstructed no-taper Table~\ref{tab:e3_leakage} analysis.
