# Pre-1.0 release-readiness checklist

The stabilization line changes the success criterion from feature count to
whether an independent researcher can choose, reproduce, audit and correctly
interpret a workflow.

## Repository policy

Historical state at the start of 0.55 was an unprotected `main`. The current
0.10 final-release qualification state is different:

- default branch: `main`;
- `main` is protected by the release-quality ruleset;
- required pull-request/status-check protection is active;
- issue #64 is closed.

This repository-policy gate is therefore satisfied for the final 0.10.0 qualification path.

### Required target policy for `main`

Configure a branch ruleset or branch-protection rule that:

- requires changes to enter through a pull request;
- requires all selected CI status checks to pass before merge;
- requires the pull-request branch to be up to date before merge;
- blocks force pushes;
- blocks branch deletion;
- requires conversation resolution;
- does not permit routine bypass of the scientific quality gates.

The current check contexts intended for protection are:

- `package`;
- `test (ubuntu-latest, 3.11)`;
- `test (ubuntu-latest, 3.12)`;
- `test (ubuntu-latest, 3.13)`;
- `test (windows-latest, 3.11)`;
- `test (windows-latest, 3.12)`;
- `test (windows-latest, 3.13)`;
- `test (macos-latest, 3.11)`;
- `test (macos-latest, 3.12)`;
- `test (macos-latest, 3.13)`;
- `docs-build`;
- `examples`;
- `scikit-fda`;
- `FDApy sparse / Python 3.11`;
- `FDApy sparse / Python 3.12`.
- `performance-envelope`.
- `release-readiness`.

Use exact names from a recent successful pull request when configuring the
ruleset. Required status checks should remain unique across workflows.

## Canonical workflow readiness

- [x] Five canonical workflow routes are defined.
- [x] Each route starts from a scientific question rather than a function list.
- [x] Each route includes assumptions, fitting, uncertainty/diagnostics and
      reporting.
- [x] Advanced/diagnostic/experimental branches are visibly separated.
- [x] One realistic research-style executable end-to-end example exists for
      every canonical route and is exercised by examples CI.

## API stability

- [x] Canonical API manifest exists and is tested.
- [x] Public naming conventions are documented.
- [x] No mass breaking rename is performed in 0.55.
- [x] Deprecation policy requires a compatibility window.
- [ ] Historical inconsistencies selected for future aliasing are individually
      documented before any removal.

## Scientific validation

- [x] Existing synthetic truth and contract tests remain mandatory.
- [x] 0.54 grouped-binomial GEE is checked against an independently represented
      row-expanded Bernoulli fit.
- [x] Independent-reference validation ledger covers selected FPCA, mixed-model,
      GEE/exposure, distance, RQA and transfer-entropy reference cases.
- [x] Reference cases include expected quantity, evidence type, tolerance and CI
      test.
- [x] Numerical tolerances are governed by quantity/reference class rather than
      one universal threshold.

Coverage remains a floor; raising line coverage alone is not a release target.
The 0.56 ledger keeps analytical truth, independent-equivalence and simulation
recovery as distinct evidence types.

## Performance qualification

- [x] Record participant count in the qualified workload scale.
- [x] Record trials per participant in the qualified workload scale.
- [x] Record functional grid length in the qualified workload scale.
- [x] Record basis/component dimension where applicable.
- [x] Record repeated runtime and peak memory for FPCA/bootstrap, nested mixed
      effects, full-refit bootstrap, generalized GEE, recurrence/RQA and
      sensitivity multiverses.
- [x] Publish a conditional single-package reference envelope without
      unsupported comparative speed claims.

The first qualified reference snapshot is a CI-sized GitHub-hosted Linux
envelope. Broader scaling curves may be added later, but they are not required
to claim that the 0.56 qualification harness itself is operational.

## Reproducibility and serialization

- [x] Define an explicit environment/software-version capture payload.
- [x] Define a portable JSON + NPZ scientific-result snapshot rather than
      permanent backend-object pickle compatibility.
- [x] Preserve scientific arrays, identifiers, units, diagnostics and
      provenance while marking opaque backend fields explicitly nonportable.
- [x] Verify round-trip preservation, schema rejection and array checksum
      integrity in CI.
- [x] Define cross-version behavior: schema compatibility is explicit and
      source/current package versions remain visible.
- [x] Add a reproducibility bundle checklist for manuscript workflows.

These 0.57 portability/environment items are pull-request qualified; exact-main
requalification remains required after merge.



## Release automation and publication

- [x] Dedicated `release.yml` is isolated from ordinary push/PR CI.
- [x] Release distributions are built exactly once and reused for TestPyPI,
      PyPI and GitHub Release attachment.
- [x] `python -m build`, `twine check`, fresh wheel install, fresh sdist
      install and an installed-package canonical smoke test are encoded in both
      release automation and non-publishing release-readiness CI.
