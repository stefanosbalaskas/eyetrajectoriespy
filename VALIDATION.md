# Validation status

This file records qualification evidence separately from implementation status. A missing hosted check is never treated as a code pass or code failure.

## Current development target

- Package line: `0.21.0.dev0`
- Scientific scope: continuous functional gaze trajectories, FPCA/MFPCA, native and genuinely sparse irregular trajectories, optional FDApy/PACE interoperability, simultaneous observed-grid functional mean inference, stability, leakage-aware reconstruction and outcome-tuned predictive component selection, descriptive and simultaneous FPC-shape uncertainty, FPCA spectrum uncertainty, FPC score basis-resampling uncertainty, Gaussian FPCR paired-bootstrap uncertainty, observed-grid simultaneous Gaussian FPCR slope bands, Gaussian FPCR future-outcome prediction intervals, heteroscedastic Gaussian FPCR fixed-target wild-bootstrap inference, stabilized-volatility wild-bootstrap truncation selection, familywise simultaneous fixed-target wild-bootstrap calibration, fixed-family wild-bootstrap hypothesis testing with single-step maxT adjustment and a global family test, finite-bootstrap Monte Carlo precision diagnostics for retained resampling tail probabilities, split-conformal FPCA anomaly review, eigengap/principal-angle subspace stability, phase/registration, compositional FPCA, and functional anomaly/influence diagnostics.
- Tests, branch protections, coverage thresholds, and scientific validation rules have not been weakened or bypassed.

## Locally validated — 2026-09-19

Environment: Linux, Python 3.13.5.

- Full available core test suite: **75 passed, 4 skipped, 0 failed**.
- Skips: four runtime tests requiring the optional `scikit-fda` dependency, which is not installed in the local runner.
- Coverage: **92.88%**, above the configured **90%** gate.
- `python -m compileall -q src tests`: passed.
- Wheel build using `pip wheel . --no-deps --no-build-isolation`: passed.
- Built wheel: `eyetrajectoriespy-0.3.0.dev0-py3-none-any.whl`.
- Installed-wheel smoke test: package import, version check, synthetic trajectory generation, and MFPCA fit passed.
- Core executable examples: **11/11 passed**.
- MkDocs navigation source check: all **42/42** configured Markdown pages exist.
- API documentation source check: all **74/74** documented public symbols resolve in the package.
- A locally discovered basis-validation ordering defect was repaired: invalid basis specifications are now rejected before optional-backend import.

## 0.4 delta validation — 2026-09-19

Environment: Linux, Python 3.13.5.

Because the local runner cannot clone GitHub or install missing dependencies from the network, the 0.4 changes were qualified in a reconstructed affected-source worktree against the previously qualified 0.3 contracts.

- New 0.4 + directly affected FPCA/stability/type regression tests: **27 passed, 0 failed**.
- Coverage on the reconstructed affected source surface: **95.74%**, above the unchanged configured **90%** gate.
- Existing FPCA transform/reconstruction, component matching, curve/participant bootstrap stability, and type/validation regression contracts passed unchanged.
- Participant-grouped reconstruction CV audit confirmed that every participant is assigned to exactly one held-out fold.
- Missing participant IDs are rejected before participant-level bootstrap resampling.
- `python -m compileall -q src tests examples`: passed on the reconstructed affected-source worktree.
- New executable example `examples/fpca_selection_uncertainty.py`: passed.
- 0.4 wheel build with `pip wheel . --no-deps --no-build-isolation`: passed in the reconstructed worktree.
- Built wheel: `eyetrajectoriespy-0.4.0.dev0-py3-none-any.whl`.
- Installed-wheel smoke: version, grouped reconstruction CV, explicit selection, and matched-bootstrap envelopes passed.
- Methodological source checks completed for FPCA eigenfunction uncertainty and component-number selection; the public API deliberately describes bootstrap envelopes as descriptive rather than calibrated confidence bands.

The full 0.3 repository baseline remains separately established above at **75 passed, 4 optional-backend skips, 92.88% coverage**. The exact integrated 0.4 branch still requires hosted/full-repository requalification when Actions or a full clone becomes available.

## Repository source integrity — 2026-09-19

These are static branch checks, not hosted CI certification.

- MkDocs navigation targets: **45/45** configured Markdown pages exist.
- API documentation declarations: **84/84** documented public symbols are present in the package export surface.
- The core examples workflow includes the new `fpca_selection_uncertainty.py` executable example.

## 0.5 delta validation — 2026-09-19

Environment: Linux, Python 3.13.5.

The local runner still cannot resolve GitHub directly, so a full branch clone is unavailable. The 0.5 scientific algorithms were therefore qualified with a standalone numerical truth/contract harness using the same weighted-FPCA geometry as the package, while repository integration was checked against the authoritative GitHub branch.

- Exact 45-degree FPC1/FPC2 rotation truth: **passed**. Individual FPC1 principal cosine was approximately 0.707 while the two-dimensional subspace principal cosines were approximately 1 and normalized projector distance was approximately 0.
- Explicit eigengap-threshold semantics: **passed**. No near-tie classification is produced without a supplied threshold; a supplied 0.05 threshold correctly flags a synthetic relative gap of 0.025.
- Participant-level bootstrap reproducibility: **passed** with deterministic random seed; normalized projector distances remained within [0, 1].
- Failure-contract checks: **passed** for invalid thresholds, invalid component blocks, boolean component arguments, and non-zero-rank boundary protection.
- Mathematical implementation check confirmed that the normalized projector distance is rotation invariant within the selected subspace.
- Methodological source verification completed for eigenvalue-spacing sensitivity and principal-angle subspace comparison.

This is **delta algorithmic validation**, not a replacement for the full repository test suite or cross-platform qualification.

## 0.5 repository source integrity — 2026-09-19

These are static branch checks, not hosted CI certification.

- Existing 0.4 MkDocs navigation baseline: **45/45** pages previously verified; the two newly configured 0.5 pages were created on the branch, giving **47 configured pages with no intentional removals**.
- API documentation declarations: **93/93** documented public symbols are present in the package export surface.
- Version metadata: package `__version__` and `pyproject.toml` both report **0.5.0.dev0**; `CITATION.cff` software version is **0.5.0.dev0** with release date 2026-09-20.
- The examples workflow includes `examples/fpca_subspace_stability.py`.
- Public API regression test includes the new subspace result objects and functions.

## 0.6 delta validation — 2026-09-20

Environment: Linux, Python 3.13.5.

The local runner cannot clone GitHub directly and does not have FDApy installed. The exact sparse/PACE affected source and tests were therefore reconstructed from the development branch and executed locally with a faithful fake FDApy API. This validates the adapter contract without claiming real-backend numerical certification.

- Backend-independent sparse/PACE contract suite: **7 passed, 0 failed**.
- Coverage on the reconstructed changed surface: **99%**, above the repository's unchanged **90%** threshold.
- `python -m compileall -q src tests`: passed for the reconstructed affected surface.
- Native curve-specific times were preserved during FDApy conversion; no common-grid interpolation was introduced.
- Explicit FDApy fitting contract passed: covariance UFPCA, PACE score recovery, fitting smoothing, score smoothing, tolerance, normalization, evaluation grid, mean-smoothing kwargs, and covariance kwargs were forwarded as specified.
- Explicit evaluation grids were represented as FDApy `DenseArgvals`; decreasing/non-finite/undersized grids were rejected before backend fitting.
- Original curve IDs, metadata, coordinate/time semantics, sample counts, smoothing settings, and interpolation status were preserved in the sparse result/provenance contract.
- Metadata-preserving `SFPC*` score-frame construction, sparse sampling summary, native sparse plotting, and manuscript reporting helper passed.
- Invalid component counts, tolerance, normalization type, smoothing settings, and non-mapping smoothing kwargs were rejected before optional backend estimation.
- Non-finite selected-dimension observations were rejected as representation errors rather than silently dropped or interpolated.
- Unexpected backend score shapes and non-finite eigenvalues triggered explicit runtime failures.
- Missing FDApy raised the documented optional-`sparse` installation message.
- FDApy is **not installed locally**; real FDApy numerical fitting and the executable sparse example therefore remain pending.

Methodological/backend verification against FDApy 1.0.3 documentation confirmed:
- `UFPCA.fit(data, points, method_smoothing, kwargs_mean, kwargs_covariance)` for covariance-operator estimation;
- `UFPCA.transform(..., method="PACE", method_smoothing=..., tol=...)` for sparse conditional-expectation scores;
- FDApy's sparse UFPCA example explicitly uses covariance UFPCA followed by PACE scores;
- FDApy sparse MFPCA documentation uses numerical-integration/inner-product scores rather than a documented multivariate PACE score transform, so eyetrajectoriespy intentionally exposes only **univariate sparse PACE** at present.

### Optional-backend compatibility boundary

The eyetrajectoriespy core remains Python **3.11–3.13**. FDApy 1.0.3 depends on NumPy **<2.0**, while NumPy 1.26.x supports Python only through **3.12**. Therefore the packaged FDApy `sparse` extra and dedicated hosted sparse workflow currently target Python **3.11–3.12**. This restriction applies only to optional FDApy interoperability.

## 0.6 repository source integrity — 2026-09-20

These are static branch checks, not hosted CI certification.

- Public API documentation declarations: **100/100** documented symbols are present in the package export surface.
- MkDocs navigation targets: **48/48** configured Markdown pages exist on the branch, including the sparse PACE guide and worked example.
- Package `__version__`, `pyproject.toml`, and `CITATION.cff` all report **0.6.0.dev0**.
- `pyproject.toml` exposes an optional FDApy sparse extra constrained to Python <3.13; the `all` extra carries the same compatibility marker.
- Dedicated `optional-sparse-fda` workflow targets Ubuntu with Python **3.11 and 3.12**.
- Dependency-marker evaluation was checked locally: the FDApy extra marker evaluates **true on Python 3.12** and **false on Python 3.13**, matching the documented backend boundary.
- That workflow runs backend-independent sparse contracts, the real FDApy integration smoke, and `examples/sparse_pace_fpca.py`.
- The standard public-API regression test includes the sparse result object and public functions.

### Real FDApy CI defect and repair — 2026-09-20

