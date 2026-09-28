---
title: Native sparse / irregular FPCA + PACE roadmap
---

# Native sparse / irregular FPCA + PACE roadmap

This page defines the **0.10.0 scientific development tranche**. It is a design
and validation contract, not an implementation claim for the current 0.9.1
maintenance line.

## Release boundary

- **0.9.1** remains maintenance/consolidation only: defects, documentation,
  compatibility, UX, validation, performance, and release hardening.
- **0.10.0** is the planned native sparse/irregular FPCA + PACE tranche.
- the existing `fit_sparse_fpca_fdapy()` API remains available during the
  transition as an explicitly backend-named compatibility/reference path;
- FDApy is not a required core dependency and is not the implementation target
  for the canonical 0.10 estimator.

The architectural rule is:

$$
\text{external reference implementation}
\neq
\text{runtime scientific dependency}.
$$

## Statistical target

For curve $i$ observed at subject-specific times $t_{ij}$,

$$
Y_{ij}=X_i(t_{ij})+\epsilon_{ij},
$$

with a latent smooth process

$$
X_i(t)=\mu(t)+\sum_{k=1}^{K}\xi_{ik}\phi_k(t).
$$

The native sparse pipeline should estimate the population mean

$$
\mu(t)=E\{X(t)\},
$$

then the latent covariance surface

$$
G(s,t)=\operatorname{Cov}\{X(s),X(t)\},
$$

while treating the measurement-error contribution on the raw covariance
diagonal separately from the smooth latent covariance.

The eigenfunctions then satisfy

$$
\int G(s,t)\phi_k(s)\,ds
=
\lambda_k\phi_k(t),
$$

and subject-specific sparse scores are recovered by conditional expectation
(PACE):

$$
\widehat{\xi}_{ik}
=
\lambda_k
\phi_{ik}^{\top}
\Sigma_i^{-1}
\left(Y_i-\widehat{\mu}_i\right),
$$

where $\phi_{ik}$ evaluates eigenfunction $k$ at curve $i
## Non-negotiable scientific choices

The implementation must keep these choices explicit and recorded in provenance:

- mean smoother and its bandwidth/penalty;
- covariance smoother and its bandwidth/penalty;
- evaluation grid and declared analysis support;
- explicit handling of observations outside that support;
- covariance-diagonal handling;
- measurement-noise variance estimator and its averaging support;
- any positive-semidefinite covariance repair;
- number of retained components;
- PACE score estimator;
- linear-system tolerance / regularization;
- support/domain restrictions;
- any exclusion criterion for extremely sparse curves.

The package must not silently:

- interpolate sparse curves to a dense common grid;
- convert absent observations to zeros;
- select smoothing parameters from downstream outcome effects;
- choose component count without an explicit rule;
- clip negative covariance eigenvalues without recording the correction;
- drop singular/ill-conditioned subject score systems;
- call separate univariate $x(t)$ and $y(t)$ fits “multivariate PACE”.

## Proposed 0.10 public API

The canonical entry point should be native and backend-independent:

```python
fit_sparse_fpca(
    trajectories,
    *,
    dimension,
    n_components,
    evaluation_grid,
    mean_smoother,
    covariance_smoother,
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

Exact argument names may change during implementation, but the scientific
choices above may not disappear behind automatic defaults.

The existing compatibility function remains explicitly backend-named:

```python
fit_sparse_fpca_fdapy(...)
```

It should not become the implementation underneath `fit_sparse_fpca()`.

## Native implementation stages

### 1. Validate native irregular observations

Input remains `IrregularTrajectorySet`. Absence is represented by absence of a
sample, not by NaN placeholders. The selected dimension, time support, per-curve
sample counts, and duplicate-time rules are validated before estimation.

The evaluation-grid endpoints define the declared analysis interval
$[a,b]\subseteq[\min T,\max T]$. If observed samples fall outside this
interval, the default behavior is to fail. They are excluded only when the
analyst explicitly requests `analysis_support_action="restrict"`; the number
of excluded observations, affected curves, and effective per-curve sample
counts are then retained in provenance. There is no automatic trimming.

### 2. Estimate the pooled mean

Estimate $\widehat{\mu}(t)$ directly from the pooled irregular observations.
The smoother and tuning parameter remain explicit.

### 3. Construct raw covariance pairs

For within-curve pairs $j\neq l$,

$$
C_{ijl}
=
\left(Y_{ij}-\widehat\mu(t_{ij})\right)
\left(Y_{il}-\widehat\mu(t_{il})\right).
$$

Off-diagonal pairs provide information about the latent covariance surface
without directly adding measurement-error variance.

### 4. Smooth the covariance surface

Estimate $\widehat G(s,t)$ on an explicit evaluation grid. Symmetry must be
enforced transparently. Any positive-semidefinite correction must be reported
as a numerical/statistical operation, not hidden.

PSD diagnostics retain both the ordinary grid-matrix correction norm and the
operator-scale quantity

$
\left\|
W^{1/2}
\left(
\widehat G_{\mathrm{repaired}}-\widehat G
\right)
W^{1/2}
\right\|_F,
$

plus its relative version. The latter is less sensitive to evaluation-grid
discretization.

### 5. Estimate measurement-error variance

Use an explicit estimator based on the raw diagonal versus the fitted smooth
latent diagonal, or another separately documented method. For the
diagonal-difference estimator, the analyst must also declare
`noise_support=(a, b)`, the interval over which the raw-minus-latent diagonal
difference is averaged. The package does not silently assume that the full
evaluation domain is optimal. Retain the estimate, support and diagnostics in
the result.

### 6. Solve the covariance eigenproblem

Use quadrature weights on the declared grid, return eigenvalues/eigenfunctions,
and apply deterministic sign conventions only for reproducibility—not as a
scientific identification claim.

The number of requested components is **not** capped at
`n_curves - 1`, because the smoothed irregular covariance operator is not the
ordinary centered empirical covariance matrix of fully observed curves.
Availability is determined instead by the number of eigenvalues of the fitted
weighted operator above `positive_eigen_tolerance`.

### 7. Recover PACE scores

For each curve, evaluate the fitted mean/eigenfunctions on its own native
sampling times, construct $\widehat\Sigma_i$, and solve the conditional-score
system. Ill-conditioning, numerical regularization, or failed solves must be
visible in diagnostics.

## Result contract

The native sparse result should retain at least:

- evaluation grid;
- fitted mean;
- fitted latent covariance;
- estimated measurement-noise variance;
- eigenvalues;
- eigenfunctions;
- PACE scores;
- curve IDs and metadata;
- time/coordinate units;
- smoother specifications;
- component-count rule;
- score-system conditioning diagnostics;
- covariance-repair diagnostics;
- complete provenance.

Opaque backend objects are not part of the canonical native result contract.

## Validation plan

0.10 is not complete when the code merely runs. Qualification requires four
evidence layers.

### Analytical / controlled truth

Use simple covariance models where numerical eigenstructure is known or can be
computed to high precision independently.

### Simulation recovery

Generate latent functional processes with known mean, eigenfunctions,
eigenvalues, scores, noise variance, irregular sampling, and sparsity. Assess
recovery of population structure and conditional scores across declared
sampling regimes.

### Evaluation-grid convergence

PACE scores inherit numerical error from representing fitted population
functions on a finite evaluation grid. Qualification therefore includes
refinement checks such as $G=21,41,81$ points and examines:

- relative eigenvalue change;
- sign/subspace-invariant eigenfunction agreement;
- principal-angle / principal-cosine stability;
- PACE score correlation under refinement.

The target claim is numerical stabilization under refinement, not that one
particular grid is intrinsically correct.

### FDApy comparison

Use FDApy only as an **independent numerical comparator** on matched synthetic
datasets/specifications. Align component sign/order before comparing and report
tolerance rules. The comparison is validation evidence, not delegated
computation.

### Cross-language reference where feasible

Add an R-based reference comparison when a sufficiently matched sparse-FPCA /
PACE contract can be specified. A comparison is only meaningful when the
smoother, grid, noise assumptions, and scoring definition are genuinely
comparable.

## Migration path

```text
0.9.1
native eyetrajectoriespy core
+ optional fit_sparse_fpca_fdapy() compatibility backend

        ↓

0.10.0
native fit_sparse_fpca()
+ native PACE scoring
+ FDApy used for reference validation / compatibility

        ↓

