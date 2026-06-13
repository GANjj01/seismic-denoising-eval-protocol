# CovNorm Case-Study Provenance Manifest

This directory documents the training-side provenance needed to audit the
CovNorm case study in the manuscript.  Model weights are not redistributed
because the public release is primarily an evaluation-protocol artifact, but
the run metadata, checkpoint-selection tables, and training-dynamics summaries
used by E1, E4, and E5 are included here.

## Selection Rule

Checkpoints were selected on the frozen development set using the preregistered
development rule.  Final-test outcomes were never used for checkpoint
selection.  Validation loss is retained as a diagnostic in E1 to show why the
self-supervised loss is a weak proxy for final report-card quality.

## Main CovNorm Runs

| Run | Lambda | Seed | Logged training epochs | Selected epoch | Selection rule | English log |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| `exp5_p0_seed42` | 0.0 | 42 | 20 | 15 | Frozen development rule | `e5_multiseed_covnorm/english_epoch_logs/exp5_p0_seed42.english_summary.txt` |
| `exp5_p0_seed43` | 0.0 | 43 | 15 | 8 | Frozen development rule | `e5_multiseed_covnorm/english_epoch_logs/exp5_p0_seed43.english_summary.txt` |
| `exp5_p0_seed44` | 0.0 | 44 | 14 | 13 | Frozen development rule | `e5_multiseed_covnorm/english_epoch_logs/exp5_p0_seed44.english_summary.txt` |
| `exp5_p05_seed42` | 0.5 | 42 | 30 | 20 | Frozen development rule | `e5_multiseed_covnorm/english_epoch_logs/exp5_p05_seed42.english_summary.txt` |
| `exp5_p05_seed43` | 0.5 | 43 | 30 | 22 | Frozen development rule | `e5_multiseed_covnorm/english_epoch_logs/exp5_p05_seed43.english_summary.txt` |
| `exp5_p05_seed44` | 0.5 | 44 | 30 | 14 | Frozen development rule | `e5_multiseed_covnorm/english_epoch_logs/exp5_p05_seed44.english_summary.txt` |

The lambda=0.1 checkpoint-ranking row in E1 is a single-seed diagnostic run and
is shown for completeness only; it is not used as multiseed evidence.

## Released Provenance Tables

### E1: Checkpoint-Ranking Divergence

- `e1_checkpoint_ranking/ranking_correlations.csv`: Spearman and Kendall
  associations among validation-loss, development-set, and final-test
  checkpoint rankings.
- `e1_checkpoint_ranking/checkpoint_selections.csv`: selected checkpoints under
  validation loss, development rule, and final oracle rule.
- `e1_checkpoint_ranking/checkpoint_ranking_table.csv`: per-checkpoint ranking
  table used for the ranking-divergence curves.
- `e1_checkpoint_ranking/selection_regret.csv`: per-run regret from selecting
  by validation loss rather than the development rule or final oracle.
- `e1_checkpoint_ranking/selection_regret_aggregate.csv`: mean and median
  regret values reported in the manuscript.

### E4: Development-Selection Stability

- `e4_checkpoint_selection_stability/single_seed_bootstrap_summary.csv`:
  original single-seed bootstrap summary.
- `e4_checkpoint_selection_stability/single_seed_selected_epoch_frequency.csv`:
  selected-epoch frequency table for the single-seed analysis.
- `e4_checkpoint_selection_stability/single_seed_size_stability_curve.csv` and
  `single_seed_size_regret_summary.csv`: development-size sensitivity tables.
- `e4_checkpoint_selection_stability/multiseed_full_run_checkpoint_selection.csv`:
  selected epoch per lambda/seed run.
- `e4_checkpoint_selection_stability/multiseed_within_seed_stability.csv`:
  within-seed bootstrap reproducibility.
- `e4_checkpoint_selection_stability/multiseed_between_seed_epoch_consistency.csv`
  and `multiseed_seed_epoch_range.csv`: between-seed dispersion summaries.
- `e4_checkpoint_selection_stability/multiseed_selected_epoch_frequency.csv`:
  multiseed selected-epoch frequency table.

### E5: Multiseed CovNorm Dynamics And Performance

- `e5_multiseed_covnorm/development_selection/checkpoint_selection.csv`:
  selected epoch and development-set scores for each paired seed run.
- `e5_multiseed_covnorm/development_selection/checkpoint_manifest.csv`:
  checkpoint manifest for all available development-sweep epochs.
- `e5_multiseed_covnorm/development_selection/selected_checkpoints.json`:
  machine-readable selected-checkpoint map.
- `e5_multiseed_covnorm/development_selection/development_all_epochs_summary.csv`:
  all-epoch development-score summary.
- `e5_multiseed_covnorm/dynamics/epoch_dynamics.csv`: per-epoch gradient norm,
  spike count, NaN count, and LayerNorm gamma trace.
- `e5_multiseed_covnorm/dynamics/dynamics_scalar_summary.csv`: compact
  per-run dynamics summary used in the text and figure captions.
- `e5_multiseed_covnorm/dynamics/paired_gamma_epoch10.csv`: paired lambda=0.5
  minus lambda=0 epoch-10 gamma drift table.
- `e5_multiseed_covnorm/dynamics/run_audit.csv`: run completion and checkpoint
  availability audit with local paths replaced by placeholders.
- `e5_multiseed_covnorm/english_epoch_logs/*.english_summary.txt`: readable
  English per-run audit logs.
- `e5_multiseed_covnorm/english_epoch_logs/*.epoch_log.csv`: per-run numeric
  epoch logs.
- `e5_multiseed_covnorm/performance/oracle_free_selected_by_run.csv`: selected
  checkpoint oracle-free scores by run.
- `e5_multiseed_covnorm/performance/paired_performance_differences.csv`:
  seed-paired lambda=0.5 minus lambda=0 terminal metric differences.
- `e5_multiseed_covnorm/performance/seed_variance_vs_lambda_effect.csv`:
  descriptive seed-variance comparison.
- `e5_multiseed_covnorm/performance/performance_stats.json`: compact
  performance summary.

## Path And Language Sanitization

The original launcher stdout contained machine-specific absolute paths and a
mixture of English plus console-encoding artifacts from Chinese status strings.
For the public release, paths are replaced by placeholders such as
`<WORKSPACE>` and `<TRAINING_WORKSPACE>`, and the readable run logs are provided
as English summaries plus numeric CSV traces.

## What Is Not Included

The release does not include raw MiniSEED waveforms or CovNorm model weights.
Users who want to rerun waveform scoring can fetch the raw waveforms from the
AM network/FDSN services using the released station and window identifiers.
Users who want to fully retrain CovNorm need the waveform downloads and the
training code bundle referenced in `training/README.md`.
