# Historical Code Map

- Tapered spectral covariates: `../experiments/scripts/analyze_station_leakage_noise_covariates.py`.
- Tapered unadjusted station leakage: `../experiments/scripts/analyze_station_leakage_gain.py`.
- Tapered regression helper: `../experiments/scripts/analyze_station_leakage_adjusted_gain.py`.
- Revision confounding audit implementation used for the manuscript provenance: `analysis/scripts/audit_station_leakage_confounding.py`.
- Frozen audit configuration: `analysis/configs/station_leakage_analysis.yml`.

The present no-taper closure applies those recovered rules to the reconstructed no-taper E3 manifest and saved tensors.