The first real FDApy 1.0.3 integration run executed on both Python 3.11 and 3.12. Backend-independent sparse contracts passed on both versions, but the real PACE smoke failed because an arbitrary 61-point `evaluation_grid` produced eigenfunctions/covariance on 61 points while FDApy's irregular PACE transform internally interpolated observations to the pooled 31-point observed grid.

The backend source confirms that FDApy 1.0.x irregular PACE calls `data.smooth(method="interpolation")` and then uses the fitted covariance/eigenfunctions directly. The adapter was therefore hardened to reject arbitrary PACE evaluation grids. An explicit grid must now equal `np.unique(np.concatenate(trajectories.time))`, or users should leave `evaluation_grid=None`.

This is a backend-compatibility guard rather than silent interpolation. The original sparse observations remain on their native grids.

### scikit-fda compatibility repair — 2026-09-20

A hosted optional-scikit-fda run failed before eyetrajectoriespy backend logic executed. The environment resolved scikit-fda 0.10.1 together with multimethod 2.1; imports then failed inside scikit-fda with a Python 3.12 metaclass conflict.

scikit-fda 0.10.1 declares multimethod >=1.5 while excluding 1.11/1.11.1 but does not cap the major version. The eyetrajectoriespy optional `fda` extra is therefore constrained to the compatible scikit-fda 0.10.x line plus `multimethod>=1.12,<2`. This preserves the interoperability tests rather than skipping them and does not alter core package dependencies.

### 0.6 finalization re-check — 2026-09-20

Additional local/static checks after the sparse-contract hardening:

- Exact current `src/eyetrajectoriespy/sparse.py` and the focused sparse contract suite were reconstructed locally and compiled successfully.
- Exact current backend-independent sparse contract suite: **7 passed, 0 failed**, with **99%** coverage on the reconstructed changed surface.
- Focused current-source sparse harness: **passed** for covariance UFPCA/PACE argument forwarding, score/provenance construction, and metadata-preserving score frames.
- Centered-rank guard: **passed**; with three curves, requesting three or more components is rejected because non-zero empirical rank is at most `n_curves - 1 = 2`.
- A test-ordering defect was found and corrected: tests targeting normalization/smoothing/kwargs/evaluation-grid validation now explicitly request `n_components=2` so they reach the intended contract rather than stopping at the earlier centered-rank guard.
- Evaluation-domain guard: **passed**; explicit FDApy evaluation grids extending below/above pooled observed support are rejected before backend fitting.
- Non-finite selected-dimension observations remain representation errors rather than implicit deletion/interpolation.
- FDApy optional dependency is bounded to the validated `>=1.0.3,<1.1` API family and remains gated to Python <3.13.
- Dependency marker evaluation locally: Python 3.11 = enabled, Python 3.12 = enabled, Python 3.13 = disabled.
- Dedicated `optional-sparse-fda` workflow YAML parsed successfully locally; its matrix is Python 3.11/3.12 and preserves the normal test/installation path rather than bypassing any gate.
- MkDocs navigation source audit: **48/48** configured Markdown targets exist.
- API source audit: **100/100** documented public symbols are exported.
- Package `__version__`, `pyproject.toml`, and `CITATION.cff` all report **0.6.0.dev0**.
- Sparse-reference formatting/backend summary re-checked after documentation cleanup.

## 0.7 delta validation — 2026-09-21

Environment: Linux, Python 3.13.5.

The local runner still cannot resolve GitHub directly, so a full branch clone is unavailable. The 0.7 statistical core was therefore executed in a reconstructed contract harness matching the committed Gaussian-multiplier algorithm, while repository integration was audited against the authoritative GitHub branch.

- Reconstructed functional mean-band contract harness: **passed**.
- Deterministic Gaussian multiplier calibration under fixed seed: **passed**.
- 99% confidence calibration was no narrower than 90% calibration using identical multiplier draws: **passed**.
- Unequal repeated-trial truth case: participant A with 3 trials and participant B with 1 trial produced the explicit equal-weight participant-average mean, distinct from the curve-weighted grand mean: **passed**.
- Zero empirical variance at an individual grid coordinate produced exactly zero standard error and zero band width without epsilon perturbation: **passed**.
- Fully constant functional observations produced critical value 0 and an exact zero-width band: **passed**.
- Failure contracts passed for invalid confidence levels, multiplier counts, inference units, participant-column misuse, missing participant IDs, non-finite trajectory values, and direct probability-simplex inference.
- Local syntax compilation of the reconstructed contract harness: **passed**.
- Methodological verification completed against the simultaneous functional-mean confidence-band literature; the public API deliberately targets the observed time-by-dimension grid and does not claim continuous-domain coverage between sampled points.

This is **delta algorithmic validation**, not a replacement for the full repository test suite or cross-platform qualification.

## 0.7 repository source integrity — 2026-09-21

These are static branch checks, not hosted CI certification.

- Package `__version__`, `pyproject.toml`, and `CITATION.cff` all report **0.7.0.dev0**.
- Public API documentation declarations: **105/105** documented symbols are present in the package export surface.
- MkDocs navigation contains **50** configured Markdown pages. The two new 0.7 pages were created on the branch; no documentation page was intentionally removed.
- The examples workflow includes `examples/functional_mean_bands.py`.
- The public API regression test includes `FunctionalMeanBandResult` and all new mean-band public functions.
- The 0.7 site includes a dedicated methodology guide, worked example, reporting/preregistration guidance, assumptions, limitations, FAQ, references, API/object documentation, decision map, quickstart, roadmap, homepage, and README integration.

## 0.8 pre-commit local algorithm validation — 2026-09-21

Environment: Linux, Python 3.13.5.

Before the predictive implementation was committed to GitHub, a standalone contract harness matching the intended fold-local weighted-FPCA/regression algorithm was executed locally.

- Predictive FPCA regression harness: **6 passed, 0 failed**.
- Affected-code coverage: **99%**.
- `python -m compileall` on the harness and tests: **passed**.
- Gaussian RMSE and MAE selection paths: **passed**.
- Binomial log-loss and Brier probability-scoring paths: **passed** with a non-separable Bernoulli truth fixture.
- Participant-grouped fold audit: each participant appeared in exactly one test fold: **passed**.
- Nested grouped CV determinism under fixed seed: **passed**.
- Numeric covariate path and rank-deficient-design rejection: **passed**.
- One-class binomial training-fold rejection: **passed**.
- A deliberately perfectly separable preliminary binomial fixture triggered the intended explicit separation failure; the ordinary binomial truth test was then changed to a probabilistic non-separable fixture rather than weakening the separation guard.

This is pre-commit delta algorithmic evidence. Exact integrated package/cross-platform certification is provided by the PR-head workflows when they run successfully.

## 0.9 pre-commit local algorithm validation — 2026-09-21

Environment: Linux, Python 3.13.5.

The execution environment could not resolve github.com, so a fresh full-repository clone was unavailable. Before the branch commit, the new simultaneous-FPC algorithm was exercised in a standalone numerical contract harness matching the committed weighted-FPCA, component-matching, sign-alignment, eigengap-screening, and studentized-maximum logic.

- deterministic repeated runs under a fixed seed: **passed**;
- lower/reference/upper ordering: **passed**;
- 99% bands no narrower than 90% bands under identical bootstrap draws: **passed**;
- familywise critical value at least as conservative as component-wise critical values: **passed**;
- matched absolute similarities remained within [0, 1]: **passed**;
- exact synthetic near-tie fixture triggered the explicit error contract: **passed**;
- near-tie warning path: **passed**;
- invalid bootstrap count, simultaneous scope, confidence level, relative-gap threshold, and near-tie action: **passed**;
- total standalone truth/contract checks: **10 passed**;
- syntax compilation of the intended new package module, focused tests, and executable example: **passed**.

This is local delta algorithmic validation, not a substitute for the repository-wide cross-platform test/coverage/docs/optional-backend workflows. Those remain GitHub CI evidence only after they actually complete.

## 0.10 pre-commit local algorithm validation — 2026-09-21

Environment: Linux, Python 3.13.5.

Before publishing the 0.10 branch, a standalone numerical harness matching the intended PCA/bootstrap/matching/studentized-calibration logic was executed locally.

- fixed-seed bootstrap determinism: **passed**;
- reference estimates fell inside symmetric calibrated intervals: **passed**;
- 99% intervals were no narrower than 90% intervals under identical bootstrap draws: **passed**;
- familywise critical values were no smaller than component-wise critical values for eigenvalues, explained-variance ratios, and cumulative variance: **passed**;
- matched absolute component similarities remained in [0, 1]: **passed**;
- cumulative explained variance retained monotone descending-rank semantics even when matched individual FPC order differed: **passed**;
- intended new spectrum module syntax compilation: **passed**.

This is local delta algorithmic validation. The environment still cannot provide a fresh full-repository clone, so cross-platform package/test/docs/optional-backend certification remains GitHub CI evidence only.

### 0.9 tip-of-main close-out — 2026-09-21

The status-ledger-only main tip `105ca4bea224319e6fc63286d1be7e8e47663d74` completed its final redundant push generation successfully after the 0.9 merge:

- tests workflow #45: **success**, including package build and all 9 Windows/Ubuntu/macOS × Python 3.11–3.13 lanes;
- examples workflow #45: **success**;
- docs workflow #45: **success**, including successful GitHub Pages deployment;
- optional-fda workflow #41: **success**;
- optional-sparse-fda workflow #29: **success**.

Thus the repository entered the 0.10 branch from a fully green current main tip.

## 0.11 pre-commit local algorithm validation — 2026-09-21

Environment: Linux, Python 3.13.5.

Before publishing the score-uncertainty branch, a standalone weighted-PCA/bootstrap harness matching the intended projection, component-matching, and sign-alignment logic was executed locally.

- fixed-seed bootstrap target projections: **deterministic**;
- lower ≤ median ≤ upper percentile envelopes: **passed**;
- bootstrap score standard deviations nonnegative: **passed**;
- component-matching similarities stayed in [0, 1]: **passed**;
- expected bootstrap tensor shape for external fixed targets: **passed**;
- sign-aligned bootstrap target scores retained positive median correlation with the full-sample reference coordinates: **passed**.

The committed implementation additionally rejects empty target sets, incompatible target time grids, dimension labels/order, coordinate systems, time units, invalid bootstrap/component counts, missing participant-bootstrap identifiers, and non-finite aligned bootstrap scores.

