# E3/E5 Reference Map

Generated for the manuscript-response integration of the reconstructed no-taper E3/E5 experiments.

## Evidence Sources

| Source | Role |
| --- | --- |
| `reconstructed_no_taper_e3_e5/EXPERIMENT_DEFINITIONS.md` | Defines E3/E5 as new reconstructed no-taper diagnostics, not historical sample-identical reruns. |
| `reconstructed_no_taper_e3_e5/RESULTS_AND_INTERPRETATION.md` | States interpretation boundaries and points to final CSV tables. |
| `reconstructed_no_taper_e3_e5/provenance/PROVENANCE.md` | Records no-taper target construction, frozen manifests, event/noise pairings, target-SNR scaling, artifact scope, and limitations. |
| `reconstructed_no_taper_e3_e5/provenance/run_summary.json` | Records metric-row counts, final manifest hashes, generation time, and script git head. |
| `reconstructed_no_taper_e3_e5/provenance/manifest_build_summary.json` | Records source no-taper case CSV and anchor-case count used to build manifests. |
| `reconstructed_no_taper_e3_e5/manifests/e3_no_taper_manifest.csv` | E3 frozen manifest: 13,056 method-case rows, 1,632 cases, `taper_applied=false`, 0 failures. |
| `reconstructed_no_taper_e3_e5/manifests/e5_no_taper_manifest.csv` | E5 frozen manifest: 8,160 method-case rows, 816 cases, `taper_applied=false`, 0 failures. |
| `reconstructed_no_taper_e3_e5/metrics/e3_per_case_metrics.csv` | E3 long metric output: 65,280 rows. |
| `reconstructed_no_taper_e3_e5/metrics/e5_per_case_metrics.csv` | E5 long metric output: 40,800 rows. |
| `reconstructed_no_taper_e3_e5/tables/e3_reconstructed_no_taper_table.csv` | Numeric source for revised Table 10. |
| `reconstructed_no_taper_e3_e5/tables/e5_reconstructed_no_taper_table.csv` | Numeric source for revised Table 12. |
| `reconstructed_no_taper_e3_e5/comparison/e3_new_notaper_vs_historical_tapered.md` | Confirms historical tapered and reconstructed no-taper values are not sample-identical replay evidence. |
| `reconstructed_no_taper_e3_e5/comparison/e5_new_notaper_vs_historical_tapered.md` | Confirms selected checkpoint identities are reused but terminal metrics are newly no-taper. |
| `reconstructed_no_taper_e3_e5/validation/artifact_repeatability_check.md` | Repeatability check: 450 metrics recomputed, maximum absolute difference `0.000e+00`. |
| `reconstructed_no_taper_e3_e5/provenance/raw_data_hashes.sha256` | Raw-data hash provenance. |
| `reconstructed_no_taper_e3_e5/provenance/checkpoint_hashes.sha256` | Checkpoint hash provenance. |
| `reconstructed_no_taper_e3_e5/provenance/file_hashes.sha256` | Full output-file hash provenance. |
| `audit/final_consistency/scoring_tracks_final.yml` | Must distinguish historical submitted tapered E3/E5 from current reconstructed no-taper E3/E5. |
| `audit/final_consistency/e3_table8_rebuild_report.yml` | Historical E3 provenance note; must be updated with current reconstructed status without deleting history. |
| `audit/final_consistency/e5_table10_rebuild_report.yml` | Historical E5 provenance note; must be updated with current reconstructed status without deleting history. |

## Current Locations and Required Actions

