# Pre-1.0 release-readiness checklist

## Final 1.0.0 qualification and publication arming

Final `1.0.0` exact-version qualification is complete on protected-main commit
`1a2afc79e43108e674f3cdd2dc1cb2d8c1b8b3f0`. Its complete pull-request
matrix passed before merge, and the complete post-merge exact-main matrix then
finished **17/17 workflow groups successfully with zero failures**.

That exact final-qualified commit passed the frozen 1.0 API boundary, package
build and Ubuntu/macOS/Windows × Python 3.11–3.13 tests, strict docs/examples,
fresh exact-`1.0.0` package-wide performance, functional-simulation
validation/stress, native sparse/PACE and sparse-MFPCA qualification,
reproducibility/product observation, optional backends, the pre-0.12 recovery
audit, and the exact external `mGSFPCA 0.2.2` comparator. The immutable
`1.0.0rc1` performance envelope remains archived under its literal RC identity;
final `1.0.0` uses separate fresh exact-version evidence.

This governance-only change jointly arms GitHub and production PyPI publication
readiness. It changes no estimator, scientific API, numerical method, analytical
default, test threshold, comparator method, dependency, or performance
methodology, and it does not itself publish `1.0.0`.

After this arming change merges, the resulting exact protected-main arming
commit must itself pass the required exact-main governance checks before the
explicit manual `release.yml` dispatch with `target=production`. Ordinary
pushes and merges remain non-publishing. The production ceremony must originate
from that later arming commit, not from the qualified-but-disarmed checkpoint
`1a2afc79e43108e674f3cdd2dc1cb2d8c1b8b3f0`. Until that production ceremony
succeeds, `0.12.0` remains the latest stable production release and `1.0.0rc1`
remains the published 1.0 prerelease.

## 1.0.0rc1 qualification and publication arming

`1.0.0rc1` has completed exact-version qualification on protected-main commit
`deb61a1b4f2f5e4c8da44d3f2b75ac09fa99430a`; stable `0.12.0` remains the
current published stable release until the RC production ceremony completes.

The complete 17-workflow pull-request matrix passed before merge, and the
post-merge exact-main matrix then finished **17/17 workflow groups green with
zero failures**. On that exact commit, package-wide performance run
`37149050366`, package/test run `37149050402`, frozen 1.0 API-stability run
`37149050398`, and sparse-MFPCA comparator-sensitivity run `37149050450` all
completed successfully. The external comparator path installed its exact
mGSFPCA dependency, ran the comparison, evaluated invariant sensitivity,
verified the contract, and uploaded evidence.

This governance-only change jointly arms GitHub and production PyPI publication
readiness. It changes no estimator, scientific API, numerical method, analytical
default, test threshold, comparator method, dependency, or performance
methodology, and it does not itself publish `1.0.0rc1`.

After the arming change is merged, the new exact protected-main arming commit
must itself pass the required exact-main governance checks before the explicit
manual `release.yml` dispatch with `target=production`. Ordinary pushes and
merges remain non-publishing. The production ceremony must originate from that
later arming commit, not from the qualified-but-disarmed checkpoint
`deb61a1b4f2f5e4c8da44d3f2b75ac09fa99430a`.

The installed-RC workflow remains intentionally pinned to published immutable
`0.12.0rc1` until `1.0.0rc1` actually exists on production PyPI. Retargeting
installed-artifact observation is a separate post-publication qualification
step.

## Final 0.12.0 qualification and publication arming

Final `0.12.0` exact-version qualification is complete on protected-main commit
`4469971885104524e7ceb62f05d63f470f838b80`. The complete post-merge
exact-main matrix finished **14/14 workflow groups green** before publication
arming.

On that exact commit, sparse-MFPCA final-qualification run `36917712173` passed
both the repeated sparse-MFPCA performance-envelope job and the public
observation-process stress job, including evidence-contract verification and
artifact upload. Comparator-sensitivity run `36917712051` passed the native
two-stage sensitivity and exact external mGSFPCA path. Package-wide performance
run `36917712042`, release-readiness run `36917712021`, and package/test run
`36917711911` also completed successfully; the latter covered package build and
Ubuntu/macOS/Windows × Python 3.11–3.13.

The final-version promotion changes package identity only. Published
`0.12.0rc1` remains immutable and its production-installed sparse-MFPCA/
joint-PACE observation remains retained as external-consumer evidence. Fresh
final-version performance is distinct from the RC performance record rather
than a relabeling of prerelease evidence.