This is local delta algorithmic validation, not a substitute for repository-wide cross-platform qualification. The local environment still cannot provide a fresh GitHub clone, so full pytest/coverage/Ruff/package/docs/optional-backend evidence remains hosted CI evidence only.

## 0.12 pre-commit local algorithm validation — 2026-09-21

Environment: Linux, Python 3.13.5.

Before publishing the Gaussian FPCR bootstrap branch, a standalone weighted-PCA/regression harness matching the intended score geometry, slope back-transformation, paired resampling, and fixed-target prediction logic was executed locally.

- dimension-SD slope back-transformation reproduced the score-regression conditional mean to machine precision (maximum absolute discrepancy approximately 1.4e-15): **passed**;
- paired curve bootstrap refitted PCA and Gaussian regression in every replicate: **passed**;
- functional-slope bootstrap tensor shape and fixed-target prediction matrix shape: **passed**;
- lower ≤ median ≤ upper percentile summaries for slope and mean predictions: **passed**;
- bootstrap slope and prediction standard deviations were nonnegative: **passed**;
- full-rank regression-design checks were exercised in the harness: **passed**.

This is local delta algorithmic validation. It does not replace full repository pytest/coverage/Ruff/package/docs/optional-backend qualification, which remains GitHub CI evidence only.

## 0.13 pre-commit local algorithm validation — 2026-09-21

Environment: Linux, Python 3.13.

A standalone calibration harness matching the 0.13 studentized maximum-deviation logic was executed locally using synthetic paired-bootstrap slope arrays.

- global critical values were no smaller than corresponding dimension-wise critical values under identical bootstrap slopes: **passed**;
- global bands were no narrower than dimension-wise bands: **passed**;
- 99% global bands were no narrower than 80% global bands under identical bootstrap slopes: **passed**;
- exact identical bootstrap slopes yielded exact zero deviation SE after reference-centering: **passed**;
- a zero-SE but non-zero-discrepancy cell triggered the intended degenerate condition: **passed**;
- the initial direct-standard-deviation formulation exposed numerical pseudo-variance for repeated identical nonzero slopes; the implementation was corrected to estimate SE from bootstrap deviations from the reference rather than loosening the zero-variance threshold.

This is local delta algorithmic validation. Full repository pytest/coverage/Ruff/package/docs/optional-backend qualification remains GitHub CI evidence.

## 0.14 pre-commit local algorithm validation — 2026-09-21

Environment: Linux, Python 3.13.

A standalone predictive-resampling harness matching the 0.14 centered empirical residual construction was executed locally.

- centered residual pool had numerical mean zero: **passed**;
- identical residual seed reproduced identical predictive draws: **passed**;
- every predictive draw equaled the stored bootstrap conditional mean plus its sampled residual: **passed**;
- lower ≤ median ≤ upper predictive quantiles: **passed**;
- 99% intervals were no narrower than 80% intervals under identical predictive draws: **passed**;
- residual variation was retained when the synthetic response contained non-zero noise: **passed**.

This is local delta algorithmic validation only. Full repository pytest/coverage/Ruff/package/docs/optional-backend qualification remains GitHub CI evidence.

## 0.15 pre-commit local algorithm validation — 2026-09-21

Environment: Linux, Python 3.13.

A standalone synthetic harness matching the 0.15 FPCA split-conformal contracts was executed locally.

- exact marginal p-value formula `(1 + # calibration >= target)/(n_calibration + 1)`: **passed**;
- p-values lay exactly on the finite calibration grid: **passed**;
- an injected high-frequency shape anomaly received the minimum attainable reconstruction-based p-value: **passed**;
- an extreme target generated inside the retained FPC span received the minimum attainable empirical-Mahalanobis p-value: **passed**;
- conservative greater-than-or-equal tie handling was verified exactly: **passed**;
- p-values remained within `[1/(n_calibration+1), 1]`: **passed**.

This is local delta algorithmic validation only. Full repository pytest/coverage/Ruff/package/docs/optional-backend qualification remains GitHub CI evidence.

## 0.16 pre-commit local algorithm validation — 2026-09-22

Environment: Linux, Python 3.13.

A standalone score-space harness matching the intended fixed-regressor wild-bootstrap regression, heteroscedastic sandwich scaling, bootstrap-level studentization, and target-root calibration was executed locally.

- deterministic normal-multiplier studentized roots under a fixed seed: **passed**;
- deterministic bootstrap-level heteroscedastic SEs under a fixed seed: **passed**;
- reference projections lay within their symmetrized studentized intervals: **passed**;
- 99% intervals were no narrower than 80% intervals under identical bootstrap roots: **passed**;
- Mammen two-point multipliers produced finite studentized roots: **passed**;
- the implemented Mammen support/probabilities have exact theoretical moments E(W)=0, Var(W)=1, and E(W^3)=1: **passed**;
- k=g pseudo-truth and h>=g truncation semantics were exercised explicitly: **passed**.

This is local delta algorithmic validation only. It is not a substitute for full repository pytest/coverage/Ruff/package/docs/optional-backend qualification.

## Locally unavailable checks

These are **pending**, not passed:

- Ruff: local runner does not have `ruff` installed and has no network access.
- Strict MkDocs build: `mkdocs`/Material/mkdocstrings are not installed locally and cannot be installed without network access.
- Twine validation: `twine` is not installed locally.
- Optional `scikit-fda` runtime tests and examples: dependency is not installed locally.
- Real FDApy sparse/PACE integration tests and sparse example: FDApy is not installed locally; these require Python 3.11 or 3.12 under the current backend dependency line.
- Python 3.11 and 3.12 local tests: only Python 3.13.5 is available in the runner.

## GitHub CI certification

The 0.1 merged release tranche was previously GitHub CI-certified.

### 0.6 PR-head certification — 2026-09-20

Exact certified PR head:

`1c7d04bb97afb1c3f6f95d4b62bc1dfd495b69f8`

All required pull-request workflows completed successfully on that exact SHA:

- package build / distribution validation: **success**;
- Windows × Python 3.11, 3.12, 3.13: **3/3 success**;
- Ubuntu × Python 3.11, 3.12, 3.13: **3/3 success**;
- macOS × Python 3.11, 3.12, 3.13: **3/3 success**;
- full pytest/coverage/compile/Ruff gate embedded in the standard workflow: **success**;
- core executable examples: **success**;
- strict MkDocs documentation build: **success**;
- optional scikit-fda basis/outlier interoperability: **success**;
- optional FDApy sparse/PACE interoperability on Python 3.11 and 3.12, including real-backend smoke and sparse example: **2/2 success**.

Two real CI defects were discovered and repaired before certification:

1. FDApy 1.0.x irregular PACE requires the fitted functional grid to match the sorted pooled observed sample-time grid. Arbitrary evaluation grids are now rejected before fitting.
2. scikit-fda 0.10.1 resolved to multimethod 2.1, which caused a Python 3.12 metaclass conflict. The optional fda extra is now constrained to scikit-fda 0.10.x with `multimethod>=1.12,<2`. No interoperability tests were skipped.

PR #8 was squash-merged as:

`5807d92eeb9c87ab6926c4081659789131f6b6bd`

The certified PR head and the squash-merged main commit have the **same Git tree object**, so the merged code/content tree is byte-for-byte the CI-certified PR tree. The commit SHA differs because of squash history.

### Exact merged-main SHA and deployment status

No push-triggered Actions runs attached to `5807d92eeb9c87ab6926c4081659789131f6b6bd` through the GitHub-app merge path.

Therefore:

- the **0.6 code/content tree is GitHub CI-certified** via exact PR head `1c7d04b...`;
- the **exact merged-main commit SHA has not separately rerun the matrix**;
- GitHub Pages deployment from the merged-main SHA is **pending / not certified**;
- do not claim successful 0.6 Pages deployment until the main-branch docs workflow actually executes its deploy job successfully.

### 0.7 PR-head certification — 2026-09-21

Exact certified PR head:

`a2f5162cc50a775a71d1a85fb019b38d801e49a0`

All pull-request qualification workflows completed successfully on that exact SHA:

- package build / distribution validation: **success**;
- Windows × Python 3.11, 3.12, 3.13: **3/3 success**;
- Ubuntu × Python 3.11, 3.12, 3.13: **3/3 success**;
- macOS × Python 3.11, 3.12, 3.13: **3/3 success**;
- full pytest/coverage/compile/Ruff gate embedded in the standard workflow: **success**;
- core executable examples, including `functional_mean_bands.py`: **success**;
- strict MkDocs documentation build: **success**;
- optional scikit-fda interoperability: **success**;
- optional FDApy sparse/PACE interoperability on Python 3.11 and 3.12: **2/2 success**.

No tests, coverage thresholds, branch protections, or scientific validation checks were weakened or bypassed.

PR #10 was squash-merged as:

`3ec7aa66849fe4f166260af93d3712c277e6d122`

The 0.7 functional-mean inference implementation is therefore **GitHub CI-certified at the exact PR head**. The squash-merged main lineage carries the same reviewed 0.7 changes, while main-branch push/deployment checks are tracked separately below.

### 0.7 merged-main deployment status — completed

The subsequent status-only main commit

`ad8f11e1851a0b5f75a1fe0c13f66471b7d452d9`

triggered a complete push-generation on the 0.7 main lineage. All five workflows completed successfully:

- tests: **success**;
- examples: **success**;
- strict docs build: **success**;
- optional scikit-fda interoperability: **success**;
- optional FDApy sparse/PACE interoperability: **success**.

The docs workflow also completed its **GitHub Pages deploy job successfully**. Therefore the former 0.7 main/deployment re-check is closed.

### 0.8 PR-head certification — 2026-09-21

Exact certified PR head:

`095917823eb8c4a52ecdb0d98610dacb741c94f8`

PR #11, **“Add outcome-tuned predictive FPCA component selection,”** completed all unchanged qualification workflows successfully on that exact SHA:

- package build / distribution validation: **success**;
- Windows × Python 3.11, 3.12, 3.13: **3/3 success**;
- Ubuntu × Python 3.11, 3.12, 3.13: **3/3 success**;
- macOS × Python 3.11, 3.12, 3.13: **3/3 success**;
- full pytest/coverage/compile/Ruff gate embedded in the standard workflow: **success**;
- core executable examples, including `predictive_fpca_selection.py`: **success**;
- strict MkDocs documentation build: **success**;
- optional scikit-fda interoperability: **success**;
- optional FDApy sparse/PACE interoperability on Python 3.11 and 3.12: **2/2 success**.