later
deprecate backend-specific runtime workflow only after
native validation and the documented deprecation window
```

No FDApy-specific API is removed as part of introducing the native estimator.
The package's pre-1.0 deprecation policy still applies.

## Explicitly out of scope for the first 0.10 tranche

- joint sparse multivariate PACE;
- automatic smoothing selection, including CV/GCV, in the critical 0.10 path;
- sparse functional mixed effects;
- full downstream propagation of sparse-FPCA estimation uncertainty;
- a generic all-purpose FDA object hierarchy.

Bandwidths are explicitly declared numeric values in the 0.10 estimator.
A future opt-in CV/GCV selector may be added only with an explicit resampling
unit, search grid, criterion, selected value and failure audit; it is not needed
for 0.10 completion.

The first target is a defensible **univariate native sparse FPCA + PACE**
implementation that preserves gaze-specific data/provenance contracts.
s observed times and

$
\widehat\Sigma_i
=
\widehat G(T_i,T_i)
+
\widehat\sigma_\epsilon^2 I
+
\gamma I.
$

The conditional score system uses the **full fitted covariance surface**.
Retaining $K$ components controls which $(\lambda_k,\phi_k)$ and scores are
returned; it does not replace $\widehat G(T_i,T_i)$ by a rank-$K$
reconstruction. The declared ridge $\gamma$ changes the score estimator and is
therefore recorded as part of the analysis specification.

## Non-negotiable scientific choices

The implementation must keep these choices explicit and recorded in provenance:

- mean smoother and its bandwidth/penalty;
- covariance smoother and its bandwidth/penalty;
- evaluation grid;
- covariance-diagonal handling;
- measurement-noise variance estimator;
- any positive-semidefinite covariance repair;
- number of retained components;
- PACE score estimator;
- linear-system tolerance / regularization;
- support/domain restrictions;
- any exclusion criterion for extremely sparse curves.

The package must not silently:

- interpolate sparse curves to a dense common grid;
- convert absent observations to zeros;
- select smoothing parameters from downstream outcome effects;
- choose component count without an explicit rule;
- clip negative covariance eigenvalues without recording the correction;
- drop singular/ill-conditioned subject score systems;
- call separate univariate $x(t)$ and $y(t)$ fits “multivariate PACE”.

## Proposed 0.10 public API

The canonical entry point should be native and backend-independent:

```python
fit_sparse_fpca(
    trajectories,
    *,
    dimension,
    n_components,
    evaluation_grid,
    mean_smoother,
    covariance_smoother,
    mean_bandwidth=None,
    covariance_bandwidth=None,
    noise_variance_method="diagonal_difference",
    score_method="PACE",
    score_tolerance=1e-8,
    covariance_psd_action="error",
)
```

Exact argument names may change during implementation, but the scientific
choices above may not disappear behind automatic defaults.

The existing compatibility function remains explicitly backend-named:

```python
fit_sparse_fpca_fdapy(...)
```

It should not become the implementation underneath `fit_sparse_fpca()`.

## Native implementation stages

### 1. Validate native irregular observations

Input remains `IrregularTrajectorySet`. Absence is represented by absence of a
sample, not by NaN placeholders. The selected dimension, time support, per-curve
sample counts, and duplicate-time rules are validated before estimation.

### 2. Estimate the pooled mean

Estimate $\widehat{\mu}(t)$ directly from the pooled irregular observations.
The smoother and tuning parameter remain explicit.

### 3. Construct raw covariance pairs

For within-curve pairs $j\neq l$,

$$
C_{ijl}
=
\left(Y_{ij}-\widehat\mu(t_{ij})\right)
\left(Y_{il}-\widehat\mu(t_{il})\right).
$$

Off-diagonal pairs provide information about the latent covariance surface
without directly adding measurement-error variance.

### 4. Smooth the covariance surface

Estimate $\widehat G(s,t)$ on an explicit evaluation grid. Symmetry must be
enforced transparently. Any positive-semidefinite correction must be reported
as a numerical/statistical operation, not hidden.

### 5. Estimate measurement-error variance

Use an explicit estimator based on the raw diagonal versus the fitted smooth
latent diagonal, or another separately documented method. Retain the estimate
and diagnostics in the result.

### 6. Solve the covariance eigenproblem

Use quadrature weights on the declared grid, return eigenvalues/eigenfunctions,
and apply deterministic sign conventions only for reproducibility—not as a
scientific identification claim.

### 7. Recover PACE scores

For each curve, evaluate the fitted mean/eigenfunctions on its own native
sampling times, construct $\widehat\Sigma_i$, and solve the conditional-score
system. Ill-conditioning, numerical regularization, or failed solves must be
visible in diagnostics.

## Result contract

The native sparse result should retain at least:

- evaluation grid;
- fitted mean;
- fitted latent covariance;
- estimated measurement-noise variance;
- eigenvalues;
- eigenfunctions;
- PACE scores;
- curve IDs and metadata;
- time/coordinate units;
- smoother specifications;
- component-count rule;
- score-system conditioning diagnostics;
- covariance-repair diagnostics;
- complete provenance.

Opaque backend objects are not part of the canonical native result contract.

## Validation plan

0.10 is not complete when the code merely runs. Qualification requires four
evidence layers.

### Analytical / controlled truth

Use simple covariance models where numerical eigenstructure is known or can be
computed to high precision independently.

### Simulation recovery

Generate latent functional processes with known mean, eigenfunctions,
eigenvalues, scores, noise variance, irregular sampling, and sparsity. Assess
recovery of population structure and conditional scores across declared
sampling regimes.

### FDApy comparison

Use FDApy only as an **independent numerical comparator** on matched synthetic
datasets/specifications. Align component sign/order before comparing and report
tolerance rules. The comparison is validation evidence, not delegated
computation.

### Cross-language reference where feasible

Add an R-based reference comparison when a sufficiently matched sparse-FPCA /
PACE contract can be specified. A comparison is only meaningful when the
smoother, grid, noise assumptions, and scoring definition are genuinely
comparable.

## Migration path

```text
0.9.1
native eyetrajectoriespy core
+ optional fit_sparse_fpca_fdapy() compatibility backend

        ↓

0.10.0
native fit_sparse_fpca()
+ native PACE scoring
+ FDApy used for reference validation / compatibility

        ↓

later
deprecate backend-specific runtime workflow only after
native validation and the documented deprecation window
```

No FDApy-specific API is removed as part of introducing the native estimator.
The package's pre-1.0 deprecation policy still applies.

## Explicitly out of scope for the first 0.10 tranche

- joint sparse multivariate PACE;
- automatic smoothing selection based on downstream effects;
- sparse functional mixed effects;
- full downstream propagation of sparse-FPCA estimation uncertainty;
- a generic all-purpose FDA object hierarchy.

The first target is a defensible **univariate native sparse FPCA + PACE**
implementation that preserves gaze-specific data/provenance contracts.
