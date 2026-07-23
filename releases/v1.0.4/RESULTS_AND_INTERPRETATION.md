# Results and interpretation

Generated: 2026-07-23T17:30:11+00:00

Use the generated CSV tables as the numeric source:

- E3: `<revision_workspace>\reconstructed_no_taper_e3_e5\tables\e3_reconstructed_no_taper_table.csv`
- E5: `<revision_workspace>\reconstructed_no_taper_e3_e5\tables\e5_reconstructed_no_taper_table.csv`

These results should be interpreted as reconstructed no-taper diagnostics. They
do not alter the already published v1.0.3 release and do not by themselves imply
that the historical submitted E3/E5 tapered diagnostics were sample-identical
no-taper reruns.

## E3 status

The reconstructed E3 run completed for methods Bandpass, DeepDenoiser, Noisy, Wiener_blind, Wiener_oracle, p01_e07, p05_e16, p0_e06 with
zero failed cases. It remains an auxiliary familiar-versus-unseen station-domain
diagnostic because A and B use different station sets.

## E5 status

The reconstructed E5 run completed for 3 paired seed rows using the
selected checkpoint identities. It remains a descriptive paired-seed terminal
diagnostic rather than a formal seed-level hypothesis test.
