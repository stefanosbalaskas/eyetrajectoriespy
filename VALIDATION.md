# Validation status

This file records qualification evidence separately from implementation status. A missing hosted check is never treated as a code pass or code failure.

## Current development target

- Package line: `0.5.0.dev0`
- Scientific scope: continuous functional gaze trajectories, FPCA/MFPCA, irregular trajectories, stability, leakage-aware component selection, descriptive FPC-shape uncertainty, eigengap/principal-angle subspace stability, phase/registration, compositional FPCA, and functional anomaly/influence diagnostics.
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
- Version metadata: package `__version__` and `pyproject.toml` both report **0.5.0.dev0**; `CITATION.cff` software version is **0.5.0.dev0** with release date 2026-09-19.
- The examples workflow includes `examples/fpca_subspace_stability.py`.
- Public API regression test includes the new subspace result objects and functions.

## Locally unavailable checks

These are **pending**, not passed:

- Ruff: local runner does not have `ruff` installed and has no network access.
- Strict MkDocs build: `mkdocs`/Material/mkdocstrings are not installed locally and cannot be installed without network access.
- Twine validation: `twine` is not installed locally.
- Optional `scikit-fda` runtime tests and examples: dependency is not installed locally.
- Python 3.11 and 3.12 local tests: only Python 3.13.5 is available in the runner.

## GitHub CI certification

The 0.1 merged release tranche was previously GitHub CI-certified.

The merged 0.2/0.3/0.4 tranches and the current 0.5 development tranche are **not fully GitHub CI-certified**. Hosted Actions are currently unavailable because the monthly Actions allowance is exhausted; queued workflows therefore do not constitute pass/fail evidence.

## Re-check when GitHub Actions becomes available

Run and require success for:

1. Windows × Python 3.11, 3.12, 3.13.
2. Ubuntu × Python 3.11, 3.12, 3.13.
3. macOS × Python 3.11, 3.12, 3.13.
4. Full pytest coverage gate.
5. Ruff and compile checks.
6. Package sdist/wheel build and Twine validation.
7. All core examples.
8. Optional `scikit-fda` tests and basis/outlier examples.
9. Strict MkDocs build.
10. GitHub Pages deployment from the exact merged `main` SHA.

Do not describe the 0.2/0.3/0.4/0.5 line as fully CI-certified until these workflows actually execute successfully.
