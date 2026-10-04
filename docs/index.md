---
title: eyetrajectoriespy
hide:
  - navigation
  - toc
---

!!! success "Current stable release — 1.0.0"
    `eyetrajectoriespy 1.0.0` is the current stable production release and the compatibility baseline for the 1.x line.

    Python 3.11–3.13 · native sparse FPCA/PACE · native sparse planar MFPCA/joint PACE · production PyPI + GitHub Release

    ```bash
    pip install eyetrajectoriespy==1.0.0
    ```

    The frozen 1.0 boundary contains 455 stable public exports and three explicitly experimental APIs. Publication is complete and post-publication GitHub/PyPI readiness is disarmed.

<div class="et-hero" markdown>
<div markdown>

# Model the viewing process, not only its summaries

**Functional analysis of continuous and sparse eye-tracking trajectories in Python.**

$$
\mathbf G_i(t)=
\begin{bmatrix}
x_i(t)\\
y_i(t)
\end{bmatrix}.
$$

<span class="et-version-pill">stable 1.0.0 · Python 3.11–3.13</span>

[Get started](quickstart.md){ .md-button .md-button--primary }
[Choose a workflow](workflows/index.md){ .md-button }
[View on GitHub](https://github.com/stefanosbalaskas/eyetrajectoriespy){ .md-button }

</div>
<div markdown>

![Sparse planar covariance blocks estimated by eyetrajectoriespy](assets/gallery/sparse-mfpca-covariance-blocks.svg)

</div>
</div>

## Sparse planar workflow

<div class="grid cards" markdown>

-   **Sparse paired x/y gaze → native joint PACE**

    Estimate the full planar covariance structure, including directional cross-channel covariance:

    $$
    \mathbf C(s,t)=
    \begin{bmatrix}
    C_{xx}(s,t) & C_{xy}(s,t)\\
    C_{xy}(t,s) & C_{yy}(s,t)
    \end{bmatrix}.
    $$

    **API:** `fit_sparse_mfpca()`

    [→ Guide](guides/sparse-multivariate-fpca.md)
    · [Example](examples/sparse-mfpca.md)
    · [Mathematics](methods/mathematical-reference.md#sparse-mfpca-joint-pace)
    · [Validation](validation/sparse-mfpca-recovery.md)

</div>

## Choose the analysis, not the function name

<div class="grid cards" markdown>

-   **Continuous gaze + FPCA** — dominant modes of common-grid continuous gaze variation.  
    [→ Open workflow](workflows/fpca-exploration.md)

-   **Experimental functional regression** — time-varying effects of declared scalar predictors.  
    [→ Open workflow](workflows/experimental-functional-regression.md)

-   **Repeated-trial mixed effects** — preserve participant → trial → time hierarchy.  
    [→ Open workflow](workflows/repeated-trial-mixed-effects.md)

-   **Binary and count responses** — explicit Bernoulli, grouped-binomial and Poisson contracts.  
    [→ Open workflow](workflows/generalized-responses.md)

-   **Nonlinear and recurrence analysis** — explicit state representation, embedding and recurrence choices.  
    [→ Open workflow](workflows/nonlinear-recurrence.md)

</div>

## From gaze samples to a defensible result

| Stage | Scientific task | What stays explicit |
| --- | --- | --- |
| **Observe** | Native gaze, timing, metadata, missingness | sampling support and data loss |
| **Represent** | Dense, irregular, sparse, multilevel, compositional | representation and projection choices |
| **Model** | FPCA, regression, mixed effects, geometry, recurrence | estimand, family, hierarchy, parameters |
| **Validate** | Stability, diagnostics, sensitivity, uncertainty | resampling unit and qualification evidence |
| **Report** | Results, limitations, provenance | analytical decisions and scope boundaries |

## What eyetrajectoriespy refuses to hide

Missingness, smoothing, registration, irregular-to-grid projection, analysis support, sparse-model bandwidths, measurement-error assumptions, PSD policy, resampling units, denominator/exposure semantics, provenance, and failure/status codes remain explicit scientific choices.

!!! important "Not a replacement for event analysis"
    Whole-trajectory FDA answers different questions from fixation, saccade, AOI-transition, and latency analyses. eyetrajectoriespy complements those methods rather than replacing them.

## Scientific qualification

- [Release readiness](release-readiness.md) — qualification history and the current post-publication state.
- [Validation ledger](validation/reference-validation-ledger.md) — independent-reference and recovery evidence.
- [Visual gallery](methods/visual-gallery.md) — deterministic figures regenerated from package code.
- [Mathematical reference](methods/mathematical-reference.md) — implementation-matched equations and scope boundaries.
- [API stability policy](reference/api-stability.md) — the stable 1.x compatibility contract and deprecation rules.

---

**Current stable release:** `1.0.0` · [PyPI](https://pypi.org/project/eyetrajectoriespy/) · [1.0.0 release notes](releases/1.0.0.md) · [API stability policy](reference/api-stability.md)
