---
title: Native functional simulation roadmap
---

# Native functional simulation framework roadmap

A richer native simulation subsystem is a candidate **0.11.0 tranche**, after
native sparse FPCA/PACE is stable. The purpose is scientific validation, not a
large object hierarchy.

## Core model

The basic configurable process is

$$
X_i(t)
=
\mu(t)
+
\sum_{k=1}^{K}\xi_{ik}\phi_k(t)
+
\epsilon_i(t).
$$

The simulation system should make the data-generating mechanism inspectable and
return both observations and truth.

## Implementation staging

The 0.11 research tranche follows the same qualification discipline used for
native sparse FPCA/PACE.

### Stage 1 — private deterministic core

The first implementation stage is intentionally private. It provides:

- analyst-supplied mean and eigenfunction callables;
- explicit descending positive eigenvalues;
- trapezoidal-grid orthonormality validation without silent normalization;
- deterministic Gaussian latent scores;
- dense or curve-specific irregular observation schedules;
- explicit sparse sample-count and irregular-time designs;
- scalar or per-dimension measurement-noise standard deviations;
- direct evaluation of latent population functions on each declared
  observation schedule;
- `TrajectorySet` or `IrregularTrajectorySet` output without hidden
  representation conversion;
- a structured truth record containing latent curves, realized scores,
  observation schedules, measurement-noise realizations, and provenance.

No public `simulate_functional_process()` API is exposed at this stage.

A critical contract is that irregular observations are simulated **directly at
their declared times**. They are not created by simulating a dense trajectory
and interpolating or subsampling it behind the user's back.

### Stage 2 — hierarchy and observation mechanisms

After Stage 1 qualification, the private core adds explicit:

- participant-level component-score variance, retained separately from
  curve-level scores;
- trial-level component-score variance, retained separately from participant
  and curve variation;
- total realized component scores as the exact sum of those sources;
- MCAR and contiguous-block missingness mechanisms with the pre-missing
  schedule, mask, and observed values retained;
- fail-closed behavior when irregular missingness leaves fewer than two
  observations;
- monotone endpoint-preserving power time warps with every realized warp
  retained on the truth grid and observation schedules;
- positive-semidefinite cross-channel measurement-noise covariance;
- vector-valued functional modes that can induce latent cross-channel
  covariance independently of measurement noise.

The simulator does not silently repair an invalid measurement-noise covariance,
resample a curve after excessive missingness, or collapse participant/trial
effects into a single unlabeled score source.

### Stage 3 — public composition

After Stages 1–2 qualification, the public composition layer exposes:

- `simulate_functional_process(...)`;
- `FunctionalSimulationResult`, containing observations plus truth;
- `FunctionalSimulationTruth`, retaining the complete realized generating
  mechanism;
- variance-matched normal or Student-t curve-level score distributions;
- the dense/irregular, hierarchy, noise, missingness and phase contracts from
  the qualified private core.

Student-t scores require more than two degrees of freedom so the declared
component variance exists. Participant/trial score effects remain Gaussian
and are retained separately.

The public function remains a thin composition layer over the qualified native
core; it does not delegate scientific generation to FDApy or another FDA
library.
## Candidate capabilities

A native simulator should allow analyst-declared:

- mean function;
- eigenfunctions;
- eigenvalue decay or explicit eigenvalues;
- score distribution;
- participant-level effects;
- trial-level effects;
- measurement noise;
- irregular observation times;
- sparsity / observation-count distribution;
- missingness mechanism;
- multichannel correlation;
- phase/time-warp variation;
- coordinate/time units;
- deterministic `random_state`.

The simulator should be able to emit `TrajectorySet` or
`IrregularTrajectorySet` without silently converting one representation into
the other.

## Proposed contract

A future entry point might look like:

```python
simulate_functional_process(
    *,
    mean,
    eigenfunctions,
    eigenvalues,
    n_participants,
    trials_per_participant=1,
    score_distribution="normal",
    participant_effect=None,
    trial_effect=None,
    measurement_noise=0.0,
    observation_design="dense",
    irregular_sampling=None,
    missingness=None,
    phase_variation=None,
    channel_correlation=None,
    random_state=None,
)
```

The exact surface is intentionally not frozen yet.

## Truth object

Simulation should return a structured truth record containing, where applicable:

- latent noiseless trajectories;
- mean/eigenfunctions/eigenvalues;
- realized latent scores;
- participant/trial effects;
- measurement-noise realizations;
- complete pre-missing observation schedule;
- missingness mask/mechanism;
- phase-warp functions;
- random seed/state metadata.

This makes simulation useful for estimator-recovery tests rather than only for
illustrative plotting.

## Validation uses

The framework should support recovery studies for:

- dense FPCA/MFPCA;
- native sparse FPCA/PACE;
- functional mixed effects;
- registration and phase FPCA;
- component stability/uncertainty;
- nonlinear and recurrence diagnostics;
- performance envelopes.

## Design boundary

FDApy's simulation subsystem is useful architectural inspiration, especially
its configurable Karhunen–Loève perspective. eyetrajectoriespy should implement
its own gaze-specific simulation contracts and should not import FDApy to
generate validation truth.

The package should also avoid a giant generic functional-data inheritance tree.
`TrajectorySet` and `IrregularTrajectorySet` remain the primary
representation contracts because they preserve participant/trial metadata,
coordinates, units, and provenance.
