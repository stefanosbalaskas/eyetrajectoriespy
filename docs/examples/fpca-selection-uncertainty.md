# Worked example: component selection and FPC uncertainty

This example keeps two questions separate:

1. **How many FPCs reconstruct unseen participant trajectories well?**
2. **How stable is the shape of the retained FPCs under participant resampling?**

The data are synthetic and reproducible.

## Generate repeated-trial trajectories

```python
from eyetrajectoriespy import (
    bootstrap_fpca_component_envelopes,
    cross_validate_fpca_reconstruction,
    fpca_component_envelope_reporting_text,
    fpca_cross_validation_reporting_text,
    plot_fpca_component_envelope,
    plot_fpca_cross_validation,
    select_fpca_components_cv,
    simulate_planar_trajectories,
    summarise_fpca_cross_validation,
)

gaze = simulate_planar_trajectories(
    n_participants=12,
    trials_per_participant=3,
    n_time=61,
    random_state=2026,
)
```

Each participant contributes three trials, so ordinary curve-level CV would allow participant leakage.

## Participant-grouped reconstruction CV

```python
cv = cross_validate_fpca_reconstruction(
    gaze,
    candidate_components=(1, 2, 3, 4, 5),
    n_splits=4,
    scaling="dimension_sd",
    cv_unit="group",
    group_column="participant_id",
)

summary = summarise_fpca_cross_validation(cv)
print(summary)
```

Check that each participant appears in one test fold only:

```python
assert (
    cv.assignments.groupby("group")["fold"].nunique() == 1
).all()
```

Plot the reconstruction curve:

```python
plot_fpca_cross_validation(cv)
```

## Apply a pre-specified rule

```python
minimum_k = select_fpca_components_cv(cv, rule="minimum")
one_se_k = select_fpca_components_cv(cv, rule="one_se")

print(minimum_k, one_se_k)
```

Do not switch between rules after inspecting which one gives the preferred substantive story. Pre-specify the rule or report both as sensitivity information.

## Bootstrap FPC shapes at the participant level

For illustration the executable example uses 20 replicates. A real analysis should use enough replicates for the intended descriptive resolution.

```python
envelopes = bootstrap_fpca_component_envelopes(
    gaze,
    n_bootstrap=500,
    n_components=one_se_k,
    scaling="dimension_sd",
    resample_unit="participant",
    participant_column="participant_id",
    level=0.95,
    random_state=2026,
)
```

Inspect the matched-component similarities:

```python
import numpy as np

print(np.median(envelopes.similarities, axis=0))
```

Then inspect the shape envelope for each dimension:

```python
plot_fpca_component_envelope(
    envelopes,
    component=0,
    dimension="x",
)
```

Repeat for y(t) before interpreting a multivariate spatial component.

## Interpretation

A useful pattern is:

- held-out reconstruction error reaches a plateau;
- the chosen FPCs show high matched-bootstrap similarity;
- their pointwise envelopes preserve the main qualitative trajectory pattern.

A warning pattern is:

- adding components continues to improve reconstruction only trivially;
- the extra component has low matching similarity;
- its envelope changes shape or sign locally across resamples.

That does not automatically mean the component is invalid. It means its interpretation should be cautious and sensitivity analyses should be reported.

## Reporting text

```python
print(fpca_cross_validation_reporting_text(cv, rule="one_se"))
print(fpca_component_envelope_reporting_text(envelopes))
```

These helpers are starting points. A manuscript should still state the candidate range, fold unit, scaling, bootstrap unit, replicate count, random seed, and whether substantive conclusions changed under nearby component counts.

## Failure case: too many candidate components

```python
cross_validate_fpca_reconstruction(
    gaze,
    candidate_components=(1, 2, 40),
    n_splits=4,
)
```

This fails rather than estimating a rank-degenerate training-fold direction.

## Next checks

After selecting the retained dimension, continue with:

- [FPCA stability and validation](../guides/stability-validation.md)
- [FPC shape uncertainty](../guides/component-uncertainty.md)
- [Outliers and influence](../guides/outliers-influence.md)
- [Interpretation](../guides/interpretation.md)
