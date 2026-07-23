# Seismic denoising evaluation protocol v1.0.4

This package provides the manuscript-matched E3/E5 no-taper reconstruction
artifacts prepared after the v1.0.3 public release.

## Contents

- `configs/`: sanitized E3/E5 reconstruction configurations.
- `manifests/`: sanitized no-taper case/method manifests with filenames and hashes.
- `metrics/`: released per-case and summary metric CSVs.
- `tables/`: numeric CSV and LaTeX tables for the reconstructed E3/E5 analyses.
- `manuscript/generated_tables/`: exact LaTeX fragments used by manuscript Tables 10 and 12.
- `provenance/`: hashes, environment notes, and original-run provenance with public paths.
- `scripts/rebuild_e3_e5_tables.py`: rebuilds Tables 10 and 12 from the released CSVs.
- `scripts/verify_release_artifacts.py`: validates counts, no-taper flags, key values, path hygiene, and table rebuilds.

Table 10 displays the frozen internal method identifier `Wiener_oracle` as
`Idealized Wiener`. That row uses evaluator-side source decomposition and is
included only as a source-aware sensitivity diagnostic; it is not a deployable
baseline and is excluded from the principal report-card interpretation. The
Noisy row is the unprocessed-input sanity control; zero-valued gain contrasts
are expected by construction where applicable.

The 2.57 GB `artifacts/` tensor directory is excluded from this default archive.
This package therefore supports manuscript-table audit from released metrics and
manifests. Full waveform-level re-execution requires external raw waveforms and
model checkpoints identified by the manifest filenames and provenance hash
listings.

## Quick validation

From the extracted package root:

```bash
python scripts/verify_release_artifacts.py
```

Expected result: `status: pass`.

Version-specific archival metadata is provided by the connected Zenodo release
record after GitHub publication.
