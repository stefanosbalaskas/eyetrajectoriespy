# Release readiness and publication state

## Experimental source line (draft PR #223)

Development source `1.2.0rc2.dev0` contains experimental E1–E4 utilities. It is not release-qualified and not published. Exact `1.2.0rc1` evidence is unchanged and must not be attributed to this source. A distinct RC2 gate requires its own scientific API audit, numerical/product evidence, release-version synchronization, protected-main CI and separate publication governance.

## Completed 1.2rc1 release-candidate qualification

`1.2.0rc1` is the active unpublished candidate source identity after PR #220 merged at exact protected-main SHA `67c59473cd6ee320298698dd25c1d4929bcf9a96`. The 29/29 successful PR-head workflows and independent post-merge exact-main qualification are distinct gates. No publication is armed by this change; published stable remains `1.1.0`.

## Current stable release — 1.1.0

`eyetrajectoriespy 1.1.0` is published on GitHub and production PyPI and is now the stable/default release for the 1.x line.

Final publication completed on **7 October 2026** from exact signed protected-main arming commit `66cfb66798a90950e28401e45ee47e98543ff5c6` through production workflow #20 (`37591747059`). The workflow:

- built the wheel and sdist exactly once;
- passed exact-main production governance and unpublished-version preflight;
- created annotated tag and final GitHub Release `v1.1.0` targeting the exact arming commit;
- generated and verified release checksums;
- published the exact distributions to production PyPI through OIDC Trusted Publishing with digital attestations; and
- passed a fresh `eyetrajectoriespy==1.1.0` production-PyPI installation smoke test.

Published final assets:

- `eyetrajectoriespy-1.1.0-py3-none-any.whl` — `sha256:bb869c7a1dd3ecd03135d1615d2977f4d0e07c8cfa4fdef10cddc83f826dbf5b`;
- `eyetrajectoriespy-1.1.0.tar.gz` — `sha256:446a42532f3812b0aae8df24e0a95a40355a0669e822e4b27cd31350f57cf87b`;
- `SHA256SUMS` — `sha256:ee04bbc6056b379df136480f033f9aaa9093447f3ec4b3c93213aa3b6efa3705`; and
- retained workflow artifact `11469042132` — `sha256:2397c33271f28ea174805a679badea859bee65385189ab22ba502c4e074cffcf`.

The annotated tag object is `9a59ba37537559b9263d908bcdc9fa1dc129c6f5` and resolves exactly to arming commit `66cfb66798a90950e28401e45ee47e98543ff5c6`.

## Next release gate — 1.2.0rc1 (not yet published)

The 1.2 W1–W4 workflow/orchestration programme is complete on protected main, including all ten typed workflow contracts and installed-wheel product qualification. [PR #220](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/220) merged the **literal** `1.2.0rc1` identity and its fresh evidence; the exact protected-main CI gate is independent. Candidate qualification is not permission to publish: the publication interlocks are disarmed until a subsequent reviewed governance-only arming step. See [workflow product qualification](validation/one-dot-two-workflow-product-qualification.md) and [workflow API](workflows/workflow-orchestration.md).

## 1.1 qualification and publication basis

The 1.1 sparse/irregular programme (#158) and integration/readiness programme (#183) progressed through the following audited gates:

- `1.1.0rc1` exact qualification and production publication;
- production-installed RC observation on Python 3.11–3.13;
- fresh literal-final `1.1.0` qualification rather than relabelling RC evidence;
- PR #201 final qualification: **26/26** pull-request workflow groups successful;
- exact final-qualified main `7eaf842214dc26c8cd1cef9eaaa72a55916974de`: **25/25** post-merge workflow groups successful;
- PR #203 governance-only arming: **25/25** pull-request workflow groups successful;
- exact signed arming main `66cfb66798a90950e28401e45ee47e98543ff5c6`: **24/24** workflow groups successful, including release-readiness, cross-platform package tests, sparse-MFPCA final qualification, and the exact external `mGSFPCA` comparator; and
- production workflow #20: successful final GitHub/PyPI publication and fresh exact-version install smoke.

No estimator, numerical method, scientific default, dependency, threshold, comparator method, performance methodology, public export, or frozen 1.0 root-API contract changed during final qualification, arming, or publication.

## Post-1.1 publication interlock (1.1 closeout snapshot)

The machine-readable authority is `RELEASE_READINESS.json`.

The following fields record the final **1.1.0 closeout snapshot**, not the newer 1.2 source identity or a claim that 1.2 has been published:

- stable/default published version = `1.1.0`;
- immutable published prerelease = `1.1.0rc1`;
- source identity at **1.1.0 closeout** = `1.1.0` (subsequently advanced to `1.2.0.dev0` on protected main for the 1.2 qualification programme);
- `production_release_ready = false`;
- `github_release_ready = false`;
- exact final-qualified main = `7eaf842214dc26c8cd1cef9eaaa72a55916974de`;
- exact final-publication arming main = `66cfb66798a90950e28401e45ee47e98543ff5c6`;
- final production release workflow = #20 (`37591747059`), successful;
- stable 1.0 root API boundary remains frozen and machine-checked; and
- the qualified 1.1 additions are stable module-scoped APIs.

Both publication-readiness flags were **false** at 1.1 closeout and remain disarmed in the 1.2 candidate qualification process. Ordinary pushes and merges remain non-publishing; a future release requires its own reviewed version/readiness cycle.

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

## 1.1.0 promotion path — completed

```text
R1 integrated API audit                         complete
        |
R2 documentation/release narrative              complete
        |
R3 end-to-end product analyses                  complete
        |
R4 exact-main evidence/performance audit         complete
        |
R5 literal 1.1.0rc1 qualification               complete
        |
        v
1.1.0rc1 publication                            complete
        |
        v
production-installed RC observation              complete
        |
        v
literal final 1.1.0 qualification                complete
        |
        v
exact final-qualified main 7eaf842214dc...       25/25 successful
        |
        v
governance-only final publication arming         PR #203
        |
        v
exact arming main 66cfb66798a9...                24/24 successful
        |
        v
manual release.yml target=production             run 37591747059
        |
        v
GitHub Release + PyPI + attestations             complete
        |
        v
fresh production-PyPI install smoke              pass
        |
        v
post-publication readiness disarm                current closeout
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

- [1.1.0](releases/1.1.0.md)
- [1.1.0rc1](releases/1.1.0rc1.md)
- [1.0.0](releases/1.0.0.md)
- [1.0.0rc1](releases/1.0.0rc1.md)
- [0.12.0](releases/0.12.0.md)
- [0.12.0rc1](releases/0.12.0rc1.md)
- [0.11.0](releases/0.11.0.md)
- [0.10.0](releases/0.10.0.md)

The raw machine-readable publication and qualification chronology is retained in `RELEASE_READINESS.json`; historical releases remain immutable rather than being rewritten to reflect later package state.