No tests, coverage thresholds, workflows, branch protections, or scientific validation checks were weakened, deleted, disabled, or bypassed.

PR #11 was squash-merged as:

`c997c4c9e72eb1390056ff79f36fd0d8b2103b2f`

The certified PR head and squash-merged main commit both point to Git tree:

`b5c22b251c6f198d0cb3d29f468a166e1a8cfaae`

so the merged scientific/code/documentation tree is byte-for-byte identical to the exact CI-certified PR-head tree.

### 0.8 exact-main qualification and deployment — 2026-09-21

The exact merged-main commit

`c997c4c9e72eb1390056ff79f36fd0d8b2103b2f`

also completed a fresh push-triggered qualification generation successfully:

- tests workflow #41: **success**, including package build and all 9 Windows/Ubuntu/macOS × Python 3.11–3.13 lanes;
- examples workflow #41: **success**;
- docs workflow #41: **success**, including strict build and **successful GitHub Pages deployment**;
- optional-fda workflow #37: **success**;
- optional-sparse-fda workflow #25: **success**, including FDApy Python 3.11 and 3.12 lanes.

Therefore the 0.8 predictive FPCA selection tranche is both **PR-head CI-certified** and **exact-main requalified**, and the corresponding documentation site deployment is certified on the merged 0.8 main lineage.

## Remaining re-checks

The current optional-backend boundary remains:

1. Reassess FDApy/Python 3.13 interoperability only when the FDApy/NumPy dependency line supports Python 3.13. This is not part of the current FDApy support contract.

Cross-platform package behavior, package construction, coverage/compile/Ruff gates, core examples, strict documentation, GitHub Pages deployment, scikit-fda interoperability, FDApy sparse/PACE interoperability on Python 3.11–3.12, and the 0.8 predictive FPCA regression-selection implementation are now GitHub CI-certified on the exact merged 0.8 main lineage.


### 0.9 PR-head certification — 2026-09-21

Exact certified PR head:

`c5b9893ae19d69de0268f7f8b6c3e853c29e1390`

PR #12, **“Add simultaneous FPC-shape uncertainty bands,”** completed all unchanged pull-request qualification workflows successfully on that exact SHA:

- package build / distribution validation: **success**;
- Windows × Python 3.11, 3.12, 3.13: **3/3 success**;
- Ubuntu × Python 3.11, 3.12, 3.13: **3/3 success**;
- macOS × Python 3.11, 3.12, 3.13: **3/3 success**;
- full pytest/coverage/compile/Ruff gate embedded in the standard workflow: **success**;
- executable examples, including `fpc_simultaneous_bands.py`: **success**;
- strict MkDocs documentation build: **success**;
- optional scikit-fda interoperability: **success**;
- optional FDApy sparse/PACE interoperability on Python 3.11 and 3.12: **2/2 success**.

No tests, coverage thresholds, workflows, branch protections, or scientific validation checks were weakened, disabled, deleted, or bypassed.

PR #12 was squash-merged as:

`b9b743bbbb62f691850833f274610950cd101701`

The certified PR head and squash-merged main commit both point to Git tree:

`75857628188e02cffa3d2681c5e463fca6b35001`

so the merged code, scientific contracts, tests, examples, and documentation are byte-for-byte identical to the exact CI-certified PR-head tree.

### 0.9 exact-main qualification and deployment — 2026-09-21

The exact merged-main commit

`b9b743bbbb62f691850833f274610950cd101701`

completed a fresh push-triggered qualification generation successfully:

- tests workflow #44: **success**, including package construction and all 9 Windows/Ubuntu/macOS × Python 3.11–3.13 lanes;
- examples workflow #44: **success**;
- docs workflow #44: **success**, including strict documentation build and **successful GitHub Pages deployment**;
- optional-fda workflow #40: **success**;
- optional-sparse-fda workflow #28: **success**, including FDApy Python 3.11 and 3.12 lanes.

Therefore the 0.9 simultaneous FPC-shape uncertainty tranche is both **PR-head CI-certified** and **exact-main requalified**, and the corresponding methods-site deployment is certified on the merged 0.9 main lineage.

## 0.9 remaining re-checks

The current optional-backend boundary remains unchanged:

1. Reassess FDApy/Python 3.13 interoperability only when the FDApy/NumPy dependency line supports Python 3.13. This is not part of the current FDApy support contract.

The 0.9 FPC-band implementation, cross-platform package behavior, package construction, coverage/compile/Ruff gates, executable examples, strict documentation, GitHub Pages deployment, scikit-fda interoperability, and FDApy sparse/PACE interoperability on Python 3.11–3.12 are GitHub CI-certified on the exact merged 0.9 main lineage.


### 0.10 PR-head certification — 2026-09-21

Exact certified PR head:

`8d136999292ad08762f33f48ccbf3df43c4e60ac`

PR #13, **“Add FPCA spectrum uncertainty,”** completed all unchanged pull-request qualification workflows successfully on that exact SHA:

- package build / distribution validation: **success**;
- Windows × Python 3.11, 3.12, 3.13: **3/3 success**;
- Ubuntu × Python 3.11, 3.12, 3.13: **3/3 success**;
- macOS × Python 3.11, 3.12, 3.13: **3/3 success**;
- full pytest/coverage/compile/Ruff gate embedded in the standard workflow: **success**;
- executable examples, including `fpca_spectrum_uncertainty.py`: **success**;
- strict MkDocs documentation build: **success**;
- optional scikit-fda interoperability: **success**;
- optional FDApy sparse/PACE interoperability on Python 3.11 and 3.12: **2/2 success**.

No tests, coverage thresholds, workflows, branch protections, or scientific validation checks were weakened, disabled, deleted, or bypassed.

PR #13 was squash-merged as:

`f68631ab255472d2787802394b7db61bc4206fb3`

The certified PR head and squash-merged main commit both point to Git tree:

`1e82c78386ada969a7335c771cb27e87ac67e50a`

so the merged code, scientific contracts, tests, examples, and documentation are byte-for-byte identical to the exact CI-certified PR-head tree.

### 0.10 exact-main qualification and deployment — 2026-09-21

The exact merged-main commit

`f68631ab255472d2787802394b7db61bc4206fb3`

completed a fresh push-triggered qualification generation successfully:

- tests workflow #47: **success**, including package construction and all 9 Windows/Ubuntu/macOS × Python 3.11–3.13 lanes;
- examples workflow #47: **success**;
- docs workflow #47: **success**, including strict documentation build and **successful GitHub Pages deployment**;
- optional-fda workflow #43: **success**;
- optional-sparse-fda workflow #31: **success**, including FDApy Python 3.11 and 3.12 lanes.

Therefore the 0.10 FPCA-spectrum-uncertainty tranche is both **PR-head CI-certified** and **exact-main requalified**, and the updated methods site is deployed from the merged 0.10 main lineage.

## 0.10 remaining re-checks

The optional-backend compatibility boundary remains unchanged:

1. Reassess FDApy/Python 3.13 interoperability only when the FDApy/NumPy dependency line supports Python 3.13. This is outside the current FDApy support contract.

The 0.10 spectrum implementation, cross-platform package behavior, package construction, coverage/compile/Ruff gates, executable examples, strict documentation, GitHub Pages deployment, scikit-fda interoperability, and FDApy sparse/PACE interoperability on Python 3.11–3.12 are GitHub CI-certified on the exact merged 0.10 main lineage.


### 0.11 PR-head certification — 2026-09-21

Exact certified PR head:

`e5373b41217086705da70c02708b0459fd0f7d48`

PR #14, **“Add FPC score basis-resampling uncertainty,”** completed all unchanged pull-request qualification workflows successfully on that exact SHA:

- package build / distribution validation: **success**;
- Windows × Python 3.11, 3.12, 3.13: **3/3 success**;
- Ubuntu × Python 3.11, 3.12, 3.13: **3/3 success**;
- macOS × Python 3.11, 3.12, 3.13: **3/3 success**;
- full pytest/coverage/compile/Ruff gate embedded in the standard workflow: **success**;
- executable examples, including `fpca_score_uncertainty.py`: **success**;
- strict MkDocs documentation build: **success**;
- optional scikit-fda interoperability: **success**;
- optional FDApy sparse/PACE interoperability on Python 3.11 and 3.12: **2/2 success**.

One earlier PR-head generation failed strict docs because the new worked example linked to the nonexistent `guides/stability.md`. The link was corrected to the existing `guides/stability-validation.md`; the exact certified head above then completed strict docs successfully. No documentation warning was suppressed and strict mode was not weakened.

No tests, coverage thresholds, workflows, branch protections, or scientific validation checks were weakened, disabled, deleted, or bypassed.

PR #14 was squash-merged as:

`eca47bffb16d072be4b88a0f17778ed675709340`

The certified PR head and squash-merged main commit both point to Git tree:

`2aa2282153e8e7d988306a23638a1368f295de21`

so the merged code, scientific contracts, tests, examples, and documentation are byte-for-byte identical to the exact CI-certified PR-head tree.

### 0.11 exact-main qualification — 2026-09-21

The exact merged-main commit

`eca47bffb16d072be4b88a0f17778ed675709340`

completed the scientific/package portion of a fresh push-triggered qualification generation successfully:

- tests workflow #54: package construction plus all 9 Windows/Ubuntu/macOS × Python 3.11–3.13 lanes: **success**;
- examples workflow #54: **success**;
- optional-fda workflow #50: **success**;
- optional-sparse-fda workflow #38: **success**, including FDApy Python 3.11 and 3.12 lanes;
- docs workflow #54 strict MkDocs build: **success**.

The main-branch docs workflow then failed only at GitHub's `actions/upload-pages-artifact` finalization stage. The generated Pages artifact uploaded its bytes, but the hosted service returned HTTP **403 Forbidden** while finalizing the artifact. The deploy job was therefore skipped.

This is recorded as a **hosted Pages/artifact-service failure, not a documentation-build or code failure**. The workflow, permissions, branch protections, tests, and documentation strictness were not changed to work around it. The status-ledger commit carrying this record is used as a clean retry of the unchanged main-branch docs/deployment workflow.

