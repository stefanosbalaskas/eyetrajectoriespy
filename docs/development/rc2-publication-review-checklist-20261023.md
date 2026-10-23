# RC2 GitHub/PyPI publication: explicit approval checklist (REVIEW PENDING)

**23 October 2026 — not a publication authorization.**

The literal RC2 source was independently exercised in [PR #471](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/471): **33/33 exact-head checks passed**. PR #471 merged to protected main `9891feee6e5daa638a9de5cada295482a5fa4884`. This is the candidate source under examination; the published stable release remains **1.1.0**.

The original 6×3 measured-performance workload is linked in [run #39945467014](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39945467014), immutable artifact #12497727453, with recorded original source SHA, original member SHA256, and separate historical RC1 evidence. The source CI and native E1–E4, W1–W4, wheel/sdist validation did not qualify generic 90% confidence bands or MNAR gaze-loss correction. Scientific blockers [#289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289) and [#296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296) remain open.

## Mandatory release sequence

1. Confirm **all** checks on the *protected main commit* `9891feee6e5daa638a9de5cada295482a5fa4884` completed successfully. PR results alone cannot replace that requirement. Freeze the resulting evidence before any authorization change.
2. Record a distinct release decision approving the **ten module-scoped W1–W4 routes only**; E1–E4 functions remain explicitly experimental importable helpers, not stable APIs. Explicitly exclude calibrated whole-trajectory confidence-band and MNAR-identification claims.
3. Review and approve a **separate governance-only PR**, synchronized with the RC2 candidate, to atomically arm `github_release_ready` and `production_release_ready` *only after* the evidence and review are complete. TestPyPI remains disabled unless independently configured; no need to upload to it for production.
4. Require exact-main CI on the publication-authorization commit. Source, installed distribution, external scientific comparators, documentation and experimental E5 gates must remain green. Do not weaken any threshold or treat neutral/skipped as success.
5. Dispatch `.github/workflows/release.yml` **manually from protected main** with **`target=production`**, using the GitHub Actions interface. The repository uses a build-once wheel+sdist path, fail-closed source/main governance, fresh GitHub tag and prerelease, then the required `pypi` environment approval and OIDC publication of the same checked distributions.
6. Verify GitHub `v1.2.0rc2` prerelease, checksums, `eyetrajectoriespy==1.2.0rc2` installed from PyPI, and a clean `pip check`/smoke test. **Do not label RC2 as stable 1.2.0**.

## Current execution boundary

This document and `RC2_PUBLICATION_REVIEW.json` are **review records** only. All actual GitHub Release, PyPI, TestPyPI, tag and readiness flags stay **false**. `scripts/validate_rc2_publication_review.py` intentionally fails if this pending-review checkpoint falsely asserts a completed main matrix, independent human approval, or publication. This audit does not contain, transmit, or use PyPI tokens.

The connected GitHub tool in this chat supports PR updates, file updates, CI reading and merging, but does **not expose a GitHub Actions workflow-dispatch operation**. It cannot execute the final manual publisher. The exact GitHub production release workflow must therefore be invoked by an authorized person after the separate governance change and required environment review.
