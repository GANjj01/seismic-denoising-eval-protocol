# Training Bundle

Training is intentionally separated from the reusable report-card interface.

The preregistered multiseed CovNorm training bundle is:

```text
../multiseed_covnorm_training
```

It contains the E5 paired seed design, seeded launcher, checkpoint-selection
sweep, and dynamics/performance analysis scripts.  New report-card users do not
need to rerun training unless they want to reproduce the CovNorm case study.

This directory also includes public provenance tables for the CovNorm case
study:

- `covnorm_case_study_manifest.md` explains the run matrix, selection rule, and
  which files support E1, E4, and E5.
- `e1_checkpoint_ranking/` contains validation-loss, development-rule, and
  final-test ranking/selection tables.
- `e4_checkpoint_selection_stability/` contains single-seed and multiseed
  checkpoint-selection stability summaries.
- `e5_multiseed_covnorm/` contains development-selection tables, English
  per-run training-dynamics logs, per-epoch numeric traces, and paired
  terminal-performance summaries.

Raw waveform downloads and CovNorm model weights are not included.  The
released tables are sufficient to audit the manuscript's checkpoint-selection
and training-dynamics claims, while full retraining requires the original
waveform retrieval step and the training bundle.

