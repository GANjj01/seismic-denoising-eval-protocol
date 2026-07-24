# v1.0.5 Verification Environment

The package-portable verification scripts require Python 3.11 or later and
NumPy. The validation run for this local package used:

- Python: 3.11 from the local `seismic` conda environment
- NumPy: 2.4.6

Expected commands after extracting the package:

```bash
conda activate seismic
python scripts/recompute_e3_adjustment_from_released_tables.py --package-root . --output-dir ./tmp_recompute
python scripts/verify_release_artifacts.py
```

The verifier does not require raw MiniSEED files, sample tensors, or model
weights. Waveform-level reconstruction is a separate external-artifact pathway.
