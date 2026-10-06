# Release readiness and publication state

## Current stable release — 1.0.0

`eyetrajectoriespy 1.0.0` is published on GitHub and production PyPI and remains the stable compatibility baseline for the 1.x line.

Final publication was completed on **4 October 2026** from exact protected-main arming commit `d90fbbeea390054019e7689badedf5011ee09c22` through production workflow #18 (`37185125898`). The workflow:

- built the wheel and sdist exactly once;
- passed exact-main production governance and unpublished-version preflight;
- created annotated tag and GitHub Release `v1.0.0`;
- verified release checksums;
- published the exact distributions through PyPI OIDC Trusted Publishing with digital attestations; and
- passed a fresh `eyetrajectoriespy==1.0.0` production-PyPI installation smoke test.

Post-publication PR #156 recorded the immutable evidence, promoted `1.0.0` as the visible stable release, and jointly disarmed GitHub/PyPI publication readiness again. Ordinary pushes and merges remain non-publishing.

## Qualified release-candidate source — 1.1.0rc1

The active source identity is **`1.1.0rc1`**. Exact-version qualification is complete; this governance-only tranche arms publication authority but does not itself publish the package or change the stable installation guidance above.

The sparse/irregular scientific programme (#158) completed A1–C1. The integration/readiness programme (#183) then completed R1–R5:

1. R1 — integrated API/public-surface audit;
2. R2 — documentation/release narrative reconciliation;
3. R3 — canonical end-to-end product analyses;
4. R4 — consolidated exact-main evidence/performance audit; and
5. R5 — literal `1.1.0rc1` qualification and exact-main closure.

R4 recorded `eligible_for_rc_decision=true`. R5 qualification PR #197 then passed its complete **26-workflow pull-request matrix**, merged through protected `main`, and produced exact qualified commit `909f7cd493fc21f643e1f923ed503e6128dc750c`. The post-merge exact-main push matrix finished **25/25 workflow groups successfully with zero failures**.

Fresh literal-RC evidence remains separate from the immutable R4 `1.1.0.dev0` development-readiness ledger and the frozen 1.0 qualification evidence. No estimator, scientific default, dependency, supported module-scoped API, or frozen 1.0 root compatibility boundary changed during RC qualification.

## Current publication interlock

The machine-readable authority is `RELEASE_READINESS.json`.

Current arming-branch state:

- stable published version = `1.0.0`;
- active source identity = `1.1.0rc1`;
- `production_release_ready = true`;
- `github_release_ready = true`;
- exact qualified RC main = `909f7cd493fc21f643e1f923ed503e6128dc750c`;
- exact RC qualification matrix = 25/25 successful post-merge workflow groups;
- stable 1.0 API boundary remains frozen and machine-checked;
- A1–C1 1.1 APIs remain module-scoped and additive;
- historical 1.0 qualification evidence remains attributed to `1.0.0`;
- the R4 development-readiness ledger remains attributed to `1.1.0.dev0` and is not relabelled as RC evidence; and
- active reference/tolerance/performance evidence is qualified under literal `1.1.0rc1`.

These true flags are **publication authority, not publication itself**. After this governance-only change merges, the resulting exact protected-main arming commit must pass the required exact-main governance checks. Only then may an explicit manual `release.yml` dispatch with `target=production` be used.

## Final 1.0 qualification

Final `1.0.0` received its own literal-version evidence rather than relabelling `1.0.0rc1` evidence.

Qualification PR #154 passed its complete **17-workflow** pull-request matrix and merged as protected-main commit `1a2afc79e43108e674f3cdd2dc1cb2d8c1b8b3f0`. The exact post-merge matrix then passed **17/17 workflow groups with zero failures**, including:

- frozen 1.0 API-boundary verification;
- package build plus Ubuntu/macOS/Windows × Python 3.11–3.13;
- strict documentation and examples;
- fresh exact-`1.0.0` package-wide performance;
- functional-simulation validation/stress;
- native sparse FPCA/PACE validation;
- sparse-MFPCA recovery and final qualification;
- reproducibility and product-observation workflows;
- optional backends; and
- exact external `mGSFPCA 0.2.2` comparator qualification.

Governance-only PR #155 armed publication only after that final-version matrix passed. The resulting arming commit `d90fbbeea390054019e7689badedf5011ee09c22` then passed its own complete **16-workflow** exact-main matrix before the manual production dispatch.

## Release-candidate observation for 1.0

Published `1.0.0rc1` remains immutable prerelease history. Before final promotion it was reinstalled from production PyPI on Python 3.11–3.13 outside the source checkout and passed the deep installed recovery/stress/portability/sparse-MFPCA observation chain.

Canonical exact-main installed-RC workflow run `37160170148` retained 42/42 declared threshold-free stress records, returned 36/36 successful sparse-MFPCA joint-PACE scores, and reported zero nonportable sparse fields. Artifact `11287283256` has digest `sha256:92d4053b50180153d0f37f99881f3f4c490a1d1d132b329cc8fd829e74fca5e4`.

No result-changing or frozen-public-API defect was identified that required another 1.0 release candidate.

## Required path before 1.1.0rc1 publication

The qualification programme is complete and the publication path is now deliberately narrow:

```text
R1 integrated API audit                         complete
        |
R2 documentation/release narrative              complete
        |
R3 end-to-end product analyses                  complete
        |
R4 exact-main evidence/performance audit         complete
        |                                        eligible_for_rc_decision=true
R5 literal 1.1.0rc1 qualification               complete
        |
        v
exact qualified main 909f7cd493fc...            25/25 successful
        |
        v
separate governance-only publication arming     current tranche
        |
        v
protected-main merge
        |
        v
exact arming-main governance matrix
        |
        v
explicit manual release.yml target=production
        |
        v
GitHub/PyPI verification
        |
        v
post-publication readiness disarm
```

The arming change contains no scientific or package-behaviour modification. Ordinary pushes and merges remain non-publishing throughout.

## Post-1.0 compatibility policy

- **1.0.x**: compatible bug fixes, documentation, portability, validation and performance improvements that preserve established scientific meaning.
- **1.x**: additive capabilities or deliberately governed compatible extensions.
- **Breaking stable API/scientific-contract changes**: deprecate deliberately and reserve actual breakage for `2.0`, unless an exceptional correction is required to prevent demonstrably wrong scientific results.

The repository does not create a new minor release merely because a feature programme is complete. Integrated product evidence and exact qualification must justify promotion.

## Repository policy

`main` is governed by the release-quality ruleset and release automation remains fail-closed:

- changes intended for `main` go through pull requests;
- scientific/package/docs qualification remains mandatory;
- normal `main` pushes do not publish;
- production release requires explicit `release.yml` dispatch with `target=production` from exact protected `main`;
- ordinary production fails if the GitHub tag/release or PyPI version already exists;
- partial-publication recovery is isolated behind explicit `target=resume-production`;
- PyPI publication uses OIDC Trusted Publishing rather than a long-lived token; and
- post-publication readiness is disarmed again after a successful immutable release.

## Historical release evidence

Detailed immutable chronology remains in the release notes:

- [1.1.0rc1](releases/1.1.0rc1.md)
- [1.0.0](releases/1.0.0.md)
- [1.0.0rc1](releases/1.0.0rc1.md)
- [0.12.0](releases/0.12.0.md)
- [0.12.0rc1](releases/0.12.0rc1.md)
- [0.11.0](releases/0.11.0.md)
- [0.10.0](releases/0.10.0.md)

The raw machine-readable publication and qualification chronology is retained in `RELEASE_READINESS.json`; historical releases remain immutable rather than being rewritten to reflect later package state.
