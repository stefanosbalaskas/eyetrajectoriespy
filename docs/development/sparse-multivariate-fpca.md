---
title: Native sparse multivariate FPCA for planar gaze
---

# Native sparse multivariate FPCA for planar gaze

This page defines the **0.12 scientific design contract**. It follows the
completed pre-0.12 recovery audit and records the implemented numerical/public
composition boundary. Full 0.12 recovery qualification remains pending.

## Release boundary

- Stable `0.11.0` remains frozen.
- The completed pre-0.12 audit found no supported-contract defect requiring an
  0.11 correction.
- `0.12` is the native sparse multivariate planar-FPCA tranche.
- Sparse participant/trial functional decomposition remains later work.
- mGSFPCA, MFPCA, FDApy, and related packages are independent
  reference/sensitivity implementations, not runtime scientific dependencies.

The architectural rule is:

```text
joint planar estimand
    !=
two unrelated univariate sparse fits
```

## Scientific object

For curve i, planar gaze is the bivariate latent process

$$
\mathbf X_i(t)
=
\begin{bmatrix}
X_i(t)\\
Y_i(t)
\end{bmatrix},
\qquad
\mathbf Y_{ij}
=
\mathbf X_i(t_{ij})+\boldsymbol\epsilon_{ij}.
$$

The population mean is

$$
\boldsymbol\mu(t)=E\{\mathbf X(t)\},
$$

and the target covariance operator is the full block surface

$$
\mathbf C(s,t)
=
\begin{bmatrix}
C_{xx}(s,t) & C_{xy}(s,t)\\
C_{yx}(s,t) & C_{yy}(s,t)
\end{bmatrix}.
$$

The cross-channel blocks are first-class estimands. A method that estimates
only Cxx and Cyy is not the canonical 0.12 estimator.

## Joint eigensystem

Joint eigenfunctions are vector-valued,

$$
\boldsymbol\phi_k(t)
=
\begin{bmatrix}
\phi_{kx}(t)\\
\phi_{ky}(t)
\end{bmatrix},
$$

and satisfy

$$
\int \mathbf C(s,t)\boldsymbol\phi_k(s)\,ds
=
\lambda_k\boldsymbol\phi_k(t),
$$

under the planar inner product

$$
\langle \mathbf f,\mathbf g\rangle
=
\int
\left\{
f_x(t)g_x(t)+f_y(t)g_y(t)
\right\}\,dt.
$$

Optional scale weighting may be considered only if it is explicit,
scientifically motivated, and retained in provenance. Normalized screen
coordinates do not justify silent channel reweighting.

## Observation covariance and conditional scores

For one curve with native observation times Ti, stack the observed planar
values as x1,y1,...,xm,ym. Let Ci be the full fitted block covariance evaluated
at the native observation times. Let the measurement-error covariance be

$$
\mathbf R_\epsilon
=
\begin{bmatrix}
\sigma_x^2 & \sigma_{xy}\\
\sigma_{xy} & \sigma_y^2
\end{bmatrix}.
$$

The score system uses

$$
\widehat{\boldsymbol\Sigma}_i
=
\widehat{\mathbf C}_i
+
I_{m_i}\otimes\widehat{\mathbf R}_\epsilon
+
\gamma I.
$$

For component k, define the stacked vector-eigenfunction evaluations
$\widehat{\boldsymbol\phi}_{ik}$. The conditional score is

$$
\widehat\xi_{ik}
=
\widehat\lambda_k
\widehat{\boldsymbol\phi}_{ik}^{\top}
\widehat{\boldsymbol\Sigma}_i^{-1}
\left\{
\mathbf y_i-\widehat{\boldsymbol\mu}_i
\right\}.
$$

As in 0.10, `n_components` controls which components and scores are returned.
It must not replace the full fitted observation covariance by a rank-K
reconstruction unless a separately named sensitivity method explicitly does so.

## Measurement-error contract

Cross-channel measurement error is scientifically consequential and must be
declared rather than guessed.

The first implementation should support:

1. `measurement_error="diagonal"`: independent x/y measurement noise with
   explicit or separately estimated sigma_x^2 and sigma_y^2;
2. `measurement_error="fixed_matrix"`: analyst-supplied positive-semidefinite
   2x2 error covariance.

Automatic estimation of sigma_xy from the same sparse covariance surface is
deferred until a defensible identifiability/estimation contract is validated.
The default must therefore not invent cross-channel measurement error.

### Latent covariance pair contract

The first direct sparse implementation estimates all latent covariance blocks
from temporally off-diagonal residual products only. For residual coordinates
r_ixj and r_iyj, the pair sets are

$$
r_{ixj}r_{ix\ell},\qquad
r_{iyj}r_{iy\ell},\qquad
r_{ixj}r_{iy\ell},
\qquad j\ne\ell.
$$

Same-time products are deliberately excluded. In particular, omitting
r_ixj r_iyj prevents an analyst-supplied contemporaneous measurement-error
covariance sigma_xy from contaminating the latent C_xy surface, provided the
measurement errors are independent across distinct time points.

