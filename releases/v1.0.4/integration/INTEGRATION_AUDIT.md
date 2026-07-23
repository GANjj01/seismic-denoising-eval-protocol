# Integration Audit

## Build Results

| Artifact | Command | Result | Warnings |
| --- | --- | --- | --- |
| Clean manuscript | `<conda_root>\envs\seismic\Library\bin\tectonic.exe BlindSpot_evaluation_framework_AIIG_elsarticle.tex` in `manuscript/` | Success, 63-page PDF | `lineno.sty` UTF-8 warning and underfull boxes; no fatal errors. |
| Response letter | `<conda_root>\envs\seismic\Library\bin\tectonic.exe response_to_reviewers.tex` in `response/` | Success, 12-page PDF | Underfull boxes at response source lines 151--152. |
| Cover letter | `<conda_root>\envs\seismic\Library\bin\tectonic.exe revision_cover_letter.tex` in `response/` | Success | No warnings reported. |
| Supplementary material | `<conda_root>\envs\seismic\Library\bin\tectonic.exe supplementary_material.tex` in `manuscript/` | Success | Existing table-width underfull/overfull warnings remain, mainly in model-training, analysis-timeline, and legacy-name tables. |

## PDF/Text Checks

- Clean PDF text confirms revised Table 10 on p. 32 with DeepDenoiser `+0.573 [+0.143, +1.048]`, Wiener-blind `+0.558 [+0.084, +1.084]`, and self-supervised clean-SNR values `-0.230`, `-0.186`, and `-0.211`.
- Clean PDF text confirms revised Table 12 on p. 39 with seed rows:
  - 42: `-0.462`, `+0.439`, `+0.025`
  - 43: `-0.063`, `-0.044`, `-0.017`
  - 44: `-0.088`, `+0.048`, `+0.032`
- Visual inspection of rendered clean PDF pages 32 and 39 confirmed revised Tables 10 and 12 are not clipped or overlapping. Temporary rendered PNGs were removed after inspection.
- Response PDF text confirms `1,632`, `13,056`, `8,160`, and `0.000e+00`.
- Log check found 0 undefined references/citations and 0 undefined control sequences in manuscript/response/supplementary logs.
- `submitted_original` diff check returned no changed files.

## Consistency Checks

| Check | Result |
| --- | --- |
| E3 cases are 1,632 | Pass |
| E5 cases are 816 | Pass |
| E3 method-case rows are 13,056 | Pass |
| E5 method-case rows are 8,160 | Pass |
| E3/E5 failed cases are 0 | Pass |
| Manuscript labels E3/E5 as reconstructed no-taper diagnostics | Pass |
| Manuscript keeps E3/E5 out of primary report-card ranking | Pass |
| Response says historical submitted artifacts were not relabeled | Pass |
| Table 10 input points to reconstructed no-taper fragment | Pass |
| Table 12 input points to reconstructed no-taper fragment | Pass |
| Old Table 10/12 final-location line numbers refreshed | Pass |
| GitHub push/release or Zenodo publish performed | No |
| v1.0.3 modified | No |

## Residual Notes

- Historical tapered table fragments remain in `manuscript/generated_tables/` but are not referenced by the current manuscript inputs for revised Tables 10 and 12.
- The strings describing the earlier submitted-tapered status remain only in the reference map and superseded provenance/audit notes, where they are explicitly marked as earlier status.
- Because the manuscript now references locally added reconstructed E3/E5 artifacts that were not part of public v1.0.3, a future public artifact update should use a new release version, recommended `v1.0.4`.
