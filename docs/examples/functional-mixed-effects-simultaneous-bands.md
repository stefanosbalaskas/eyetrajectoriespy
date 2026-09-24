# Worked simultaneous mixed-effects coefficient bands

This example fits a trial-varying condition effect and then constructs a
participant-cluster simultaneous band for the complete observed coefficient
trajectory.

```python
import numpy as np
import pandas as pd

from eyetrajectoriespy import (
    TrajectorySet,
    bootstrap_functional_mixed_effects_coefficients,
    fit_functional_mixed_effects_regression,
    functional_mixed_effects_coefficient_frame,
    functional_mixed_effects_reporting_text,
    functional_mixed_effects_simultaneous_bands,
    plot_functional_mixed_effects_coefficient,
)

rng = np.random.default_rng(2026)
n_participants = 12
trials_per_participant = 3
time = np.linspace(0.0, 1.0, 9)

participants = np.repeat(
    [f"P{i:02d}" for i in range(n_participants)],
    trials_per_participant,
)
condition = np.tile([0.0, 1.0, 0.5], n_participants)

beta0 = 0.20 + 0.15 * time
beta_condition = 0.15 + 0.40 * time

basis = np.column_stack([1.0 - time, time])
random_coefficients = rng.multivariate_normal(
    [0.0, 0.0],
    [[0.030, 0.004], [0.004, 0.020]],
    size=n_participants,
)

values = []
curve_ids = []
for participant_index in range(n_participants):
    random_function = random_coefficients[participant_index] @ basis.T
    for trial_index in range(trials_per_participant):
        row = participant_index * trials_per_participant + trial_index
        values.append(
            (
                beta0
                + condition[row] * beta_condition
                + random_function
                + rng.normal(0.0, 0.04, size=time.size)
            )[:, None]
        )
        curve_ids.append(f"C{row:03d}")

trajectories = TrajectorySet(
    time=time,
    values=np.asarray(values),
    curve_ids=tuple(curve_ids),
    dimension_names=("metric",),
    metadata=pd.DataFrame({"participant_id": participants}),
    coordinate_system="unknown",
    time_unit="s",
)

design = pd.DataFrame(
    {
        "curve_id": trajectories.curve_ids,
        "condition": condition,
    }
)

fit = fit_functional_mixed_effects_regression(
    trajectories,
    design,
    predictors=("condition",),
    participant_column="participant_id",
    dimension="metric",
    fixed_basis_size=2,
    random_basis_size=2,
    spline_degree=1,
)

boot = bootstrap_functional_mixed_effects_coefficients(
    fit,
    n_bootstrap=500,
    random_state=44,
)

band = functional_mixed_effects_simultaneous_bands(
    boot,
    confidence_level=0.95,
    simultaneous_scope="coefficient",
)
```

## Inspect the whole-function band

```python
ax = plot_functional_mixed_effects_coefficient(
    band,
    coefficient="condition",
)
```

The shaded region is now a 95% **observed-grid simultaneous band**, not the
pointwise Wald interval shown when the plotting function receives the raw fit.

## Export auditable values

```python
table = functional_mixed_effects_coefficient_frame(
    fit,
    band=band,
)

print(
    table.query("coefficient == 'condition'")[
        [
            "time",
            "estimate",
            "bootstrap_standard_error",
            "lower_simultaneous",
            "upper_simultaneous",
            "simultaneous_critical_value",
        ]
    ]
)
```

## Verify the resampling contract

```python
print(boot.sampled_participant_indices.shape)
print(
    boot.provenance[
        "functional_mixed_effects_bootstrap"
    ]
)
```

Each row of `sampled_participant_indices` contains one bootstrap draw of
participant indices. Every occurrence contributes that participant's complete
trial bundle.

The covariance model is held fixed; this is therefore not a full
variance-component bootstrap.

## Familywise coefficient scope

To control one maximum across the intercept, condition coefficient, and the
observed time grid:

```python
family_band = functional_mixed_effects_simultaneous_bands(
    boot,
    confidence_level=0.95,
    simultaneous_scope="family",
)
```

Use family scope only when that coefficient family is genuinely the planned
inferential family.

## Reporting text

```python
print(
    functional_mixed_effects_reporting_text(
        fit,
        band=band,
    )
)
```

Report the participant count, number of source curves, fixed/random basis
sizes, covariance structure, number of participant bootstrap replicates,
simultaneous scope, observed-grid interpretation, and the fact that variance
components and basis choices were conditioned on rather than re-estimated.
