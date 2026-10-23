# RC2 publication authorization hand-off — 23 October 2026

**Owner requested the `1.2.0rc2` production prerelease. This is a request to publish, not evidence of an independent GitHub review, nor an executed release.**

## Confirmed engineering evidence

- Candidate commit `9891feee6e5daa638a9de5cada295482a5fa4884`: PR #471 passed 33/33 checks; exact-main 30/30 passed.
- Separate E5 scope-review PR #473 passed 25/25 checks and was merged as a **nonpublishing** audit. The twelve E1–E4 importable helpers are **proposed for experimental prerelease-only inclusion**; the ten supported module-scoped W1–W4 workflow contracts and frozen 455+3 root boundary remain unchanged.
- Research [#289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289) and [#296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296) remain open. Explicit inferential/MNAR claim exclusions must persist. Their resolution is **not asserted** as a release prerequisite for the narrowly scoped orchestration prerelease.
- This PR updates the release documentation's **arming evidence check** to require the real literal `1.2.0rc2` exact-main SHA/30-run proof. The previous gate accidentally referred to final `1.1.0` qualification (commit `7eaf842...`, 25/25) and must not be reused for RC2.

## Required human and environment actions

1. Independent reviewer: review E5 RC2 content and narrow API/scientific boundaries; record approval (or request module exclusion and new source qualification). A model-authored note or the owner's instruction to proceed is **not** evidence of this review.
2. Separate publication-authorization PR: following review, intentionally update the scope and E5 ledgers, reconcile their transition validators/tests, and jointly arm `RELEASE_READINESS.json` values `production_release_ready=true` and `github_release_ready=true`; leave TestPyPI disarmed. Do **not** toggle the two flags without revising/checking the review policies, as current hold-only validators are designed to fail.
3. After authorization PR merge, verify **every required check on that exact new protected-main commit**; keep main protected and ensure issue #64 remains closed.
4. Repository owner: navigate to [release Actions](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/workflows/release.yml), select **Run workflow**, branch **main**, target **production**. The connected GitHub plugin cannot dispatch workflows.
5. Authorized environment reviewer: approve the **`pypi` GitHub environment** as configured. The release workflow first tags and attaches checksum-verified `v1.2.0rc2` assets as a prerelease and then publishes their identical wheel/sdist to production PyPI via OIDC.
6. Verify GitHub tag target, PyPI `eyetrajectoriespy==1.2.0rc2` files and hashes, fresh pip-installed smoke, and disarm the two publication flags in a final PR. Do not initiate an ordinary `production` run twice; use the documented `resume-production` route only for a verified interrupted upload.

**At creation:** RC2 is **not published**; the latest verified public GitHub release remains `v1.1.0`. This PR fixes stale preflight evidence, **not** production approval or flags.
