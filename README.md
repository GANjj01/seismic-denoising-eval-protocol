# seismic-denoising-eval-protocol

Release candidate for the paper:

> A Controlled Evaluation Protocol for Self-Supervised Three-Component Blind-Spot Seismic Denoising

This package turns the manuscript protocol into reusable artifacts: frozen
station splits, case indices, per-case report-card tables, identity and
adversarial controls, matched N2V outputs, noise-correlation diagnostics, and
small dependency-light utilities for summarizing a new baseline.

Raw Raspberry Shake waveforms are not redistributed.  The release provides
station IDs, event/window identifiers, derived metric tables, and a FDSN fetch
helper so users can retrieve waveforms from the AM network through official
services.

## Quickstart

On the original Windows workstation:

```bat
call scripts\run_smoke_test.cmd
```

Portable Python invocation:

```bash
python scripts/run_smoke_test.py
```

The smoke test reads:

```text
per_case_metrics/oracle_free_816_all_methods.csv
```

and writes:

```text
smoke_outputs/oracle_free_report_card_smoke.csv
```

This verifies that the report-card summarizer can consume the released
per-case table without touching raw waveforms or training checkpoints.

## Repository Layout

```text
seismic-denoising-eval-protocol/
  src/blindspot_eval_protocol/    reusable metrics, baselines, report-card code
  scripts/                        smoke test and FDSN fetch helper
  splits/                         frozen 54-station split manifests
  indices/                        event/window identifiers, no waveform data
  per_case_metrics/               derived report-card tables
  diagnostics/                    noise-correlation and regional summaries
  baselines/                      notes for identity/adversarial/N2V controls
  configs/                        schema and example path config
  environments/                   conda environment exports
  training/                       pointer to the multiseed CovNorm bundle
```

The neighboring folder `../multiseed_covnorm_training` contains the
preregistered E5 training bundle.  It is kept separate because model training
is not the reusable report-card interface.

## Data Policy

- Code is intended for release under MIT.
- Released split files, case indices, diagnostic summaries, and metric tables
  are intended for release under CC-BY-4.0.
- Raw MiniSEED waveforms remain with the Raspberry Shake AM network/FDSN data
  providers and are not included.

## How To Add A New Baseline

The protocol contract is deliberately small:

1. Read each mixture waveform in the frozen index.
2. Produce an output waveform with the same shape and sample rate.
3. Score the output with the same final-real and oracle-free metric functions.
4. Append per-case rows using the report-card schema.
5. Run `blindspot_eval_protocol.report_card` to summarize.

Required oracle-free per-case columns:

```text
case_id, station_template, method, output_vs_clean_snr,
corr_z, amp_ratio_clean, background_suppression_db
```

If the file includes `Noisy` or `Identity` rows for each case, clean-SNR gain is
computed relative to that baseline.  The released SeisBench adapter sketch in
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

The paper's full training and checkpoint-selection reruns still require the
original local training workspace and waveform downloads.  The environment
exports are in `environments/`.

## Zenodo Release Checklist

For submission, create the repository from the release-candidate staging folder,
then:

1. connect the GitHub repository to Zenodo;
2. tag `v1.0.0` as the paper-supporting release;
3. cite the Zenodo concept DOI in the manuscript;
4. keep the version DOI for exact reproducibility of the submitted state.

`CITATION.cff` is a separate repository-level citation file.  Update it with
the final DOI and paper metadata before the public release.
