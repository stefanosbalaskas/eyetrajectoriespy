# Proposed narrow eyetrajectoriespy 1.2 release surface — review only

**23 October 2026 · UNAPPROVED DRAFT · NO RELEASE AUTHORIZATION**

This is the next step after the complete source/build/installed-product release audit in [draft PR #467](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/467). PR #467 was verified **27/27 exact-head workflows successful**. Its new clean-install qualification run [#39939291565](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39939291565) passed on Python **3.11, 3.12 and 3.13**. Each environment built and smoke-tested a wheel and sdist, compared the installed source against **published stable 1.1.0**, and exercised all **ten** W1–W4 candidates installed from the development wheel. All ten reported zero release-blocking friction. PR #467 remains **DRAFT**, unmerged.

**Decision proposed, not accepted:** It may be technically feasible to release a narrower 1.2 containing the completed *transparent workflow orchestration* programme, but only as a separately reviewed literal release candidate after full exact-version qualification. Nothing here qualifies numerical coverage or an MNAR correction. Nothing has been published or promoted.

## Narrow scope: include only the existing audited orchestration contracts

The machine-readable [RELEASE_SCOPE_1_2_PROPOSAL.json](https://github.com/stefanosbalaskas/eyetrajectoriespy/blob/audit/one-dot-two-narrow-release-scope-proposal-20261023/RELEASE_SCOPE_1_2_PROPOSAL.json) lists the exact candidate module and ten names frozen in `WORKFLOW_API_AUDIT.json`: `eyetrajectoriespy.workflows`, with **no package-root promotion**.

| Proposed workflow entry point | Release-scope interpretation |
| --- | --- |
| `run_sparse_fpca_workflow` | Explicit native sparse-PACE workflow composition and reporting; no automatic missing-gaze correction |
| `run_sparse_mfpca_workflow` | Paired planar covariance/PACE composition under declared fitted-model assumptions |
| `run_sparse_mfpca_async_workflow` | Coordinate-native asynchronous x/y observations; no hidden synchronization or fabricated observations |
| `run_sparse_multilevel_workflow` | Participant/trial decomposition with explicit basis and diagnostic boundaries, not guaranteed small-cluster intervals |
| `run_sparse_prediction_workflow` | Partial-trajectory prediction with declared Gaussian and training/calibration conditions; not MNAR recovery |
| `run_fpca_workflow` | Fitted common-grid FPCA composition and provenance; no new inferential interval claim |
| `run_function_on_scalar_workflow` | **Observed-grid coefficient estimation only** under documented assumptions; its W3 wild-HC1 90% simultaneous coverage remains *unqualified* |
| `run_functional_mixed_effects_workflow` | Explicit Gaussian mixed-effects model composition; no promotion of unresolved fitted-covariance CR2/random-slope inferential calibration |
| `run_generalized_functional_workflow` | Declared outcome family, offsets/exposure and model assumptions; no automatic family or inferential-guarantee selection |
| `run_recurrence_workflow` | Explicit embedding/radius and RQA choices; descriptive diagnostics, not missing data inference |

The proposal is **about packaging and product scope**, not declaring these ten statistical methods individually validated for every design. The surrounding previously supported stable 1.1 functionality remains installed. We must not silently remove or rewrite any stable 1.1 functionality just because a research example found inferential limitations. Instead document exactly which newer guarantees are **not** offered.

## Stability and scientific interpretation barriers

- The historical 1.0 package-root compatibility freeze is **458 names**, consisting of **455 stable and three explicitly experimental** exports. Preserving all 458 names does not make the three experimental names stable. Maintain original signatures/result schemas and 1.1 module-scoped additions.
- The 1.2 workflow audit requires ten candidate routes, stable contract identifiers, no root API promotion and typed provenance. New workflow orchestration must not automatically interpolate, delete incomplete units, alter bandwidths or choose models without analyst consent.
- Issue [#289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289) remains **OPEN**. Simulated W3 nominal-90% whole-grid simultaneous intervals substantially undercover under some leveraging/marginal/covariance designs. Independent replay of failed coverage does not make them calibrated. The narrow 1.2 candidate must avoid **any new general 90% simultaneous confidence-band promise** or unconditional fitted-CR2 guarantee.
- Issue [#296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296) remains **OPEN**. R82–R95 randomized audit, selective return, observational-equivalence and sharp-set results prove limits of identification under assumed experimental laws, not actual return of unobserved eye-tracking data. No **MNAR identification or automatic missing-gaze reconstruction** promise may be promoted.
- The R1–R95 original and independent research draft PRs are valuable archives. They are **not** implicitly included as supported experimental estimators in this narrower product.
- A real-sensor GP3 independent qualification corpus, external validation of missingness and a 90% functional-inference release standard remain scientifically unresolved. They should be treated as explicit future research, not hidden gates accidentally judged green by ordinary CI.

## Why current green tests do not justify a release

| Verification layer | Evidence or missing gate |
| --- | --- |
| Protected main packaging and current development compatibility | Verified CI; stable 1.1 remains public |
| 1.2 candidate installed wheel/sdist, Python 3.11–3.13 | [PR #467](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/467), fully green dedicated qualification and artifacts |
| Exact binary/source published identity | **Not met:** current source is `1.2.0rc2.dev0` |
| Last frozen full scientific/performance qualification identity | `1.2.0rc1`, not source-identical `1.2.0rc2.dev0` |
| Approved 1.2 release surface and new claims | **Not met:** this document is an unapproved proposal |
| Full literal candidate source/install/performance evidence | **Not met:** must be generated fresh and attributed to precisely that candidate |
| Release/publication approval | **Disarmed** in `RELEASE_READINESS.json`; no TestPyPI/production dispatch |

## Recommended exit sequence

1. Review the ten route-level interpretation boundaries and explicit omissions; do **not** merge this or PR #467 just to trigger a release.
2. Decide whether the release is allowed to ship these already-tested orchestration routes **without a new statistical guarantee**, while retaining clearly labeled existing 1.1 APIs and experimental status.
3. Only after explicit scope approval, independently prepare the literal 1.2 release candidate on a separate change: synchronize `pyproject.toml`, `__version__`, `CITATION.cff`, readiness declarations, docs and machine-readable workflow version. **Do not reuse RC1 frozen performance figures as RC2 evidence.**
4. Rebuild and retest exact-version candidate distributions across supported Python versions and target operating systems; test real installed artifacts, not editable-only imports. Run exact-source scientific/product/performance gates with an immutable evidence snapshot.
5. Require complete protected-main checks and then a **separately approved governance-only publication decision**. A green draft PR does not confer authorization.
6. If release scope cannot be separated scientifically and technically, maintain 1.2 HOLD, archive failure cases and continue focused methods research instead.

## Reproducibility of this *review-only* proposal

`scripts/validate_one_dot_two_release_scope.py` compares the proposed manifest against `WORKFLOW_API_AUDIT.json`, the frozen 1.0 root export counts and `RELEASE_READINESS.json`. It fails closed on missing workflow contracts, removed hold claims, closed/missing scientific blocker declarations, promotion to package root, publication arming, unsupported version changes or fabricating already-verified qualification evidence. `tests/test_one_dot_two_release_scope.py` mutates each prohibition as a negative test; a new dedicated nonpublishing Python 3.11–3.13 CI workflow runs those tests. This is only a declaration consistency test: **it does not independently certify real gaze data, inferential calibration, or GitHub issue state**.

**Status: DRAFT ONLY. No protected-main merge, no tag, no GitHub Release, no TestPyPI/PyPI publication, no W3 inferential guarantee.**
