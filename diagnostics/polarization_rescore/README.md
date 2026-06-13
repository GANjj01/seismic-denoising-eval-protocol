# Polarization Rescoring Diagnostic

This folder contains the three-component polarization rescoring diagnostic used
to audit whether the Z-component report-card correlation unfairly penalizes
CovNorm-style models that couple Z/N/E channels.

Files:

- `oracle_free_polarization_rescore.py`: script that rebuilds the deterministic
  oracle-free case set, reruns the listed model/checkpoint outputs, and computes
  three-component polarization metrics.
- `polarization_rescore_summary.csv`: method-level polarization and
  three-component correlation summary across all 816 oracle-free continuous
  cases.
- `polarization_rescore_by_snr.csv`: summary stratified by injected target SNR.
- `polarization_station_bootstrap_vs_identity.csv`: station-level bootstrap
  contrasts against the identity baseline.
- `polarization_covnorm_pair_bootstrap.csv`: paired CovNorm station-bootstrap
  contrasts.
- `polarization_rescore_detail.csv`: per-case polarization and component-wise
  correlation table.
- `covnorm_dcov_noisy_vs_clean.png`: diagnostic scatter/summary figure for
  CovNorm covariance-distance behavior.

The diagnostic complements the main Z-component report card by reporting
component-wise correlations, covariance-distance scores, polarization-angle
error, and rectilinearity/planarity errors.