This governance-only change jointly arms GitHub and production PyPI publication
readiness. It changes no estimator, scientific API, numerical method, analytical
default, test threshold, comparator method, dependency, or performance
methodology, and it does not itself publish `0.12.0`.

After the arming change is merged, the new exact protected-main arming commit
must itself pass the required exact-main governance checks before the explicit
manual `release.yml` dispatch with `target=production`. Ordinary pushes and
merges remain non-publishing. The production ceremony must originate from that
later arming commit, not from the qualified-but-disarmed checkpoint
`4469971885104524e7ceb62f05d63f470f838b80`.

## 0.12.0rc1 qualification and publication arming

`0.12.0rc1` has completed exact-version qualification on protected main commit
`a30a3297250f60bea7b433591e01052b707155ba`; stable `0.11.0` remains the
current published stable pre-1.0 release until the RC production ceremony
completes.

The complete post-merge exact-main qualification matrix finished **14/14
workflow groups green**. Exact RC sparse-MFPCA final-qualification workflow run
`36839573704` passed on that commit; its `sparse-mfpca-performance-envelope`
job ran the repeated exact-version performance workload, verified the evidence
contract, and uploaded the performance evidence, while the companion
`observation-process-stress` job also completed successfully. External
comparator workflow run `36839573801` also passed on the same exact commit. Its
`mgsfpca-sensitivity` job installed exact mGSFPCA 0.2.2, ran the external
comparator, evaluated invariant sensitivity, verified the external sensitivity
contract, and uploaded the comparator evidence successfully.

This governance-only change jointly arms GitHub and production PyPI publication
readiness. It changes no estimator, scientific API, numerical method, test
threshold, comparator method, dependency, or performance methodology. After the
arming change is merged, the new exact protected-main arming commit must itself
pass the required exact-main governance checks before the explicit manual
`release.yml` dispatch with `target=production`. Ordinary pushes and merges
remain non-publishing. The production ceremony must originate from that later
arming commit, not from the qualified-but-disarmed commit
`a30a3297250f60bea7b433591e01052b707155ba`.

## 0.12.0rc1 entry decision — 1 October 2026

The 0.12 native sparse-MFPCA development surface completed its planned
pre-RC evidence collection on protected main commit
`6b02310b4abb2d16e9df96293e9c8f1a63c34984`.

The entry decision was **ready for exact-version RC qualification**, based on:

- direct joint block-covariance estimator and public `fit_sparse_mfpca()`
  composition;
- analytical/operator and ordering/measurement-error checks;
- identification-aware known-truth recovery over negative, zero and positive
  cross-channel coupling;
- directional asymmetric-Cxy and correlated-measurement-error cases;
- grid and score-ridge descriptive sensitivity;
- internal two-stage marginal-basis sensitivity;
- external mGSFPCA 0.2.2 sensitivity with no equivalence/winner claim;
- public-estimator observation-process stress with 21/21 fits completed and
  zero score failures;
- dedicated sparse-MFPCA repeated runtime/peak-RSS evidence with zero score
  failures in all three declared workloads;
- portable-result zero-loss checks, docs/examples, optional backends,
  release-readiness, and Ubuntu/macOS/Windows × Python 3.11–3.13 CI.

At that pre-RC entry decision, publication remained deliberately disarmed and
the package identity remained `0.11.0`; the decision itself did **not** authorize
a release. It required a separate exact-version alignment/qualification change
followed by a distinct reviewed governance-only arming change.

Those exact-version alignment and qualification requirements are now satisfied
by PR #134 and protected-main commit
`a30a3297250f60bea7b433591e01052b707155ba`. Publication readiness is being
armed only after that complete exact-main evidence passed; the arming commit
must still pass its own exact-main governance checks before manual production
dispatch.

The installed-RC workflow remains intentionally pinned to published immutable
`0.11.0rc1` until the new candidate actually exists on production PyPI.

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

## 0.11.0rc1 published state

At the time `0.11.0rc1` was published, the stable release remained `0.10.0`.
The prerelease is still available from both GitHub Releases and production PyPI
as an immutable historical record.

Pre-RC stabilization is complete:

- stable 0.10.0 was reconciled into the isolated 0.11 line;
- the feature surface is frozen around the known-truth simulation/recovery laboratory;
- fresh recovery qualification and development performance evidence passed;
- threshold-free stress evidence is reproducible and retains failed replicates;
- the exact post-merge stress run retains the difficult estimated-noise
  diagonal-difference regime rather than clipping non-positive estimates or
  widening thresholds.

