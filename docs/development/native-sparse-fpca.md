---
title: Native sparse / irregular FPCA + PACE roadmap
---

# Native sparse / irregular FPCA + PACE roadmap

This page defines the **0.10.0 scientific development tranche**. It is a design,
implementation, and validation contract for the dedicated 0.10 development branch;
it is not an implementation claim for the 0.9.1 maintenance line.

## Release boundary

- **0.9.1** remains maintenance/consolidation only: defects, documentation,
  compatibility, UX, validation, performance, and release hardening.
- **0.10.0** is the native sparse/irregular FPCA + PACE tranche.
- `fit_sparse_fpca_fdapy()` remains an explicitly backend-named compatibility
  and external-reference path during migration.
- FDApy is not a required core dependency and is not the implementation
  underneath the canonical native estimator.

The architectural rule is:

$$
\text{external reference implementation}
\neq
\text{runtime scientific dependency}.
$$

## Statistical target

For curve $i$ observed at curve-specific times $t_{ij}$,

$$
Y_{ij}=X_i(t_{ij})+\epsilon_{ij},
$$

with latent process

$$
X_i(t)=\mu(t)+\sum_{k=1}^{K}\xi_{ik}\phi_k(t).
$$

The native pipeline estimates the population mean

$$
\mu(t)=E\{X(t)\},
$$

and latent covariance surface

$$
G(s,t)=\operatorname{Cov}\{X(s),X(t)\},
$$

while treating measurement-error variance separately from the smooth latent
covariance diagonal.

The covariance eigenfunctions satisfy

$$
\int G(s,t)\phi_k(s)\,ds
=
\lambda_k\phi_k(t).
$$

PACE scores use conditional expectation:

$$
\widehat{\xi}_{ik}
=
\widehat\lambda_k
\widehat\phi_k(T_i)^{\top}
\widehat\Sigma_i^{-1}
\left\{Y_i-\widehat\mu(T_i)\right\},
$$

with

$$
\widehat\Sigma_i
=
\widehat G(T_i,T_i)
+
\widehat\sigma_\epsilon^2 I
+
\gamma I.
$$

The conditional score system uses the **full fitted covariance surface**.
Retaining $K$ components controls which $(\lambda_k,\phi_k)$ and scores are
returned; it does not replace $\widehat G(T_i,T_i)$ by a rank-$K$
reconstruction. The declared ridge $\gamma$ changes the estimator and is
therefore recorded as part of the statistical/numerical specification.

## Model evaluation is not raw-data interpolation

Evaluating $\widehat\mu(t)$, $\widehat G(s,t)$, or
$\widehat\phi_k(t)$ at a curve\'s native observation times is evaluation of
a fitted population object. It does **not** create a dense version of the raw
sparse trajectory.

The native implementation records both facts explicitly:

```text
raw_sparse_trajectory_interpolation_performed = False
population_function_evaluation_at_native_times = True
```

## Non-negotiable scientific choices

The implementation keeps these choices explicit and retains them in provenance:

- mean smoother and bandwidth/penalty;
- covariance smoother and bandwidth/penalty;
- evaluation grid and declared analysis support;
- explicit handling of observations outside that support;
- covariance-diagonal handling;
- measurement-noise estimator and its averaging support;
- positive-semidefinite covariance policy and tolerance;
- number of retained components;
- PACE score system and conditioning threshold;
- score ridge / regularization;
- failure behavior for sparse or ill-conditioned curves;
- any support/domain restriction.

The package must not silently:

- interpolate sparse curves to a dense common grid;
- convert absent observations to zeros;
- choose smoothing parameters;
- choose component count;
- clip a materially indefinite covariance without recording it;
- drop singular or ill-conditioned score systems;
- restrict observations to an analysis interval;
- call separate univariate $x(t)$ and $y(t)$ fits “multivariate PACE”.

## Public 0.10 estimator contract

The canonical native entry point is:

```python
fit_sparse_fpca(
    trajectories,
    *,
    dimension,
    n_components,
    evaluation_grid,
    mean_bandwidth,
    covariance_bandwidth,
    noise_bandwidth=None,
    noise_support=None,
    analysis_support_action="error",
    noise_variance_method="diagonal_difference",
    measurement_error_variance=None,
    psd_action="error",
    psd_tolerance=1e-8,
    positive_eigen_tolerance=1e-10,
    score_ridge=0.0,
    score_condition_limit=1e12,
    score_failure_action="error",
)
```

The existing compatibility function remains explicitly backend-named:

```python
fit_sparse_fpca_fdapy(...)
```

It must not become the implementation underneath `fit_sparse_fpca()`.

## Analysis support

The evaluation-grid endpoints define the declared analysis interval
$[a,b]\subseteq[\min T,\max T]$. A grid need not extend to the two most
extreme pooled observations.

If samples fall outside $[a,b]$, the default behavior is to fail. Samples are
excluded only when the analyst explicitly requests
`analysis_support_action="restrict"`. In that case the result retains:

- total observations outside the support;
- number of affected curves;
- per-curve outside counts;
- original sample counts;
- effective in-support sample counts;
- number of curves with no in-support observations.

There is no automatic trimming.

## Native implementation stages

### 1. Validate native irregular observations

Input remains `IrregularTrajectorySet`. Absence is represented by absence of a
sample rather than NaN/Inf placeholders in the selected dimension.

### 2. Estimate the pooled mean

Estimate $\widehat\mu(t)$ directly from pooled irregular observations on the
declared analysis support. The initial 0.10 implementation uses explicitly
declared local-linear / Epanechnikov smoothing.

### 3. Construct raw covariance pairs

For within-curve pairs $j\neq l$,

