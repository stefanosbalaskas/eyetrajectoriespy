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

**Stable:** `0.12.0` · **1.0 release candidate under qualification:** `1.0.0rc1` · **Python:** 3.11–3.13

```bash
pip install eyetrajectoriespy
# exact reproducible stable release
pip install eyetrajectoriespy==0.12.0
```

[Documentation](https://stefanosbalaskas.github.io/eyetrajectoriespy/) ·
[Quick start](https://stefanosbalaskas.github.io/eyetrajectoriespy/quickstart/) ·
[Choose a workflow](https://stefanosbalaskas.github.io/eyetrajectoriespy/workflows/) ·
[Mathematics](https://stefanosbalaskas.github.io/eyetrajectoriespy/methods/mathematical-reference/) ·
[Visual gallery](https://stefanosbalaskas.github.io/eyetrajectoriespy/methods/visual-gallery/) ·
[Validation](https://stefanosbalaskas.github.io/eyetrajectoriespy/validation/reference-validation-ledger/)

> **Current stable release: `0.12.0`**  
> `0.12.0` adds the qualified native sparse multivariate FPCA / joint-PACE workflow for jointly observed planar gaze. Release qualification, immutable hashes, OIDC/attestation evidence, and publication chronology are retained in the [0.12.0 release notes](https://stefanosbalaskas.github.io/eyetrajectoriespy/releases/0.12.0/) and validation records rather than repeated on this landing page.
>
> **1.0 release candidate under qualification: `1.0.0rc1`**  
> The candidate freezes the evidence-backed 1.0 API boundary without adding a new estimator or changing scientific behavior. Publication readiness remains disarmed until fresh exact-RC performance and the complete PR plus protected-main qualification matrices pass.

![Sparse planar covariance structure estimated by eyetrajectoriespy](docs/assets/gallery/sparse-mfpca-covariance-blocks.svg)

## What can it model?

| Scientific object | Main route |
|---|---|
| Dense/common-grid continuous x/y gaze | `fit_mfpca()` |
| Sparse/irregular single-coordinate gaze | `fit_sparse_fpca()` + PACE |
| Sparse/irregular paired planar x/y gaze | `fit_sparse_mfpca()` + joint PACE |
| Repeated participant/trial functions | functional mixed effects / multilevel FPCA |

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
- [API stability and hierarchy](https://stefanosbalaskas.github.io/eyetrajectoriespy/reference/api-stability/)
- [Mathematical reference](https://stefanosbalaskas.github.io/eyetrajectoriespy/methods/mathematical-reference/)
- [Capability status and roadmap](https://stefanosbalaskas.github.io/eyetrajectoriespy/methods/status-roadmap/)
- [Reference validation & performance envelope](https://stefanosbalaskas.github.io/eyetrajectoriespy/validation/reference-validation-ledger/)

## Release lineage and reproducibility

The stable pre-1.0 sequence remains explicit: `0.10.0` introduced the native sparse univariate FPCA/PACE line, the immutable `0.11.0rc1` prerelease preceded final 0.11 known-truth recovery infrastructure, and `0.12.0` added the native sparse planar MFPCA/joint-PACE line. Published tags and distributions remain immutable historical records.

- [Portable scientific results](https://stefanosbalaskas.github.io/eyetrajectoriespy/reproducibility/portable-results/)
- [Reproducibility bundle checklist](https://stefanosbalaskas.github.io/eyetrajectoriespy/reproducibility/checklist/)
- [Release process](https://stefanosbalaskas.github.io/eyetrajectoriespy/release-process/)

## Documentation and reproducibility

- [Sparse planar MFPCA / joint PACE guide](https://stefanosbalaskas.github.io/eyetrajectoriespy/guides/sparse-multivariate-fpca/)
- [Implementation-matched mathematical reference](https://stefanosbalaskas.github.io/eyetrajectoriespy/methods/mathematical-reference/)
- [Function → equation index](FUNCTION_EQUATION_INDEX.md)
- [Mathematical contracts](MATHEMATICAL_CONTRACTS.md)
- [Workflow atlas](WORKFLOW_ATLAS.md)
- [Validation ledger](VALIDATION.md)
- [0.12.0 release notes](docs/releases/0.12.0.md)

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
