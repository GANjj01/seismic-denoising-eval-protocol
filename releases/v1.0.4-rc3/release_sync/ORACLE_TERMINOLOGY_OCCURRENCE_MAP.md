# Oracle terminology occurrence map

Date: 2026-07-24

Search terms:

- `Wiener-oracle`
- `Wiener oracle`
- `oracle Wiener`
- `non-oracle`
- `nonoracle`
- `principal non-oracle`
- `non-oracle methods`
- `non-oracle interpretation`

| File | Line | Match | Context | Public-facing? | Action |
| ---- | ---: | ----- | ------- | -------------- | ------ |
| `manuscript/BlindSpot_evaluation_framework_AIIG_elsarticle.tex` | 335 | `principal non-oracle interpretation` | Table 10 caption | yes | Replaced with `principal report-card interpretation`. |
| `manuscript/BlindSpot_evaluation_framework_AIIG_elsarticle.tex` | 343 | `principal non-oracle methods` | E3 Results paragraph | yes | Replaced with `principal report-card methods`. |
| `response/response_to_reviewers.tex` | 227 | `principal non-oracle methods` | Reviewer 2 Comment 11 response | yes | Replaced with `principal report-card methods`. |
| `release_staging/v1.0.4/seismic-denoising-eval-protocol_v1.0.4-rc2/README.md` | 20 | `principal non-oracle interpretation` | rc2 README role note | yes, stale rc2 candidate | Not edited in place; rc3 regenerated from fixed staging source. |
| `release_staging/v1.0.4/seismic-denoising-eval-protocol_v1.0.4-rc2/release_sync/TERMINOLOGY_AUDIT.md` | 19 | `principal non-oracle interpretation` | rc2 audit summary | stale rc2 audit | Not edited in place; rc3 regenerated from fixed staging source. |
| `release_staging/v1.0.4/seismic-denoising-eval-protocol_v1.0.4-rc2/release_sync/E3_ANALYSIS_CHAIN_MAP.md` | 13 | `principal non-oracle methods` | rc2 analysis-chain map | stale rc2 audit | Not edited in place; rc3 regenerated from fixed staging source. |
| `reconstructed_no_taper_e3_e5/release_sync/TERMINOLOGY_AUDIT.md` | 42--45 | banned phrases containing `non-oracle` | Banned-term migration record | allowlisted audit | Retained only as quoted banned-term list with replacement mapping. |
| `analysis/scripts/stage_v104_rc.py` | verifier banned phrase list | banned phrases containing `non-oracle` | Verifier policy source | allowlisted verifier policy | Retained so verifier can fail current public-facing forbidden hits. |
| `analysis/scripts/final_scientific_consistency_repair.py` | 353 | `Wiener-oracle` | Historical repair-test diagnostic source | no | Left unchanged as out-of-scope historical helper; not copied into rc3 package. |
| `analysis/scripts/test_postdiff_repair.py` | 115 | `Wiener-oracle` | Historical test string | no | Left unchanged as out-of-scope historical helper; not copied into rc3 package. |

Current-public action summary:

- Manuscript current hits: fixed.
- Response current hits: fixed.
- rc2 stale hits: superseded by rc3, not modified in place.
- rc3 verifier policy/audit migration hits: allowlisted.
