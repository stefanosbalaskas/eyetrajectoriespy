---
title: Functional simulation validation
---

# Functional simulation validation

This page records qualification evidence for the **0.11 native functional
simulation research branch**. The simulator is intended to generate exact,
inspectable truth for estimator-recovery studies rather than decorative
synthetic curves.

## Validation questions

The current qualification asks five separate questions:

1. Does the public dense simulator support ordinary FPCA recovery of the
   declared population mean, covariance structure, retained subspace, scores,
   eigenvalues, and reconstructions?
2. Does the native irregular sparse FPCA/PACE estimator recover its targets
   when measurement-noise variance is supplied?
3. Does the same sparse pipeline remain numerically/scientifically recoverable
   when measurement-noise variance must instead be estimated by the declared
   diagonal-difference procedure?
4. Does variance-matched Student-t score generation remain compatible with
   functional-subspace recovery?
5. Do realized curve, participant, and trial score sources recover their
   separately declared finite-sample variance scales?

The same recovery contract also supports post-fit evaluation of multivariate
FPCA, participant/trial mixed-effects variance functions, and registration
phase warps. Those broader audits are not silently promoted to CI thresholds
until dedicated qualification scenarios are predeclared.

## Dense Gaussian recovery

The dense scenario generates two orthonormal modes with declared component
variances and low Gaussian measurement noise. `fit_fpca()` is then applied to
the observed `TrajectorySet` without using the truth during estimation.

Qualification retains semantic recovery quantities rather than anonymous
floats. For FPCA/MFPCA these include:

- integrated squared error (ISE) for the population mean and covariance;
- relative eigenvalue error;
- sign-invariant matched-component similarity;
- principal cosines and principal angles for the retained subspace;
- sign-aligned score correlation and score RMSE;
- latent-trajectory reconstruction ISE.

When leading eigenvalues are tied or nearly tied, individual eigenfunctions are
not treated as uniquely identified; retained-subspace geometry is the primary
recovery target.

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

Qualification checks the common functional metrics above and additionally
records:

- PACE score RMSE and correlation;
- structured score-system failure rate;
- median, 95th-percentile, and maximum score-system condition numbers;
- whether PSD repair was actually applied and its relative weighted-operator
  correction magnitude;
- measurement-noise variance absolute/relative error.

The fixed-noise and estimated-noise cases are separate qualification scenarios.
A fit given the true noise variance is not evidence that the diagonal-difference
noise estimator recovers the same quantity. Sparse covariance ISE is computed
from the **full fitted covariance surface**, not from a rank-truncated
reconstruction using only returned components.

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

## Qualification matrix versus stress matrix

The package deliberately separates two scenario roles.

**Qualification scenarios** are small, deterministic, and have predeclared CI
guards. They are integration qualifications for specific seeded workloads, not
claims about universal operating regions.

**Stress scenarios** are broader and descriptive. Named cases currently cover
very sparse curves, strongly unequal sample counts, clustered or boundary-poor
observation times, high measurement noise, nearly tied eigenvalues,
heavy-tailed scores, participant-heavy and trial-heavy hierarchy, phase
variation, MCAR and contiguous-block missingness, and correlated multichannel
measurement noise.

Stress scenarios do **not** acquire automatic pass/fail thresholds merely
because they are difficult. A poor result remains evidence about a declared
regime and is retained in benchmark tables.

The public scenario catalog is available through
`functional_recovery_scenario_catalog_frame()`.

## Post-fit truth boundary

The orchestration preserves the sequence

$
(\text{observations},\text{declared scenario})
\longrightarrow
\text{fit},
$

followed only afterward by

$
(\text{fit},\text{latent truth})
\longrightarrow
\text{recovery assessment}.
$

A recovery evaluator therefore cannot become a hidden estimator-tuning input.
The evaluators also fail closed on grid mismatches rather than silently
interpolating truth.

For registration, generated observations satisfy
$Y_i(t)=X_i(w_i(t))$. The landmark-registration result stores the inverse
mapping used to recover reference time, so the correct known-truth target is
$w_i^{-1}(t)$.

For mixed effects, participant/trial recovery is evaluated through variance
functions in the observed time domain. Spline-basis covariance entries are not
equated to simulator KL eigenvalues. Curve-level KL variation is likewise not
silently relabeled as scalar iid residual variance.

## Monte Carlo summaries

Multiple replicates retain the empirical mean, median, standard deviation,
interquartile range, selected quantiles, and Monte Carlo standard error of the
mean. Explicit recorded failures remain in the scenario denominator.

For failure proportion $\hat p$ over $R$ replicates, the reported Monte Carlo
standard error is

$
\operatorname{MCSE}(\hat p)
=
\sqrt{\frac{\hat p(1-\hat p)}{R}}.
$

The default qualification runner remains fail-fast. Broader stress studies may
explicitly use `failure_action="record"` so simulation, fit, or recovery
failures remain visible rather than being silently dropped.

## Reproducible qualification artifact

The dedicated workflow runs:

```bash
python scripts/run_functional_simulation_validation.py \
  --replicates 3 \
  --output functional-simulation-validation.json
```

The JSON artifact records every qualification scenario, its predeclared
thresholds, semantic per-replicate metrics, evaluator provenance, qualification
extrema, and Monte Carlo distribution summaries. Stress matrices are kept
separate from this CI-gating artifact.

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
