# GitHub release handoff

## Target

- Final commit SHA: record from `git rev-parse HEAD` after the release-preparation
  commit is created and pushed.
- Tag to create: `v1.0.4`
- Target: final commit on `main`.
- Release title: `v1.0.4 - Manuscript-matched reconstructed no-taper E3/E5 release`
- Release label: latest
- Pre-release: false
- Release notes source path: `releases/v1.0.4/RELEASE_NOTES_v1.0.4.md`

## Assets To Upload

1. `seismic-denoising-eval-protocol_v1.0.4.zip`
2. `seismic-denoising-eval-protocol_v1.0.4.zip.sha256`

Do not upload the older rc3 ZIP.

## Asset Checks

- Final ZIP SHA-256: `5cb7e14789bc26b24fb27e444c4ac197490d48a208b785eb3a107cd6467b30b4`
- Final ZIP size: `2988971` bytes
- Formal package verifier result: `pass`
- Root checksum result: `pass`
- v1.0.3 preservation result: the existing `v1.0.3` tag is not moved or
  overwritten.

## Zenodo

Zenodo is expected to archive the GitHub release through the existing connected
record. Do not enter a version DOI until Zenodo creates the version-specific
record.
