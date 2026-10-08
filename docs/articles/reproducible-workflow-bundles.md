---
title: Reproducible workflow bundles
---

# From a workflow to a reproducible analytical record

A 1.2 workflow result is a typed research object: it contains a primitive scientific fit, an explicit configuration, provenance for meaningful decisions, ordered execution steps, reports, tables and portable state. The workflow layer **does not** choose preprocessing or a scientific model on the analyst's behalf.

!!! info "Release boundary"
    The following `eyetrajectoriespy.workflows` API belongs to the **1.2 candidate source**. It is not available in the published 1.1.0 installation.

!!! warning "Installation prerequisite"
    The published `pip install eyetrajectoriespy` installs stable **1.1.0**, which does **not** include `run_*_workflow()`. All Python examples below require a **1.2 candidate source checkout**, not the published stable package.

## 1. Fit an explicitly configured example

```python
from eyetrajectoriespy import simulate_planar_trajectories
from eyetrajectoriespy.workflows import (
    FPCAWorkflowConfig,
    run_fpca_workflow,
)

gaze = simulate_planar_trajectories(
    n_participants=18,
    trials_per_participant=1,
    n_time=61,
    random_state=2201,
)
result = run_fpca_workflow(
    gaze,
    config=FPCAWorkflowConfig(n_components=2, scaling="dimension_sd"),
)
```

This is a deterministic synthetic input used to explain the software, **not** a participant study or ground-truth validation claim.

## 2. Inspect decisions and step records

```python
from eyetrajectoriespy.workflows import (
    workflow_decisions_frame,
    workflow_steps_frame,
    workflow_summary_frame,
    workflow_reporting_text,
)

print(workflow_summary_frame(result))
print(workflow_decisions_frame(result.decisions))
print(workflow_steps_frame(result.steps))
print(workflow_reporting_text(result))
```

The decision table distinguishes:

| Source | Interpretation |
| --- | --- |
| `analyst` | An explicitly supplied and scientifically relevant input |
| `audited_selector` | A named qualified selector with retained criterion |
| `workflow_contract` | A fixed property of the versioned workflow |
| `derived` | Calculated from declared inputs, **not** an additional analyst choice |

### Figures from the same audit records

![Decision provenance across synthetic workflow examples](../assets/gallery/workflow-audit-provenance.svg)

![Recorded order and completion statuses of synthetic FPCA workflow steps](../assets/gallery/workflow-audit-steps.svg)

The figures document provenance and ordering; they do not measure estimator quality or comparative speed. The scripts use the retained result objects rather than handwritten provenance categories.

## 3. Export reports, figures and portable state

```python
from eyetrajectoriespy.workflows import (
    export_workflow_bundle,
    save_workflow_figure,
)

save_workflow_figure(
    result,
    "fpca-component.svg",
    plot="fpca_component",
    component=0,
    dimension=gaze.dimension_names[0],
)
export_workflow_bundle(result, "my-analysis-bundle")
```

The figure's scientific plot type and coordinate are **explicit**. The bundle contains a serialized workflow/configuration record, provenance/environment, `steps.csv`, `decisions.csv`, portable scientific-result manifest/arrays, reports, tables and `SHA256SUMS`. Backend-native objects that cannot be represented portably are **not silently pickled**.

## 4. Audit what can—and cannot—be reproduced

Reproducibility checks should include the package and workflow schema/contract version, input definitions and preprocessing provenance, operating environment, outcome family, resampling/calibration units, failure/warning handling and the retained export checksums. The bundle does **not** by itself contain or validate access permissions for a restricted original dataset.

For real analyses, archive a legal/ethical provenance record for source data separately; do not use synthetic examples as a substitute for empirical validation.

## 5. Match the analysis claim to its evidence

A completed workflow demonstrates that its composed functions were executed and serialized under a declared contract. It does not show that fitted values are unbiased, that confidence regions cover at their nominal rate, or that a model is scientifically preferable. See [workflow product qualification](../validation/one-dot-two-workflow-product-qualification.md), [scientific methods and limits](../methods/limitations.md), and [reproducibility checklist](../reproducibility/checklist.md).
