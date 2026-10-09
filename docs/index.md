---
title: eyetrajectoriespy
hide:
  - navigation
  - toc
---

!!! success "Published stable release — 1.1.0"
    **1.1.0** is the current published stable release (Python 3.11–3.13). It preserves the 1.0 root API compatibility boundary and adds qualified sparse/irregular capabilities as stable **module-scoped 1.1 APIs**.

    ```bash
    pip install eyetrajectoriespy==1.1.0
    ```

!!! info "1.2 development — experimental source, not a published release"
    W1–W4 and all ten workflow contracts have passed installed-wheel product qualification. Frozen source **1.2.0rc1** remains unpublished. E1–E4 experimental interfaces were merged to protected `main` as **1.2.0rc2.dev0** under [PR #223](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/223), but a new literal RC2 has **not** been qualified or published. Publication remains disarmed. A plain PyPI installation still gives **stable 1.1.0**, without the 1.2 workflow APIs.

<div class="et-hero" markdown>
<div markdown>

<!-- Protected-main experimental source version 1.2.0rc2.dev0; not a published release. -->

# Model the viewing process, not only its summaries

**Functional analysis of continuous, irregular and sparse eye-tracking trajectories in Python.**

Preserve the time-indexed planar gaze process rather than reducing every trial immediately to fixation counts:

$$
\mathbf G_i(t)=
\begin{bmatrix}
x_i(t)\\
y_i(t)
\end{bmatrix}.
$$

<span class="et-version-pill">Stable: 1.1.0 · Research development: 1.2 (unpublished) · Python 3.11–3.13</span>

[Install and get started](quickstart.md){ .md-button .md-button--primary }
[Choose an analysis](articles/choosing-the-ten-workflows.md){ .md-button }
[Research method finder](development/method-finder.md){ .md-button }
[Explore figures](methods/visual-gallery.md){ .md-button }

</div>
<div markdown>

![Native sparse planar covariance estimated from deterministic synthetic data](assets/gallery/sparse-mfpca-covariance-blocks.svg)

</div>
</div>

## See the methods

All plotted examples below use **deterministic synthetic data** and are regenerated from package code during the documentation build. They illustrate outputs and diagnostics, not human-subject findings.

<div class="grid cards et-gallery" markdown>

- **Functional principal components**

  ![FPCA workflow component](assets/gallery/workflow-fpca-component.svg)

  Visualize a declared component/dimension of common-grid gaze variation.

  [FPCA workflow](workflows/fpca-exploration.md) · [Interpret the plot](articles/interpreting-workflow-figures.md)

- **Time-varying experimental effect**

  ![Function-on-scalar coefficient](assets/gallery/workflow-function-on-scalar.svg)

  Inspect a declared predictor coefficient function over trial time.

  [Functional regression](workflows/experimental-functional-regression.md) · [Interpret the plot](articles/interpreting-workflow-figures.md)

- **Recurrence in state space**

  ![Fixed-parameter recurrence plot](assets/gallery/workflow-recurrence.svg)

  Display recurrence with analyst-declared embedding, lag, radius and Theiler window.

  [Recurrence workflow](workflows/nonlinear-recurrence.md) · [Interpret the plot](articles/interpreting-workflow-figures.md)

</div>

## The ten transparent workflows (1.2 candidate)

!!! warning "Candidate APIs are not installed by pip"
    The published stable `pip install eyetrajectoriespy` installs **1.1.0**, which does **not** include `run_sparse_mfpca_workflow()` or any other `run_*_workflow()` API. Those examples require the **1.2 candidate source**, not stable 1.1.


<div class="grid cards" markdown>

- **Five sparse routes**

  Native sparse FPCA/PACE, paired sparse planar MFPCA, asynchronous planar MFPCA, sparse multilevel decomposition, and partial-trajectory prediction.

  [Select a sparse route](articles/choosing-the-ten-workflows.md) · [Method validation](validation/one-dot-two-workflow-product-qualification.md)

- **Four dense/regression routes**

  Common-grid FPCA, function-on-scalar regression, functional mixed effects and generalized functional responses.

  [Compare assumptions](articles/choosing-the-ten-workflows.md) · [Workflow API](workflows/workflow-orchestration.md)

- **One recurrence route**

  Explicit state-space embedding, fixed-radius recurrence and RQA, with no automatic nonlinear-parameter tuning.

  [Recurrence guide](workflows/nonlinear-recurrence.md) · [Reporting decisions](articles/reproducible-workflow-bundles.md)

</div>

## Every analysis has an evidence trail

![Workflow audit decision provenance across deterministic examples](assets/gallery/workflow-audit-provenance.svg)

The audit layer distinguishes **analyst input**, **audited selectors**, **fixed workflow contracts** and **derived values**. Provenance counts above are descriptive illustrations of the candidate workflows, not comparative performance or methodological superiority.

[How to export an auditable bundle](articles/reproducible-workflow-bundles.md) · [Reproducibility checklist](reproducibility/checklist.md)

## Follow the scientific question

| Research aim | Default starting point | Main caveat |
|---|---|---|
| Dominant whole-path variation | [FPCA / MFPCA](workflows/fpca-exploration.md) | Component alignment and selection uncertainty |
| Sparse asynchronous x/y tracking | [Asynchronous MFPCA](guides/sparse-multivariate-async.md) | Preserve native coordinate-specific times |
| Effect of a condition over trial time | [Function-on-scalar regression](workflows/experimental-functional-regression.md) | Repeated-measures structure must be declared |
| Participant/trial heterogeneity | [Functional mixed effects](workflows/repeated-trial-mixed-effects.md) | Covariance and resampling assumptions |
| Binary or count functional outcome | [Generalized functional response](workflows/generalized-responses.md) | Explicit family, denominator or exposure |
| Temporal recurrence | [Recurrence/RQA](workflows/nonlinear-recurrence.md) | Strong dependence on embedding/threshold choices |

## Evidence before promotion

Scientific contracts, limitations, full qualification provenance, and a machine-checked public API boundary accompany the software. The [Bayesian B4 feasibility decision](articles/bayesian-feasibility-boundary.md) motivates a separate native research/design programme; it does **not** select a replacement estimator or make Bayesian inference a 1.2 production feature.

!!! important "Functional analysis complements event-based eye tracking"
    This package begins with a scientifically interpretable time/coordinate representation. It complements rather than replaces fixation, saccade, AOI-sequence, event detection and instrument-level QC workflows.

[Visual gallery](methods/visual-gallery.md) · [All workflows](workflows/index.md) · [Mathematical reference](methods/mathematical-reference.md) · [Public API](reference/api.md) · [GitHub repository](https://github.com/stefanosbalaskas/eyetrajectoriespy) · [PyPI](https://pypi.org/project/eyetrajectoriespy/)
