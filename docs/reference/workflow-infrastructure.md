---
title: Workflow infrastructure
---

# Workflow infrastructure

`eyetrajectoriespy.workflows` provides the completed candidate 1.2 orchestration foundation. The initial **W1 infrastructure tranche** introduced typed contracts without scientific estimators; W2–W4 subsequently added ten module-scoped composed workflows, canonical plot dispatch and installed-wheel product qualification. The published stable release remains 1.1.0 while the literal 1.2.0rc1 undergoes qualification.

## Design rule

A workflow is an explicitly configured scientific analysis chain:

```text
explicit decisions
→ ordered composition
→ diagnostics
→ inference
→ reporting
→ provenance
```

It is not an automatic system that guesses scientifically consequential choices.

## Shared records

`WorkflowDecisionRecord` retains a scientific value together with how it entered the workflow:

- `analyst` — explicitly supplied by the analyst;
- `audited_selector` — produced by a named qualified selection procedure and accompanied by its criterion;
- `workflow_contract` — fixed by the versioned workflow contract rather than inferred from data; or
- `derived` — mechanically derived from already declared inputs.

`WorkflowStepRecord` retains the ordered function call, status, parameters, elapsed time and warnings for one orchestration step.

`workflow_steps_frame()`, `workflow_decisions_frame()` and `workflow_summary_frame()` provide stable tabular audit surfaces without flattening the underlying scientific result objects.

## Preprocessing

`PreprocessingPlan` contains an ordered tuple of `PreprocessingStepConfig` objects. The empty plan means no preprocessing.

W1 deliberately defines no default interpolation, smoothing, normalization, resampling or registration chain. Every requested transformation must be named, parameterized and accompanied by a short statement of its scientific effect. Concrete W2+ workflows must additionally reject route-specific incompatible operations, such as hidden raw interpolation before native sparse PACE analysis.

## Stable workflow identity

Every concrete workflow result must retain:

- `workflow_schema_version`;
- a named `workflow_contract` such as `sparse_fpca:v1`;
- the frozen/typed config;
- ordered step records;
- decision provenance; and
- workflow provenance.

The schema/version pair exists because adding a new diagnostic or step can change the meaning of an orchestration pipeline even when all primitive estimators remain stable.

## Bundle export

`export_workflow_bundle()` writes an auditable directory containing:

```text
workflow.json
config.json
provenance.json
environment.json
steps.csv
decisions.csv

result/
    manifest.json
    arrays.npz

reports/
tables/

SHA256SUMS
```

The nested `result/` directory uses the existing portable scientific-result contract. Unsupported backend-native objects therefore remain explicit rather than being silently serialized.

Figure export was intentionally **outside W1**. W4 subsequently qualified explicit workflow plot dispatch (`plot_workflow_result()` and `save_workflow_figure()`) over canonical plotting functions, without guessing which scientific plot is appropriate.

## Public-surface boundary

W1 remains module-scoped:

```python
from eyetrajectoriespy.workflows import (
    WorkflowDecisionRecord,
    WorkflowStepRecord,
    PreprocessingPlan,
    PreprocessingStepConfig,
    export_workflow_bundle,
)
```

These names are not mechanically added to the frozen 1.0 package-root export boundary. The completed 1.2 candidate retains all ten scientific workflows **module-scoped**, as machine-checked in `WORKFLOW_API_AUDIT.json`; no root export promotion was authorized.
