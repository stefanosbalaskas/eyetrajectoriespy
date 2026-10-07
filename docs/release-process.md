# Coordinated GitHub Release and PyPI publication

## 1.1.0 final exact-version qualification

`1.1.0` final qualification follows successful `1.1.0rc1` qualification, publication, and production-installed observation. The final transition is version-only and must generate fresh literal-version evidence. Historical `1.1.0.dev0`, `1.1.0rc1`, and frozen 1.0 evidence remain attributed to their original identities. Publication remains disarmed throughout final qualification; arming and production publication require later, separate governance.

`eyetrajectoriespy 1.0.0` is the current stable release. The release machinery is intentionally fail-closed: ordinary pushes and merges do not publish, and a public version is produced only after exact-version qualification, protected-main requalification, a separate governance-only arming change, and an explicit manual production dispatch.

The active source identity is `1.1.0` under exact-version qualification. It is non-publishing; `1.0.0` remains the stable release and `1.1.0rc1` remains the published prerelease until final publication succeeds.

## Current 1.1 readiness sequence

The post-1.0 A1–C1 sparse/irregular scientific programme is complete. The integrated development surface remains module-scoped and the frozen 1.0 root boundary remains unchanged.

Issue #183 governs readiness through five deliberately separate tranches:

1. **R1 — integrated API audit:** complete; supported module-scoped 1.1 imports are documented and machine-checked.
2. **R2 — documentation/release narrative:** complete.
3. **R3 — end-to-end product analyses:** complete with zero release-blocking friction.
4. **R4 — consolidated development evidence/performance audit:** complete with `eligible_for_rc_decision=true`.
5. **R5 — RC/final decision:** RC qualification, publication, and installed observation are complete; literal final `1.1.0` qualification is now in progress.

If R4 or R5 identifies unresolved scientific ambiguity, compatibility risk, or product friction, the project remains on `1.1.0.dev0`. Feature completion alone is not sufficient reason to create an RC.

Publication readiness remains jointly false throughout R1–R5 and throughout any future RC qualification.

## Post-1.0 versioning posture

The stable 1.0 public boundary is a compatibility promise:

- **1.0.x** — compatible bug fixes, documentation, portability, validation and performance improvements that preserve established scientific meaning;
- **1.x** — additive capabilities or deliberately governed compatible extensions;
- **2.0** — breaking stable API/scientific-contract changes after explicit deprecation, except where an exceptional correction is necessary to prevent demonstrably wrong scientific results.

A new minor release is not created merely because the previous milestone or a feature programme is complete. Integrated product evidence and exact qualification must justify promotion.

## Standard release sequence

Every future public release follows the same fail-closed publication chain used for 1.0. For 1.1, the R1–R5 readiness programme happens **before** this release-specific chain begins.

```text
explicit release/RC decision
        |
        v
review and freeze the intended release surface
        |
        v
align literal package/citation/docs/validation identity
        |
        v
generate fresh exact-version evidence
        |
        v
pass the complete pull-request qualification matrix
        |
        v
merge through protected main
        |
        v
pass the complete exact-main matrix
        |
        v
arm publication in a separate governance-only change
        |
        v
pass the exact arming-main governance matrix
        |
        v
manual release.yml dispatch with target=production
        |
        v
verify GitHub Release + hashes + attestations + production PyPI install
        |
        v
post-publication closeout and joint disarm
```

Historical evidence is never relabelled as evidence for a new package identity. A release candidate, final release, or patch release must receive its own exact-version qualification whenever the release contract requires fresh evidence.

## 1.1 RC decision boundary

An eventual `1.1.0rc1` is not an automatic rename of `1.1.0.dev0`.

Before any RC version change:

- R1–R4 must be complete;
- R4 must explicitly recommend `eligible_for_rc_decision=true` on one exact qualified protected-main commit;
- R5 must review open scientific/product/performance issues and explicitly approve RC entry.

If RC entry is approved, the RC qualification PR must be version/governance-only:

- no estimator addition;
- no analytical-default or threshold change;
- no hidden resampling/interpolation/correction change;
- no dependency change unless separately justified and reviewed;
- active version declarations aligned to literal `1.1.0rc1`;
- fresh literal-RC performance and qualification evidence;
- complete PR and post-merge exact-main matrices; and
- `production_release_ready = false` and `github_release_ready = false` throughout qualification.

A successful RC qualification still does not publish anything. Publication arming remains a separate later governance-only change.

## Qualification before publication

Before publication may be armed:

1. the intended public/scientific surface must be reviewed;
2. active version declarations must agree;
3. qualification ledgers must refer to the literal target version;
4. fresh performance evidence must be generated rather than copied from another version;
5. package, cross-platform, documentation, examples, optional backends and scientific qualification workflows must pass on the pull-request head;
6. the exact merged protected-main commit must pass the corresponding complete matrix; and
7. publication readiness must remain jointly false until a separate reviewed arming change.

For stable 1.x releases, the frozen API contract is an additional release constraint: stable exports/signatures/result schemas must not drift silently.

## Publication arming

Publication arming is deliberately separated from version/scientific qualification.

The arming change should contain governance/readiness state only and must not introduce an estimator, new scientific API, analytical-default change, threshold change, dependency change or performance-methodology change.

Both readiness flags move together:

```json
{
  "production_release_ready": true,
  "github_release_ready": true
}
```

The arming commit itself must then pass the required exact-main governance checks. A green qualification commit is not sufficient if the later publication-authority commit has not been independently checked.

## Production dispatch

Production is an explicit manual workflow dispatch:

```text
workflow: release.yml
target: production
ref: main
```

The workflow is designed to:

- require exact protected `main`;
- verify the repository's production-governance checks;
- reject development versions;
- reject a pre-existing GitHub tag/release or PyPI version for ordinary production;
- build the wheel and sdist once;
- validate and smoke-test both distributions;
- create the GitHub Release first;
- verify checksums;
- publish the same distributions to PyPI through OIDC Trusted Publishing;
- generate digital attestations; and
- reinstall the exact production-PyPI version in a fresh environment.

`target=resume-production` is reserved for explicitly validated partial-publication recovery. It must not be used as a routine way to bypass the ordinary unpublished-version preflight.

## Post-publication closeout

After successful production publication:

1. record workflow/run/artifact/checksum provenance;
2. update public release-status documentation if necessary;
3. jointly set GitHub/PyPI readiness back to `false`;
4. merge that closeout through the normal qualification path; and
5. leave the published tag and distributions immutable.

A later documentation commit is allowed to describe the finished release, but it must not move the published tag or rewrite release artifacts.

## 1.0.0 production precedent

Final `1.0.0` demonstrates the complete process:

- qualification PR #154 → protected-main `1a2afc79e43108e674f3cdd2dc1cb2d8c1b8b3f0` → 17/17 exact-main workflows green;
- governance-only arming PR #155 → protected-main `d90fbbeea390054019e7689badedf5011ee09c22` → 16/16 exact-main workflows green;
- production workflow #18 (`37185125898`) → GitHub Release `v1.0.0`, production PyPI OIDC publication, checksums/attestations and fresh exact-version install verification;
- post-publication PR #156 → stable public status recorded and publication readiness jointly disarmed.

See the [1.0.0 release notes](releases/1.0.0.md) and [release-readiness page](release-readiness.md) for the exact evidence record.

## Historical releases

Earlier release-specific qualification narratives remain in their immutable release notes rather than being treated as the current process:

- [1.0.0rc1](releases/1.0.0rc1.md)
- [0.12.0](releases/0.12.0.md)
- [0.12.0rc1](releases/0.12.0rc1.md)
- [0.11.0](releases/0.11.0.md)
- [0.11.0rc1](releases/0.11.0rc1.md)
- [0.10.0](releases/0.10.0.md)

Those records describe the release state that existed at the time and should not be rewritten merely because the package later advanced to 1.0 or entered the 1.1 development cycle.
