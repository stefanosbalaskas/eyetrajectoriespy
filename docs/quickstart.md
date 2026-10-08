# Quick start — three complete 1.2 workflows

!!! warning "Unpublished development API"
    **1.1.0** remains the published stable PyPI release. The `eyetrajectoriespy.workflows` orchestrators shown here require the reviewed **1.2 development source** until a separately qualified RC is published. They are not available in the stable 1.1 wheel. The extensive original Quick start remains preserved in [advanced recipes](tutorials/advanced-recipes.md).

Install the 1.2 development checkout with `python -m pip install -e ".[dev]"`. Then run one of the three **complete, independently executable Python files**, each using seeded *synthetic teaching data*, not empirical observations:

| Start with | Run | Output |
|---|---|---|
| Common-grid x/y gaze | `python examples/quickstart_dense_fpca.py` | Component figure, configuration/report text, summary CSV |
| Jointly sampled sparse x/y | `python examples/quickstart_sparse_planar.py` | Observed-support figure, sparse joint fit, summary CSV |
| Independent trajectories and predictor | `python examples/quickstart_functional_regression.py` | Coefficient figure, regression report, summary CSV |

Outputs are saved under `build/quickstarts/`. Each script declares the data representation, model parameters, plot selector and export location explicitly. The [ten-workflow decision guide](articles/choosing-the-ten-workflows.md) explains how to choose the right route; these examples are about execution.

## 1. Common-grid FPCA

```python
from eyetrajectoriespy import simulate_planar_trajectories
from eyetrajectoriespy.workflows import (
    FPCAWorkflowConfig, run_fpca_workflow, plot_workflow_result,
    workflow_summary_frame, workflow_reporting_text,
)
gaze = simulate_planar_trajectories(
    n_participants=16, trials_per_participant=2, n_time=41, random_state=1201
)
result = run_fpca_workflow(
    gaze, config=FPCAWorkflowConfig(n_components=2, scaling="dimension_sd")
)
print(workflow_summary_frame(result))
print(workflow_reporting_text(result))
ax = plot_workflow_result(result, plot="fpca_component", component=0, dimension="x")
ax.figure.savefig("fpca-component-x.svg")
```

**Interpretation:** the component is a mode of observed variability, not a validated psychological construct. Report coordinate units, time support, number of curves and clustering when real samples are used. The [complete runnable script](https://github.com/stefanosbalaskas/eyetrajectoriespy/blob/feature/1-2-real-data-usability-onboarding/examples/quickstart_dense_fpca.py) includes CSV/report exports.

## 2. Paired sparse planar FPCA

Keep genuinely irregular x/y observation times native. The [executable sparse example](https://github.com/stefanosbalaskas/eyetrajectoriespy/blob/feature/1-2-real-data-usability-onboarding/examples/quickstart_sparse_planar.py) builds a typed `IrregularTrajectorySet` and calls `run_sparse_mfpca_workflow()` with declared evaluation grid, mean/covariance bandwidths and measurement-error model. Its support figure plots the **actual recorded sample positions of the teaching fixture**, without manufacturing a dense raw trajectory.

**Interpretation:** a sparse joint covariance model estimates modes of x/y variation; it is not the same as two independently fitted univariate models. Different timestamps per channel need the separate asynchronous workflow.

## 3. Functional regression

The [executable regression example](https://github.com/stefanosbalaskas/eyetrajectoriespy/blob/feature/1-2-real-data-usability-onboarding/examples/quickstart_functional_regression.py) constructs one independent functional response per participant, explicitly aligns `curve_id` with a scalar condition table and fits `run_function_on_scalar_workflow()`. It saves a condition coefficient curve, the reporting text and a summary CSV.

**Interpretation:** a coefficient function describes a declared design association; a picture alone is not an inferential test. If the same participant contributes repeated trials with a trial-varying predictor, use [functional mixed effects](workflows/repeated-trial-mixed-effects.md) rather than silently treating curves as independent.

## 4. Bring your own data

Begin with [input schema and import examples](guides/input-schemas.md) for common-grid, paired sparse, asynchronous sparse and repeated-trial structures. Preserve participant/trial IDs, time and coordinate units, observation masks and source processing flags.

For a source-pinned *authentic* eye-tracking run using E1–E4, see the [real-gaze usability case](articles/real-gaze-usability.md). It assesses execution and auditability, not known-truth estimator recovery.

Explore [advanced recipes](tutorials/advanced-recipes.md), [E1–E4 candidate orchestration](workflows/experimental-expansion.md) or the [visual gallery](methods/visual-gallery.md) after choosing your route.
