# Transparent workflow orchestration in 1.2

Version 1.2 introduces a typed orchestration layer under
`eyetrajectoriespy.workflows`. The workflow layer composes already-qualified
scientific primitives; it is not an auto-analysis system and does not replace
the underlying `fit_*`, diagnostic, reporting or plotting functions.

The governing rule is:

`workflow = explicit decisions + ordered composition + reporting + provenance`.

## Import surface

Workflow APIs remain module-scoped in the 1.2 release candidate:

~~~python
from eyetrajectoriespy.workflows import (
    FPCAWorkflowConfig,
    run_fpca_workflow,
)
~~~

They are deliberately not promoted into the package root. This keeps the
existing stable root namespace unchanged while giving the workflow layer its own
auditable versioned contract.

## Available workflows

The 1.2 candidate surface contains ten orchestration entry points:

| Route | Workflow |
|---|---|
| sparse univariate FPCA/PACE | `run_sparse_fpca_workflow()` |
| paired sparse planar MFPCA | `run_sparse_mfpca_workflow()` |
| asynchronous sparse planar MFPCA | `run_sparse_mfpca_async_workflow()` |
| sparse participant/trial decomposition | `run_sparse_multilevel_workflow()` |
| sparse partial-trajectory prediction | `run_sparse_prediction_workflow()` |
| common-grid FPCA | `run_fpca_workflow()` |
| observed-grid function-on-scalar regression | `run_function_on_scalar_workflow()` |
| Gaussian functional mixed effects | `run_functional_mixed_effects_workflow()` |
| generalized functional regression | `run_generalized_functional_workflow()` |
| delay-embedded recurrence/RQA | `run_recurrence_workflow()` |

Every workflow returns a frozen typed result retaining the primitive scientific
result object, ordered `WorkflowStepRecord` values, decision provenance,
manuscript-oriented reports and tidy tables.

## No hidden preprocessing

A `PreprocessingPlan` is always explicit and ordered. In the current 1.2
candidate, the scientific workflows require an empty plan because no generic
transformation executor has been qualified.

This is intentional. Interpolation, smoothing, registration, resampling,
normalization and coordinate transforms can change the estimand or observation
model. Perform them explicitly upstream with the relevant package API and
retain their provenance before starting a workflow.

## Sparse routes

Sparse FPCA and paired sparse MFPCA allow exactly one bandwidth source:
analyst-specified fixed values or the existing audited selector configuration.
The asynchronous and multilevel routes do not expose selectors that have not
been independently qualified.

Sparse prediction requires separate proper-training, calibration and target
inputs. No random role split is performed by the workflow.

## Dense and regression routes

The dense FPCA workflow records the requested component rule and the realized
retained rank separately. Function-on-scalar regression never infers a
mixed-effects model. The mixed-effects workflow keeps basis dimensions,
random-effect structure, residual correlation, REML/ML choice and optimizer
explicit.

The generalized workflow requires `family`; it does not infer a response
family. Grouped-binomial denominators, Poisson exposures and exposure units
remain separate analyst-declared inputs.

## Recurrence workflow

The W4 recurrence route makes the main recurrence specification explicit:

~~~python
from eyetrajectoriespy.workflows import (
    RecurrenceWorkflowConfig,
    run_recurrence_workflow,
)

result = run_recurrence_workflow(
    trajectories,
    config=RecurrenceWorkflowConfig(
        curve="P01|1",
        dimensions=("x", "y"),
        embedding_dimension=2,  # m
        delay=2,                # tau
        radius=0.12,            # epsilon
        theiler_window=2,
        min_diagonal_length=2,
        min_vertical_length=2,
    ),
)
~~~

The workflow performs delay embedding, fixed-radius recurrence construction and
RQA in that order. It does **not** select the embedding dimension (m), delay (tau), recurrence radius (epsilon), the
Theiler window or line thresholds. Use the existing diagnostic and sensitivity
APIs when several specifications are scientifically defensible.

## Reporting and audit frames

~~~python
from eyetrajectoriespy.workflows import (
    workflow_decisions_frame,
    workflow_reporting_text,
    workflow_steps_frame,
    workflow_summary_frame,
)

print(workflow_reporting_text(result))
print(workflow_summary_frame(result))
print(workflow_steps_frame(result.steps))
print(workflow_decisions_frame(result.decisions))
~~~

Decision records distinguish `analyst`, `audited_selector`,
`workflow_contract` and `derived` sources. A derived value is never
relabeled as an analyst choice.

## Workflow figures

Workflow plotting is also explicit:

~~~python
from eyetrajectoriespy.workflows import plot_workflow_result

ax = plot_workflow_result(
    fpca_workflow,
    plot="fpca_component",
    component=0,
    dimension="x",
)
~~~

The dispatcher delegates to canonical package plotting functions. It does not
choose a component, coefficient, dimension or plot type automatically. Routes
without a qualified canonical workflow plot fail explicitly rather than
receiving an invented substitute.

![Workflow FPCA figure](../assets/gallery/workflow-fpca-component.svg)

![Workflow recurrence figure](../assets/gallery/workflow-recurrence.svg)

## Reproducibility bundles

~~~python
from eyetrajectoriespy.workflows import export_workflow_bundle

export_workflow_bundle(result, "analysis-bundle")
~~~

A workflow bundle retains configuration, decisions, ordered steps, provenance,
environment metadata, portable scientific state, reports, tables and SHA-256
checksums. Opaque backend-native fields are marked explicitly by the portable
result layer rather than silently serialized with pickle.

## Stability boundary

The machine-readable candidate boundary is stored in
`WORKFLOW_API_AUDIT.json` and checked by
`scripts/validate_workflow_api_audit.py`. For 1.2, the workflow layer remains
module-scoped and does not expand the established package-root API.
