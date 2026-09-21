# Validation status

This file records qualification evidence separately from implementation status. A missing hosted check is never treated as a code pass or code failure.

## Current development target

- Package line: `0.8.0.dev0`
- Scientific scope: continuous functional gaze trajectories, FPCA/MFPCA, native and genuinely sparse irregular trajectories, optional FDApy/PACE interoperability, simultaneous observed-grid functional mean inference, stability, leakage-aware reconstruction and outcome-tuned predictive component selection, descriptive FPC-shape uncertainty, eigengap/principal-angle subspace stability, phase/registration, compositional FPCA, and functional anomaly/influence diagnostics.
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
