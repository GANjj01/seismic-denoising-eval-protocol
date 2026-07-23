# Verifier banned-term policy

Date: 2026-07-24

## Forbidden in current public-facing files

- `Wiener-oracle`
- `Wiener oracle`
- `oracle Wiener`
- `non-oracle`
- `principal non-oracle`
- `non-oracle methods`
- `non-oracle interpretation`
- `release candidate`
- `candidate package`
- `pre-release`
- `publication authorization`
- `ready for publication authorization`
- `v1.0.4-rc3`
- `rc3`

The verifier scans package text files and reports each hit as:

```text
file
line
matched phrase
allowlisted or forbidden
```

Forbidden hits in current public-facing files fail validation.

## Allowlist

The following contexts may quote old terms:

- `release_sync/ORACLE_TERMINOLOGY_OCCURRENCE_MAP.md`
- `release_sync/ORACLE_TERMINOLOGY_CLEANUP.md`
- `release_sync/VERIFIER_BANNED_TERM_POLICY.md`
- `release_sync/TERMINOLOGY_AUDIT.md`
- `release_sync/PRE_RELEASE_PATCH_CHANGELOG.md`
- `scripts/verify_release_artifacts.py`
- `GITHUB_RELEASE_HANDOFF.md`

Allowed hits must be quoted banned-term lists, migration records, or verifier
policy. They must not be used as current scientific interpretation.
