# E3 No-Taper Confounding Closure Validation

Generated after the final repeat run on 2026-07-24 JST.

## Commands

- `conda run -n seismic python -u analysis\scripts\rebuild_e3_no_taper_confounding_closure.py`
- `conda run -n seismic python -u analysis\scripts\stage_v105_formal.py`
- fresh extract verifier: `python <fresh_extract>/seismic-denoising-eval-protocol_v1.0.5/scripts/verify_release_artifacts.py`

## Coverage

- Frozen manifest: `reconstructed_no_taper_e3_e5/manifests/e3_no_taper_manifest.csv`
- Frozen metric table: `reconstructed_no_taper_e3_e5/metrics/e3_detail_wide.csv`
- E3 cases: 1,632
- E3 method-case rows: 13,056
- Covariate failures: 0
- `taper_applied`: all false in the reconstructed no-taper manifest
- Unadjusted Table 10 consistency: exact match to frozen reconstructed no-taper Table 10 values; maximum absolute discrepancy zero

## Reproducibility

The same closure command was rerun after staging. The following output hashes were unchanged before versus after rerun:

- `results/e3_regression_adjusted_results.csv`: `077D6846477E4D5412143AC0CAC08054E51600B543F747FBD8FE8AFE925CD0FB`
- `results/e3_matched_results.csv`: `2DCC141113F6B4FB80DE6C1BD04508A97019F70E612469097AAD0E702D703169`
- `results/e3_balance_before_after.csv`: `C3C3B95F9B1AAA0034905166397CE37D3B1C0C5045501BC8E7DCA90E7EE11D01`
- `results/e3_matching_pairs.csv`: `01292AC4CAF0EE728F92CB9108C5C98D85AEE385AFD26E1E061D850F9AA89BD9`
- `results/e3_model_coefficients.csv`: `0EE8601D801B6CC08C20F4FE8A336ED8F96B4F9412530C7A448CED0DFCBE09EB`
- `results/e3_direction_and_zero_exclusion_audit.csv`: `C72E75A8F6DCC645F0F6881B05AC963A432C819D82DB8256E25FB94F6A3739E1`

Direction consistency is 30/32 overall and 30/31 after excluding the Noisy clean-SNR sanity-control row. Zero-exclusion consistency is 29/32. The prespecified matching retained 15/15 familiar stations and 15/33 unseen stations, forming 15 matched pairs, but did not improve worst-case covariate balance: maximum absolute SMD increased from 0.479 before matching to 0.555 after matching because of residual noise-RMS imbalance.

## Formal Release Checks

- Local formal directory: `release_staging/v1.0.5/seismic-denoising-eval-protocol_v1.0.5`
- Local formal zip: `release_staging/v1.0.5/seismic-denoising-eval-protocol_v1.0.5.zip`
- Fresh-extract verifier result: `PASS: v1.0.5 formal artifact checks succeeded`
- Machine-path scan over the formal package and closure directory: no matches for local absolute workstation paths
- Raw waveform/weight/tensor suffix scan over the formal package: no `.mseed`, `.miniseed`, `.npz`, `.npy`, `.pt`, `.pth`, `.ckpt`, or `.sac` files found

## Boundary

No training, inference, checkpoint selection, frozen predictions, per-case metrics, bootstrap rules, v1.0.4 tag, v1.0.4 release asset, or Zenodo v1.0.4 record was modified by this closure.
