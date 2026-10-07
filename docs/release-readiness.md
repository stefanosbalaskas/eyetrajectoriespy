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

## Published release candidate — 1.1.0rc1

The active source identity is **`1.1.0`** under exact-version final qualification. `1.1.0rc1` remains the published prerelease on GitHub and production PyPI, and **`1.0.0` remains the stable/default release** until final `1.1.0` publication succeeds.

The sparse/irregular scientific programme (#158) completed A1–C1. The integration/readiness programme (#183) then completed R1–R5:

1. R1 — integrated API/public-surface audit;
2. R2 — documentation/release narrative reconciliation;
3. R3 — canonical end-to-end product analyses;
4. R4 — consolidated exact-main evidence/performance audit; and
5. R5 — literal `1.1.0rc1` qualification and exact-main closure.

R4 recorded `eligible_for_rc_decision=true`. R5 qualification PR #197 passed its complete **26-workflow pull-request matrix**, merged through protected `main`, and produced exact qualified commit `909f7cd493fc21f643e1f923ed503e6128dc750c`. The post-merge exact-main push matrix finished **25/25 workflow groups successfully with zero failures**.

Governance-only PR #198 then armed publication. Its exact protected-main arming commit `f4405897e2a7a2392c03523cc7fa18e43df00e5e` passed the complete **24/24 exact-main arming matrix** with zero failures, including the exact external `mGSFPCA` comparator.

Production workflow #19 (`37511987332`) completed successfully on **6 October 2026** from that exact arming commit. It:

- built the wheel and sdist exactly once;
- passed exact-main production governance and unpublished-version preflight;
- created annotated tag and GitHub prerelease `v1.1.0rc1` targeting exact commit `f4405897e2a7a2392c03523cc7fa18e43df00e5e`;
- checksum-verified the release distributions before publication;
- published both distributions to production PyPI through OIDC Trusted Publishing with digital attestations; and
- installed `eyetrajectoriespy==1.1.0rc1` from production PyPI successfully on the **first visibility attempt**, followed by a passing release smoke test.

Published release assets:

- `eyetrajectoriespy-1.1.0rc1-py3-none-any.whl` — `sha256:875242e0c7cd1fae0fdb9e472a33ecf687e99e886e3f36302748563dddede151`;
- `eyetrajectoriespy-1.1.0rc1.tar.gz` — `sha256:f67cf81f93aef8e47d47d918f0945bdaaa437d542381f60316ff0996e2370846`;
- `SHA256SUMS` — `sha256:d849ef5b21eea95dd81626e2f071723a28110556b27911a57d69bc59ab5b8bc4`; and
- retained workflow artifact `11435448783` — `sha256:3572f75c8339f73a2a77845cc01072097309a3b32f5207e0dcffcdf777c99e83`.

Fresh literal-RC evidence remains separate from the immutable R4 `1.1.0.dev0` development-readiness ledger and frozen 1.0 qualification evidence. No estimator, scientific default, dependency, supported module-scoped API, or frozen 1.0 root compatibility boundary changed during RC qualification or publication.

## Current publication interlock

The machine-readable authority is `RELEASE_READINESS.json`.

Current qualification state:

- stable published version = `1.0.0`;
- published prerelease = `1.1.0rc1`;
- active source identity = `1.1.0` (qualification only; not yet published);
- `production_release_ready = false`;
- `github_release_ready = false`;
- exact qualified RC main = `909f7cd493fc21f643e1f923ed503e6128dc750c`;
- exact RC qualification matrix = 25/25 successful post-merge workflow groups;
- exact publication-arming main = `f4405897e2a7a2392c03523cc7fa18e43df00e5e`;
- exact publication-arming matrix = 24/24 successful workflow groups;
- production release workflow = #19 (`37511987332`), successful;
- stable 1.0 API boundary remains frozen and machine-checked;
- A1–C1 1.1 APIs remain module-scoped and additive;
- historical 1.0 qualification evidence remains attributed to `1.0.0`;
- the R4 development-readiness ledger remains attributed to `1.1.0.dev0` and is not relabelled as RC evidence; and
- active reference/tolerance evidence is aligned to literal `1.1.0`; fresh package-wide final performance evidence comes from run `37528714581`, while archived `1.1.0rc1` evidence remains immutable.

Both publication-readiness flags are now **false**. This prevents accidental republication of the immutable RC. Ordinary pushes and merges remain non-publishing. A later final `1.1.0` release must enter a new exact-version qualification and publication-arming cycle rather than reusing the RC authority.

## Current decision gate — exact final 1.1.0 qualification

Production-installed RC observation is complete. Final `1.1.0` is now being qualified as a **version-only promotion** of the frozen, observed `1.1.0rc1` scientific/API surface.

Fresh exact-final package-wide performance qualification passed in workflow run `37528714581` on source commit `cb3ecd82112e41ab1ac2b20961eeb79250da96cb`. Artifact `11443198062` has digest `sha256:fb6c12cae67df237b5ad5b8f172787d0e63fe75cca31199b712d6abf96e94647`. The canonical final envelope is archived separately under `validation/performance/PERFORMANCE_ENVELOPE-1.1.0.json`; the RC envelope remains unchanged.

The remaining qualification gates are the complete pull-request matrix, protected-main merge, and the complete exact-main matrix on the resulting final-qualified commit. Publication remains jointly disarmed. If those gates pass without a result-changing or compatibility-breaking defect, a separate governance-only PR may arm final `1.1.0` publication.

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

## 1.1.0rc1 publication path — completed

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
separate governance-only publication arming     PR #198
        |
        v
exact arming main f4405897e2a7...                24/24 successful
        |
        v
manual release.yml target=production             run 37511987332
        |
        v
GitHub prerelease + PyPI + attestations          complete
        |
        v
fresh production-PyPI install smoke test         pass, attempt 1
        |
        v
post-publication readiness disarm                current tranche
        |
        v
production-installed RC observation              complete
        |
        v
literal final 1.1.0 qualification                current
```

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
