# eyetrajectoriespy 1.2 — draft release qualification audit (23 October 2026)

**Decision: RELEASE HOLD.** This is a source-, workflow- and governance-based audit, not an authorization to publish. All fixes here are confined to a *draft pull request*. Do not merge, tag, invoke the release publisher, publish to TestPyPI or PyPI, or claim that a passing numerical simulation establishes nominal inference coverage.

## Source, evidence and publication identity

Frozen audit baseline: [protected-main source at `6d9bc5396ebf596ea22f9187d87e44b9dd5c03a6`](https://github.com/stefanosbalaskas/eyetrajectoriespy/commit/6d9bc5396ebf596ea22f9187d87e44b9dd5c03a6). The main GitHub Actions runs inspected on 23 October comprise **24/24 successful current-head workflow runs** (includes Linux/macOS/Windows matrix in the `tests` workflow; source packaging, docs, examples, release-readiness and optional/functional/sparse qualifications).

Important distinction: **24 passing workflow runs ≠ all possible 1.2 release gates**. Other source-path or manual-dispatch workflows do not run on documentation-only main commits. In particular, the 1.2 installed W1–W4 product qualification workflow and the PyPI-installed-RC workflow have separate triggers and are not proved on a fresh literal RC2 by a passing documentation build. The installed-RC workflow in `main` is still pinned to older **1.1.0rc1** and cannot qualify a new 1.2 RC.

| Contract | Verified status and release significance |
| --- | --- |
| Stable published version | **1.1.0** on PyPI; keep unchanged |
| Current development distribution source | **1.2.0rc2.dev0**, in `pyproject.toml`, `__version__`, `CITATION.cff` and readiness declarations |
| Last retained exact frozen qualification evidence | **1.2.0rc1** (`REFERENCE_VALIDATION.json`, `VALIDATION_TOLERANCES.json`, `PERFORMANCE_ENVELOPE.json`) |
| Literal 1.2 RC2 qualification | **NOT established**; do not relabel RC1 evidence or infer qualification from editable-source/green-docs tests |
| GitHub Release readiness | `github_release_ready=false` |
| Production release readiness | `production_release_ready=false` |
| TestPyPI readiness | Now explicitly declared `testpypi_publication_ready=false`; trusted publishing declaration also false |
| Stable root API boundary | `ONE_DOT_ZERO_API_STABILITY.json` freezes the 458-entry 1.0 root boundary; root compatibility tests exist |
| W1–W4 workflow candidates | Ten `run_*_workflow()` entry points are **module-scoped and unpublished** in stable 1.1.0 |
| Scientific coverage blocker | [#289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289) **OPEN**: frequentist nominal-90% simultaneous slope/family coverage is not generally calibrated |
| Missing-gaze observation blocker | [#296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296) **OPEN**: missingness-sensitive estimation and MNAR mechanisms are not generally identified or corrected |

## Existing workflow and compatibility coverage

- `tests.yml`: source checkout, editable `.[dev]` install, tests/coverage, compile and Ruff; **Ubuntu, Windows and macOS × Python 3.11, 3.12 and 3.13**. These tests protect code behavior but are *not* nine independent released-wheel installs.
- `release-readiness.yml`: wheel + sdist build, Twine check, isolated installed wheel and sdist smoke on **Python 3.12**, source version equality and release-hardening contracts. Passing is **necessary, not sufficient**.
- `workflow-product-qualification.yml`: module-level workflow contracts on Python 3.11–3.13, **installed wheel W1–W4 ten-route** product checks on 3.12. It runs when designated workflow/code paths change; not a fresh RC2 acceptance certificate.
- `one-dot-zero-api-stability.yml` and `scripts/freeze_one_dot_zero_api.py`: frozen root API signatures/schemas and exact export boundary. `WORKFLOW_API_AUDIT.json` requires 1.2 workflow candidates to stay module-scoped.
- `installed-rc-qualification.yml`: external installed **1.1.0rc1** PyPI reference; useful historical baseline but does not install 1.2 RC2.
- `release.yml`: manual dispatch defaults to `build-only`; production governance historically required GitHub readiness, exact protected main, an issue and required checks. Publication routes additionally have separate environment gates. Neither a green CI run nor this audit starts a release.

The source tree includes many independently audited draft W3 experiments that are **not merged**. A large research PR backlog must not be confused with an eligible source/API surface. Do not silently cherry-pick research estimators into a release.

## Audit fixes prepared, not merged

1. `scripts/verify_release_publication_gate.py` checks **every manually selected release target** before building. The non-publishing `build-only` path remains possible while disarmed. TestPyPI needs a separate explicitly reviewed publication flag plus trusted publisher declaration; production and resume-production require both independent production and GitHub readiness decisions, environment reviewer/trusted publishing and exact-main governance declarations.
2. `release.yml` runs that target-policy gate **before building any distribution**. No publishing can occur from this draft by itself; the unchanged readiness flags remain false.
3. `scripts/verify_release_governance.py` additionally requires `production_release_ready=true` and treats only **completed successful** mandatory checks as valid. Neutral, skipped, queued or failed checks no longer satisfy a release requirement.
4. `tests/test_release_publication_gate.py` and release-governance fixture updates explicitly regression-test every disarmed target, wrongly skipped/neutral mandatory CI statuses, missing approval flags and retained RC1 evidence.
5. `one-dot-two-release-qualification-audit.yml` attempts a **non-publishing Python 3.11–3.13 installed wheel and sdist matrix**, importing the stable 1.1.0 PyPI distribution as a separate root-API reference. It checks candidate wheel imports outside the source checkout, retained 1.1 public root exports, unchanged module-scoped ten workflow entry points, isolated wheel/sdist installation plus `pip check`, and installed-wheel ten-workflow product output. The workflow **does not publish or upload its wheel or source distribution**; only qualification JSON reports are retained.

These tests are *planned evidence* at PR creation. Record their GitHub Actions results, failures and platform-specific gaps as actually observed; do not mark them successful before jobs complete.

## Remaining scientific and production qualification gates

A future narrower 1.2 candidate is possible **only if the release scope deliberately excludes all unqualified W3/MNAR confidence-band or missing-gaze correction claims**, clearly keeps these research methods out of a supported public API, maintains stable 1.1 root compatibility and gets its own reviewed exact-version release qualification. A fresh literal RC, not current `1.2.0rc2.dev0`, needs matching source/version, qualification JSON and new wheel/sdist/install evidence; the source-level W3 negative results and preregistered refusals must remain available.

For any method advertising statistical 90% simultaneous confidence coverage, issue #289 requires an independently designed, predeclared, adequately sized *new-source* coverage assessment, including high leverage, independent units, covariance/marginal/reference interactions, negative cases and Monte Carlo uncertainty. For any correction of response-dependent lost gaze, #296 requires externally grounded observation/recovery assumptions; random audit assignment does not guarantee actual audit return, and identified-set evidence is not a calibrated interval. Neither issue may be claimed resolved by a website deployment.

No qualified **real GP3 human gaze dataset** or reproducibly licensed real-sensor observation/missingness validation was established by this GitHub inspection. The documented synthetic evidence is valid *as synthetic evidence* only.

## Exit criteria and decision

Before considering any further release PR: (a) finish new audit exact-head CI including installed artifacts; (b) resolve any actual failed contract without lowering thresholds; (c) review compatibility diffs; (d) document a narrow supported 1.2 release API or continue the hold; (e) qualify a fresh literal version; (f) have all exact-source CI and scientific declarations pass on protected main; and (g) require a **separate, expressly requested** governance-only release authorization. No merge, tag, TestPyPI or production PyPI action is included in this audit.
