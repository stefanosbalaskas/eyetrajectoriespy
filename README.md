# eyetrajectoriespy

[![PyPI version](https://img.shields.io/pypi/v/eyetrajectoriespy.svg)](https://pypi.org/project/eyetrajectoriespy/)
[![GitHub Release](https://img.shields.io/github/v/release/stefanosbalaskas/eyetrajectoriespy)](https://github.com/stefanosbalaskas/eyetrajectoriespy/releases)
[![Python](https://img.shields.io/pypi/pyversions/eyetrajectoriespy.svg)](https://pypi.org/project/eyetrajectoriespy/)
[![Documentation](https://img.shields.io/badge/docs-GitHub%20Pages-blue)](https://stefanosbalaskas.github.io/eyetrajectoriespy/)

**Functional analysis of continuous and sparse eye-tracking trajectories in Python.**

Instead of immediately reducing gaze to fixation counts, dwell summaries, or symbolic scanpaths, `eyetrajectoriespy` treats gaze as a time-indexed functional process

$$
\mathbf G_i(t)=
\begin{bmatrix}
x_i(t)\\
y_i(t)
\end{bmatrix}.
$$

**Stable:** `1.1.0` · **Python:** 3.11–3.13

```bash
pip install eyetrajectoriespy
# exact reproducible stable release
pip install eyetrajectoriespy==1.1.0
```

[Documentation](https://stefanosbalaskas.github.io/eyetrajectoriespy/) ·
[Quick start](https://stefanosbalaskas.github.io/eyetrajectoriespy/quickstart/) ·
[Choose a workflow](https://stefanosbalaskas.github.io/eyetrajectoriespy/workflows/) ·
[Mathematics](https://stefanosbalaskas.github.io/eyetrajectoriespy/methods/mathematical-reference/) ·
[Visual gallery](https://stefanosbalaskas.github.io/eyetrajectoriespy/methods/visual-gallery/) ·
[Validation](https://stefanosbalaskas.github.io/eyetrajectoriespy/validation/reference-validation-ledger/)

> **Current stable release: `1.1.0`**  
> `1.1.0` is the exact-version-qualified final promotion of the production-observed `1.1.0rc1` surface. It preserves the frozen 1.0 root compatibility boundary while making the qualified 1.1 sparse/irregular additions stable module-scoped APIs. Final publication completed from exact protected-main arming commit `66cfb66798a90950e28401e45ee47e98543ff5c6`; immutable qualification, checksums, attestations, and publication provenance are retained in the [1.1.0 release notes](https://stefanosbalaskas.github.io/eyetrajectoriespy/releases/1.1.0/) and validation records.

![Sparse planar covariance structure estimated by eyetrajectoriespy](docs/assets/gallery/sparse-mfpca-covariance-blocks.svg)

## What can it model?

| Scientific object | Main route | Status |
|---|---|---|
| Dense/common-grid continuous x/y gaze | `fit_mfpca()` | stable 1.0 |
| Sparse/irregular single-coordinate gaze | `fit_sparse_fpca()` + PACE | stable 1.0 |
| Sparse/irregular paired planar x/y gaze | `fit_sparse_mfpca()` + joint PACE | stable 1.0 |
| Repeated participant/trial functions | functional mixed effects / multilevel FPCA | stable 1.0 |
| Conditional uncertainty for sparse PACE and joint PACE scores | `sparse_score_uncertainty` / `sparse_multivariate_score_uncertainty` | stable 1.1 module API |
| Audited sparse smoothing-bandwidth selection | `sparse_bandwidth_selection` / `sparse_multivariate_bandwidth_selection` | stable 1.1 module API |
| Candidate-sample observation-process diagnostics | `observation_process` | stable 1.1 module API |
| Sparse participant/trial hierarchical decomposition | `sparse_multilevel` | stable 1.1 module API |
| Coordinate-specific asynchronous sparse planar gaze | `sparse_multivariate_async` | stable 1.1 module API |
| Future/partially observed sparse trajectory prediction and participant-aware conformal bands | `sparse_partial_prediction` / `sparse_partial_conformal` | stable 1.1 module API |

The post-1.0 module-scoped APIs are documented in the [1.1 module API](https://stefanosbalaskas.github.io/eyetrajectoriespy/reference/one-dot-one-module-api/) and [integration audit](https://stefanosbalaskas.github.io/eyetrajectoriespy/reference/one-dot-one-integration-audit/). They remain intentionally module-scoped rather than root re-exports and are stable `1.1.0` functionality under the published final release.

## Which workflow do I need?

| Scientific question | Start here |
|---|---|
| What are the dominant modes of continuous gaze variation? | [Continuous gaze exploration + FPCA](https://stefanosbalaskas.github.io/eyetrajectoriespy/workflows/fpca-exploration/) |
| How does an experimental predictor change a continuous functional response? | [Experimental functional regression](https://stefanosbalaskas.github.io/eyetrajectoriespy/workflows/experimental-functional-regression/) |
| How do repeated participant trials affect functional inference? | [Repeated-trial functional mixed effects](https://stefanosbalaskas.github.io/eyetrajectoriespy/workflows/repeated-trial-mixed-effects/) |
| How do predictors change repeated binary or count functional responses? | [Generalized binary/count responses](https://stefanosbalaskas.github.io/eyetrajectoriespy/workflows/generalized-responses/) |
| Is recurrence or nonlinear temporal organization the scientific target? | [Nonlinear/recurrence analysis](https://stefanosbalaskas.github.io/eyetrajectoriespy/workflows/nonlinear-recurrence/) |

## Minimal dense/common-grid example

```python
from eyetrajectoriespy import fit_mfpca, simulate_planar_trajectories

gaze = simulate_planar_trajectories(
    n_participants=20,
    trials_per_participant=6,
    random_state=7,
)
fit = fit_mfpca(gaze, n_components=0.95, scaling="dimension_sd")
print(fit.explained_variance_ratio)
```

## Minimal sparse paired-planar example

```python
import numpy as np
from eyetrajectoriespy import fit_sparse_mfpca

fit = fit_sparse_mfpca(
    irregular,
    dimensions=("x", "y"),
    n_components=2,
    evaluation_grid=np.linspace(0.0, 1.0, 41),
    mean_bandwidth=0.20,
    covariance_bandwidth=0.30,
    measurement_error="diagonal",
    measurement_error_variance=(0.0025, 0.0025),
    psd_action="project",
    score_failure_action="retain_nan",
)
```

The sparse estimator uses native paired observations to estimate a joint population mean/covariance model. Evaluating fitted population functions at native times for PACE is **not** raw-trajectory interpolation.

## What eyetrajectoriespy refuses to hide

Consequential choices stay explicit: missingness, interpolation, smoothing, registration, time/coordinate normalization, analysis support, measurement-error assumptions, PSD policy, family/model selection, resampling unit, denominator/exposure semantics, and failure/status codes.

## Scope

`eyetrajectoriespy` starts once gaze has a scientifically interpretable time and coordinate representation. Event detection, general gaze QC, survival analysis, AOI perturbation robustness, and symbolic sequence models belong upstream or in specialist packages.

The package deliberately separates stable public methods, advanced diagnostics, external-backend interoperability, and experimental methods. Scientific product qualification matters more than estimator count.

## Where is the full advanced API?

The README is intentionally a compact entry point rather than the exhaustive function catalogue.

- [Capability inventory](https://stefanosbalaskas.github.io/eyetrajectoriespy/reference/capability-inventory/)
- [Public API](https://stefanosbalaskas.github.io/eyetrajectoriespy/reference/api/)
- [1.1 module-scoped API](https://stefanosbalaskas.github.io/eyetrajectoriespy/reference/one-dot-one-module-api/)
- [1.1 integration audit](https://stefanosbalaskas.github.io/eyetrajectoriespy/reference/one-dot-one-integration-audit/)
- [API stability and hierarchy](https://stefanosbalaskas.github.io/eyetrajectoriespy/reference/api-stability/)
- [Mathematical reference](https://stefanosbalaskas.github.io/eyetrajectoriespy/methods/mathematical-reference/)
- [Capability status and roadmap](https://stefanosbalaskas.github.io/eyetrajectoriespy/methods/status-roadmap/)
- [Reference validation & performance envelope](https://stefanosbalaskas.github.io/eyetrajectoriespy/validation/reference-validation-ledger/)

## Release lineage and reproducibility

The stable pre-1.0 sequence remains explicit: `0.10.0` introduced the native sparse univariate FPCA/PACE line, the immutable `0.11.0rc1` prerelease preceded final 0.11 known-truth recovery infrastructure, and `0.12.0` added the native sparse planar MFPCA/joint-PACE line. `1.0.0` froze the stable 1.x compatibility baseline. Published tags and distributions remain immutable historical records. The completed A1–C1 and R1–R5 programme progressed through immutable prerelease `1.1.0rc1`, production-installed observation, fresh final-version qualification, governance-only arming, and final `1.1.0` production publication.

- [Portable scientific results](https://stefanosbalaskas.github.io/eyetrajectoriespy/reproducibility/portable-results/)
- [Reproducibility bundle checklist](https://stefanosbalaskas.github.io/eyetrajectoriespy/reproducibility/checklist/)
- [Release process](https://stefanosbalaskas.github.io/eyetrajectoriespy/release-process/)

## Documentation and reproducibility

- [Sparse planar MFPCA / joint PACE guide](https://stefanosbalaskas.github.io/eyetrajectoriespy/guides/sparse-multivariate-fpca/)
- [Implementation-matched mathematical reference](https://stefanosbalaskas.github.io/eyetrajectoriespy/methods/mathematical-reference/)
- [Function → equation index](FUNCTION_EQUATION_INDEX.md)
- [Mathematical contracts](MATHEMATICAL_CONTRACTS.md)
- [Workflow atlas](WORKFLOW_ATLAS.md)
- [Current validation ledger](https://stefanosbalaskas.github.io/eyetrajectoriespy/validation/reference-validation-ledger/)
- [1.1.0 release notes](docs/releases/1.1.0.md)
- [1.1.0rc1 release notes](docs/releases/1.1.0rc1.md)
- [1.0.0 release notes](docs/releases/1.0.0.md)

Development checks:

```bash
python -m pytest --cov=eyetrajectoriespy
python -m compileall -q src
python scripts/generate_function_equation_index.py --check
python scripts/generate_docs_gallery.py
python scripts/generate_sparse_mfpca_docs_figure.py
python scripts/validate_docs_contracts.py
mkdocs build --strict
```

## Citation and license

See [`CITATION.cff`](CITATION.cff) for citation metadata. MIT © 2026 Stefanos Balaskas.