### 0.11 status-tip Pages retry and close-out — 2026-09-21

The status-ledger-only main tip

`fadd1865d3ad4755ddff1ae8b6de66f158d67522`

retried the unchanged main workflows after the earlier hosted Pages-artifact 403. The retry completed successfully:

- tests workflow #55: **success**, including package build and all 9 Windows/Ubuntu/macOS × Python 3.11–3.13 lanes;
- examples workflow #55: **success**;
- docs workflow #55: **success**, including strict MkDocs build, Pages artifact upload, and **successful GitHub Pages deployment**;
- optional-fda workflow #51: **success**;
- optional-sparse-fda workflow #39: **success**, including FDApy Python 3.11 and 3.12 lanes.

The prior Pages 403 is therefore closed as a transient hosted-service failure. No workflow, permission, test, or documentation strictness was changed to obtain the successful retry.

## 0.11 remaining re-checks

1. Reassess FDApy/Python 3.13 interoperability only when the FDApy/NumPy dependency line supports Python 3.13; this remains outside the current FDApy support contract.

The 0.11 FPC score basis-resampling implementation, package construction, all 9 core cross-platform lanes, coverage/compile/Ruff gates, executable examples, strict documentation, GitHub Pages deployment, scikit-fda interoperability, and FDApy sparse/PACE interoperability on Python 3.11–3.12 are GitHub CI-certified on the current 0.11 main lineage.


### 0.12 PR-head certification — 2026-09-21

Exact certified PR head:

`b9b36ff3dcf65c9de0b54fe7f9937099d0b8011d`

PR #15, **“Add Gaussian FPCR paired-bootstrap uncertainty,”** completed all unchanged pull-request qualification workflows successfully on that exact SHA:

- package build / distribution validation: **success**;
- Windows × Python 3.11, 3.12, 3.13: **3/3 success**;
- Ubuntu × Python 3.11, 3.12, 3.13: **3/3 success**;
- macOS × Python 3.11, 3.12, 3.13: **3/3 success**;
- full pytest/coverage/compile/Ruff gate embedded in the standard workflow: **success**;
- executable examples, including `fpcr_regression_uncertainty.py`: **success**;
- strict MkDocs documentation build: **success**;
- optional scikit-fda interoperability: **success**;
- optional FDApy sparse/PACE interoperability on Python 3.11 and 3.12: **2/2 success**.

No tests, coverage thresholds, workflows, branch protections, or scientific validation checks were weakened, disabled, deleted, or bypassed.

PR #15 was squash-merged as:

`1116793866e903e04ef65ec1bb26536865da7a74`

The certified PR head and squash-merged main commit both point to Git tree:

`c9b085b2d8f431cd441b96561022c4f7e0066b97`

so the merged code, scientific contracts, tests, examples, and documentation are byte-for-byte identical to the exact CI-certified PR-head tree.

### 0.12 exact-main qualification and deployment — 2026-09-21

The exact merged-main commit

`1116793866e903e04ef65ec1bb26536865da7a74`

completed a fresh push-triggered qualification generation successfully:

- tests workflow #58: **success**, including package construction and all 9 Windows/Ubuntu/macOS × Python 3.11–3.13 lanes;
- examples workflow #58: **success**;
- docs workflow #58: **success**, including strict MkDocs build and **successful GitHub Pages deployment**;
- optional-fda workflow #54: **success**;
- optional-sparse-fda workflow #42: **success**, including FDApy Python 3.11 and 3.12 lanes.

Therefore the 0.12 Gaussian FPCR paired-bootstrap uncertainty tranche is both **PR-head CI-certified** and **exact-main requalified**, and the corresponding methods-site deployment is certified on the merged 0.12 main lineage.

## 0.12 remaining re-checks

1. Reassess FDApy/Python 3.13 interoperability only when the FDApy/NumPy dependency line supports Python 3.13; this remains outside the current FDApy support contract.
2. The 0.12 percentile bootstrap is not the operator-scaled FPCR significance test described in 2026 theory. A future tranche may evaluate a dedicated implementation only if its assumptions, scaling, null bootstrap, and reporting contract can be reproduced faithfully.

The 0.12 FPCR uncertainty implementation, package construction, all 9 core cross-platform lanes, coverage/compile/Ruff gates, executable examples, strict documentation, GitHub Pages deployment, scikit-fda interoperability, and FDApy sparse/PACE interoperability on Python 3.11–3.12 are GitHub CI-certified on the merged 0.12 scientific tree.


### 0.13 PR-head certification — 2026-09-21

Exact certified PR head:

`09cac05cb7b489d28f65dccd42f814fd68e4f4a6`

PR #16, **“Add simultaneous Gaussian FPCR slope bands,”** completed all unchanged pull-request qualification workflows successfully on that exact SHA:

- package build / distribution validation: **success**;
- Windows × Python 3.11, 3.12, 3.13: **3/3 success**;
- Ubuntu × Python 3.11, 3.12, 3.13: **3/3 success**;
- macOS × Python 3.11, 3.12, 3.13: **3/3 success**;
- full pytest/coverage/compile/Ruff gate embedded in the standard workflow: **success**;
- executable examples, including `fpcr_slope_simultaneous_band.py`: **success**;
- strict MkDocs documentation build: **success**;
- optional scikit-fda interoperability: **success**;
- optional FDApy sparse/PACE interoperability on Python 3.11 and 3.12: **2/2 success**.

The local calibration harness had exposed a numerical edge case before PR qualification: directly computing standard deviation on repeated identical nonzero slope values could produce floating-point pseudo-variance. The implementation was corrected to compute pointwise SE from bootstrap deviations from the full-sample reference slope, preserving exact zero-variance semantics without weakening the threshold.

No tests, coverage thresholds, workflows, branch protections, or scientific validation checks were weakened, disabled, deleted, or bypassed.

PR #16 was squash-merged as:

`7a6dc22408b72e03bf58ca3f629db86d47d7425a`

The certified PR head and squash-merged main commit both point to Git tree:

`c930c3f9db8bf1cb00be065da44bae3c56c2db1a`

so the merged code, scientific contracts, tests, examples, and documentation are byte-for-byte identical to the exact CI-certified PR-head tree.

### 0.13 exact-main qualification and deployment — 2026-09-21

The exact merged-main commit

`7a6dc22408b72e03bf58ca3f629db86d47d7425a`

completed a fresh push-triggered qualification generation successfully:

- tests workflow #62: **success**, including package construction and all 9 Windows/Ubuntu/macOS × Python 3.11–3.13 lanes;
- examples workflow #62: **success**;
- docs workflow #62: **success**, including strict MkDocs build and **successful GitHub Pages deployment**;
- optional-fda workflow #58: **success**;
- optional-sparse-fda workflow #46: **success**, including FDApy Python 3.11 and 3.12 lanes.

Therefore the 0.13 simultaneous Gaussian FPCR slope-band tranche is both **PR-head CI-certified** and **exact-main requalified**, and the corresponding methods-site deployment is certified on the merged 0.13 main lineage.

## 0.13 remaining re-checks

1. Reassess FDApy/Python 3.13 interoperability only when the FDApy/NumPy dependency line supports Python 3.13; this remains outside the current FDApy support contract.

The 0.13 observed-grid simultaneous Gaussian FPCR slope-band implementation, package construction, all 9 core cross-platform lanes, coverage/compile/Ruff gates, executable examples, strict documentation, GitHub Pages deployment, scikit-fda interoperability, and FDApy sparse/PACE interoperability on Python 3.11–3.12 are GitHub CI-certified on the exact merged 0.13 main lineage.


### 0.14 PR-head certification — 2026-09-21

Exact certified PR head:

`0df6a805dbfce9eb9f619501ade4eea7e916df8e`

PR #17, **“Add Gaussian FPCR future-outcome prediction intervals,”** completed all unchanged pull-request qualification workflows successfully on that exact SHA:

- package build / distribution validation: **success**;
- Windows × Python 3.11, 3.12, 3.13: **3/3 success**;
- Ubuntu × Python 3.11, 3.12, 3.13: **3/3 success**;
- macOS × Python 3.11, 3.12, 3.13: **3/3 success**;
- full pytest/coverage/compile/Ruff gate embedded in the standard workflow: **success**;
- executable examples, including `fpcr_future_prediction_intervals.py`: **success**;
- strict MkDocs documentation build: **success**;
- optional scikit-fda interoperability: **success**;
- optional FDApy sparse/PACE interoperability on Python 3.11 and 3.12: **2/2 success**.

Local delta validation before PR publication confirmed centered empirical residuals, deterministic predictive draws, exact decomposition of each predictive draw into a stored paired-bootstrap conditional mean plus its sampled residual, ordered predictive quantiles, and non-decreasing interval width as confidence increased.

The residual-resampling RNG was separated into a spawned deterministic stream so an analyst may use the same numeric seed for the paired FPCR bootstrap and future-response layer without reusing the same initial pseudo-random sequence.

No tests, coverage thresholds, workflows, branch protections, or scientific validation checks were weakened, disabled, deleted, or bypassed.

PR #17 was squash-merged as:

`977eebd954e2efc1fcc98e3d54968023a42635ff`

The certified PR head and squash-merged main commit both point to Git tree:

`f3a5057084a39d581bcedaa75e48f6e38ae24af8`

so the merged code, scientific contracts, tests, examples, and documentation are byte-for-byte identical to the exact CI-certified PR-head tree.

### 0.14 exact-main qualification and deployment — 2026-09-21

The exact merged-main commit

`977eebd954e2efc1fcc98e3d54968023a42635ff`

completed a fresh push-triggered qualification generation successfully:

- tests workflow #65: **success**, including package construction and all 9 Windows/Ubuntu/macOS × Python 3.11–3.13 lanes;
- examples workflow #65: **success**;
- docs workflow #65: **success**, including strict MkDocs build and **successful GitHub Pages deployment**;
- optional-fda workflow #61: **success**;
- optional-sparse-fda workflow #49: **success**, including FDApy Python 3.11 and 3.12 lanes.

Therefore the 0.14 Gaussian FPCR future-outcome prediction tranche is both **PR-head CI-certified** and **exact-main requalified**, and the corresponding methods-site deployment is certified on the merged 0.14 main lineage.

## 0.14 remaining re-checks

