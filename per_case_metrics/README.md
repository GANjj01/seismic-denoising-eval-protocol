# Derived Per-Case Metrics

These CSV files are derived evaluation outputs, not raw waveform data.

- `oracle_free_816_all_methods.csv`: legacy-named per-case controlled
  reference-based mixture metrics for all paper methods in the main comparison.
- `final_real_272_all_methods.csv`: sanitized final real-event metrics with
  local absolute paths replaced by file names.
- `six_way_oracle_free_report_card.csv`: identity/N2V/CovNorm report card.
- `station_bootstrap_vs_identity.csv`: station-level paired intervals versus
  identity.

Use `python scripts/run_smoke_test.py` to regenerate a report-card summary from
the released controlled-mixture per-case table. The `oracle_free` filename is
retained for compatibility with earlier releases.
