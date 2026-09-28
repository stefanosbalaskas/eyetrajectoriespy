---
title: Functional simulation validation
---

# Functional simulation validation

This page records qualification evidence for the **0.11 native functional
simulation research branch**. The simulator is intended to generate exact,
inspectable truth for estimator-recovery studies rather than decorative
synthetic curves.

## Validation questions

The current validation asks four separate questions:

1. Does the public dense simulator generate data from which ordinary FPCA can
   recover the declared leading functional subspace and scores?
2. Does the public irregular simulator support recovery through the native
   sparse FPCA/PACE estimator without hidden dense interpolation?
3. Does variance-matched Student-t score generation remain compatible with
   functional-subspace recovery?
4. Do realized curve, participant and trial score sources recover their
   separately declared variance scales over a finite simulation?

## Dense Gaussian recovery

The dense scenario generates two orthonormal modes with declared component
variances and low Gaussian measurement noise. `fit_fpca()` is then applied to
the observed `TrajectorySet` without using the truth during estimation.

Qualification compares:

- quadrature-weighted principal cosines;
- sign-invariant component similarity;
- relative eigenvalue error;
- sign-aligned score correlation.

## Heavy-tailed score recovery

The same dense process is repeated with variance-matched Student-t curve-level
scores. Because individual eigenfunctions can be unstable when finite samples
contain extreme scores, the qualification emphasizes retained-subspace
agreement as well as component-wise metrics.

## Native sparse recovery

The irregular scenario is generated directly at curve-specific observation
times with 8–12 samples per curve. The native `fit_sparse_fpca()` estimator
is given declared numerical smoothing specifications and the known
measurement-noise variance.

The estimator never receives dense latent truth, and the simulator never
creates the irregular observations through hidden dense-to-irregular
interpolation.

Qualification checks:

- retained functional-subspace principal cosines;
- component similarity;
- PACE score correlation;
- structured score-system failure rate.

## Hierarchical score-source recovery

A separate scenario generates

$$
\xi_{ijk}
=
\xi^{(curve)}_{ijk}
+
b^{(participant)}_{ik}
+
u^{(trial)}_{ijk}
$$

with independent declared variance scales. Qualification compares realized
finite-sample variances for each score source with their generating values.

This validates the simulator's decomposition. It is not a claim that a mixed
effects estimator can always recover those variances at the same accuracy.

## Declared scenario contract

The recovery workflow now expresses each finite-sample data-generating design
through `FunctionalSimulationScenario`. The same scenario object carries the
sample size, truth grid, component variances, dense/irregular observation
design, sparse sample-count contract, measurement noise, hierarchy,
distribution, deterministic seed, and provenance labels.

This separation is intentional: scenario specification controls **data
generation**, while estimator settings remain declared in the estimator
portion of the validation script. The estimator is not given the latent truth
or allowed to choose smoothing, component count, regularization, or other
settings by inspecting recovery performance.

The reusable scenario layer can therefore support broader matrices over
participant/trial counts, sampling density, noise, sparsity, missingness,
eigenvalue separation, and phase variation without changing estimator
contracts.

## Reproducible qualification artifact

The dedicated workflow runs:

```bash
python scripts/run_functional_simulation_validation.py \
  --replicates 3 \
  --output functional-simulation-validation.json
```

The JSON artifact records every scenario, its predeclared qualification
thresholds, per-replicate metrics, and summary extrema.

## What the thresholds mean

The thresholds in the validation script are **qualification guards for the
declared seeded workloads**. They are not universal statistical guarantees,
sample-size recommendations, or automatic tuning rules.

The generating truth is never used to select FPCA component count, sparse
bandwidths, PSD policy, or score regularization inside a fitted replicate.

## Failure philosophy

The simulator and validation harness remain fail-closed. Examples include:

- non-orthonormal supplied modes are rejected instead of silently repaired;
- invalid measurement-noise covariance is rejected instead of projected;
- Student-t scores require finite variance (`df > 2`);
- irregular missingness that leaves too few observations fails rather than
  silently redrawing samples;
- estimator failures remain visible instead of being removed from the
  validation denominator.

## Relationship to FDApy

FDApy inspired the idea of a serious functional simulation subsystem, but it
is not used to generate canonical truth. Public simulation truth is generated
natively by eyetrajectoriespy, which keeps the validation source independent
of the optional FDApy sparse compatibility path.
