---
title: Native functional simulation
---

# Native functional simulation

The 0.11 research branch provides a native simulator for generating functional
trajectory observations together with the **exact realized data-generating
truth**.

Use it when you need to validate an estimator, demonstrate a workflow, or study
failure behavior under known functional structure.

## Core process

The basic curve-level process is

$$
X_i(t)
=
\mu(t)
+
\sum_{k=1}^{K}
\xi_{ik}\phi_k(t).
$$

The public simulator may additionally include participant and trial score
effects, phase variation, measurement noise, irregular observation schedules,
and explicit missingness.

```python
import numpy as np

from eyetrajectoriespy import simulate_functional_process


def mean(t):
    return 0.25 + 0.30 * np.asarray(t)


def phi1(t):
    return np.sqrt(2.0) * np.sin(np.pi * np.asarray(t))


def phi2(t):
    return np.sqrt(2.0) * np.sin(2.0 * np.pi * np.asarray(t))


sim = simulate_functional_process(
    mean=mean,
    eigenfunctions=(phi1, phi2),
    eigenvalues=(1.0, 0.35),
    truth_grid=np.linspace(0.0, 1.0, 81),
    n_participants=30,
    trials_per_participant=2,
    participant_eigenvalues=(0.20, 0.05),
    trial_eigenvalues=(0.10, 0.02),
    measurement_noise_sd=0.05,
    random_state=42,
)
```

`sim.observations` is the analysis object. `sim.truth` retains the generating
mechanism.

## What truth is retained

The truth object contains, where applicable:

- declared mean, eigenfunctions and component variances;
- realized curve, participant, trial and total scores;
- noiseless latent trajectories;
- complete pre-missing observation schedules;
- final observation schedules;
- phase warps on the truth grid;
- latent values at observed times;
- measurement-noise realizations and covariance;
- pre-missing noisy observations;
- missingness masks;
- participant/trial metadata;
- units, dimension names, random state and provenance.

This means recovery studies do not need to reconstruct the data-generating
truth after the fact.

## Dense versus irregular observations

Dense observations are generated directly on `truth_grid`.

For irregular data:

```python
sim = simulate_functional_process(
    mean=mean,
    eigenfunctions=(phi1, phi2),
    eigenvalues=(1.0, 0.35),
    truth_grid=np.linspace(0.0, 1.0, 81),
    n_participants=40,
    observation_design="irregular",
    samples_per_curve=(6, 12),
    irregular_time_design="center_clustered",
    measurement_noise_sd=0.08,
    random_state=7,
)
```

Irregular latent functions are evaluated **directly at the declared irregular
times**. The simulator does not create a dense raw curve and silently
interpolate it to the irregular schedule.

## Hierarchical variation

Curve-, participant-, and trial-level component-score variation are separate:

$$
\xi_{ijk}
=
\xi^{(curve)}_{ijk}
+
b^{(participant)}_{ik}
+
u^{(trial)}_{ijk}.
$$

Declare participant and trial component variances separately:

```python
participant_eigenvalues=(0.20, 0.05)
trial_eigenvalues=(0.10, 0.02)
```

Every realized source is retained independently in `sim.truth`.

## Missingness

Missingness is an explicit observation mechanism rather than a preprocessing
side effect.

```python
missingness={"kind": "mcar", "probability": 0.10}
```

or

```python
missingness={"kind": "block", "fraction": 0.20}
```

For dense outputs, missing positions remain explicit `NaN`s. For irregular
outputs, missing samples are removed from the final sparse schedule while the
complete pre-missing schedule and mask remain in truth. If too few irregular
samples remain, the simulator fails instead of silently resampling.

## Phase variation

Endpoint-preserving monotone power warps are available explicitly:

```python
phase_variation={"kind": "power", "sd": 0.15}
```

Every realized warp is retained on the truth grid.

## Measurement noise

Independent channel noise can be specified by standard deviation:

```python
measurement_noise_sd=(0.03, 0.05)
```

or a full multichannel covariance can be supplied:

```python
measurement_noise_sd=None
measurement_noise_covariance=np.array(
    [[0.04, 0.018],
     [0.018, 0.09]]
)
```

An invalid covariance is rejected. It is not silently projected to positive
semidefinite form.