The rc1 qualification and expanded exact-main matrix completed before
publication. The final release dispatch used exact protected-main commit
`af86a96bfafe3838ac8bd27818c164418b981fc5`, which passed all ten workflow
groups, including functional recovery, threshold-free stress, native sparse/PACE
validation, and package + Ubuntu/macOS/Windows × Python 3.11–3.13.

Production workflow #12 created GitHub prerelease `v0.11.0rc1`, published the
checksum-verified wheel and sdist to production PyPI through OIDC Trusted
Publishing, and completed the fresh production-PyPI installation smoke test on
its second attempt after normal index propagation. Ordinary pushes and merges
remain non-publishing.

## Final 0.11.0 published state

Final `0.11.0` is the current stable pre-1.0 release. Published
`0.11.0rc1` remains an immutable prerelease record.

The production-installed rc1 observation established the external-consumer
basis for promotion:

- exact production-PyPI `0.11.0rc1` installed on Python 3.11–3.13 outside the
  source checkout;
- deterministic seeded simulation replay passed;
- the established four-scenario recovery qualification passed from the
  installed package;
- all 42 declared stress-replicate records were retained;
- the known estimated-noise diagonal-difference regime retained 2/3
  fail-closed `noise_variance_invalid` fits rather than clipping or widening
  thresholds;
- mixed-effects recovery converged without a boundary fit;
- registration recovery targeted the inverse simulator warp;
- portable export/load, reporting, plotting, and environment capture passed;
- exact-main evidence artifact `11059511070` has digest
  `sha256:a01bddd0818c09b298d93596a5698f6f8f835a6e3cde9735857780c2167f289e`.

Final-version qualification was repeated under package identity `0.11.0`.
PR #120 merged as exact protected-main commit
`f0b328dabd9d5050fa9988e3c157d034efb0ee7f`, which passed the complete
final-version matrix and fresh exact-version performance qualification. PR #121
then armed publication without changing scientific code or API behavior.
Its exact protected-main merge commit
`2616675ad2dfc095bf17a442c1d350ba88fd030a` passed the complete post-arming
matrix, including package construction, Ubuntu/macOS/Windows × Python 3.11–3.13,
docs, examples, optional backends, release-readiness, performance,
functional-simulation recovery/stress, and native sparse/PACE validation.

Production release workflow #13 (run `36628220308`) completed successfully on
29 September 2026. It created annotated tag and GitHub Release `v0.11.0`,
published the exact wheel and sdist to production PyPI through OIDC Trusted
Publishing with digital attestations, and passed a fresh
`eyetrajectoriespy==0.11.0` production-PyPI installation smoke test. The
published GitHub Release asset digests are:

- wheel: `sha256:7cba258531ae5f5a41e0a95dbfc1d0604c29456dd121c3a422adc9f576f2e481`;
- sdist: `sha256:99b5285226a675f14a4f42369e6b4a696615b273cbd347c1716387f14250a4bc`.

Post-publication GitHub/PyPI readiness is jointly disarmed again to prevent
accidental republication of immutable `0.11.0`. Ordinary pushes and merges
remain non-publishing; a future release must begin a new reviewed
version/readiness cycle.

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

`0.11.0` is the current stable release. Stable `0.9.0` and `0.10.0`, plus prereleases `0.10.0rc1`, `0.10.0rc2`, and `0.11.0rc1`, remain immutable historical records. Production workflow #11 published final `0.10.0` through GitHub-first release creation and checksum-verified PyPI OIDC Trusted Publishing from exact protected-main commit `1a14f2f6544b18740e73729ebe193ed348cb23bc`; the fresh production-PyPI install check passed.

Final `0.10.0` promotes the corrected rc2 code without scientific/API expansion. The package identity, validation manifests, documentation contracts, fresh performance envelope, complete pull-request matrix, post-arming exact-main matrix, and public-artifact verification all completed successfully. Publication readiness is now deliberately disarmed; ordinary merges remain non-publishing, and a future release must begin a new reviewed version/readiness cycle.

### Production publisher authority

Production authority is registered for GitHub environment `pypi`, and issue
#69 is closed after removal of the obsolete production publisher claim tied to
`testpypi`. The dedicated `pypi` environment is therefore the intended
production publishing authority for the 0.10 release path.
