# Validation status

This file records qualification evidence separately from implementation status. A missing hosted check is never treated as a code pass or code failure.

## Current development target

- Package line: `0.3.0.dev0`
- Scientific scope: continuous functional gaze trajectories, FPCA/MFPCA, irregular trajectories, stability, phase/registration, compositional FPCA, and functional anomaly/influence diagnostics.
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

## Locally unavailable checks

These are **pending**, not passed:

- Ruff: local runner does not have `ruff` installed and has no network access.
- Strict MkDocs build: `mkdocs`/Material/mkdocstrings are not installed locally and cannot be installed without network access.
- Twine validation: `twine` is not installed locally.
- Optional `scikit-fda` runtime tests and examples: dependency is not installed locally.
- Python 3.11 and 3.12 local tests: only Python 3.13.5 is available in the runner.

## GitHub CI certification

The 0.1 merged release tranche was previously GitHub CI-certified.

The current 0.2/0.3 development tranches are **not fully GitHub CI-certified**. Hosted Actions are currently unavailable because the monthly Actions allowance is exhausted; queued workflows therefore do not constitute pass/fail evidence.

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

Do not describe the 0.2/0.3 line as fully CI-certified until these workflows actually execute successfully.
