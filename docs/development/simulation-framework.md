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
