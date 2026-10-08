# E5 qualification: literal `1.2.0rc2` (not yet authorized)

> **Current source: `1.2.0rc2.dev0`; published stable: `1.1.0`.**
> This is a qualification protocol, **not** RC2 qualification, release approval, or permission to publish.
> The machine-readable prequalification ledger is [`RC2_QUALIFICATION_STATUS.json`](../../RC2_QUALIFICATION_STATUS.json).
> Tracking issue: [#225](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/225).

## Completed preconditions

- E1–E4 engineering qualification: PR #223 passed 33/33 on its exact head, merged to `565097d12e184310b44f2737ef41f33a13546996`, then protected-main workflow groups passed 32/32.
- Researcher-readiness PR #224: 26/26 workflow groups on exact head `cc4429e5e0d6cc027dc5403722c96182b5713d54`, squash-merged to protected-main commit `807ee3e131591620f6b1be15e488e80f73dd7c83`. All 25/25 post-merge workflow groups subsequently passed.
- An authentic-data CI example executed E1–E4 using 16 source-pinned windows, selecting 15 explicit complete-case windows; it is **research usability**, not known-truth estimator verification. The original CC BY-NC 4.0 source recordings are not redistributed.
- The ten legacy W1–W4 workflow contracts and the 12 experimental E1–E4 exports remain separately audited; no production publication flags have been armed.

## Required literal-candidate transition

1. Prepare a **separate RC2 qualification pull request** based on the fully green protected-main development source; do not overwrite frozen RC1 Git blobs or relabel its reference, tolerance, API or performance evidence. Maintain both readiness flags false.
2. Introduce one consistent literal `1.2.0rc2` identity across `pyproject.toml`, package `__version__`, `CITATION.cff`, `CANONICAL_WORKFLOWS.json`, `RELEASE_READINESS.json`, documentation and the candidate metadata. `verify_release_version.py` must remain fail-closed until **fresh** exact-version qualification ledgers exist.
3. Re-execute known-truth analytical and simulation-validation tests for the unchanged estimators. Capture exact Python/platform, tolerances, fit failures and result invariants; where necessary write new *RC2-specific* reference and tolerance evidence instead of changing RC1's frozen files. Re-evaluate performance on literal RC2, with original sources preserved for historical comparison.
4. Build literal RC2 wheel/sdist, inspect distribution metadata, hash the build artifacts, verify `pip check` and install the wheel in an isolated environment **outside the source checkout**. Execute all ten W1–W4 workflow routes and the full E1–E4 empirical or synthetic product case using the installed package. No hidden source imports.
5. Verify the empirical-gaze dataset identity and licensing, all 16-to-15 window decisions, missingness reports and failure-retaining sensitivity output. The CC BY-NC 4.0 third-party raw trials must stay out of Git artifacts. The CI product evidence must distinguish real-data usability, known-truth simulation recovery and performance measurements.
6. Check E1 processing order, explicit interpolation permissions and no silent sparse densification; E2 warns but never silently excludes; E3 retains failed specifications and does not infer statistical significance; E4 reports actual results and cryptographic file manifests without invented p-values. Check the frozen 12-export signatures and 10-workflow contracts against their audits.
7. Obtain complete pull-request CI (Linux, macOS, Windows × Python 3.11–3.13, documentation, estimator/scientific tests, external sparse/Bayesian comparators, performance and installed analyses), record exact head SHA, workflow run IDs and SHA256 artifact digests. Zero unresolved required checks.
8. Merge the independently reviewed literal candidate through protected `main` and **repeat the full exact-main qualification**, including regenerated documentation and installed-wheel evidence. Only then separately consider publication arming, release tagging, TestPyPI/PyPI/GitHub publication and installed-candidate observation.

## Release decision contract

All of the following remain **false** until their own gates finish: `literal_rc2_pr_qualified`, `literal_rc2_exact_main_qualified`, `literal_rc2_installed_wheel_qualified`, `literal_rc2_scientific_evidence_qualified`, `literal_rc2_perf_envelope_qualified`, and `release_publication_authorized`.

The Bayesian B2/B3 comparator supports methodological feasibility only. Native Bayesian FPCA, effect-region localization, irregular mixed-effects estimators and neural models are excluded from RC2.
