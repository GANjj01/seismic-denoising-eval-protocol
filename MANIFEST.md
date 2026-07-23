# Manifest

Version: v1.0.4.

The v1.0.4 manuscript-matched release package is staged in
`releases/v1.0.4/` and does not overwrite the preserved v1.0.3 tag or release.
The public GitHub Release is
<https://github.com/GANjj01/seismic-denoising-eval-protocol/releases/tag/v1.0.4>.
The v1.0.4 Zenodo version DOI is <https://doi.org/10.5281/zenodo.21516779>;
the project concept DOI is <https://doi.org/10.5281/zenodo.20681569>.

## Reusable Protocol Code

- `src/blindspot_eval_protocol/metrics.py`
- `src/blindspot_eval_protocol/baselines.py`
- `src/blindspot_eval_protocol/report_card.py`
- `src/blindspot_eval_protocol/seisbench_adapter.py`

## Scripts

- `scripts/run_smoke_test.py`
- `scripts/run_smoke_test.cmd`
- `scripts/fetch_raspberryshake_windows.py`

## Frozen Splits And Indices

- `splits/train_val_stations.txt`
- `splits/development_stations.txt`
- `splits/final_test_stations.txt`
- `indices/oracle_free_816_case_index.csv` (legacy filename; controlled
  reference-based mixture index in revised terminology)
- `indices/final_real_272_event_index.csv`

## Derived Tables

- `per_case_metrics/oracle_free_816_all_methods.csv` (legacy filename;
  controlled reference-based mixture metrics in revised terminology)
- `per_case_metrics/final_real_272_all_methods.csv`
- `per_case_metrics/self_supervised_identity_summary_gain.csv`
- `per_case_metrics/six_way_oracle_free_report_card.csv`
- `per_case_metrics/station_bootstrap_vs_identity.csv`

## CovNorm Case-Study Provenance

- `training/covnorm_case_study_manifest.md`
- `training/e1_checkpoint_ranking/ranking_correlations.csv`
- `training/e1_checkpoint_ranking/checkpoint_selections.csv`
- `training/e1_checkpoint_ranking/checkpoint_ranking_table.csv`
- `training/e1_checkpoint_ranking/selection_regret.csv`
- `training/e1_checkpoint_ranking/selection_regret_aggregate.csv`
- `training/e4_checkpoint_selection_stability/single_seed_bootstrap_summary.csv`
- `training/e4_checkpoint_selection_stability/single_seed_selected_epoch_frequency.csv`
- `training/e4_checkpoint_selection_stability/single_seed_size_stability_curve.csv`
- `training/e4_checkpoint_selection_stability/single_seed_size_regret_summary.csv`
- `training/e4_checkpoint_selection_stability/multiseed_full_run_checkpoint_selection.csv`
- `training/e4_checkpoint_selection_stability/multiseed_within_seed_stability.csv`
- `training/e4_checkpoint_selection_stability/multiseed_between_seed_epoch_consistency.csv`
- `training/e4_checkpoint_selection_stability/multiseed_seed_epoch_range.csv`
- `training/e4_checkpoint_selection_stability/multiseed_selected_epoch_frequency.csv`
- `training/e5_multiseed_covnorm/development_selection/checkpoint_selection.csv`
- `training/e5_multiseed_covnorm/development_selection/checkpoint_manifest.csv`
- `training/e5_multiseed_covnorm/development_selection/selected_checkpoints.json`
- `training/e5_multiseed_covnorm/development_selection/development_all_epochs_summary.csv`
- `training/e5_multiseed_covnorm/dynamics/epoch_dynamics.csv`
- `training/e5_multiseed_covnorm/dynamics/dynamics_scalar_summary.csv`
- `training/e5_multiseed_covnorm/dynamics/paired_gamma_epoch10.csv`
- `training/e5_multiseed_covnorm/dynamics/run_audit.csv`
- `training/e5_multiseed_covnorm/english_epoch_logs/*.english_summary.txt`
- `training/e5_multiseed_covnorm/english_epoch_logs/*.epoch_log.csv`
- `training/e5_multiseed_covnorm/performance/oracle_free_selected_by_run.csv`
- `training/e5_multiseed_covnorm/performance/paired_performance_differences.csv`
- `training/e5_multiseed_covnorm/performance/seed_variance_vs_lambda_effect.csv`
- `training/e5_multiseed_covnorm/performance/performance_stats.json`

## Diagnostics

- `diagnostics/noise_correlation_diagnostic_summary.csv`
- `diagnostics/noise_correlation_by_station.csv`
- `diagnostics/covnorm_region_consistency.csv`
- `diagnostics/recovery_probe/README.md`
- `diagnostics/recovery_probe/oracle_free_recovery_probe.py`
- `diagnostics/recovery_probe/recovery_probe_summary.csv`
- `diagnostics/recovery_probe/recovery_probe_by_snr.csv`
- `diagnostics/recovery_probe/recovery_probe_station_bootstrap_vs_identity.csv`
- `diagnostics/recovery_probe/recovery_probe_monotonic_checks.csv`
- `diagnostics/recovery_probe/recovery_probe_detail.csv`
- `diagnostics/polarization_rescore/README.md`
- `diagnostics/polarization_rescore/oracle_free_polarization_rescore.py`
- `diagnostics/polarization_rescore/polarization_rescore_summary.csv`
- `diagnostics/polarization_rescore/polarization_rescore_by_snr.csv`
- `diagnostics/polarization_rescore/polarization_station_bootstrap_vs_identity.csv`
- `diagnostics/polarization_rescore/polarization_covnorm_pair_bootstrap.csv`
- `diagnostics/polarization_rescore/polarization_rescore_detail.csv`
- `diagnostics/polarization_rescore/covnorm_dcov_noisy_vs_clean.png`

## Environments

- `environments/environment-seismic.yml`
- `environments/environment-deepdenoiser.yml`

## Provenance Scripts

Legacy one-off scripts were consolidated into reusable modules under `src/`.
Unreleased local scripts are not required for the released smoke test,
report-card reproduction, or CovNorm case-study audit tables.

## Release Metadata

- `CITATION.cff`
- `LICENSE`
- `LICENSE-CODE`
- `LICENSE-DATA`
- `RELEASE_NOTES_v1.0.3.md`
- `releases/v1.0.4/README.md`
- `releases/v1.0.4/RELEASE_NOTES_v1.0.4.md`
- `releases/v1.0.4/FINAL_RELEASE_VALIDATION.md`
- `releases/v1.0.4/GITHUB_RELEASE_HANDOFF.md`
- `releases/v1.0.4/PUBLIC_SHA256SUMS.txt`
- `releases/v1.0.4/scripts/verify_release_artifacts.py`
- `seismic-denoising-eval-protocol_v1.0.4.zip`
- `seismic-denoising-eval-protocol_v1.0.4.zip.sha256`
- `SHA256SUMS.txt`
