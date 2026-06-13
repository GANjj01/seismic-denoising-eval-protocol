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

## Diagnostics

- `diagnostics/noise_correlation_diagnostic_summary.csv`
- `diagnostics/noise_correlation_by_station.csv`
- `diagnostics/covnorm_region_consistency.csv`

## Environments

- `environments/environment-seismic.yml`
- `environments/environment-deepdenoiser.yml`

## Provenance Scripts

Paper-era evaluator scripts are retained only in the internal workspace, not in
the anonymous release-candidate bundle.  Prefer the reusable modules in `src/`
for new baselines.