1. Reassess FDApy/Python 3.13 interoperability only when the FDApy/NumPy dependency line supports Python 3.13; this remains outside the current FDApy support contract.
2. Future-outcome prediction currently assumes a pooled exchangeable/common residual distribution. A heteroscedastic/wild-bootstrap extension should be considered only as a separate method with its own assumptions, theory, tests, and reporting contract.

The 0.14 future-outcome prediction implementation, package construction, all 9 core cross-platform lanes, coverage/compile/Ruff gates, executable examples, strict documentation, GitHub Pages deployment, scikit-fda interoperability, and FDApy sparse/PACE interoperability on Python 3.11–3.12 are GitHub CI-certified on the exact merged 0.14 main lineage.


### 0.15 PR-head certification — 2026-09-21

Exact certified PR head:

`d8fabfd3ca7011cec4c4979605e0faf578807bad`

PR #18, **“Add split-conformal FPCA anomaly review,”** completed all unchanged pull-request qualification workflows successfully on that exact SHA:

- package build / distribution validation: **success**;
- Windows × Python 3.11, 3.12, 3.13: **3/3 success**;
- Ubuntu × Python 3.11, 3.12, 3.13: **3/3 success**;
- macOS × Python 3.11, 3.12, 3.13: **3/3 success**;
- full pytest/coverage/compile/Ruff gate embedded in the standard workflow: **success**;
- executable examples, including the conformal anomaly example: **success**;
- strict MkDocs documentation build: **success**;
- optional scikit-fda interoperability: **success**;
- optional FDApy sparse/PACE interoperability on Python 3.11 and 3.12: **2/2 success**.

No tests, coverage thresholds, workflows, branch protections, or scientific validation checks were weakened, disabled, deleted, or bypassed.

PR #18 was squash-merged as:

`901b2cf057c57d99d9f02fbfdf71dd6dc07dc667`

The certified PR head and squash-merged main commit both point to Git tree:

`cb516a458464aed2a8f65dcf8c9a0b1c8e49cd2b`

so the merged code, scientific contracts, tests, examples, and documentation are byte-for-byte identical to the exact CI-certified PR-head tree.

### 0.15 exact-main qualification and deployment — 2026-09-21

The exact merged-main commit

`901b2cf057c57d99d9f02fbfdf71dd6dc07dc667`

completed a fresh push-triggered qualification generation successfully:

- tests workflow #69: **success**, including package construction and all 9 Windows/Ubuntu/macOS × Python 3.11–3.13 lanes;
- examples workflow #69: **success**;
- docs workflow #69: **success**, including strict MkDocs build and **successful GitHub Pages deployment**;
- optional-fda workflow #65: **success**;
- optional-sparse-fda workflow #53: **success**, including FDApy Python 3.11 and 3.12 lanes.

Therefore the 0.15 split-conformal FPCA anomaly-review tranche is both **PR-head CI-certified** and **exact-main requalified**, and the corresponding methods-site deployment is certified on the merged 0.15 main lineage.

## 0.15 remaining re-checks

1. Reassess FDApy/Python 3.13 interoperability only when the FDApy/NumPy dependency line supports Python 3.13; this remains outside the current FDApy support contract.
2. Conformal anomaly p-values remain curve-level marginal review diagnostics under the declared split/exchangeability contract; calibration-conditional adjustment, repeated-participant dependence, and multiple-target FDR/familywise procedures remain separate future methods.

The 0.15 split-conformal anomaly implementation, package construction, all 9 core cross-platform lanes, coverage/compile/Ruff gates, executable examples, strict documentation, GitHub Pages deployment, scikit-fda interoperability, and FDApy sparse/PACE interoperability on Python 3.11–3.12 are GitHub CI-certified on the exact merged 0.15 main lineage.


### 0.16 PR-head certification — 2026-09-22

Exact certified PR head:

`a01c3ecd30302909f9655d780d83ca67d86294c6`

PR #19, **“Add heteroscedastic Gaussian FPCR wild-bootstrap inference,”** completed all unchanged pull-request qualification workflows successfully on that exact SHA:

- package build / distribution validation: **success**;
- Windows × Python 3.11, 3.12, 3.13: **3/3 success**;
- Ubuntu × Python 3.11, 3.12, 3.13: **3/3 success**;
- macOS × Python 3.11, 3.12, 3.13: **3/3 success**;
- full pytest/coverage/compile/Ruff gate embedded in the standard workflow: **success**;
- executable examples, including `fpcr_wild_bootstrap_projection.py`: **success**;
- strict MkDocs documentation build: **success**;
- optional scikit-fda interoperability: **success**;
- optional FDApy sparse/PACE interoperability on Python 3.11 and 3.12: **2/2 success**.

Local delta validation before PR publication confirmed deterministic normal-multiplier studentized roots and bootstrap-level heteroscedastic standard errors, monotone interval width as confidence increased, finite Mammen-multiplier inference, and exact theoretical Mammen moments E(W)=0, Var(W)=1, and E(W^3)=1.

The implementation keeps functional regressors and the FPCA/MFPCA basis fixed during wild resampling, uses residual/pseudo-truth truncation k=g, requires inference truncation h>=g, and recomputes the heteroscedastic studentization scale inside every pseudo-sample.

No tests, coverage thresholds, workflows, branch protections, or scientific validation checks were weakened, disabled, deleted, or bypassed.

PR #19 was squash-merged as:

`9d5567c7014197137654cabe69428dbf52830133`

The certified PR head and squash-merged main commit both point to Git tree:

`d37f55ecd1b5a30516ae286994270169ce5c1eb8`

so the merged code, scientific contracts, tests, examples, and documentation are byte-for-byte identical to the exact CI-certified PR-head tree.

### 0.16 exact-main qualification and deployment — 2026-09-22

The exact merged-main commit

`9d5567c7014197137654cabe69428dbf52830133`

completed a fresh push-triggered qualification generation successfully:

- tests workflow #72: **success**, including package construction and all 9 Windows/Ubuntu/macOS × Python 3.11–3.13 lanes;
- examples workflow #72: **success**;
- docs workflow #72: **success**, including strict MkDocs build and **successful GitHub Pages deployment**;
- optional-fda workflow #68: **success**;
- optional-sparse-fda workflow #56: **success**, including FDApy Python 3.11 and 3.12 lanes.

Therefore the 0.16 heteroscedastic Gaussian FPCR wild-bootstrap tranche is both **PR-head CI-certified** and **exact-main requalified**, and the corresponding methods-site deployment is certified on the merged 0.16 main lineage.

## 0.16 remaining re-checks

1. Reassess FDApy/Python 3.13 interoperability only when the FDApy/NumPy dependency line supports Python 3.13; this remains outside the current FDApy support contract.
2. The wild-bootstrap API currently assumes independent curve rows. Clustered/repeated-participant wild-bootstrap inference requires a separate method and validity contract.
3. k=g and h are analyst-declared truncations. Data-driven truncation-selection uncertainty and the stabilized-volatility selection method from the 2026 literature are not yet implemented.
4. The 0.16 intervals are target-wise centered-projection intervals, not simultaneous target intervals and not future-outcome prediction intervals.

The 0.16 wild-bootstrap implementation, package construction, all 9 core cross-platform lanes, coverage/compile/Ruff gates, executable examples, strict documentation, GitHub Pages deployment, scikit-fda interoperability, and FDApy sparse/PACE interoperability on Python 3.11–3.12 are GitHub CI-certified on the exact merged 0.16 main lineage.


## 0.17 pre-PR local algorithm validation — 2026-09-22

A standalone score-space harness matching the 0.17 shared-multiplier truncation scan and stabilized-volatility rule was executed locally.

- largest scan candidate exactly matched the standalone 0.16 fixed-h wild-bootstrap reference projection: **passed**;
- largest scan candidate exactly matched standalone heteroscedastic reference SEs: **passed**;
- largest scan candidate exactly matched standalone studentized bootstrap roots under the same seed: **passed**;
- largest scan candidate exactly matched standalone lower and upper interval limits: **passed**;
- repeated scans with the same seed produced identical shared-multiplier roots: **passed**;
- synthetic truth fixture with known width/center changes selected the earliest qualifying h=3 under rho_w=0.10, rho_c=0.05, r=1: **passed**;
- a second synthetic target with no stable run remained explicitly unselected: **passed**.

This is local delta algorithmic evidence only. Full repository pytest/coverage/Ruff/package/docs/examples/optional-backend qualification remains a GitHub CI responsibility for the exact PR head.


### 0.17 PR-head certification — 2026-09-22

Exact certified PR head:

`47dd5ef8200fb4d80db7947dd6c1ffe5117243c7`

PR #20, **“Add stabilized-volatility FPCR wild-bootstrap selection,”** completed all unchanged pull-request qualification workflows successfully on that exact SHA:

- package build / distribution validation: **success**;
- Windows × Python 3.11, 3.12, 3.13: **3/3 success**;
- Ubuntu × Python 3.11, 3.12, 3.13: **3/3 success**;
- macOS × Python 3.11, 3.12, 3.13: **3/3 success**;
- full pytest/coverage/compile/Ruff gate embedded in the standard workflow: **success**;
- executable examples, including `fpcr_wild_bootstrap_selection.py`: **success**;
- strict MkDocs documentation build: **success**;
- optional scikit-fda interoperability: **success**;
- optional FDApy sparse/PACE interoperability on Python 3.11 and 3.12: **2/2 success**.

Local delta validation before PR publication confirmed exact agreement between the largest shared-multiplier scan candidate and the standalone 0.16 fixed-h wild-bootstrap projection, heteroscedastic SEs, studentized roots, and interval limits under the same seed. A synthetic stabilized-volatility truth fixture selected the earliest qualifying h=3 under rho_w=0.10, rho_c=0.05, r=1, while a second target with no stable run remained explicitly unselected.

The implementation fixes k, sets g=k, requires consecutive h candidates with h>=g, reuses identical wild multiplier draws across h within each bootstrap replicate, and applies analyst-supplied absolute width/center thresholds plus the published r-run criterion. No package default of 0.01 and no silent largest-h fallback were introduced.

No tests, coverage thresholds, workflows, branch protections, or scientific validation checks were weakened, disabled, deleted, or bypassed.

PR #20 was squash-merged as:

`e38b5767b68af08508ce5a5f7afd428b736a14c8`

The certified PR head and squash-merged main commit both point to Git tree:

`1208697e2bd5dd58f13c94ec425d62289d8129f4`

so the merged code, scientific contracts, tests, examples, and documentation are byte-for-byte identical to the exact CI-certified PR-head tree.

### 0.17 exact-main qualification and deployment — 2026-09-22

The exact merged-main commit

`e38b5767b68af08508ce5a5f7afd428b736a14c8`

completed a fresh push-triggered qualification generation successfully:

- tests workflow #75: **success**, including package construction and all 9 Windows/Ubuntu/macOS × Python 3.11–3.13 lanes;
- examples workflow #75: **success**;
- docs workflow #75: **success**, including strict MkDocs build and **successful GitHub Pages deployment**;
- optional-fda workflow #71: **success**;
- optional-sparse-fda workflow #59: **success**, including FDApy Python 3.11 and 3.12 lanes.

Therefore the 0.17 stabilized-volatility FPCR wild-bootstrap selection tranche is both **PR-head CI-certified** and **exact-main requalified**, and the corresponding methods-site deployment is certified on the merged 0.17 main lineage.

## 0.17 remaining re-checks

1. Reassess FDApy/Python 3.13 interoperability only when the FDApy/NumPy dependency line supports Python 3.13; this remains outside the current FDApy support contract.
2. Stabilized-volatility thresholds rho_w and rho_c remain analyst-declared absolute outcome-scale tolerances; no universal threshold is claimed.
3. The method is a practical tuning heuristic, not a coverage-optimality guarantee.
4. Clustered/repeated-participant wild-bootstrap inference remains outside the 0.17 contract.

The 0.17 shared-multiplier truncation scan and stabilized-volatility selector, package construction, all 9 core cross-platform lanes, coverage/compile/Ruff gates, executable examples, strict documentation, GitHub Pages deployment, scikit-fda interoperability, and FDApy sparse/PACE interoperability on Python 3.11–3.12 are GitHub CI-certified on the exact merged 0.17 main lineage.

## 0.18 pre-PR algorithm and repository integrity — 2026-09-22

Before PR publication, a standalone numerical harness and the exact GitHub branch were used to validate the new familywise post-calibration contract.

- replicate-wise familywise statistic exactly defined as the maximum absolute studentized root over the declared target family: **passed**;
- familywise critical value no smaller than every same-level target-wise critical value: **passed**;
- one-target family exactly reduced to the target-wise calibration: **passed**;
- adding an all-zero root coordinate left the maximum calibration unchanged: **passed**;
- critical values were nondecreasing as confidence increased: **passed**;
- exact branch source audit: **72/72** configured MkDocs navigation targets existed;
- exact branch API audit: **170/170** documented public symbols resolved;
- package, project, citation, README, methods-status, and homepage version surfaces all reported the 0.18 development line;
- `examples/fpcr_wild_bootstrap_simultaneous.py` was registered in the unchanged examples workflow;
- the branch was six commits ahead and zero behind `main` immediately before PR creation.

This pre-PR evidence was delta/structural validation only. Full integrated cross-platform qualification is recorded below.

### 0.18 PR-head certification — 2026-09-22

Exact certified PR head:

`dad24a3bf2e11b68f582e86fb268d337b33676df`

PR #21, **“Add simultaneous fixed-target FPCR wild-bootstrap inference,”** completed all unchanged pull-request qualification workflows successfully on that exact SHA:

- tests workflow #77: **success**, including package construction and all **9/9** Windows/Ubuntu/macOS × Python 3.11–3.13 lanes;
- representative completed core logs reported **164 passed, 5 skipped**, **92.39% coverage**, and successful Ruff checks against the unchanged 90% coverage gate;
- examples workflow #77: **success**, including `fpcr_wild_bootstrap_simultaneous.py`;
- docs workflow #77: **success** with strict MkDocs build;
- optional-fda workflow #73: **success**;
- optional-sparse-fda workflow #61: **success**, including FDApy Python 3.11 and 3.12 lanes.

The implementation is a pure post-calibration of the exact studentized root matrix retained by `FPCAWildBootstrapProjectionResult`. It takes one maximum absolute studentized root across the complete fixed-target family within each bootstrap replicate and uses its requested empirical quantile as a common familywise critical value. It does not rerun FPCA, score regression, residual estimation, multiplier generation, or the wild bootstrap.

No tests, coverage thresholds, workflows, branch protections, or scientific validation checks were weakened, disabled, deleted, or bypassed.

PR #21 was squash-merged as:

`d325ed573282f7ac53000c6d684c8128291896df`

The certified PR head and squash-merged main commit both point to Git tree:

`97afdab71ed82c582311641e497464d0cffa6d16`

so the merged implementation, tests, examples, scientific contracts, and documentation are byte-for-byte identical to the exact CI-certified PR-head tree.

### 0.18 exact-main qualification and deployment — 2026-09-22

The exact merged-main commit

`d325ed573282f7ac53000c6d684c8128291896df`

completed a fresh push-triggered qualification generation successfully:

- tests workflow #78: **success**, including package construction and all **9/9** Windows/Ubuntu/macOS × Python 3.11–3.13 lanes;
- examples workflow #78: **success**, including the new simultaneous fixed-target executable example;
- docs workflow #78: **success**, including strict MkDocs build and **successful GitHub Pages deployment**;
- optional-fda workflow #74: **success**;
- optional-sparse-fda workflow #62: **success**, including FDApy Python 3.11 and 3.12 lanes.

Therefore the 0.18 simultaneous fixed-target heteroscedastic Gaussian FPCR wild-bootstrap tranche is both **PR-head CI-certified** and **exact-main requalified**, and the corresponding methods-site deployment is certified on the merged 0.18 scientific lineage.

## 0.18 remaining re-checks

1. Reassess FDApy/Python 3.13 interoperability only when the FDApy/NumPy dependency line supports Python 3.13; this remains outside the current FDApy support contract.
2. The simultaneous target family should be scientifically declared before confirmatory inspection. Adaptive target-family selection is not covered by the current familywise statement.
3. The familywise calibration is conditional on the base k=g and h truncations. Data-driven truncation/component-selection uncertainty is not propagated automatically.
4. Clustered/repeated-participant wild-bootstrap inference remains outside the current independent-curve contract.
5. These intervals cover fixed centered FPCR target projections. They are not joint future-outcome prediction regions and do not add future scalar-response noise.

The 0.18 familywise max-|t| fixed-target post-calibration, package construction, all 9 core cross-platform lanes, coverage/compile/Ruff gates, executable examples, strict documentation, GitHub Pages deployment, scikit-fda interoperability, and FDApy sparse/PACE interoperability on Python 3.11–3.12 are GitHub CI-certified on the exact merged 0.18 scientific lineage.

## 0.19 pre-PR algorithm and repository integrity — 2026-09-22

Before PR publication, the fixed-family testing contract was checked with hand-calculated finite-bootstrap fixtures and exact branch integration audits.

- hand-constructed studentized roots reproduced the expected target-wise plus-one tail probabilities: **passed**;
- the same fixture reproduced the expected single-step maxT-adjusted probabilities: **passed**;
- the complete-family global maximum statistic and bootstrap probability matched the direct calculation: **passed**;
- adjusted probabilities were no smaller than their corresponding target-wise probabilities: **passed**;
- a one-target family reduced exactly to the target-wise/global calibration: **passed**;
- scalar and target-specific finite null values were supported explicitly;
- zero reference SE with zero null discrepancy produced a zero observed statistic, while a non-zero null discrepancy with zero SE failed explicitly;
- plus-one and raw empirical Monte Carlo probability rules remained explicit method choices;
- exact branch source audit: **74/74** configured MkDocs navigation targets existed;
- exact branch API audit: **175/175** documented public symbols resolved;
- package, project, citation, README, methods-status, and homepage version surfaces all reported the 0.19 development line;
- `examples/fpcr_wild_bootstrap_family_test.py` was registered in the unchanged examples workflow;
- the branch was eight commits ahead and zero behind `main` immediately before PR creation.

This pre-PR evidence was algorithmic/structural validation only. Full integrated cross-platform qualification is recorded below.

### 0.19 PR-head certification — 2026-09-22

Exact certified PR head:

`0e885c014305c8906ba4019c7f434aacadae1586`

PR #22, **“Add fixed-family FPCR wild-bootstrap hypothesis tests,”** completed all unchanged pull-request qualification workflows successfully on that exact SHA:

- tests workflow #80: **success**, including package construction and all **9/9** Windows/Ubuntu/macOS × Python 3.11–3.13 lanes;
- a representative completed core log reported **169 passed, 5 skipped**, **92.40% coverage**, and successful Ruff checks against the unchanged 90% coverage gate;
- examples workflow #80: **success**, including `fpcr_wild_bootstrap_family_test.py`;
- docs workflow #80: **success** with strict MkDocs build;
- optional-fda workflow #76: **success**;
- optional-sparse-fda workflow #64: **success**, including FDApy Python 3.11 and 3.12 lanes.

The implementation reuses the exact studentized root matrix retained by `FPCAWildBootstrapProjectionResult`. For each supplied scalar or target-specific null projection, it forms a two-sided observed studentized discrepancy, reports a target-wise bootstrap tail probability, reports a single-step maxT-adjusted probability from the replicate-wise maximum absolute root, and reports one complete-family global max-statistic p-value.

The default finite-Monte-Carlo rule is `(r+1)/(B+1)`, preventing zero p-values from a finite bootstrap sample; the raw empirical exceedance fraction remains available only as an explicit alternative. Zero reference SE is accepted only when the null discrepancy is numerically zero.

The testing layer does not rerun FPCA, score regression, residual estimation, multiplier generation, or bootstrap sampling. Provenance records that the resampling distribution is not explicitly regenerated under the target null, and the package does not claim strong family-wise error control for arbitrary subsets of null hypotheses without additional subset-pivotality or closed/step-down conditions.

No tests, coverage thresholds, workflows, branch protections, or scientific validation checks were weakened, disabled, deleted, or bypassed.

PR #22 was squash-merged as:

`9fe5135d4b7477da0c68cf58a134245d30ff5678`

The certified PR head and squash-merged main commit both point to Git tree:

`9f8d9adb42caf2c68912abf2d688df8bd41d0e98`

so the merged implementation, tests, examples, scientific contracts, and documentation are byte-for-byte identical to the exact CI-certified PR-head tree.

