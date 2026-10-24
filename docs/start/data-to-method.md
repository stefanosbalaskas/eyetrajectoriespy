---
title: From gaze data to a defensible functional method
description: Research-first guide to matching time support, coordinate sampling, experimental design and statistical uncertainty to stable eyetrajectoriespy 1.2.0 methods.
---

# From gaze data to a defensible functional method

**Choose the research question and observation structure before choosing a function.** Published `eyetrajectoriespy==1.2.0` provides stable module-scoped workflow routes for continuous, sparse and repeated-trial gaze, but a successful model fit is not proof of valid statistical inference.

## 1. What did the recorder actually observe?

| Data structure | Preserve | Recommended starting point |
| --- | --- | --- |
| Common aligned x/y time grid | Coordinate and time units, observed gaps, participant and trial IDs | [Continuous FPCA](../workflows/fpca-exploration.md) |
| Paired sparse x/y samples at shared times | Raw observation times, sample support per curve | [Sparse planar MFPCA](../guides/sparse-multivariate-fpca.md) |
| x/y coordinates sampled at different times | Two coordinate-specific time vectors; **no fabricated common grid** | [Irregular/asynchronous sampling](../guides/irregular-trajectories.md) |
| Multiple trials within each participant | The participant–trial hierarchy and covariate alignment | [Repeated-trial functional mixed effects](../workflows/repeated-trial-mixed-effects.md) |

Do not silently replace missing gaze by zero, interpolate across long gaps or drop unsuccessful trials. Review the [input schemas](../guides/input-schemas.md) before converting data into functional objects.

## 2. What is your scientific question?

<div class="grid cards" markdown>

- **What are the dominant modes of variation?**

  FPCA/MFPCA summarizes how x/y trajectories vary over time. Components are mathematical modes, **not validated psychological constructs**.

  [Continuous FPCA workflow](../workflows/fpca-exploration.md)

- **How does a condition change gaze over time?**

  Functional regression estimates a specified time-varying association. Check whether each curve is independent or belongs to repeated trials.

  [Functional regression](../workflows/experimental-functional-regression.md)

- **How do repeated participants or trials differ?**

  Preserve within-person clustering in estimation, prediction and reporting; do not treat repeated trials as independent people.

  [Mixed-effects route](../workflows/repeated-trial-mixed-effects.md)

- **Is recurrence or temporal organization the target?**

  Declare embedding, time delay, distance and recurrence threshold rather than tuning them after seeing the result.

  [Recurrence analysis](../workflows/nonlinear-recurrence.md)

</div>

## 3. What can the sample justify?

Before running an analysis, record the following five decisions:

1. **Independent unit:** participant, curve or trial; number of independent units and repeats.
2. **Observed support:** recording window, time units, channel-specific gaps, exclusions and missingness.
3. **Target:** descriptive variability, prediction, functional coefficient, pointwise uncertainty or a whole-curve inference.
4. **Dependence:** participant clustering, temporal autocorrelation and planar x/y covariance.
5. **Claim boundary:** does the method's engineering qualification cover the operation, and is there independent evidence for the desired statistical claim?

The unresolved [simultaneous band calibration issue #289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289) and [outcome-dependent missing gaze issue #296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296) mean that no blanket W3 confidence-band or MNAR recovery guarantee should be inferred from the stable package release.

## 4. Try one reproducible supported workflow

```bash
python -m pip install "eyetrajectoriespy==1.2.0"
```

The [three complete quick starts](../quickstart.md) demonstrate dense planar FPCA, sparse planar MFPCA and function-on-scalar regression using **seeded synthetic teaching data**. They are not measured participant observations. For all ten W1–W4 route/configuration choices, use the [workflow-selection guide](../articles/choosing-the-ten-workflows.md).

![Synthetic overview of planar x/y gaze, time-indexed curves and assumption-dependent inference](../assets/site/hero-trajectories.svg)

*Conceptual synthetic illustration, not evidence of estimator calibration or hardware performance.*

## 5. Preserve interpretation and provenance

Report data source and permissions, package version, preprocessing and transformation decisions, participant/trial grouping, model specification, sensitivity analyses, diagnostics, warnings, failures and the precise inferential target. Use the [reporting checklist](../methods/reporting.md), [portable workflow bundles](../articles/reproducible-workflow-bundles.md) and [scientific figure atlas](../figures/index.md) to keep claims tied to their sources.

[Start a complete example](../quickstart.md){ .md-button .md-button--primary }
[Public API stability](../reference/api-stability.md){ .md-button }
[Research boundaries](../research/index.md){ .md-button }
