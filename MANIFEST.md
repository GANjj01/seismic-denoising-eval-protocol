# Manifest

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
- `indices/oracle_free_816_case_index.csv`
- `indices/final_real_272_event_index.csv`

## Derived Tables

- `per_case_metrics/oracle_free_816_all_methods.csv`
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

## Environments

- `environments/environment-seismic.yml`
- `environments/environment-deepdenoiser.yml`

## Provenance Scripts

Legacy one-off scripts were consolidated into reusable modules under `src/`.
Unreleased local scripts are not required for the released smoke test,
report-card reproduction, or CovNorm case-study audit tables.