| File | Section/line | Current wording/value | Required action | New source |
| --- | --- | --- | --- | --- |
| `manuscript/BlindSpot_evaluation_framework_AIIG_elsarticle.tex` | Metrics/scoring tracks, lines 134--138 | Tables 10 and 12 "retain the submitted tapered target definition" and are "not presented as confirmed no-taper reruns." | Redefine Tables 10 and 12 as reconstructed no-taper shared-target diagnostics; state they are not primary report-card rankings and not historical sample-identical reruns. | `EXPERIMENT_DEFINITIONS.md`; `PROVENANCE.md`; final manifests. |
| `manuscript/BlindSpot_evaluation_framework_AIIG_elsarticle.tex` | E3, lines 326--350 | E3 text and caption describe submitted tapered target; table input uses historical `table08_station_leakage_diagnostic.tex`. | Replace with reconstructed no-taper E3 description, counts, no-failure provenance, A--B direction, updated table input, and conservative interpretation. | `e3_reconstructed_no_taper_table.csv`; `e3_reconstructed_no_taper_table.tex`; `comparison/e3_new_notaper_vs_historical_tapered.md`. |
| `manuscript/BlindSpot_evaluation_framework_AIIG_elsarticle.tex` | E5, lines 383--407 | Terminal contrasts retain submitted tapered target; table input uses historical `table10_e5_terminal_differences.tex`. | Replace terminal-performance wording and table with reconstructed no-taper selected-checkpoint diagnostic; keep training dynamics separate. | `e5_reconstructed_no_taper_table.csv`; `e5_reconstructed_no_taper_table.tex`; `comparison/e5_new_notaper_vs_historical_tapered.md`. |
| `manuscript/BlindSpot_evaluation_framework_AIIG_elsarticle.tex` | Discussion, line 461 | E5 wording is broadly consistent but does not identify reconstructed no-taper status. | Add that reconstructed E3/E5 diagnostics strengthen the protocol-oriented interpretation while remaining qualified diagnostics, not rankings. | E3/E5 comparison files; repeatability check. |
| `manuscript/BlindSpot_evaluation_framework_AIIG_elsarticle.tex` | Limitations, lines 508--524 | Target-definition limitations do not mention E3/E5 reconstructed versus historical non-identity. | Add concise limitation: reconstructed E3/E5 do not prove historical sample identity and new/historical differences cannot be attributed only to taper removal. | `PROVENANCE.md`; comparison files. |
| `manuscript/generated_tables/table_analysis_timeline.tex` | Rows for E3/E5/E6 | E3/E5 rows state submitted tapered current diagnostics. | Update E3/E5 rows to reconstructed no-taper shared-target diagnostics; preserve historical tapered/matching/balance rows as provenance where applicable. | `scoring_tracks_final.yml`; reconstructed provenance. |
| `response/response_to_reviewers.tex` | Reviewer 2 Comment 5, lines 151--157 | Says no-taper rerun unavailable and Tables 10/12 retain submitted tapered target. | Replace with repository-audit plus reconstructed no-taper E3/E5 explanation, counts, zero failures, hashes/provenance/repeatability, and updated no-taper/scoring-track statement. | `response_letter_candidate.md`; final manifests; repeatability check. |
| `response/response_to_reviewers.tex` | Reviewer 2 Comment 9, lines 201--205 | Says E5 terminal contrasts retain submitted tapered target. | State E5 terminal contrasts are newly reconstructed no-taper diagnostics using historical selected checkpoint identities, not sample-identical reruns. | E5 table CSV; E5 comparison file. |
| `response/response_to_reviewers.tex` | Reviewer 2 Comment 11, lines 225--229 | Says E3 retains submitted tapered target and is not no-taper rerun. | Replace with reconstructed no-taper E3 result summary and provenance; keep residual imbalance/matching caveats as historical confounding context if retained. | E3 table CSV; E3 comparison file; historical rebuild report. |
| `response/response_to_reviewers.tex` | Author-initiated scoring tracks, line 239 | Labels Tables 10/12 as submitted-tapered exceptions. | Update to reconstructed no-taper shared-target diagnostic track and historical-tapered provenance distinction. | `scoring_tracks_final.yml`; reconstructed provenance. |
| `response/revision_cover_letter.tex` | Summary paragraph, line 25 | Mentions station-leakage confounding but not reconstructed E3/E5. | Add concise mention of reconstructed no-taper E3/E5 diagnostics with provenance, without claiming release update. | `PROVENANCE.md`; final manifests. |
| `audit/final_consistency/scoring_tracks_final.yml` | Track 3, lines 37--44 | Current track is `qualified_shared_target_tapered_diagnostics`. | Add historical submitted tapered provenance track and current reconstructed no-taper diagnostic track. | final manifests; comparison files. |
| `audit/final_consistency/e3_table8_rebuild_report.yml` | Full file | Historical note says no no-taper A-group artifact found. | Retain prior historical note but append `current_revision_update` with reconstructed no-taper status, full-run counts, and source files. | final manifests; run summary. |
| `audit/final_consistency/e5_table10_rebuild_report.yml` | Full file | Historical note says no explicit no-taper selected-checkpoint artifact found. | Retain prior historical note but append `current_revision_update` with reconstructed no-taper status, selected checkpoint identities, full-run counts, and source files. | final manifests; run summary. |

## Numeric Anchors

| Item | Value | Source |
| --- | ---: | --- |
| E3 cases | 1,632 | final E3 manifest |
| E3 method-case rows | 13,056 | final E3 manifest |
| E3 metric rows | 65,280 | `run_summary.json` |
| E3 failures | 0 | final E3 manifest |
| E5 cases | 816 | final E5 manifest |
| E5 method-case rows | 8,160 | final E5 manifest |
| E5 metric rows | 40,800 | `run_summary.json` |
| E5 failures | 0 | final E5 manifest |
| E3 manifest SHA256 | `8d065333c5e8dec4331e8440c5d83c1cb98709ebe8930fbb29f50ea59990a481` | `run_summary.json`; `artifact_repeatability_check.md` |
| E5 manifest SHA256 | `6fd76b713ade296f3c419e31ddb58bc6e3e8be6dde52869e9a627091a0bd5da1` | `run_summary.json`; `artifact_repeatability_check.md` |
| Repeatability metrics checked | 450 | `validation/artifact_repeatability_check.md` |
| Repeatability max absolute difference | `0.000e+00` | `validation/artifact_repeatability_check.md` |

## Forbidden Wording for This Integration

Do not describe the reconstructed E3/E5 experiments as historical no-taper reruns, sample-identical reruns, exact reproductions of submitted E3/E5, recomputed historical results, taper-only reruns, or fully reproduced submitted experiments.