$$
C_{ijl}
=
\left(Y_{ij}-\widehat\mu(t_{ij})\right)
\left(Y_{il}-\widehat\mu(t_{il})\right).
$$

Off-diagonal pairs inform the latent covariance without directly adding
measurement-error variance.

### 4. Smooth and audit the covariance surface

Estimate $\widehat G(s,t)$ on the declared evaluation grid and enforce
symmetry transparently. PSD inspection is performed on the quadrature-weighted
operator $W^{1/2}\widehat G W^{1/2}$.

PSD diagnostics retain the pre-repair spectrum, negative-eigenvalue counts,
the ordinary grid-matrix correction norm, and the operator-scale quantity

$$
\left\|
W^{1/2}
\left(
\widehat G_{\mathrm{repaired}}-\widehat G
\right)
W^{1/2}
\right\|_F,
$$

plus its relative version. A tiny numerical negative and a materially
indefinite estimated covariance are therefore not represented as the same
problem.

### 5. Estimate measurement-error variance

With `noise_variance_method="diagonal_difference"`, the analyst must declare
both `noise_bandwidth` and `noise_support=(a,b)`. The raw-minus-latent
diagonal difference is averaged only over that declared interval. The package
does not silently assume that the whole fitted support is the appropriate
noise-estimation domain.

Alternatively, `noise_variance_method="fixed"` accepts an explicitly supplied
non-negative measurement-error variance.

### 6. Solve the covariance eigenproblem

The eigensolver uses quadrature weights and deterministic sign conventions for
reproducibility only.

The requested component count is **not** capped at `n_curves - 1`. A covariance
surface obtained by smoothing irregular pairwise products is not the ordinary
centered empirical covariance matrix of fully observed curves. Component
availability is therefore determined by the number of eigenvalues of the
fitted weighted operator above `positive_eigen_tolerance`.

### 7. Recover PACE scores

For each curve, evaluate the fitted mean, covariance, and retained
eigenfunctions at its native in-support observation times and solve the full
covariance-plus-noise conditional system. Per-curve diagnostics retain sample
count, condition number, smallest/largest system eigenvalue, ridge, solve
status, and structured failure code.

## Failure/status distinctions

The native layer distinguishes failure modes including:

```text
insufficient_pooled_support
insufficient_mean_local_support
insufficient_within_curve_covariance_pairs
insufficient_covariance_local_support
insufficient_noise_support
noise_variance_invalid
covariance_psd_failure
insufficient_positive_components
native_time_outside_fitted_support
curve_too_sparse_for_score_system
score_covariance_not_positive_definite
score_covariance_ill_conditioned
nonfinite_sparse_observation
evaluation_grid_outside_pooled_support
observations_outside_analysis_support
```

## Result contract

The native result retains at least:

- evaluation grid and declared analysis support;
- fitted mean and full fitted/repaired latent covariance;
- measurement-noise estimate and declared noise support;
- eigenvalues/eigenfunctions and quadrature weights;
- PACE scores;
- per-curve score-system diagnostics;
- local mean/covariance support counts;
- PSD pre-repair spectrum and both grid/operator correction norms;
- curve IDs, metadata, time/coordinate units, and complete provenance.

## Evaluation-grid convergence

PACE scores inherit numerical error from representing fitted population
objects on a finite grid. Qualification therefore includes refinement checks
at $G=21,41,81$ grid points and evaluates:

- relative retained-eigenvalue change;
- sign/subspace-invariant eigenfunction agreement;
- principal-angle / principal-cosine stability;
- PACE score correlation under refinement.

The intended claim is stabilization under grid refinement, not that one
particular grid is intrinsically correct.

## Validation plan

0.10 is not complete merely because the estimator runs.

### Analytical / controlled truth

Use covariance models where numerical eigenstructure is known or can be
computed independently to high precision.

### Simulation recovery

Use known mean, eigenfunctions, eigenvalues, latent scores, measurement noise,
irregular sampling, and sparsity. Evaluate mean/covariance error, eigenvalue
error, subspace error, PACE score accuracy, and failure frequency.

### FDApy comparison

Use FDApy as an **independent numerical comparator** only where specifications
can be aligned. Where smoothing, covariance reconstruction, interpolation, or
PACE score-system definitions differ, label the exercise
**cross-implementation sensitivity**, not equivalence.

### Cross-language reference where feasible

Use an R comparison only when mean smoothing, covariance smoothing, noise
treatment, evaluation support, and score definitions can be matched
defensibly. “No defensible exact equivalence case” is preferable to a forced
comparison with different estimands.

## Bandwidth selection is deferred

0.10 requires explicit numeric smoothing bandwidths. Automatic CV/GCV is not
part of the release-completion path. A later opt-in selector would need to
declare the resampling unit, search grid, criterion, selected value, and
failures; observation-level and curve-level CV are not interchangeable for
sparse repeated measurements.

## Explicitly out of scope for 0.10

- joint sparse multivariate PACE;
- automatic bandwidth selection;
- sparse functional mixed effects;
- full downstream propagation of sparse-FPCA estimation uncertainty;
- a generic all-purpose FDA object hierarchy.

Separate sparse fits for `x(t)` and `y(t)` remain two univariate
decompositions and do not model cross-channel covariance.

## Migration path

```text
0.9.1 maintenance main
+ optional fit_sparse_fpca_fdapy() compatibility backend

        ↓

0.10 development branch
+ native fit_sparse_fpca()
+ native PACE scoring
+ independent validation / stress testing

        ↓

full qualification
+ PR into protected main
```

No FDApy-specific API is removed simply because the native estimator exists.
The normal pre-1.0 deprecation policy continues to apply.
