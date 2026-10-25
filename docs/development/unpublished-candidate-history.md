# Historical research candidates and release decisions

!!! info "Current publication status"
    The published stable release is **eyetrajectoriespy 1.2.0**, released on
    24 October 2026. This is an **archival decision trail**, not a current
    release hold or a substitute for the [live release-readiness record](../release-readiness.md).
    The dates and qualification assertions in the linked October documents
    are historical snapshots. They do not revoke or retrospectively authorize
    a production release.

## Historical technical and governance decision records

The records are presented in their contemporary sequence, with their original
scope and scientific qualifications intact:

- [1.0 stabilization decision](one-dot-zero-decision-audit.md) — why the
  post-0.12 stabilization audit did not justify adding another estimator.
- [1.2 release-qualification audit, 23 October](one-dot-two-release-qualification-audit-20261023.md) —
  source/package evidence and limitations before the eventual publication.
- [Proposed narrow 1.2 scope, 23 October](one-dot-two-narrow-release-scope-decision-20261023.md) —
  initial proposal for ten W1–W4 orchestration contracts.
- [RC2 E5 content decision request, 23 October](rc2-e5-content-decision-request-20261023.md) —
  experimental E1–E4 scope considered separately from stable workflow support.
- [RC2 publication review checklist, 23 October](rc2-publication-review-checklist-20261023.md) —
  qualifications and safeguards requested at that date.
- [RC2 publisher handoff, 23 October](rc2-production-publisher-handoff-20261023.md) —
  production authorization and the required human/environment controls.
- [Owner-directed RC2 authorization, 24 October](rc2-owner-production-authorization-20261024.md) —
  owner request, not evidence of independent review at the time.

For the **eventual completed 1.2.0 release**, use the
[published 1.2.0 notes](../releases/1.2.0.md),
[separate stable-publication governance](../releases/1.2.0-publication-governance.md),
and [release readiness with GitHub and PyPI evidence](../release-readiness.md).

## Earlier development-candidate context (retained)

The prior development source `1.2.0rc2.dev0` was unpublished at the time
of its original reviews; the literal `1.2.0rc2` then underwent its own
separate prerelease qualification. These are **past development states**,
not assertions about today's stable distribution.

Historical **1.2.0rc1** workflow qualification is preserved under the
[archived RC1 page](../releases/1.2.0rc1.md). Its qualification records remain
immutable: F1–F6 experimental science cannot be retroactively attributed to
that candidate.

The F1–F6 development draft [PR #227](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/227)
had 27/27 GitHub workflow groups green on exact head
`d48c939b01fbfa19f0e060902b6a61ebddbe7aa6`.
That is historical engineering evidence, **not calibration** of new hypothesis
tests.

The later [draft PR #235](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/235)
introduced early study-design and quality utilities for separate review.
Its contemporaneous pending tests and publication posture must not be
presented as the current 1.2.0 release status.

!!! warning "Scientific qualifications remain distinct"
    Published **1.2.0** does not resolve the whole-function coverage
    [issue #289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289)
    or missing-gaze identification
    [issue #296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296).
