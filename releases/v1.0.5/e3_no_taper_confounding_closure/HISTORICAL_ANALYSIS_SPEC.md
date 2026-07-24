# Historical E3 Confounding Analysis Specification

Recovered from the revision audit script and the original station-leakage helper scripts.

- Units: case-level outcomes are aggregated to station-level means before A--B contrasts where applicable.
- Outcome: A--B familiar-versus-unseen station contrast for clean-SNR, clean-reference amplitude ratio, waveform correlation, and background suppression.
- A/B encoding: `group_A=1` for held-out training/internal-validation station noise; `group_A=0` for unseen final-station noise.
- Covariates: target SNR, log10 10 s injection-window noise RMS, dominant 1--20 Hz frequency, 1--20 Hz spectral slope, log10 10--20/1--5 Hz bandpower ratio, and 4 s frame-RMS coefficient of variation.
- Spectral covariates: Welch PSD per component, mean PSD across components, 1--20 Hz analysis band, and trapezoidal bandpowers.
- Regression: ordinary least squares with intercept, group_A, and within-fit z-scored covariates; no interactions, no weights, no robust covariance estimator.
- Regression uncertainty: independent station-cluster bootstrap within A and B, B=1000, seed base 20260611.
- Matching: greedy 1:1 nearest-neighbor without replacement on station-level standardized covariates, caliper 2.5, ties by station name.
- Matched uncertainty: bootstrap over matched station-pair differences.
- Interpretation: rows with direction changes or limited matching retention are graded suggestive; otherwise qualified-consistent.
