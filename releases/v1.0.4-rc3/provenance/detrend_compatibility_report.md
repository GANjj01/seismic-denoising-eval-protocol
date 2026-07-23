# Detrend compatibility report

Generated: 2026-07-23T17:30:11+00:00

Directly invoking `<conda:seismic>/python` reproduced the prior
silent failure around SciPy/ObsPy signal preprocessing because the Conda
activation environment was not fully established. Re-running the same minimal
SciPy detrend/filter checks through `conda run -n seismic` and through
`cmd /c "call <conda_root>/Scripts/activate.bat seismic && ..."` succeeded.

The reconstructed no-taper full runs therefore use the activated `seismic`
environment, not a bare interpreter call. The activated environment provides
GPU PyTorch, ObsPy/SciPy preprocessing, and SeisBench/DeepDenoiser after the
approved local installation of `seisbench==0.4.1`.

No historical script or result file was modified. The preprocessing definition
remains the submitted definition: demean, linear detrend, optional resampling to
100 Hz, 1--20 Hz bandpass filtering, and no onset taper for the reconstructed
target.
