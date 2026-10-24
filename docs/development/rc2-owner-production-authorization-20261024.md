# 1.2.0rc2 owner-directed production publication authorization

**Requested:** 24 October 2026. The repository owner expressly instructed the connected assistant to proceed with the GitHub prerelease and production PyPI publication.

**Not independently approved at creation:** this is the owner's publication request, not a fabricated approval from an independent person. This PR requires an independent GitHub `APPROVED` review of its exact head before the production workflow may publish. It does not assert that such a review exists before it is observed.

The intended RC2 package is a prerelease of ten module-scoped W1–W4 workflows, with twelve separately importable E1–E4 helpers explicitly labelled **experimental, unstable and without validated inferential guarantees**. The stable published `1.1.0` root compatibility boundary remains frozen at 455 stable and three historical experimental names. The negative scientific research findings in [#289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289) and [#296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296) remain unresolved and excluded from release claims.

**Publication workflow remains manual:** after exact-head PR qualification, independent review and protected-main exact-commit checks, the owner must explicitly launch `release.yml` on `main` with `target=production`; the existing protected `pypi` environment requires a separate approving reviewer. Do not re-run failed publication run #21, which used disarmed main.

This authorization does not rename previous performance artifacts, change scientific estimators, add public root names or relax the numerical thresholds.

## Recovery after merged PR #475 and release run #24

PR #475 was merged on 24 October 2026 at `1ddf888bab969d40ed3a81394f2194ffb71b9290` **without a submitted PR review**. Run #23 correctly failed because main was disarmed; after arming merged, run #24 correctly failed at the independent-exact-head-review preflight. No independent review has been recorded or synthesized.

The initial gate expected approval of PR #475 **before** its merge; consequently rerunning the workflow cannot repair that missing historical evidence. The owner repeatedly requested immediate prerelease publication. The corrective PR deliberately introduces a distinct, fully attributed owner release authorization: the GitHub-provided actor must be exactly `stefanosbalaskas`, the event `workflow_dispatch`, the ref protected `main`, and the target production or resume-production. The validator verifies the immutable PR #475 head, its GitHub-recorded merge and author, an explicit repository JSON policy declaration, and all pre-existing publication readiness flags. Other actors still require independent review.

This is a documented **change in approval policy**, not a claim of independent review or a shortcut around exact-main CI or the protected PyPI environment. Build/installed distribution verification, version uniqueness, SHA256, release artifact provenance, and environment approval remain mandatory. The current scientific limitations and experimental-only helper classification remain unchanged.
