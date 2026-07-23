# Provenance

Generated: 2026-07-23T17:30:11+00:00

This bundle contains new reconstructed no-taper E3/E5 experiments. It is not a
historical sample-identical replay and must not be described as confirmation of
the submitted tapered E3/E5 artifacts.

Manifests are generated from `<project_workspace>\experiments\results\oracle_free_final_notaper\oracle_free_continuous_detail.csv` with explicit raw-data hashes,
checkpoint hashes, target-SNR values, onset locations, taper flags, and method
identities. Inference reads these manifests and writes outputs under
`<revision_workspace>\reconstructed_no_taper_e3_e5` only.

Taper is disabled in the evaluator template by calling `make_template(...,
taper=False)`. The manifest records `taper_applied=false` for every case-method
row. Target-SNR scaling is recomputed from the no-taper template and selected
noise window.

Known limitations: the new E3 A-group noise plan follows the historical station
cycling rule but is a newly frozen manifest; historical sample identity is not
claimed. E5 uses the historical selected checkpoint identities but recomputes
terminal metrics under the new no-taper manifest.
