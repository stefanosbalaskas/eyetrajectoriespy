# Workflow infrastructure API

Version `1.2.0.dev0` introduces infrastructure for transparent analysis workflows under the module-scoped namespace `eyetrajectoriespy.workflows`.

W1 deliberately does **not** add any `run_*_workflow()` scientific analysis function. It establishes the contracts that later workflow implementations must satisfy.

## Design boundary

A workflow is an explicitly configured composition of existing scientific primitives. It is not an auto-analysis engine.

The infrastructure therefore does not select a model family, infer paired versus asynchronous sampling, choose smoothing or bandwidth values, preprocess data, decide which diagnostics should run, divide participants into analysis roles, or rank competing scientific architectures.

Concrete workflows must retain those decisions as explicit configuration or explicit audited selector output. The workflow namespace remains module-scoped; W1 does not add names to the frozen package-root 1.x compatibility boundary.

## Versioned workflow identity

`WorkflowContract` gives every concrete workflow definition its own semantic version independent of the package version.

```python
from eyetrajectoriespy.workflows import WorkflowContract

contract = WorkflowContract(
    name="sparse_fpca",
    version=1,
    scientific_scope="Sparse FPCA orchestration",
    prohibitions=("no hidden bandwidth selection",),
)

assert contract.identifier == "sparse_fpca:v1"
```

The package-level `WORKFLOW_SCHEMA_VERSION` is currently `1`. A later change to the meaning or automatic composition of a workflow must be governed as a workflow-contract change even when underlying primitive functions remain API-compatible.

## Decision provenance

`WorkflowDecision` records how a consequential value entered the analysis:

```python
from eyetrajectoriespy.workflows import WorkflowDecision

decision = WorkflowDecision(
    value=0.36,
    source="select_sparse_fpca_bandwidths",
    criterion="participant_grouped_cv",
    details={"candidate_id": "candidate_0003"},
)
```

The intended provenance triple is `value`, `source`, and `criterion`. Analyst-declared values use a source such as `"analyst"`; automatically selected values identify the exact selector and criterion rather than appearing as unexplained scalar values.

## Ordered step audit

`WorkflowStepRecord` retains one record for each composed primitive call. Allowed status values are `"ok"`, `"skipped"`, and `"failed"`; warnings are retained explicitly. `workflow_steps_frame()` creates a compact ordered audit table without discarding the typed step objects.

## Explicit preprocessing plan

`PreprocessingPlan` and `PreprocessingStepConfig` record only preprocessing explicitly requested by the analyst. An empty plan means no preprocessing.

W1 does not execute preprocessing operations. Each future concrete workflow validates whether a requested operation is scientifically compatible with that workflow. In particular, future sparse PACE workflows must not silently interpolate raw sparse samples.

## Serialization contract

`workflow_config_dict()` and `workflow_provenance_dict()` convert typed workflow metadata to strict JSON-safe structures. Unsupported opaque values, non-finite floating-point values, and invalid mapping keys fail closed rather than being represented ambiguously.

## W1 public module API

::: eyetrajectoriespy.workflows.WorkflowContract
::: eyetrajectoriespy.workflows.WorkflowDecision
::: eyetrajectoriespy.workflows.WorkflowStepRecord
::: eyetrajectoriespy.workflows.PreprocessingStepConfig
::: eyetrajectoriespy.workflows.PreprocessingPlan
::: eyetrajectoriespy.workflows.workflow_config_dict
::: eyetrajectoriespy.workflows.workflow_provenance_dict
::: eyetrajectoriespy.workflows.workflow_steps_frame
::: eyetrajectoriespy.workflows.WorkflowBundleSnapshot
::: eyetrajectoriespy.workflows.export_workflow_bundle
::: eyetrajectoriespy.workflows.load_workflow_bundle

## What comes next

Issue #211 separates the workflow programme into W1-W4. W2 may begin only after W1 is qualified. The first scientific workflow should compose an already qualified analysis path rather than inventing new methodology, and its configuration must preserve all primitive scientific contracts.