- [x] Normal `main` pushes never publish; production requires an explicit `release.yml` dispatch with `target=production` from exact protected `main`.
- [x] Ordinary `production` fails if the GitHub tag/release or PyPI version already exists.
- [x] Partial-publication recovery is isolated behind explicit `target=resume-production`.
- [x] Production creates the GitHub Release first, then publishes the identical checksum-verified wheel/sdist to PyPI.
- [x] PyPI publishing uses the OIDC Trusted Publishing action and no long-lived
      API token.
- [x] TestPyPI rehearsal is supported through the same build artifact.
- [x] Production checks live GitHub governance and exact-main CI before
      publishing.
- [x] For the 0.11 release line, exact-main governance additionally requires the `recovery` functional-simulation qualification check and the threshold-free `stress-evidence` check; both workflows run on `main` as well as the isolated 0.11 release branch.
- [x] Exact-main governance also requires native sparse/PACE `sparse-performance`, `stress-recovery`, and `noise-variance-recovery`; `sparse-native-validation` runs on `main` and the active 0.11 release branch.
- [ ] TestPyPI Trusted Publisher/rehearsal remains available as an optional rehearsal.
- [x] Dedicated production PyPI Trusted Publisher is configured for GitHub environment `pypi`.
- [x] `pypi` GitHub environment has the intended required-reviewer protection.
- [x] `main` is protected and issue #64 is closed.
- [x] Final `0.10.0` was armed only after PR #106 and exact protected-main qualification passed.
- [x] Production workflow #11 published `v0.10.0` from exact protected-main commit `1a14f2f6544b18740e73729ebe193ed348cb23bc`, and the fresh production-PyPI install check passed.
- [x] `RELEASE_READINESS.json` is jointly disarmed after publication to prevent accidental republication of `0.10.0`.

The first public prerelease `0.9.0rc1` successfully exercised GitHub-first
publication followed by production PyPI OIDC publication and clean installation.
Version `0.9.0` repeated the complete qualification under the final version
rather than relabeling RC evidence. Production workflow authority now points
only at the dedicated `pypi` environment. Issue #69 is closed and the obsolete
production publisher cleanup remains complete for final 0.10.0 qualification.

## 0.11.0rc1 candidate state

The current stable release remains `0.10.0`. The active release-candidate
qualification target is `0.11.0rc1`.

Pre-RC stabilization is complete:

- stable 0.10.0 was reconciled into the isolated 0.11 line;
- the feature surface is frozen around the known-truth simulation/recovery laboratory;
- fresh recovery qualification and development performance evidence passed;
- threshold-free stress evidence is reproducible and retains failed replicates;
- the exact post-merge stress run retains the difficult estimated-noise
  diagonal-difference regime rather than clipping non-positive estimates or
  widening thresholds.

The rc1 qualification and expanded exact-main matrix are complete. Protected-main
commit `4be7d13186dbef7487a03e3d81c05e0eefb751e0` passed all ten workflow
groups, including functional recovery, threshold-free stress, native sparse/PACE
validation, and package + Ubuntu/macOS/Windows × Python 3.11–3.13.

This separate governance-only change arms both GitHub and production readiness.
Publication remains an explicit manual production action; ordinary pushes and
merges do not publish.

## Release-candidate gate

Do not enter a 0.9-style release-candidate phase until:

1. branch protection/rulesets enforce required PR checks;
2. all five canonical workflows have independent researcher-oriented examples;
3. selected independent-reference validation cases pass on supported platforms;
4. practical performance envelopes are documented;
5. serialization/reproducibility policy is tested;
6. documentation clearly distinguishes canonical, advanced, diagnostic and
   experimental APIs;
7. no known scientific correctness issue is hidden by a warning, fallback or
   undocumented default.


## Post-0.9.0 state

`0.10.0` is the current stable release. Stable `0.9.0` and prereleases `0.10.0rc1` and `0.10.0rc2` remain immutable historical records. Production workflow #11 published final `0.10.0` through GitHub-first release creation and checksum-verified PyPI OIDC Trusted Publishing from exact protected-main commit `1a14f2f6544b18740e73729ebe193ed348cb23bc`; the fresh production-PyPI installation smoke test passed.

Final `0.10.0` promotes the corrected rc2 code without scientific/API expansion. The package identity, validation manifests, documentation contracts, fresh performance envelope, complete pull-request matrix, post-arming exact-main matrix, and public-artifact verification all completed successfully. Publication readiness is now deliberately disarmed; ordinary merges remain non-publishing, and a future release must begin a new reviewed version/readiness cycle.

### Production publisher authority

Production authority is registered for GitHub environment `pypi`, and issue
#69 is closed after removal of the obsolete production publisher claim tied to
`testpypi`. The dedicated `pypi` environment is therefore the intended
production publishing authority for the 0.10 release path.
