---
title: Choosing among ten functional gaze workflows
---

# Choosing among ten functional gaze workflows

The **observation design and scientific estimand come first**. A workflow is an audited composition of already-qualified methods; it does not decide on preprocessing, smoothing, family, conditional variance, response denominator, fixed effects, random effects or recurrence parameters without the analyst.

!!! info "Availability"
    These ten APIs are **1.2 release-candidate, module-scoped source functionality**. The current published stable distribution is **1.1.0**. The literal `1.2.0rc1` release candidate is not yet published.

## A ten-route comparison

| Workflow entry point | Appropriate data and question | What must remain explicit |
| --- | --- | --- |
| `run_sparse_fpca_workflow()` | One sparsely observed time-varying coordinate; population mean, covariance and PACE score reconstruction | Native sampling times, noise, bandwidth source, PSD and score failures |
| `run_sparse_mfpca_workflow()` | Paired sparse planar x/y observations; joint modes and cross-channel covariance | Shared paired support, both dimensions, smoothing, measurement error |
| `run_sparse_mfpca_async_workflow()` | x/y channels observed on different time grids | Channel-specific timestamps; **no hidden synchronization/interpolation** |
| `run_sparse_multilevel_workflow()` | Sparse participant/trial repeated functions | Participant/trial grouping, decomposition level, support and fitting assumptions |
| `run_sparse_prediction_workflow()` | Prediction from partial sparse histories | Proper training/calibration/target separation; prediction horizon and coverage scope |
| `run_fpca_workflow()` | Common-grid dense functional data; dominant directions of variation | Scaling, component rule and realized retained rank |
| `run_function_on_scalar_workflow()` | Continuous functional response and declared scalar predictors | Covariates, response dimension, independence/cluster assumption |
| `run_functional_mixed_effects_workflow()` | Repeated functional responses with participant/trial hierarchy | Fixed/random basis, covariance, serial dependence, optimizer, resampling unit |
| `run_generalized_functional_workflow()` | Binary, grouped-binomial or count functional responses | Response family, link, binomial denominators, Poisson exposure and units |
| `run_recurrence_workflow()` | Dynamical recurrence of one declared trajectory | State representation, embedding dimension, delay, radius, Theiler window, RQA line limits |

All routes are imported from `eyetrajectoriespy.workflows`, not the root package. See the [implementation guide](../workflows/workflow-orchestration.md) for the exact API contract and [product qualification](../validation/one-dot-two-workflow-product-qualification.md) for installed-wheel evidence.

## A practical decision sequence

1. **Check support:** is the raw observation actually common-grid, irregular-but-projectable, sparse paired x/y, or coordinate-specific asynchronous?
2. **Define the response:** continuous gaze position, derived function, partially observed future path, binary/count response, or delay-embedded trajectory?
3. **Respect hierarchy:** are curves independent, or are repeated trials nested within participants? Never treat every sample as a separate independent person.
4. **Declare scientific choices:** noise and bandwidth, FPC retention, covariates, random effects, family, denominator/exposure, calibration design or recurrence parameters.
5. **Match uncertainty to its target:** conditional sparse-score uncertainty is not full fitted-population uncertainty; grouped conformal coverage is not a per-person scientific guarantee; fixed-covariance bootstrap conditions on covariance estimates.
6. **Inspect failures and sensitivity:** retain observations rejected, steps skipped, numeric warnings, and alternative defensible predeclared specifications.

## Visual orientation

<div class="grid cards et-gallery" markdown>

- **Common-grid FPCA**

  ![Declared first component for synthetic FPCA workflow](../assets/gallery/workflow-fpca-component.svg)

  [Read FPCA interpretation](interpreting-workflow-figures.md)

- **Time-varying predictor effects**

  ![Synthetic function-on-scalar coefficient](../assets/gallery/workflow-function-on-scalar.svg)

  [Read regression interpretation](interpreting-workflow-figures.md)

- **Recurrence of reconstructed state**

  ![Synthetic recurrence plot](../assets/gallery/workflow-recurrence.svg)

  [Read recurrence interpretation](interpreting-workflow-figures.md)

</div>

## When not to use an orchestration route

- A native sparse PACE fit is **not** justified by dense curves with artificially removed samples merely to fit the sparse API.
- Asynchronous planar samples should **not** be silently paired at interpolated timestamps to force a paired route.
- Function-on-scalar regression without a repeated-measures model may not answer the scientific question when participant-specific functional effects are central.
- Recurrence plots are descriptive nonlinear-state representations; parameters matter, and visually structured diagonals are not evidence of causal influence.
- A workflow result is not an automatically validated causal or predictive claim.

!!! warning "Installation prerequisite"
    `pip install eyetrajectoriespy` installs the published stable **1.1.0** package; it **does not** expose `run_*_workflow()`. The runnable example below requires the **1.2 candidate source checkout**, which is not published on production PyPI.

## Minimal candidate-source illustration

```python
from eyetrajectoriespy import simulate_planar_trajectories
from eyetrajectoriespy.workflows import (
    FPCAWorkflowConfig,
    run_fpca_workflow,
    workflow_reporting_text,
    workflow_summary_frame,
)

trajectories = simulate_planar_trajectories(
    n_participants=18,
    trials_per_participant=1,
    n_time=61,
    random_state=2201,
)
result = run_fpca_workflow(
    trajectories,
    config=FPCAWorkflowConfig(
        n_components=2,
        scaling="dimension_sd",
    ),
)
print(workflow_reporting_text(result))
print(workflow_summary_frame(result))
```

The example is **synthetic** and mirrors the qualified 1.2 documentation gallery setup. It illustrates contract usage and audit output, not an estimator-recovery experiment. Continue to [bundle export](reproducible-workflow-bundles.md) before interpreting a substantive study.
