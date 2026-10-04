# Release readiness and publication state

## Current state — stable 1.0.0

`eyetrajectoriespy 1.0.0` is published on GitHub and production PyPI and is the stable compatibility baseline for the 1.x line.

Final publication was completed on **4 October 2026** from exact protected-main arming commit `d90fbbeea390054019e7689badedf5011ee09c22` through production workflow #18 (`37185125898`). The workflow:

- built the wheel and sdist exactly once;
- passed exact-main production governance and unpublished-version preflight;
- created annotated tag and GitHub Release `v1.0.0`;
- verified release checksums;
- published the exact distributions through PyPI OIDC Trusted Publishing with digital attestations; and
- passed a fresh `eyetrajectoriespy==1.0.0` production-PyPI installation smoke test.

Post-publication PR #156 recorded the immutable evidence, promoted `1.0.0` as the visible stable release, and jointly disarmed GitHub/PyPI publication readiness again. Ordinary pushes and merges remain non-publishing.

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

## Release-candidate observation

Published `1.0.0rc1` remains immutable prerelease history. Before final promotion it was reinstalled from production PyPI on Python 3.11–3.13 outside the source checkout and passed the deep installed recovery/stress/portability/sparse-MFPCA observation chain.

Canonical exact-main installed-RC workflow run `37160170148` retained 42/42 declared threshold-free stress records, returned 36/36 successful sparse-MFPCA joint-PACE scores, and reported zero nonportable sparse fields. Artifact `11287283256` has digest `sha256:92d4053b50180153d0f37f99881f3f4c490a1d1d132b329cc8fd829e74fca5e4`.

No result-changing or frozen-public-API defect was identified that required another release candidate.

## Current publication interlock

The machine-readable authority is `RELEASE_READINESS.json`.

Current post-publication state:

- `production_release_ready = false`;
- `github_release_ready = false`;
- package identity = `1.0.0`;
- stable 1.0 API boundary frozen and machine-checked;
- future publication requires a new reviewed version/readiness cycle.

A future release must not be produced by simply toggling a version string. The expected sequence remains:

```text
reviewed source/version change
        |
        v
fresh exact-version qualification evidence
        |
        v
complete pull-request matrix
        |
        v
merge through protected main
        |
        v
complete exact-main matrix
        |
        v
separate governance-only publication arming
        |
        v
exact arming-main matrix
        |
        v
explicit manual release.yml target=production dispatch
        |
        v
GitHub/PyPI verification and post-publication disarm
```

## Post-1.0 compatibility policy

- **1.0.x**: compatible bug fixes, documentation, portability, validation and performance improvements that preserve established scientific meaning.
- **1.x**: additive capabilities or deliberately governed compatible extensions.
- **Breaking stable API/scientific-contract changes**: deprecate deliberately and reserve actual breakage for `2.0`, unless an exceptional correction is required to prevent demonstrably wrong scientific results.

The repository should not create a new minor release merely because 1.0 is complete. External use, issue observation, real-data case studies, documentation and dissemination are the preferred post-1.0 evidence sources.

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

- [1.0.0](releases/1.0.0.md)
- [1.0.0rc1](releases/1.0.0rc1.md)
- [0.12.0](releases/0.12.0.md)
- [0.12.0rc1](releases/0.12.0rc1.md)
- [0.11.0](releases/0.11.0.md)
- [0.10.0](releases/0.10.0.md)

The raw machine-readable publication and qualification chronology is retained in `RELEASE_READINESS.json`; historical releases remain immutable rather than being rewritten to reflect later package state.
