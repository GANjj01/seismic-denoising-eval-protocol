# v1.0.5 Release Notes

This version adds the reconstructed no-taper E3 confounding closure. The
package-portable pathway uses the frozen reconstructed no-taper E3 manifest,
released per-case metrics, and released covariate tables to recompute
station-level OLS adjustment, prespecified greedy station matching,
pre/post-match balance, station bootstrap intervals, and direction/zero-
exclusion audits.

The prespecified matching retained all 15 familiar stations and 15 of 33
unseen stations, forming 15 matched pairs. Matching did not improve
worst-case covariate balance: maximum absolute SMD increased from 0.479
before matching to 0.555 after matching because of residual noise-RMS
imbalance. Matched estimates are therefore limited-overlap secondary
sensitivity analyses, not definitive deconfounded effects.

The GitHub release URL is
https://github.com/GANjj01/seismic-denoising-eval-protocol/releases/tag/v1.0.5.
The Zenodo concept DOI remains https://doi.org/10.5281/zenodo.20681569; Zenodo
assigns the version-specific DOI after archival.

The existing v1.0.4 tag, assets, and Zenodo version are preserved.
