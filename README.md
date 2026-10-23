# eyetrajectoriespy

[![PyPI](https://img.shields.io/pypi/v/eyetrajectoriespy.svg)](https://pypi.org/project/eyetrajectoriespy/)
[![Python](https://img.shields.io/pypi/pyversions/eyetrajectoriespy.svg)](https://pypi.org/project/eyetrajectoriespy/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Documentation](https://img.shields.io/badge/docs-scientific%20site-4f46e5.svg)](https://stefanosbalaskas.github.io/eyetrajectoriespy/)

**Functional analysis of continuous, sparse and irregular eye-tracking trajectories in Python.**

Instead of reducing every trial immediately to fixation counts, dwell times or a symbolic scanpath, `eyetrajectoriespy` models gaze as a time-indexed planar process `G(t) = [x(t), y(t)]`, with explicit observation and scientific-inference contracts.

![Illustrative gaze trajectory, time representation and scientific analysis](docs/assets/site/hero-trajectories.svg)

> **Published stable:** `1.1.0` · Python 3.11–3.13.  
> **Unpublished development:** `1.2.0rc2.dev0` source—not a separately qualified and published literal RC2. Frozen `1.2.0rc1` was qualified but remains unpublished. The ten `run_*_workflow()` orchestration routes are **not present in stable 1.1.0**. **1.2 GitHub Release/PyPI remains on HOLD.**

[**Documentation**](https://stefanosbalaskas.github.io/eyetrajectoriespy/) · [Start here](https://stefanosbalaskas.github.io/eyetrajectoriespy/start/) · [Choose a workflow](https://stefanosbalaskas.github.io/eyetrajectoriespy/workflows/) · [Figure atlas](https://stefanosbalaskas.github.io/eyetrajectoriespy/figures/) · [Research evidence](https://stefanosbalaskas.github.io/eyetrajectoriespy/research/) · [News](https://stefanosbalaskas.github.io/eyetrajectoriespy/news/) · [Release status](https://stefanosbalaskas.github.io/eyetrajectoriespy/news/release-status/)

## Install stable 1.1.0

```bash
pip install eyetrajectoriespy==1.1.0
```

```python
from eyetrajectoriespy import fit_mfpca, simulate_planar_trajectories

gaze = simulate_planar_trajectories(
    n_participants=20, trials_per_participant=6, random_state=7,
)
fit = fit_mfpca(gaze, n_components=0.95, scaling="dimension_sd")
print(fit.explained_variance_ratio)
```

This illustration uses **deterministic synthetic data**, not human-subject observations. For complete sparse examples, use the [paired planar sparse guide](https://stefanosbalaskas.github.io/eyetrajectoriespy/guides/sparse-multivariate-fpca/).

## What do you want to analyze?

| Question | Method family | Guide |
| --- | --- | --- |
| Dominant variation across x/y paths | FPCA / planar MFPCA | [Continuous FPCA](https://stefanosbalaskas.github.io/eyetrajectoriespy/workflows/fpca-exploration/) |
| Irregular and sparsely observed gaze | Sparse FPCA/PACE, joint PACE | [Sparse planar gaze](https://stefanosbalaskas.github.io/eyetrajectoriespy/guides/sparse-multivariate-fpca/) |
| Coordinate-asynchronous x/y samples | Sparse asynchronous multivariate | [Qualified 1.1 module APIs](https://stefanosbalaskas.github.io/eyetrajectoriespy/reference/one-dot-one-module-api/) |
| Time-varying condition effects | Function-on-scalar regression | [Functional regression](https://stefanosbalaskas.github.io/eyetrajectoriespy/workflows/experimental-functional-regression/) |
| Repeated participant/trial outcomes | Functional mixed effects / multilevel | [Repeated-trial models](https://stefanosbalaskas.github.io/eyetrajectoriespy/workflows/repeated-trial-mixed-effects/) |
| Temporal recurrence and dynamics | Recurrence / RQA | [Nonlinear analysis](https://stefanosbalaskas.github.io/eyetrajectoriespy/workflows/nonlinear-recurrence/) |

## Product and research qualification

| Surface | State |
| --- | --- |
| Frozen 1.0 root API compatibility boundary | **Stable** |
| Qualified 1.1 sparse/irregular module-scoped additions | **Stable 1.1.0** |
| Ten transparent `eyetrajectoriespy.workflows` orchestration routes | **Unpublished 1.2 candidate** |
| W3 nominal-90% whole-function inference | **Not generally calibrated** — [#289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289) |
| Outcome-dependent missing gaze and selective validation | **Not field-identified** — [#296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296) |
| 1.2 GitHub Release / PyPI promotion | **Disarmed / HOLD** |

A successful synthetic benchmark or independent artifact replay is **not the same** as calibrated statistical inference or production release qualification. [Read the scientific evidence guide](https://stefanosbalaskas.github.io/eyetrajectoriespy/articles/evidence-vs-qualification/).

## Research news, figures and reproducibility

The W3 R76–R95 programme has published documentation of influential-unit, covariance, missingness, external-validation and identifiability experiments, including negative results. The [scientific study map](https://stefanosbalaskas.github.io/eyetrajectoriespy/research/studies/) links original papers; the [figure atlas](https://stefanosbalaskas.github.io/eyetrajectoriespy/figures/) includes source-derived synthetic plots. The [R93](https://stefanosbalaskas.github.io/eyetrajectoriespy/articles/w3-r93-exact-observed-law-nonidentification/), [R94](https://stefanosbalaskas.github.io/eyetrajectoriespy/articles/w3-r94-external-audit-completion-bounds/) and [R95](https://stefanosbalaskas.github.io/eyetrajectoriespy/articles/w3-r95-monotone-audit-return-identification/) sharp-set proofs are conditional population mathematics—not confidence intervals or real-gaze MNAR corrections.

[October 2026 news](https://stefanosbalaskas.github.io/eyetrajectoriespy/news/2026-10-23/) · [Original and independent evidence](https://stefanosbalaskas.github.io/eyetrajectoriespy/development/research-development-hub/) · [Validation ledger](https://stefanosbalaskas.github.io/eyetrajectoriespy/validation/reference-validation-ledger/)

## Documentation and contribution

[Quick start](https://stefanosbalaskas.github.io/eyetrajectoriespy/quickstart/) · [Input schemas](https://stefanosbalaskas.github.io/eyetrajectoriespy/guides/input-schemas/) · [Mathematics](https://stefanosbalaskas.github.io/eyetrajectoriespy/methods/mathematical-reference/) · [Visual gallery](https://stefanosbalaskas.github.io/eyetrajectoriespy/methods/visual-gallery/) · [Reproducibility guide](https://stefanosbalaskas.github.io/eyetrajectoriespy/development/research-reproducibility/) · [Contributing](CONTRIBUTING.md) · [Cite](CITATION.cff)

The package complements, rather than replaces, upstream fixation/saccade detection, instrument quality control, AOI event analysis and symbolic scanpath pipelines. MIT © 2026 Stefanos Balaskas.