## Curve-level score distributions

The default score distribution is Gaussian.

For heavier tails:

```python
score_distribution="student_t"
score_df=6.0
```

The Student-t draws are rescaled so the declared component variances remain the
target variances. `score_df` must exceed 2 so that variance exists.

## Audit tables and reporting

```python
from eyetrajectoriespy import (
    functional_simulation_reporting_text,
    functional_simulation_truth_frame,
)

audit = functional_simulation_truth_frame(sim)
print(functional_simulation_reporting_text(sim))
```

The audit frame contains per-curve observation counts, missingness, phase
displacement, and realized score sources.

## Diagnostic plots

```python
from eyetrajectoriespy import (
    plot_functional_simulation_curve,
    plot_functional_simulation_phase_warps,
    plot_functional_simulation_score_variances,
)

plot_functional_simulation_curve(
    sim,
    curve=0,
    dimension=0,
    show_pre_missing=True,
)
plot_functional_simulation_phase_warps(sim)
plot_functional_simulation_score_variances(sim)
```

The first plot compares retained observations with exact latent truth. The
second audits realized phase warps. The third compares declared and realized
score-source variances.

## Declared scenario matrices and recovery

For repeated recovery studies, define the data-generating design once with
`FunctionalSimulationScenario` rather than reconstructing simulator keyword
arguments inside every estimator-specific script.

```python
from eyetrajectoriespy import (
    FunctionalSimulationScenario,
    expand_functional_simulation_scenarios,
    functional_simulation_scenario_frame,
)

base = FunctionalSimulationScenario(
    name="sparse-recovery",
    truth_grid=np.linspace(0.0, 1.0, 41),
    eigenvalues=(1.0, 0.35),
    n_participants=80,
    observation_design="irregular",
    samples_per_curve=(8, 12),
    measurement_noise_sd=0.05,
    replicates=5,
    seed_start=1200,
)

scenarios = expand_functional_simulation_scenarios(
    base,
    {
        "n_participants": (80, 160),
        "measurement_noise_sd": (0.05, 0.10),
        "samples_per_curve": ((8, 12), (5, 8)),
    },
    seed_policy="shared",
)

design_table = functional_simulation_scenario_frame(scenarios)
```

The Cartesian expansion is explicit. With `seed_policy="shared"`, matching
replicates use the same seeds across scenarios, which supports paired
common-random-number comparisons. With `seed_policy="disjoint"`, each
scenario receives a non-overlapping seed block. The framework never chooses a
seed policy silently.

Use `run_functional_recovery_scenarios()` when a common estimator/scorer pair
can be applied across the matrix. Its callback boundary is deliberate:

```text
scenario
   |
   v
simulate -> observations --------> estimator
   |                                  |
   +--> exact latent truth             v
                     recovery scorer <- fitted result
```

The estimator callback receives **observations and the declared scenario, but
not the latent truth**. Truth is supplied only after fitting to the recovery
scorer. This makes it possible to calculate bias, score recovery, subspace
recovery, coverage, failure frequency, or other declared metrics without
using truth to tune the estimator.

`functional_recovery_frame()` returns the resulting replicate-level metrics
in tidy form. Qualification thresholds remain the responsibility of the
validation design; the scenario framework does not invent universal pass/fail
cutoffs.

## Validation use

The 0.11 qualification harness uses the **public** simulator to test recovery
through existing package methods rather than validating only internal arrays.

Current scenarios include:

- dense Gaussian FPCA recovery;
- dense variance-matched Student-t FPCA recovery;
- native sparse FPCA/PACE recovery;
- recovery of declared curve/participant/trial score-source variances.

These are finite-sample qualification scenarios, not universal guarantees.

See [functional simulation validation](../validation/functional-simulation-validation.md).

## Scientific boundaries

The simulator does not:

- silently normalize or orthogonalize supplied eigenfunctions;
- silently repair an invalid noise covariance;
- silently interpolate dense curves into irregular ones;
- silently redraw missing observations to make a curve usable;
- collapse participant and trial variation into an unlabeled score;
- select estimator tuning parameters from generating truth.

The full realized truth exists to make assumptions and failures inspectable,
not to let downstream estimators cheat.
