# Native sparse multivariate FPCA contract (0.12)

## Status

This document defines the first 0.12 estimator tranche. It is a development
contract, not a claim that the estimator is qualified or release-ready.

The starting point is stable `0.11.0` plus the merged targeted pre-0.12 audit.
That audit found no supported-contract defect requiring an 0.11 correction and
showed that cross-channel covariance can carry substantial planar structure
while the univariate marginal covariance functions remain fixed.

## Scientific object

For selected functional dimensions
```text
G_i(t) = [X_i1(t), ..., X_iD(t)]^T
```
observed sparsely on curve-specific time grids, the target covariance operator is

```text
C_ab(s,t) = Cov{X_ia(s), X_ib(t)}
```

for every ordered channel pair `(a,b)`. The assembled operator is

```text
C(s,t) =
[[C_11(s,t), ..., C_1D(s,t)],
 ...
 [C_D1(s,t), ..., C_DD(s,t)]]
```

with the functional symmetry contract
`C_ba(s,t) = C_ab(t,s)`.

The estimator must represent this block covariance explicitly. Two independent
univariate sparse-FPCA fits are not a multivariate estimator.

## Observation representation

Input is `IrregularTrajectorySet`. Raw sparse observations remain on their
native grids. Population means, covariance surfaces and eigenfunctions are
smooth fitted objects evaluated on an analyst-declared grid and, for scoring,
at native observation times. This is model evaluation; raw trajectories are
not silently interpolated.

The first tranche assumes the selected channels of a curve share the time
vector already encoded by `IrregularTrajectorySet`. It does not invent
dimension-specific observation times.

## Mean and covariance estimation

Each selected channel receives its own pooled local-linear mean estimate.
Within-channel latent covariance uses the qualified 0.10 off-diagonal
local-linear covariance machinery and the same explicit measurement-noise
contract.

For `a != b`, cross-covariance is estimated from all within-curve residual
products

```text
R_ia(s_j) R_ib(t_k)
```

including equal-index/equal-time products. Under the first-tranche measurement
error contract, cross-channel measurement errors are independent, so those
products do not contain a cross-channel noise covariance term. The cross
surface is not forced to be symmetric in `s,t`; instead the paired block is
constructed by transpose:

```text
C_ba(s,t) := C_ab(t,s).
```

No cross-channel measurement-error covariance is estimated implicitly.

## Measurement error

The public contract must state the assumption explicitly:

```text
cross_channel_measurement_error = "independent"
```

Only that value is supported in the first tranche.

Marginal measurement-error variances are either estimated separately by the
qualified diagonal-difference procedure or supplied explicitly per selected
channel. The score covariance adds those variances only to the corresponding
channel blocks.

## Block covariance and PSD policy

With `D` dimensions and `M` evaluation-grid points, the block covariance is
represented internally as a `(D*M) x (D*M)` dimension-major matrix.

Quadrature weights are the trapezoidal grid weights repeated once per
dimension. PSD auditing and optional projection therefore act on

```text
W^(1/2) C W^(1/2)
```

using the repeated block weight vector, not on an unweighted matrix.

As in 0.10, a substantial negative operator eigenvalue fails closed when
`psd_action="error"`. Projection must be explicitly requested.

## Joint eigensystem

The canonical estimator solves one eigensystem for the full repaired block
operator. Returned components have shape

```text
(n_components, n_grid, n_dimensions)
```

and satisfy the multivariate weighted inner-product convention

```text
sum_d integral phi_kd(t) phi_ld(t) dt = delta_kl.
```

Component signs are made deterministic by the largest-magnitude entry of the
flattened joint eigenfunction.

The two-stage route (univariate sparse bases followed by a joint score
covariance) remains a validation/sensitivity comparator. It is not the
canonical estimator.

## Joint conditional scores

For curve `i`, selected channel observations are stacked in dimension-major
order. The full conditional covariance is built from all fitted block
covariance surfaces evaluated at that curve's native times, plus the declared
marginal measurement-error covariance and any explicit numerical score ridge.

For retained joint eigenfunctions `Phi_i`, scores use

```text
E[xi_i | Y_i]
  = Lambda Phi_i^T Sigma_i^{-1} (Y_i - mu_i).
```

Crucially, `Sigma_i` is constructed from the **full fitted block covariance**.
`n_components` controls returned eigenfunctions/scores only; it must not
truncate the covariance used in the conditional score system.

Per-curve conditioning, minimum eigenvalue, status code and solve status are
retained. Failed curves are either rejected or retained with NaN scores under
an explicit action, matching the fail-closed 0.10 philosophy.

## First public API

The canonical entry point is planned as

```python
fit_sparse_mfpca(
    trajectories,
    *,
    dimensions=None,
    n_components,
    evaluation_grid,
    mean_bandwidth,
    covariance_bandwidth,
    cross_covariance_bandwidth=None,
    noise_bandwidth=None,
    noise_support=None,
    noise_variance_method="diagonal_difference",
    measurement_error_variances=None,
    cross_channel_measurement_error="independent",
    analysis_support_action="error",
    psd_action="error",
    ...
)
```

`dimensions=None` means all dimensions in their existing order. At least two
dimensions are required.

The first tranche uses one declared mean bandwidth and one declared marginal
covariance bandwidth across selected channels. A separately declared
cross-covariance bandwidth may be supplied; otherwise it equals the marginal
covariance bandwidth. Automatic bandwidth or dimension selection is out of
scope.

## Result contract

`SparseMFPCAResult` must retain at least:

- curve IDs and metadata;
- selected dimension names and units;
- evaluation grid and quadrature weights;
- fitted channel means;
- full block covariance and joint eigenfunctions;
- joint eigenvalues and explained-variance ratios;
- joint conditional scores;
- marginal measurement-error variances;
- per-curve score diagnostics;
- block-PSD diagnostics;
- mean, marginal-covariance and cross-covariance support diagnostics;
- full provenance, including the cross-channel noise assumption;
- explicit markers that raw sparse interpolation and automatic bandwidth
  selection were not performed.

## Validation sequence

The estimator is not scientifically promoted merely because unit tests pass.
Qualification must proceed in this order:

1. analytical block-operator algebra and weighted orthonormality;
2. deterministic known-truth planar recovery with controlled `rho_xy`;
3. score recovery and conditioning/failure-path tests;
4. evaluation-grid and bandwidth sensitivity;
5. signal-dependent observation-loss stress;
6. independent mGSFPCA sensitivity on the frozen pre-0.12 fixture;
7. runtime/RSS qualification;
8. documentation/API/release-contract checks.

Sparse participant/trial decomposition remains outside this tranche.