### 0.19 exact-main qualification and deployment — 2026-09-22

The exact merged-main commit

`9fe5135d4b7477da0c68cf58a134245d30ff5678`

completed a fresh push-triggered qualification generation successfully:

- tests workflow #81: **success**, including package construction and all **9/9** Windows/Ubuntu/macOS × Python 3.11–3.13 lanes;
- examples workflow #81: **success**, including the fixed-family testing executable example;
- docs workflow #81: **success**, including strict MkDocs build and **successful GitHub Pages deployment**;
- optional-fda workflow #77: **success**;
- optional-sparse-fda workflow #65: **success**, including FDApy Python 3.11 and 3.12 lanes.

Therefore the 0.19 fixed-family heteroscedastic Gaussian FPCR wild-bootstrap hypothesis-testing tranche is both **PR-head CI-certified** and **exact-main requalified**, and the corresponding methods-site deployment is certified on the merged 0.19 scientific lineage.

## 0.19 remaining re-checks

1. Reassess FDApy/Python 3.13 interoperability only when the FDApy/NumPy dependency line supports Python 3.13; this remains outside the current FDApy support contract.
2. The testing family and null projection values should be scientifically declared before confirmatory inspection. Adaptive target-family selection is not covered by the current multiplicity statement.
3. The bootstrap comparison distribution is not regenerated under an explicitly imposed target null; the implementation is a post-processing test approximation built from the certified centered studentized roots.
4. Single-step maxT adjustment is reported for the complete declared family. Strong FWER for arbitrary subsets of true nulls is not claimed without additional subset-pivotality or closed/step-down theory.
5. The tests remain conditional on the base k=g and h truncations. Data-driven truncation/component-selection uncertainty is not propagated automatically.
6. Clustered/repeated-participant wild-bootstrap inference remains outside the independent-curve contract.
7. These tests concern fixed centered FPCR target projections. They are not future-outcome hypothesis tests and do not add future scalar-response noise.

The 0.19 fixed-family target-wise and maxT-adjusted testing layer, complete-family global test, package construction, all 9 core cross-platform lanes, coverage/compile/Ruff gates, executable examples, strict documentation, GitHub Pages deployment, scikit-fda interoperability, and FDApy sparse/PACE interoperability on Python 3.11–3.12 are GitHub CI-certified on the exact merged 0.19 scientific lineage.



## 0.20 exact-main scientific qualification and deployment — 2026-09-22

Exact scientific main commit:

`3c8b3cb9f83bd78bcbcbe441b47034669f687072`

Version 0.20 adds finite-bootstrap Monte Carlo precision diagnostics for the 0.19 fixed-family Gaussian FPCR wild-bootstrap testing layer.

Scientific/numerical contract:

- target-wise, single-step maxT-adjusted, and complete-family global exceedance counts are reconstructed from the exact retained studentized-root matrix;
- raw exceedance fractions `r/B` are diagnostic quantities and do not replace the configured 0.19 plus-one/raw hypothesis-test p-values;
- plug-in Monte Carlo standard errors are reported alongside exact Clopper-Pearson binomial intervals, including `r=0` and `r=B` boundary cases;
- decision-stability diagnostics require the complete Monte Carlo interval to lie on the same side of alpha as the already reported 0.19 decision;
- no FPCA fit, score regression, residual calculation, multiplier draw, or bootstrap replicate is rerun;
- provenance distinguishes Monte Carlo simulation precision from scientific sampling uncertainty;
- no new strong-FWER, subset-pivotality, clustered-bootstrap, component-selection, or sequential-stopping guarantee is claimed.

Exact-main GitHub qualification on `3c8b3cb9f83bd78bcbcbe441b47034669f687072`:

- tests workflow #85: **success**;
- package job: **success**;
- Windows × Python 3.11, 3.12, 3.13: **3/3 success**;
- Ubuntu × Python 3.11, 3.12, 3.13: **3/3 success**;
- macOS × Python 3.11, 3.12, 3.13: **3/3 success**;
- representative macOS / Python 3.13 log: **172 passed, 5 skipped**, **92.52% coverage** against the unchanged 90% gate, and Ruff **All checks passed**;
- examples workflow #85: **success**, including the new Monte Carlo diagnostics example;
- docs workflow #85: **success**, including strict build and **successful GitHub Pages deployment**;
- optional-fda workflow #81: **success**;
- optional-sparse-fda workflow #69: **success**, with FDApy Python 3.11 and 3.12 both green.

No tests, coverage thresholds, workflows, branch protections, or scientific validation gates were weakened, disabled, deleted, or bypassed.

## 0.20 remaining re-checks

1. Reassess FDApy/Python 3.13 interoperability only when the FDApy/NumPy dependency line supports Python 3.13.
2. The Monte Carlo intervals quantify finite-resampling simulation precision only; they are not scientific-effect confidence intervals.
3. The diagnostics do not strengthen the 0.19 single-step maxT multiplicity claim or establish strong FWER for arbitrary subsets.
4. Clustered/repeated-participant wild-bootstrap inference remains outside the independent-curve contract.
5. k/g/h and other component-selection uncertainty remain outside the precision diagnostic.
6. Version 0.20 does not implement sequential/optional-stopping Monte Carlo testing; increasing B after inspecting results must be reported transparently.

The 0.20 Monte Carlo precision implementation, package construction, all 9 core cross-platform lanes, coverage/compile/Ruff gates, executable examples, strict documentation, GitHub Pages deployment, scikit-fda interoperability, and FDApy sparse/PACE interoperability on Python 3.11–3.12 are GitHub CI-certified on the exact scientific main commit above.


## 0.21 mathematical-contract and visual-site qualification — 2026-09-22

Version 0.21 makes the repository/site mathematical specification and visual documentation a tested package surface without changing the numerical estimators introduced through 0.20.

Exact CI-certified PR head:

\`36d046fe21542260451e9dc8308742a12fff54dc\`

PR #24, **“Add mathematical contracts and reproducible visual gallery,”** completed every unchanged pull-request qualification workflow successfully on that exact SHA:

- tests workflow #93: **success**, including package construction and all **9/9** Windows/Ubuntu/macOS × Python 3.11–3.13 lanes;
- representative macOS / Python 3.13 log: **172 passed, 5 skipped**, **92.52% coverage** against the unchanged 90% gate, and Ruff **All checks passed**;
- examples workflow #93: **success**, including the executable mathematical-contract example;
- docs workflow #93: **success** with deterministic gallery generation, documentation-contract validation, and strict MkDocs build;
- docs-contract audit reported **78 navigation targets**, **180 documented API symbols**, **5 generated gallery SVG assets**, and **7 validated mathematical deep links**;
- optional-fda workflow #89: **success**;
- optional-sparse-fda workflow #77: **success**, including FDApy Python 3.11 and 3.12.

The 0.21 documentation contract includes:

- repository-level \`MATHEMATICAL_CONTRACTS.md\` with GitHub-rendered LaTeX;
- an expanded site mathematical reference matching the implemented quadrature weighting, FPCA/MFPCA, reconstruction, functional L2 distance, multilevel decomposition, compositional ALR, landmark registration, simultaneous functional-mean inference, Gaussian FPCR, heteroscedastic wild bootstrap, max-|t| calibration, fixed-family testing, Monte Carlo precision, and split-conformal p-value calculations;
- a deterministic SVG gallery generated from the real public plotting APIs using seeded synthetic data, deterministic SVG hashing, and timestamp-free metadata;
- a MathJax instant-navigation hook that re-typesets equations after client-side navigation;
- stable explicit mathematical deep-link anchors checked by CI;
- homepage/tutorial/API/object/quickstart navigation linking methods, equations, examples, plots, and public APIs;
- documentation dependency bounds on the compatible Material-for-MkDocs 9.x / MkDocs 1.x line for this tranche.

No tests, coverage thresholds, scientific contracts, optional-backend checks, branch protections, or quality gates were weakened, disabled, deleted, or bypassed.

PR #24 was squash-merged as:

\`76da25c41d28f1c0c39c482df73f2ffb8fe54a0a\`

The exact PR head and squash-merged main commit both point to Git tree:

\`ffe3914017882e1bb1a9e91aaf6ff8ce5a2d65ac\`

so the merged package metadata, mathematical contracts, examples, workflows, gallery generator, site UX, and documentation checks are byte-for-byte identical to the exact CI-certified PR-head tree.

### 0.21 exact-main qualification and deployment — 2026-09-22

The exact merged-main commit

\`76da25c41d28f1c0c39c482df73f2ffb8fe54a0a\`

completed a fresh push-triggered qualification generation successfully:

- tests workflow #94: **success**, including package construction and all **9/9** Windows/Ubuntu/macOS × Python 3.11–3.13 lanes;
- examples workflow #94: **success**;
- docs workflow #94: **success**, including gallery regeneration, documentation-contract validation, strict MkDocs build, and **successful GitHub Pages deployment**;
- optional-fda workflow #90: **success**;
- optional-sparse-fda workflow #78: **success**, including FDApy Python 3.11 and 3.12.

Therefore 0.21 is both **PR-head CI-certified** and **exact-main requalified**, and the mathematical reference / reproducible visual gallery are deployed on the merged main lineage.

## 0.21 remaining re-checks

1. Reassess FDApy/Python 3.13 interoperability only when the FDApy/NumPy dependency line supports Python 3.13.
2. The Material-for-MkDocs 9.x / MkDocs 1.x documentation stack is intentionally pinned for this tranche; any future site-framework migration should be qualified independently and must not alter scientific/API contracts.
3. The mathematical reference documents the equations implemented by the package. It is not a claim that every underlying method is novel to eyetrajectoriespy; methodological attribution remains in the references/method guides.
4. Generated gallery figures use deterministic synthetic data for documentation and should not be interpreted as empirical study results.
5. A future documentation tranche may expand the gallery to additional optional-backend and uncertainty plots while preserving CI-small generation time.

The 0.21 mathematical contracts, reproducible gallery generator, documentation-contract validator, executable equations example, package construction, all 9 core cross-platform lanes, coverage/Ruff gates, strict documentation, GitHub Pages deployment, scikit-fda interoperability, and FDApy sparse/PACE interoperability on Python 3.11–3.12 are GitHub CI-certified on the exact merged 0.21 main lineage.
