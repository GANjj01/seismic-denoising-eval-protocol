# Repeatability report

Generated: 2026-07-23T17:30:11+00:00

Manifest hashes are recorded in the `.sha256` sidecars. The run command
reads the frozen manifest and does not resample during inference.

Observed full-run hashes:
- `e3_detail_wide.csv`: `f79c6bc2aeeec81436bc6d67b8d4d56da1a88f861d5824b93c6345403ee5202d`
- `e3_per_case_metrics.csv`: `54e50abe38df40526eafb7e224cbbff8d0107855b51b3dfb3db71a2159d0da15`
- `e3_summary.csv`: `167dbe6e6a36d015ea424fce667e49d151163183ad209afd6edd5ef161df02c1`
- `e5_detail_wide.csv`: `843a4fc2829504c1cf950870f0905d0b3f177a3908fddd9a0eb281690a2fe7a5`
- `e5_per_case_metrics.csv`: `e839f725600e308adc6c709706028c4d0f2469ddf20196a8ae171d16cbdeeced`
- `e5_summary.csv`: `13130287fb1016a73ef6683f8edbe80267b9cfcfef709ea63626b14723e42262`
- E3 manifest SHA256: 8d065333c5e8dec4331e8440c5d83c1cb98709ebe8930fbb29f50ea59990a481
- E5 manifest SHA256: 6fd76b713ade296f3c419e31ddb58bc6e3e8be6dde52869e9a627091a0bd5da1

Full deterministic rerun was not repeated in this pass because the completed
GPU full run already produced zero failures and saved per-case metadata/output
artifacts. Re-running the commands in `provenance/commands.ps1` should read
the same manifests; any future bit-level GPU nondeterminism should be assessed
against the hashes above.
