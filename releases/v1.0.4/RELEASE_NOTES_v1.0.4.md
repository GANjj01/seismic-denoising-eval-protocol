# Release notes: v1.0.4

This release adds manuscript-matched reconstructed no-taper E3/E5 audit
artifacts prepared after v1.0.3. It preserves the existing v1.0.3 release and
adds a separate versioned package for the revised manuscript pathway.

## Added

- Reconstructed no-taper E3 frozen manifest.
- Reconstructed no-taper E5 frozen manifest.
- E3/E5 per-case metrics and summary metrics.
- Manuscript-matched Table 10 and Table 12 LaTeX sources.
- Raw-data, checkpoint, configuration, and public-file hashes.
- Repeatability verifier and public table rebuild scripts.
- Fresh-extract validation evidence.
- Provenance records separating reconstructed no-taper diagnostics from the
  submitted tapered analyses.

## E3

- 1,632 cases.
- 13,056 method-case rows.
- 0 failures.
- `taper_applied=false` for all manifest rows.
- Qualitative signs and zero-exclusion conclusions are preserved relative to
  the submitted tapered diagnostic.
- The agreement supports robustness but does not prove taper-only causation.

## E5

- 816 cases.
- 8,160 method-case rows.
- 0 failures.
- `taper_applied=false` for all manifest rows.
- The three clean-SNR seed contrasts are negative.
- Amplitude-ratio and correlation contrasts are mixed.
- Optimization stability did not yield uniform recovery improvement.

## Method roles

- `Wiener-blind`: deployable blind signal-processing baseline.
- `Idealized Wiener`: evaluator-side source-aware sensitivity diagnostic.
- `Noisy`: unprocessed-input sanity control.
- Reconstructed E3/E5: diagnostics, not primary rankings.

## Artifact scope

The package includes code, manifests, metrics, tables, hashes, provenance, and
validation files. It does not redistribute raw MiniSEED waveforms, local sample
tensors, or model weights. Summary/table reproduction and metric/bootstrap audit
can be run directly from the included files. Waveform-level reconstruction
requires reacquiring data from FDSN and supplying the external checkpoints
identified by the provenance hashes.

## Version history

v1.0.3 is preserved unchanged as an earlier public release. v1.0.4 does not
overwrite v1.0.3. Historical submitted tapered artifacts are retained only for
provenance, while v1.0.4 is the manuscript-matched revision release.
