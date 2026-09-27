# Pre-1.0 release-readiness checklist

The stabilization line changes the success criterion from feature count to
whether an independent researcher can choose, reproduce, audit and correctly
interpret a workflow.

## Repository policy

Historical state at the start of 0.55 was an unprotected `main`. The current
0.9 release state is different:

- default branch: `main`;
- `main` is protected by the release-quality ruleset;
- required pull-request/status-check protection is active;
- issue #64 is closed.

This repository-policy gate is therefore satisfied for 0.9.0.

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
- [ ] TestPyPI Trusted Publisher/rehearsal remains available as an optional rehearsal.
- [x] Dedicated production PyPI Trusted Publisher is configured for GitHub environment `pypi`.
- [x] `pypi` GitHub environment has the intended required-reviewer protection.
- [x] `main` is protected and issue #64 is closed.
- [x] `RELEASE_READINESS.json` was armed for 0.9.0; it is deliberately disarmed again on `0.9.1.dev0`.

The first public prerelease `0.9.0rc1` successfully exercised GitHub-first
publication followed by production PyPI OIDC publication and clean installation.
Version `0.9.0` repeats the complete qualification under the final version
rather than relabeling RC evidence. Production workflow authority now points
only at the dedicated `pypi` environment. Issue #69 is a mandatory blocker until
the matching PyPI Trusted Publisher claim is migrated there.

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

Stable release `0.9.0` is immutable on GitHub and PyPI. The active development
line is `0.9.1.dev0`. Release automation is manual-dispatch only, so ordinary
maintenance merges cannot trigger a production upload. Before the next release,
the version and readiness manifests must be deliberately armed through a
reviewed pull request, and issue #69 should be resolved by migrating the
production Trusted Publisher claim to the dedicated `pypi` environment.


### Remaining publisher cleanup

Production authority is now correctly registered for GitHub environment
`pypi`. PyPI still shows the older production publisher claim bound to
`testpypi`; remove that obsolete publisher before the next public release so
the dedicated `pypi` environment is the only production publishing authority.
Issue #69 tracks that final cleanup.
