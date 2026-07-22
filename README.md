# seismic-denoising-eval-protocol

[![DOI](https://zenodo.org/badge/1268525598.svg)](https://doi.org/10.5281/zenodo.20681569)

Code license: MIT. Released split files, case indices, diagnostic summaries,
and derived metric tables: CC-BY-4.0.

Version: v1.0.3.

This repository supports the manuscript:

> A Reproducible Evaluation Protocol for Self-Supervised Three-Component
> Blind-Spot Seismic Denoising

The package turns the manuscript protocol into reusable artifacts: frozen
station splits, case indices, per-case report-card tables, identity and
adversarial controls, matched N2V outputs, noise-correlation diagnostics, and
dependency-light utilities for summarizing a new baseline.

Raw Raspberry Shake waveforms are not redistributed. The release provides
station IDs, event/window identifiers, derived metric tables, and a FDSN fetch
helper so users can retrieve waveforms from the AM network through official
services.

## Quickstart

On Windows:

```bat
call scripts\run_smoke_test.cmd
```

Portable Python invocation:

```bash
python scripts/run_smoke_test.py
```

The smoke test reads the legacy-named file:

```text
per_case_metrics/oracle_free_816_all_methods.csv
```

and writes:

```text
smoke_outputs/oracle_free_report_card_smoke.csv
```

The `oracle_free` filename is retained for backward compatibility with earlier
artifacts. In the revised manuscript terminology, these rows correspond to
controlled reference-based mixture evaluation with evaluator-held pseudo-clean
references. The smoke test verifies that the report-card summarizer can consume
the released per-case table without touching raw waveforms or training
checkpoints.

## Repository Layout

```text
seismic-denoising-eval-protocol/
  src/blindspot_eval_protocol/    reusable metrics, baselines, report-card code
  scripts/                        smoke test and FDSN fetch helper
  splits/                         frozen 54-station split manifests
  indices/                        event/window identifiers, no waveform data
  per_case_metrics/               derived report-card tables
  diagnostics/                    noise, recovery-probe, polarization, and regional summaries
  baselines/                      notes for identity/adversarial/N2V controls
  configs/                        schema and example path config
  environments/                   conda environment exports
  training/                       CovNorm case-study provenance tables
```

The reusable evaluation interface is separated from the full CovNorm training
workflow. The `training/` directory contains the released provenance tables,
checkpoint-selection summaries, and multiseed diagnostics required to audit the
case study. Full retraining requires the separate training workflow and the
corresponding waveform inputs.

## Data Policy

- Code is released under MIT.
- Released split files, case indices, diagnostic summaries, and metric tables
  are released under CC-BY-4.0.
- Raw MiniSEED waveforms remain with the Raspberry Shake AM network/FDSN data
  providers and are not included.

## Baseline And AdvGate Notes

The manuscript-reproduction pathway is exposed as
`blindspot_eval_protocol.baselines.adv_gate_sta_lta` and uses the archived
STA/LTA configuration. It calls ObsPy's `classic_sta_lta` on the
three-component energy trace and is the implementation corresponding to the
manuscript AdvGate results. The legacy provenance script
`legacy_scripts/adversarial_baselines_eval.py` maps its `AdvGate` row to this
STA/LTA path.

The package also provides
`blindspot_eval_protocol.baselines.adv_gate_quantile`, a dependency-light
quantile-energy variant for smoke tests and interface demonstrations. It serves
the same adversarial-control purpose but is not the implementation used to
generate the manuscript AdvGate results.

The backward-compatible name `blindspot_eval_protocol.baselines.adv_gate`
continues to resolve to the quantile-energy variant used by earlier package
interfaces. New code should call `adv_gate_sta_lta` or `adv_gate_quantile`
explicitly.

STA/LTA reproduction requires ObsPy:

```bash
pip install .[manuscript]
```

## How To Add A New Baseline

The protocol contract is deliberately small:

1. Read each mixture waveform in the frozen index.
2. Produce an output waveform with the same shape and sample rate.
3. Score the output with the same final-real and controlled-mixture metric
   functions.
4. Append per-case rows using the report-card schema.
5. Run `blindspot_eval_protocol.report_card` to summarize.

Required controlled-mixture per-case columns:

```text
case_id, station_template, method, output_vs_clean_snr,
corr_z, amp_ratio_clean, background_suppression_db
```

If the file includes `Noisy` or `Identity` rows for each case, clean-SNR gain is
computed relative to that baseline. The SeisBench adapter sketch in
`src/blindspot_eval_protocol/seisbench_adapter.py` shows how to wrap a
SeisBench denoiser behind the same `waveform_3c -> waveform_3c` contract.

## Reproducing The Paper Tables

Key released derived tables:

- `per_case_metrics/oracle_free_816_all_methods.csv`
- `per_case_metrics/final_real_272_all_methods.csv`
- `per_case_metrics/six_way_oracle_free_report_card.csv`
- `per_case_metrics/station_bootstrap_vs_identity.csv`
- `diagnostics/noise_correlation_diagnostic_summary.csv`
- `diagnostics/covnorm_region_consistency.csv`
- `diagnostics/recovery_probe/`
- `diagnostics/polarization_rescore/`
- `training/covnorm_case_study_manifest.md`
- `training/e1_checkpoint_ranking/`
- `training/e4_checkpoint_selection_stability/`
- `training/e5_multiseed_covnorm/`

Several retained filenames use `oracle_free` for provenance and compatibility;
the revised manuscript describes these artifacts as controlled reference-based
mixture evaluation with evaluator-held pseudo-clean references.

The release supports three practical levels of reproduction:

| Level | What users can do | Raw waveforms needed? | Training weights needed? |
| --- | --- | --- | --- |
| Released-table reproduction | Run the smoke test, regenerate report-card summaries from released per-case tables, and audit station-level contrasts from derived tables | No | No |
| Waveform-level evaluation | Reacquire AM/FDSN waveforms with the released station/window indices and score a new baseline through the same metric interface | Yes | No, unless the baseline requires them |
| CovNorm training-side reproduction | Audit the released CovNorm checkpoint-selection, development-composition, and multiseed diagnostics; full retraining additionally requires the training workflow and waveform inputs | No for released summaries; yes for full retraining | No for audit; optional for retraining |

The environment exports are in `environments/`. Full CovNorm retraining is not
a one-command workflow in this evaluation-protocol release, but the
training-side logs and checkpoint-selection summaries used by the manuscript
are public under `training/`.

## Citation And Archiving

This repository is archived on Zenodo under the concept DOI
[`10.5281/zenodo.20681569`](https://doi.org/10.5281/zenodo.20681569).

Each versioned release is preserved as a separate Zenodo record. For exact
reproduction, cite the version-specific DOI listed in `CITATION.cff` for the
release used in the analysis. The concept DOI can be used to access the
complete version history.