The cross surface is directional:

$$
C_{xy}(s,t)\ne C_{xy}(t,s)
$$

in general. The implementation must therefore fit C_xy(s,t) directly from the
ordered x-at-s / y-at-t products and must never symmetrize C_xy against its own
transpose. C_yx is not estimated as a fourth noisy surface; it is defined by

$$
C_{yx}(s,t)=C_{xy}(t,s).
$$

The first canonical implementation uses one explicit mean bandwidth shared by
x and y and one explicit covariance bandwidth shared by xx, xy, and yy.
Per-channel or per-block bandwidths remain deferred until recovery evidence
shows that the added flexibility is scientifically necessary.

## Canonical architecture

The canonical estimator is the **direct block-covariance route**:

```text
native irregular planar observations
        ->
pooled vector mean
        ->
four covariance blocks Cxx, Cxy, Cyx, Cyy
        ->
symmetry + PSD audit of the weighted block operator
        ->
joint eigensystem
        ->
joint conditional scores
```

The implementation must estimate the cross-channel blocks directly from paired
within-curve observations and carry them through the operator and score system.

### Required benchmark architecture

A two-stage benchmark should also be implemented for validation:

```text
univariate sparse basis for x
+ univariate sparse basis for y
        ->
joint covariance of retained univariate scores
        ->
secondary joint rotation
```

This route is useful for sensitivity and debugging. It is not the canonical
scientific endpoint because its cross-channel representation is conditional on
the independently chosen marginal bases and truncations.

## Irregular observation contract

The estimator operates directly on `IrregularTrajectorySet`.

The first 0.12 implementation assumes both planar coordinates are observed at
the same retained time stamps within a curve. Coordinate-specific missingness
must either be rejected explicitly or represented through a later generalized
observation-layout contract; it must not be silently filled or synchronized by
interpolation.

Population mean/covariance/eigenfunction evaluation at native times is allowed.
Raw sparse trajectory interpolation remains false.

## Public composition status

PR A implemented the direct sparse vector mean and xx/xy/yy covariance-block
fit. PR B implemented direction-preserving native-time surface evaluation,
explicit channel-major to time-major ordering, strict two-channel
measurement-error validation, and full-covariance joint PACE scoring.

PR C exposes those same numerical pieces through `fit_sparse_mfpca()` and
`SparseMFPCAResult`; it does not introduce a second estimator path. Public
mean/eigenfunction arrays use time before dimension, while the internal
operator remains channel-major. The initial public contract requires explicit
`diagonal` or `fixed_matrix` measurement-error input. It does not expose
channel weights or automatic measurement-error estimation.

## Public API target

The canonical entry point is:

```python
fit_sparse_mfpca(
    trajectories,
    *,
    dimensions=("x", "y"),
    n_components,
    evaluation_grid,
    mean_bandwidth,
    covariance_bandwidth,
    analysis_support_action="error",
    measurement_error,
    measurement_error_variance=None,
    measurement_error_covariance=None,
    psd_action="error",
    psd_tolerance=1e-8,
    positive_eigen_tolerance=1e-10,
    score_ridge=0.0,
    score_condition_limit=1e12,
    score_failure_action="error",
)
```

The implemented PR C signature intentionally omits channel weights and other
placeholder options. Every public parameter corresponds to implemented and
tested behavior.

## Result contract

The result must retain at least:

- evaluation grid and analysis support;
- selected dimension names;
- vector mean function;
- all four fitted covariance blocks;
- the directly smoothed pre-PSD covariance blocks separately from the
  covariance blocks actually used downstream after joint PSD handling;
- pre/post-repair weighted block-operator spectra;
- PSD repair diagnostics and correction norms;
- measurement-error covariance and its provenance;
- joint eigenvalues and vector-valued eigenfunctions;
- quadrature weights;
- joint conditional scores;
- per-curve score-system diagnostics;
- original curve IDs, metadata, units, coordinate system, and provenance;
- explicit flags that raw sparse trajectories were not interpolated.

A user must be able to reconstruct and inspect the estimated Cxy(s,t) surface
directly.

## PSD and symmetry contract

The fitted block operator must satisfy the covariance symmetry relation

$$
C_{yx}(s,t)=C_{xy}(t,s).
$$

Numerical enforcement of this identity must be explicit.

PSD inspection must be performed on the quadrature-weighted joint operator, not
on each covariance block independently. Repair, if requested, must retain the
pre-repair spectrum, negative-eigenvalue diagnostics, and both absolute and
relative correction norms.

A pair of individually PSD marginal blocks does not imply a valid joint block
covariance.

## Failure/status distinctions

The joint estimator should distinguish at least:

```text
insufficient_joint_support
insufficient_cross_covariance_pairs
insufficient_cross_covariance_local_support
invalid_measurement_error_covariance
joint_covariance_symmetry_failure
joint_covariance_psd_failure
insufficient_positive_joint_components
coordinate_specific_missingness_unsupported
native_time_outside_fitted_support
curve_too_sparse_for_joint_score_system
joint_score_covariance_not_positive_definite
joint_score_covariance_ill_conditioned
nonfinite_sparse_planar_observation
observations_outside_analysis_support
```

Failures must remain visible in per-curve/per-fit diagnostics.

## Validation gates

0.12 is not complete because the estimator runs.

### 1. Analytical/operator checks

Use controlled block-covariance constructions with known numerical joint
eigenstructure. Verify symmetry, PSD behavior, normalization, orthogonality,
eigenvalue ordering, sign/subspace invariance, and reconstruction.

### 2. Known-truth recovery

Use the 0.11 simulation laboratory with fixed marginal covariance and varying
cross-channel dependence. Recover:

- vector mean;
- each covariance block;
- joint eigenvalues;
- joint eigenspace;
- joint scores;
- latent planar trajectory reconstruction.

The rho_xy = 0, 0.3, 0.6, 0.9 family from the pre-0.12 audit becomes a
first-class qualification scenario. Qualification must also include negative
cross-channel coupling and at least one construction with a deliberately
non-symmetric C_xy(s,t) while preserving C_yx(s,t)=C_xy(t,s).

PR D implements `evaluate_sparse_mfpca_recovery()` with named-block covariance
ISE and identification-aware tied-eigenspace score recovery. The deterministic
qualification family is extended to `rho_xy=-0.6, 0, 0.3, 0.6, 0.9`, plus one
deliberately asymmetric Cxy case and one correlated-measurement-error case.
Grid and ridge sensitivity remain descriptive and do not select tuning values.
### 3. Observation-process stress

Repeat recovery under MCAR and declared signal-dependent observation loss.
Stress evidence remains separate from qualification thresholds unless a
specific supported-contract defect is demonstrated.

This final validation tranche runs the public `fit_sparse_mfpca()` estimator
under the frozen row-level MCAR, signal-dependent x/y, eccentricity, velocity
and phase loss mechanisms. Paired x/y native timestamps remain synchronized,
and the workflow records recovery/conditioning changes descriptively with
`threshold_gate_applied=false` and no parameter selection.

### 4. Direct versus two-stage sensitivity

Compare direct block-covariance and two-stage benchmark routes using invariant
objects:

- covariance-block error;
- joint subspace principal angles/cosines;
- score-subspace agreement;
- reconstruction error;
- sensitivity to marginal basis truncation.

No automatic architecture winner is selected from one simulation.

PR E implements the two-stage marginal-basis benchmark with declared
marginal ranks 1 and 2 on a frozen rho_xy=0.6 fixture. It compares named
covariance-block error, joint functional subspaces, score subspaces and latent
reconstruction against truth and the canonical direct estimator. The evidence
sets `automatic_rank_selection=false` and
`architecture_winner_selected=false`.

### 5. Independent external sensitivity

Use mGSFPCA 0.2.2 as the primary cross-language comparator on frozen fixtures
with explicit rank/basis settings. Compare invariant subspaces and scores, not
raw signs or implementation-specific normalization.

PR E runs this comparator on the same frozen rho_xy=0.6 native/truth fixture
and records mGSFPCA-versus-truth, native-versus-truth and
mGSFPCA-versus-native functional and score subspaces. The comparator remains a
validation-only dependency and the evidence explicitly forbids an equivalence
claim or automatic architecture selection.

Exact equivalence must not be claimed when smoothing, likelihood, basis,
normalization, or score contracts differ.

### 6. Grid refinement and conditioning

Repeat the joint operator/score pipeline over increasing evaluation-grid
resolution. Record eigenspace stability, score stability, covariance-block
stability, condition numbers, and ridge sensitivity.

## Non-negotiable exclusions

0.12 does not automatically include:

- sparse participant/trial functional decomposition;
- generalized coordinate-specific asynchronous observation layouts;
- automatic bandwidth selection;
- automatic component selection;
- Bayesian sparse MFPCA;
- downstream predictive models that hide sparse-score uncertainty;
- rotation chosen to optimize an outcome;
- silent channel standardization or whitening;
- silent interpolation.

## Promotion decision

The tranche can move toward a 0.12 release candidate only after:

1. the direct joint estimator exists behind the explicit API contract;
2. analytical/operator checks pass;
3. known-truth planar recovery passes;
4. the two-stage benchmark is available and differences are characterized;
5. external mGSFPCA sensitivity evidence is reproducible;
6. observation-process stress is retained separately;
7. documentation, serialization/provenance, examples, performance, and
   cross-platform CI are green.

The dedicated final qualification workflow adds a sparse-MFPCA-specific
single-package performance envelope with fresh-process repeated runtime and
peak-RSS measurements. No comparative speed claim or release speed threshold is
introduced. Completion of that workflow closes the planned evidence collection
before an explicit 0.12 RC decision.

Until then, 0.12 remains a research/development line rather than a stable
release claim.
