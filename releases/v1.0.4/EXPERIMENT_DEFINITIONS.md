# Reconstructed no-taper E3/E5 experiment definitions

Generated: 2026-07-23T16:52:37+00:00

These experiments are new reconstructed no-taper diagnostics. They are not
historical reruns, not sample-identical reruns, and not confirmed reproductions
of the submitted E3/E5 tapered artifacts.

## E3: reconstructed no-taper station-domain contrast

Scientific question: do methods perform differently when continuous-noise
windows come from stations familiar to training/development versus unseen final
stations, while injected event templates, target SNR values, and hidden onset
locations are held fixed within each group definition?

Design retained from historical E3: A group uses training/internal-validation
station noise (`rs_train_holdout_noise`); B group uses final-set noise
(`rs_external_2025pre`) from the current no-taper final controlled-mixture case
table. The A/B station sets differ, so summaries use independent station-group
bootstrap and are interpreted as familiar-versus-unseen station-domain
diagnostics, not as identified causal station memorization effects.

Methods: Noisy, Bandpass, Wiener_blind, Wiener_oracle, p0_e06, p01_e07, p05_e16, DeepDenoiser.

Target definition: evaluator-held pseudo-clean event template, 1--20 Hz
bandpass, pre-P samples zeroed, post-event tail zeroed after 20 s, no P-onset
ramp/taper.

Case construction: event templates, target SNR values, and onset times are
anchored to the frozen primary no-taper final controlled-mixture table. A-group
noise choices are deterministically generated from the train/development
holdout noise pool using seed 20260611. B-group noise choices are read from the
primary no-taper case table. Target-SNR scaling is recomputed from the no-taper
template and selected noise.

## E5: reconstructed no-taper paired terminal checkpoint contrast

Scientific question: for paired seeds 42, 43, and 44, how do selected terminal
checkpoints for lambda_pol=0.5 compare with lambda_pol=0 under the no-taper
controlled-mixture target?

Design retained from historical E5: the same selected checkpoint identities are
used for each paired seed. Terminal metrics are recomputed on the frozen
primary no-taper final case manifest. Training-dynamics quantities are not
rerun here because they are target-independent.

Methods: Noisy, Bandpass, Wiener_blind, Wiener_oracle, exp5_p0_seed42_e015, exp5_p0_seed43_e008, exp5_p0_seed44_e013, exp5_p05_seed42_e020, exp5_p05_seed43_e022, exp5_p05_seed44_e014.

Target definition: identical to E3, with taper disabled throughout target,
mixture, output, scoring, and plotting steps.

## Aggregation and inference

Per-case metrics are written in long format. E3 station-leakage contrasts use
independent station-group bootstrap with B=20,000, seed 20260611, equal station
weighting, and percentile 95% intervals. E5 terminal selected-checkpoint rows
are summarized by method over the no-taper manifest and reported as paired
within-seed contrasts without treating n=3 seeds as a formal hypothesis test.
