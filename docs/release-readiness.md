# Pre-1.0 release-readiness checklist

The stabilization line changes the success criterion from feature count to
whether an independent researcher can choose, reproduce, audit and correctly
interpret a workflow.

## Repository policy

Current observed repository state at the start of 0.55:

- default branch: `main`;
- `main` is **not protected**;
- no repository ruleset targets `main`.

This is a release-readiness blocker, not a statistical-method defect.

Tracked in [GitHub issue #64](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/64).

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

Use exact names from a recent successful pull request when configuring the
ruleset. Required status checks should remain unique across workflows.

## Canonical workflow readiness

- [x] Five canonical workflow routes are defined.
- [x] Each route starts from a scientific question rather than a function list.
- [x] Each route includes assumptions, fitting, uncertainty/diagnostics and
      reporting.
- [x] Advanced/diagnostic/experimental branches are visibly separated.
- [ ] Realistic external-data end-to-end examples are qualified for every route.

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
- [ ] Independent-reference validation ledger covers selected FPCA, mixed-model,
      GEE/exposure, distance, RQA and transfer-entropy reference cases.
- [ ] Reference cases include expected quantity, tolerance and CI test.

The unchecked external-reference items are the primary 0.56 validation target.
Coverage remains a floor; raising line coverage alone is not a release target.

## Performance qualification

- [ ] Benchmark participant count.
- [ ] Benchmark trials per participant.
- [ ] Benchmark functional grid length.
- [ ] Benchmark basis dimension.
- [ ] Record runtime and peak memory for FPCA/bootstrap, nested mixed effects,
      full-refit bootstrap, generalized GEE, recurrence/RQA and sensitivity
      multiverses.
- [ ] Publish practical-envelope guidance rather than unsupported speed claims.

These items are planned for 0.56.

## Reproducibility and serialization

- [ ] Define a stable environment/software-version capture payload.
- [ ] Audit serialization of representative result objects.
- [ ] Verify round-trip preservation of consequential provenance.
- [ ] Define compatibility behavior across development versions.
- [ ] Add a reproducibility bundle/checklist for manuscript workflows.

These items are planned for the 0.57 hardening tranche.

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
