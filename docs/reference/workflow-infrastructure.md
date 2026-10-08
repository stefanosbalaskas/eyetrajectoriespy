---
title: Workflow infrastructure
---

# Workflow infrastructure

`eyetrajectoriespy.workflows` is the feature-frozen orchestration surface for the `1.2.0rc1` release-candidate line.

The W1 contract is intentionally infrastructure-only. It does not add a `run_*_workflow()` scientific analysis function, introduce a new estimator, or alter the qualified scientific defaults.

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

Figure export is intentionally not part of W1. Workflow-level plotting and figure-bundle qualification belong to the later gallery/product tranche so W1 does not silently introduce backend-specific figure serialization.

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

These names are not mechanically added to the frozen 1.0 package-root export boundary. Promotion of concrete workflow APIs is a separate 1.2 public-surface decision under issue #209.
