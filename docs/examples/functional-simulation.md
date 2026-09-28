---
title: Native functional simulation with exact truth
---

# Native functional simulation with exact truth

This worked example generates irregular repeated-trial functional data while
retaining the exact curve, participant, trial, phase, noise, and missingness
truth needed for recovery studies.

## Define the latent functional process

```python
import numpy as np

from eyetrajectoriespy import simulate_functional_process


def mean(t):
    t = np.asarray(t, dtype=float)
    return 0.25 + 0.30 * t


def phi1(t):
    t = np.asarray(t, dtype=float)
    return np.sqrt(2.0) * np.sin(np.pi * t)


def phi2(t):
    t = np.asarray(t, dtype=float)
    return np.sqrt(2.0) * np.sin(2.0 * np.pi * t)
```

The declared component variances are 1.0 and 0.35. Additional participant and
trial score variation is kept separate.

## Generate irregular repeated-trial observations

```python
sim = simulate_functional_process(
    mean=mean,
    eigenfunctions=(phi1, phi2),
    eigenvalues=(1.0, 0.35),
    truth_grid=np.linspace(0.0, 1.0, 81),
    n_participants=24,
    trials_per_participant=2,
    observation_design="irregular",
    samples_per_curve=(7, 12),
    irregular_time_design="center_clustered",
    participant_eigenvalues=(0.20, 0.05),
    trial_eigenvalues=(0.10, 0.02),
    measurement_noise_sd=0.05,
    missingness={"kind": "mcar", "probability": 0.08},
    phase_variation={"kind": "power", "sd": 0.12},
    random_state=1101,
)
```

`sim.observations` is an `IrregularTrajectorySet` ready for analysis.
`sim.truth` contains the complete generating mechanism.

## Inspect the curve-level audit table

```python
from eyetrajectoriespy import functional_simulation_truth_frame

audit = functional_simulation_truth_frame(sim)
print(
    audit[[
        "curve_id",
        "participant_id",
        "trial_id",
        "n_pre_missing_samples",
        "n_observed_samples",
        "n_missing_by_design",
        "max_phase_displacement",
    ]].head()
)
```

The score columns in the same table keep total, curve-level, participant-level,
and trial-level realized component scores separate.

## Compare observed data with exact latent truth

```python
from eyetrajectoriespy import plot_functional_simulation_curve

plot_functional_simulation_curve(
    sim,
    curve=0,
    dimension="value",
    show_pre_missing=True,
)
```

The line is the exact latent process on the truth grid. Retained observations
are shown separately, and samples removed by the declared missingness
mechanism can be displayed without pretending they were observed.

## Audit phase variation

```python
from eyetrajectoriespy import plot_functional_simulation_phase_warps

plot_functional_simulation_phase_warps(sim, max_curves=20)
```

The identity line represents no phase distortion. Every simulated warp is
stored in the truth object, so the phase mechanism can be validated directly.

## Audit score-source variances

```python
from eyetrajectoriespy import plot_functional_simulation_score_variances

plot_functional_simulation_score_variances(sim)
```

Finite samples will not reproduce the declared variances exactly. The plot is
an audit of the realized simulation, not a requirement that empirical and
declared bars coincide.

## Produce reporting text

```python
from eyetrajectoriespy import functional_simulation_reporting_text

print(functional_simulation_reporting_text(sim))
```

The generated text records the score distribution, hierarchy, observation
design, missingness, phase mechanism, measurement-noise covariance, random
state, and the no-hidden-interpolation contract.

## Use the same simulator for estimator recovery

For a sparse-FPCA recovery study, fit the observed object without passing
`sim.truth` into the estimator:

```python
from eyetrajectoriespy import fit_sparse_fpca

fit = fit_sparse_fpca(
    sim.observations,
    dimension="value",
    n_components=2,
    evaluation_grid=np.linspace(0.0, 1.0, 31),
    mean_bandwidth=0.24,
    covariance_bandwidth=0.34,
    noise_variance_method="fixed",
    measurement_error_variance=0.05**2,
    psd_action="project",
)
```

Only after fitting should the recovered population structure or PACE scores be
compared with the retained truth. This keeps validation separate from estimator
configuration.

## Interpretation boundary

Simulation truth makes recovery measurable; it does not make one finite
simulation representative of all gaze experiments. Vary sample size,
sparsity, noise, phase variation, missingness, eigenvalue separation, and
estimator specifications deliberately when using the simulator for a
methodological claim.
