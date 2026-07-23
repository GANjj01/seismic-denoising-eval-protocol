# Final release validation

Package: `seismic-denoising-eval-protocol_v1.0.4`

Validation command:

```bash
python scripts/verify_release_artifacts.py
```

Expected verifier result: `status: pass`.

Checks covered by the verifier:

- No local absolute path pollution in scanned public text files.
- No forbidden current-public terminology outside allowlisted historical audit
  and verifier-policy contexts.
- E3 manifest rows: 13,056.
- E3 unique cases: 1,632.
- E3 failures: 0.
- E3 `taper_applied`: `false` for all manifest rows.
- E5 manifest rows: 8,160.
- E5 unique cases: 816.
- E5 failures: 0.
- E5 `taper_applied`: `false` for all manifest rows.
- E3 per-case metric rows: 65,280.
- E5 per-case metric rows: 40,800.
- E3 summary table rows: 32.
- E5 summary table rows: 3.
- Key E3 values verified from released CSVs.
- Key E5 seed-42 values verified from released CSVs.
- Table 10 and Table 12 LaTeX fragments rebuilt from released CSVs and matched
  the manuscript fragments exactly.
- Public file SHA256 checks passed.
- The misnamed duplicate `tables/table10_reconstructed_no_taper_candidate.tex`
  is absent.

Boundary:

The default archive excludes the 2.57 GB sample tensor directory. It supports
table-level audit from released metrics and manifests. Full waveform inference
requires external raw waveforms and model checkpoints identified by filenames
and provenance hashes.
