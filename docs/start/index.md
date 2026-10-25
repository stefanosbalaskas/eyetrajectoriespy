---
title: Start here
description: Choose a stable eyetrajectoriespy analysis route and find installation, data schemas and worked examples.
---

# Start here

**From continuous gaze data to a defensible functional analysis.** Published `eyetrajectoriespy==1.2.0` supports continuous, sparse and irregular methods, plus ten stable module-scoped W1–W4 orchestration routes. Separate E1–E4 helpers remain experimental.

<div class="grid cards" markdown>

- **Install stable 1.2.0**

  `pip install eyetrajectoriespy==1.2.0`

  [Quick start](../quickstart.md) · [Stable API](../reference/api.md)

- **Understand your data**

  Choose common-grid, paired sparse, asynchronous coordinate-specific or repeated-trial representation **before** model fitting.

  [Data-to-method guide](data-to-method.md) · [Input schemas](../guides/input-schemas.md) · [Representation guide](../concepts/representations.md)

- **Choose a scientific method**

  FPCA/MFPCA, functional regression, repeated effects, generalized responses or recurrence.

  [Decision map](../concepts/decision-map.md) · [Methods](../methods/index.md)

- **Learn through examples**

  Inspect deterministic synthetic illustrations and the assumptions behind every plot.

  [Visual gallery](../methods/visual-gallery.md) · [Tutorials](../tutorials/index.md)

</div>

## Practical interactive tools

[Local CSV structure inspector](../tools/data-readiness.md){ .md-button .md-button--primary } — check long-format columns, time support and repeated-trial structure before import. It does not impute gaze or diagnose a missingness mechanism.


[Choose a starting method](../tools/method-selector.md){ .md-button .md-button--primary }
[Compare ten workflows](../tools/workflow-comparison.md){ .md-button }
[Run a small synthetic CSV](../tutorials/reproducible-starter.md){ .md-button }

The selector is guidance, not automated model validation. The downloadable teaching fixture is not empirical gaze or calibrated uncertainty.

## Connect other Python eye-tracking packages

The [integration hub](../integrations/index.md) compares pymovements, PyNeon, Polars, Pandera, eyekit, PupEyes, Eye-Tracking-BIDS and existing functional-data extras. Start with the [optional, fail-closed table example](../integrations/tabular-handoff.md) only after recording true column mapping, time and coordinate units.

## Three questions before any fit

1. **Observation unit** — independent curve, participant, trial or repeated participant cluster?
2. **Time representation** — aligned common grid or irregular/asynchronous native samples?
3. **Uncertainty target** — descriptive variation, prediction, pointwise effect or simultaneous functional inference? Not all targets are qualified.

The [scientific contracts](../concepts/contracts.md) document when an analysis refuses to proceed. The [research evidence library](../research/index.md) documents important experimental failures rather than hiding them.

## What is actually available?

| Surface | Today | Where to read |
| --- | --- | --- |
| Stable package | Published **1.2.0**, Python 3.11–3.13 | [Stable release](../releases/1.2.0.md) |
| Sparse/irregular 1.1 methods | Stable qualified module-scoped methods | [1.1 API](../reference/one-dot-one-module-api.md) |
| Ten transparent `run_*_workflow()` routes | **Published stable 1.2.0 module API** | [Workflow guide](../workflows/workflow-orchestration.md) |
| R76–R95 W3 inference studies | Separate research and evidence, not production estimators | [Research studies](../research/studies.md) |

**Do not infer that a research figure corresponds to a released estimator or calibrated confidence interval.**
