# seismic-denoising-eval-protocol v1.0.5

Formal v1.0.5 release materials prepared 2026-07-24T01:05:59+00:00 for the reconstructed
no-taper E3/E5 revision package. The existing public v1.0.4 tag, assets, and Zenodo version are retained unchanged.

Release URL to be used after publication:
https://github.com/GANjj01/seismic-denoising-eval-protocol/releases/tag/v1.0.5

Zenodo concept DOI:
https://doi.org/10.5281/zenodo.20681569

Zenodo assigns the version-specific v1.0.5 DOI only after archival.

Included:

- frozen no-taper E3 confounding-closure config;
- package-portable E3 recomputation script using released CSV/table inputs;
- external-artifact wrapper documenting the separate waveform-level pathway;
- source no-taper E3 manifest, metrics, and Table 10 source table;
- case/station covariate tables;
- unadjusted, regression-adjusted, matched, balance, pair, direction, and
  tapered-vs-no-taper evidence tables;
- manuscript-matched generated table fragments;
- provenance, hashes, validation records, license, environment notes, citation
  metadata, terminology map, and the release verifier.

Reproducibility levels:

1. Package-portable verification: run the verifier and recompute E3 adjustment,
   matching, bootstrap summaries, and table fragments from released CSV inputs.
2. External-artifact reconstruction: reacquire raw waveforms, tensors, and model
   checkpoints, then use the documented wrapper and source configuration.
3. Historical provenance review: inspect frozen manifests, checksums, metadata,
   and manuscript-matched generated table fragments.

Excluded:

- raw waveform files;
- saved sample tensors;
- model weights/checkpoints;
- local cache or build outputs.

The machine identifier `Wiener_oracle` is retained only for frozen provenance
compatibility. The manuscript-facing display name is Idealized Wiener; see
TERMINOLOGY_MAP.md.
