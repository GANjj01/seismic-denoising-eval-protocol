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
| Earlier local staging package README | 20 | `principal non-oracle interpretation` | stale candidate README role note | historical local staging | Not edited in place; v1.0.4 was regenerated from fixed staging source. |
| Earlier local staging package terminology audit | 19 | `principal non-oracle interpretation` | stale candidate audit summary | historical local staging | Not edited in place; v1.0.4 was regenerated from fixed staging source. |
| Earlier local staging package E3 analysis-chain map | 13 | `principal non-oracle methods` | stale candidate analysis-chain map | historical local staging | Not edited in place; v1.0.4 was regenerated from fixed staging source. |
| `reconstructed_no_taper_e3_e5/release_sync/TERMINOLOGY_AUDIT.md` | 42--45 | banned phrases containing `non-oracle` | Banned-term migration record | allowlisted audit | Retained only as quoted banned-term list with replacement mapping. |
| `analysis/scripts/stage_v104_rc.py` | verifier banned phrase list | banned phrases containing `non-oracle` | Verifier policy source | allowlisted verifier policy | Retained so verifier can fail current public-facing forbidden hits. |
| `analysis/scripts/final_scientific_consistency_repair.py` | 353 | `Wiener-oracle` | Historical repair-test diagnostic source | no | Left unchanged as out-of-scope historical helper; not copied into the formal package. |
| `analysis/scripts/test_postdiff_repair.py` | 115 | `Wiener-oracle` | Historical test string | no | Left unchanged as out-of-scope historical helper; not copied into the formal package. |

Current-public action summary:

- Manuscript current hits: fixed.
- Response current hits: fixed.
- Earlier staging hits: superseded by the formal v1.0.4 package, not modified
  in place.
- Formal verifier policy/audit migration hits: allowlisted.
