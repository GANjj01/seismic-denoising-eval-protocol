# Oracle Recovery Probe

This folder contains the oracle-recovery diagnostic tables used to calibrate
the report-card metrics against a controlled recovery fraction.  The diagnostic
is not a deployable denoiser; it is a metric probe that mixes the noisy input
with known clean target information at fixed recovery fractions.

Files:

- `oracle_free_recovery_probe.py`: script that rebuilds the deterministic
  oracle-free case set and scores synthetic oracle-recovery outputs.
- `recovery_probe_summary.csv`: method-level summary across all 816
  oracle-free continuous cases.
- `recovery_probe_by_snr.csv`: summary stratified by injected target SNR.
- `recovery_probe_station_bootstrap_vs_identity.csv`: station-level bootstrap
  contrasts against the identity baseline.
- `recovery_probe_monotonic_checks.csv`: monotonicity checks for the oracle
  recovery fractions.
- `recovery_probe_detail.csv`: per-case metric table.

These tables help interpret the dynamic range of clean-SNR gain, waveform
correlation, amplitude ratio, lag, and background suppression under a known
oracle recovery ladder.
