# Artifact packaging decision

- Version: v1.0.4
- Prepared: 2026-07-23T19:02:55Z
- Scope: manuscript-matched E3/E5 reconstructed no-taper audit artifacts.
- Excluded by default: `artifacts/` sample tensors (31,008 files, 2.57 GB).
- Included: configs, sanitized manifests, metrics, summary tables, manuscript
  table fragments, provenance, validation evidence, and public rebuild scripts.

The package distinguishes the new reconstructed no-taper E3/E5 analyses from the
already published v1.0.3 release. It does not modify, replace, delete, or
retag v1.0.3.

Full waveform inference remains a higher-cost reproduction path because raw
MiniSEED waveforms and model checkpoints are external assets. The release
package preserves filenames and SHA256 hashes needed to audit those assets.
