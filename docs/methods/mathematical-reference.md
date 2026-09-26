---
title: Mathematical reference
---

# Mathematical contracts

Need a concise function-level lookup instead of the expanded derivation? Use the generated [function → equation index](../reference/function-equation-index.md) or query `get_mathematical_contract()` directly. Both are backed by the same 0.22 registry and validated in CI.

This page records the equations implemented by `eyetrajectoriespy`. It is a **software contract reference**: each equation is paired with the public API that implements it and with the scope limits that matter for interpretation.

!!! note "Notation"
    \(i\) indexes trajectories or independent units, \(t_m\) the observed common grid, \(d\) functional dimensions, and \(k\) retained functional principal components. Bold symbols denote vectors or matrices.

## Quadrature on the observed grid { #quadrature }

For strictly increasing grid points \(t_1,\ldots,t_M\), `functional_trapezoid_weights()` uses trapezoidal weights

$$
w_1=\frac{t_2-t_1}{2},\qquad
w_M=\frac{t_M-t_{M-1}}{2},
$$

and for \(m=2,\ldots,M-1\),

$$
w_m=\frac{(t_m-t_{m-1})+(t_{m+1}-t_m)}{2}.
$$

When `normalize=True`,

$$
\widetilde w_m=\frac{w_m}{\sum_{\ell=1}^{M}w_\ell}.
$$

**API:** `functional_trapezoid_weights()`.

## Quadrature-weighted FPCA / MFPCA { #fpca }

Let \(\mathbf G_i(t_m)\in\mathbb R^D\) and

$$
\widehat{\boldsymbol\mu}(t_m)
=
\frac{1}{n}\sum_{i=1}^{n}\mathbf G_i(t_m).
$$

With `scaling="dimension_sd"`, dimension \(d\) is scaled by the square root of its mean integrated variance,

$$
s_d
=
\left[
\sum_{m=1}^{M}
w_m
\left\{
\frac{1}{n}
\sum_{i=1}^{n}
\bigl(G_{id}(t_m)-\widehat\mu_d(t_m)\bigr)^2
\right\}
\right]^{1/2}.
$$

For `scaling="none"`, \(s_d=1\).

The implementation forms the weighted Euclidean representation

$$
Z_{i,m,d}
=
\frac{G_{id}(t_m)-\widehat\mu_d(t_m)}{s_d}\sqrt{w_m},
$$

fits ordinary PCA to the flattened \(Z_i\), and maps the Euclidean loading vector back to the functional component

$$
\widehat\phi_{k,d}(t_m)
=
\frac{v_{k,m,d}}{\sqrt{w_m}}\,s_d.
$$

For a compatible target trajectory \(\mathbf G\), the stored score projection is

$$
\widehat\xi_k
=
\sum_{m=1}^{M}\sum_{d=1}^{D}
\frac{G_d(t_m)-\widehat\mu_d(t_m)}{s_d}
\sqrt{w_m}\,
v_{k,m,d}.
$$

Reconstruction with \(K\) components is

$$
\widehat{\mathbf G}^{(K)}_i(t_m)
=
\widehat{\boldsymbol\mu}(t_m)
+
\sum_{k=1}^{K}\widehat\xi_{ik}\widehat{\boldsymbol\phi}_k(t_m).
$$

The interpretation curves from `component_trajectories()` are

$$
\widehat{\boldsymbol\mu}(t)
+
a\sqrt{\widehat\lambda_k}\,
\widehat{\boldsymbol\phi}_k(t),
$$

where \(a\) is an analyst-selected score-SD multiplier.

**API:** `fit_fpca()`, `fit_mfpca()`, `transform_fpca()`, `reconstruct_fpca()`, `component_trajectories()`.

## Integrated functional \(L^2\) distance { #functional-l2 }

For two complete multivariate trajectories \(\mathbf a,\mathbf b\) and optional non-negative dimension weights \(\omega_d\),

$$
d_{L^2}(\mathbf a,\mathbf b)
=
\left[
\sum_{m=1}^{M}
w_m
\sum_{d=1}^{D}
\omega_d
\{a_d(t_m)-b_d(t_m)\}^2
\right]^{1/2}.
$$

**API:** `functional_l2_distance()`, `pairwise_functional_distances()`.

## Discrete Fréchet trajectory distance { #discrete-frechet }

For ordered point sequences \(P=(p_1,\ldots,p_m)\) and \(Q=(q_1,\ldots,q_n)\), define the optional weighted Euclidean local distance

$$
d_w(\mathbf p_i,\mathbf q_j)
=
\left[
\sum_r \omega_r(p_{ir}-q_{jr})^2
\right]^{1/2}.
$$

The dynamic-programming recurrence is

$$
D_{i,j}
=
\max\left\{
d_w(\mathbf p_i,\mathbf q_j),
\min(D_{i-1,j},D_{i-1,j-1},D_{i,j-1})
\right\},
$$

with first-row and first-column cumulative maxima and

$$
\delta_{dF}(P,Q)=D_{m,n}.
$$

The admissible coupling is monotone and does not backtrack. Elapsed timestamps do not appear in the recurrence. Version 0.32 does not interpolate, resample, normalize, simplify, smooth, or delete trajectory points before evaluation.

When an audit result is requested, the package returns one deterministic optimal coupling. Multiple optimal couplings can exist, so that path is not claimed to be unique.

**API:** `discrete_frechet_distance()`, `pairwise_discrete_frechet_distances()`.

## Dynamic time warping trajectory distance { #dynamic-time-warping }

For complete ordered point sequences \(P=(p_1,\ldots,p_m)\) and \(Q=(q_1,\ldots,q_n)\), the implementation uses weighted Euclidean local cost

$$
d_w(\mathbf p_i,\mathbf q_j)
=
\left[
\sum_r \omega_r(p_{ir}-q_{jr})^2
\right]^{1/2},
$$

where all \(\omega_r\ge 0\) and at least one dimension weight is positive.

### symmetric1: preserved 0.33 raw-cost contract

The backward-compatible default is

$$
C^{(s1)}_{i,j}
=
d_w(\mathbf p_i,\mathbf q_j)
+
\min
\left(
C_{i-1,j-1},
C_{i-1,j},
C_{i,j-1}
\right).
$$

Every visited point contributes one local-distance unit. This pattern is retained so existing 0.33 calls keep the same numerical meaning. It does not have the path-independent \(m+n\) normalization used by symmetric2, so normalize=True is rejected rather than inventing a denominator.

### symmetric2: normalizable symmetric weighting

For symmetric2, a diagonal advance contributes two local-distance units and horizontal/vertical advances contribute one:

$$
C^{(s2)}_{i,j}
=
\min
\left\{
C_{i-1,j-1}+2d_w(\mathbf p_i,\mathbf q_j),
C_{i-1,j}+d_w(\mathbf p_i,\mathbf q_j),
C_{i,j-1}+d_w(\mathbf p_i,\mathbf q_j)
\right\}.
$$

The initial point has weight two, so for a complete global alignment the total step weight has the path-independent denominator \(m+n\). The normalized distance is therefore

$$
d^{(s2)}_{\mathrm{norm}}(P,Q)
=
\frac{C^{(s2)}_{m,n}}{m+n}.
$$

The audit result retains the raw cumulative distance, the normalized symmetric2 distance when defined, every path-local distance, every step weight, and every weighted local contribution. Their weighted sum must reproduce the raw dynamic-programming optimum.

### Sakoe-Chiba sample-index constraint

With an explicit non-negative radius \(w\), only cells satisfying

$$
|i-j|\le w
$$

are admissible. The band is expressed in sample indices. It is not a tolerance in milliseconds or seconds. A band that cannot connect unequal-length endpoints fails explicitly rather than being widened.

### Interpretation boundary

Recorded timestamps do not appear in either recurrence. DTW can therefore align away latency, dwell, or local progression-rate differences that may be scientifically meaningful. Use a time-preserving complementary analysis when elapsed trial time is part of the estimand.

Version 0.34 does not interpolate, resample, smooth, normalize coordinates, simplify paths, delete missing observations, choose a step pattern, tune a window, or choose normalization automatically.

**API:** dynamic_time_warping_distance(), pairwise_dynamic_time_warping_distances().


## Trajectory-distance specification sensitivity { #trajectory-distance-sensitivity }

Version 0.38 compares the same trajectories under multiple **declared**
distance contracts rather than adding another trajectory-distance metric.

For specification \(s\), let \(D^{(s)}\) be the complete pairwise distance
matrix and collect the unique unordered curve-pair distances as

$
\mathbf v^{(s)}
=
\{D_{ij}^{(s)}:1\le i<j\le n\}.
$

The first global diagnostic is the Spearman correlation of the pair-distance
rankings,

$
\rho_S(s,r)
=
\operatorname{corr}
\left(
\operatorname{rank}\mathbf v^{(s)},
\operatorname{rank}\mathbf v^{(r)}
\right).
$

Average ranks are used for ties. The implementation also retains the mean,
median, and maximum absolute difference between pair-distance ranks. Raw-scale
Pearson correlation is reported only as a descriptive secondary quantity.

### Local neighborhood agreement

For curve \(i\), define its \(k\)-nearest-neighbor set under specification
\(s\) as \(\mathcal N_k^{(s)}(i)\). The per-curve overlap is

$
J_k^{(s,r)}(i)
=
\frac{
|\mathcal N_k^{(s)}(i)\cap\mathcal N_k^{(r)}(i)|
}{
|\mathcal N_k^{(s)}(i)\cup\mathcal N_k^{(r)}(i)|
}.
$

The result stores both the per-curve Jaccard values and their specification-pair
mean. It also reports the fraction of curves having exactly the same top-\(k\)
neighbor set and the nearest-neighbor identity agreement

$
A_1^{(s,r)}
=
\frac{1}{n}
\sum_{i=1}^{n}
\mathbb I
\{
\mathcal N_1^{(s)}(i)=\mathcal N_1^{(r)}(i)
\}.
$

Neighbor ordering uses a stable deterministic curve-order tie break for
reproducibility. If the \(k\)th and \((k+1)\)th distances are tied at the
selection boundary, that fact is flagged so a deterministic ordering is not
mistaken for uniquely identified neighbors.

### Scale and inference boundary

L2, discrete Fréchet, raw DTW, and normalized DTW are not forced onto a common
numeric scale. Version 0.38 therefore keeps every distance matrix on its native
scale and emphasizes rank and neighbor agreement for cross-contract
comparison.

No p-value is attached to the correlation of upper-triangle distances because
those pairwise entries reuse trajectories and are not treated as independent
observations. No consensus distance, weighted average, "robustness score," or
best-metric selection is produced.

**API:** `trajectory_distance_sensitivity()`,
`trajectory_distance_comparison_frame()`,
`trajectory_distance_neighbor_frame()`.

## Continuous planar trajectory geometry { #trajectory-geometry }

For a declared planar trajectory

$$
\mathbf G(t)=
\begin{bmatrix}
x(t)\\
y(t)
\end{bmatrix},
$$

the wrapped heading function is

$$
\theta(t)
=
\operatorname{atan2}
\left\{
y'(t),
x'(t)
\right\}.
$$

`heading_function()` reports this angle in radians on the recorded coordinate axes. It does not unwrap the angle automatically.

The signed curvature is

$$
\kappa(t)
=
\frac{
x'(t)y''(t)-y'(t)x''(t)
}{
\left\{
x'(t)^2+y'(t)^2
\right\}^{3/2}
}.
$$

The signed turning rate is

$$
\omega(t)
=
\frac{
x'(t)y''(t)-y'(t)x''(t)
}{
x'(t)^2+y'(t)^2
}
=
\kappa(t)
\left\|
\mathbf G'(t)
\right\|.
$$

The implementation differentiates numerically with respect to the observed time grid using `numpy.gradient(..., edge_order=2)`. It does not smooth, interpolate, rescale, or add a denominator epsilon.

Heading, curvature, and turning rate are undefined where

$$
\left\|
\mathbf G'(t)
\right\|
\le
v_{\min},
$$

where `min_speed` is an explicit analysis parameter. The default \(v_{\min}=0\) masks only mathematically stationary samples; a positive threshold must be chosen explicitly if near-zero velocity is scientifically regarded as unstable. Under `undefined_policy="nan"`, undefined samples remain missing rather than being changed to zero. Under `undefined_policy="raise"`, any such sample aborts the calculation.

For a complete observed path, tortuosity is defined as

$$
T
=
\frac{
\sum_{m=1}^{M-1}
\left\|
\mathbf G(t_{m+1})-\mathbf G(t_m)
\right\|_2
}{
\left\|
\mathbf G(t_M)-\mathbf G(t_1)
\right\|_2
}.
$$

A straight path has \(T=1\). If endpoint displacement is at or below the declared `min_displacement`, the ratio is undefined; the same explicit `nan` versus `raise` policy applies.

These quantities depend on the **metric and orientation of the supplied coordinates**. Separately normalized screen axes can distort Euclidean geometry if horizontal and vertical units are not commensurate. Likewise, if recorded screen \(y\) increases downward, the visual interpretation of curvature/turning sign is reversed relative to a conventional Cartesian \(y\)-up display. The package does not guess or silently flip either axis.

**API:** `heading_function()`, `signed_curvature_function()`, `turning_rate_function()`, and `trajectory_tortuosity()`.

## Two-level functional decomposition { #multilevel }

For participant \(i\), trial \(j\), the implemented transparent functional-ANOVA decomposition is

$$
\mathbf G_{ij}(t)
=
\boldsymbol\mu(t)
+
\mathbf U_i(t)
+
\mathbf V_{ij}(t),
$$

with

$$
\mathbf U_i(t)
=
\overline{\mathbf G}_{i\cdot}(t)-\boldsymbol\mu(t),
\qquad
\mathbf V_{ij}(t)
=
\mathbf G_{ij}(t)-\overline{\mathbf G}_{i\cdot}(t).
$$

Separate FPCAs are then fit to \(\mathbf U_i\) and \(\mathbf V_{ij}\).

**API:** `fit_multilevel_fpca()`.

## Compositional AOI trajectories { #compositional }

At every time point the AOI probabilities obey

$$
p_k(t)\ge 0,\qquad
\sum_{k=1}^{K}p_k(t)=1.
$$

After explicit zero replacement \(p_k^\epsilon(t)=\max\{p_k(t),\epsilon\}\) and renormalization, the additive log-ratio coordinate relative to reference component \(r\) is

$$
z_k(t)
=
\log\frac{p_k^\epsilon(t)}{p_r^\epsilon(t)},
\qquad k\ne r.
$$

For inverse ALR, define \(q_r(t)=1\) and \(q_k(t)=\exp\{z_k(t)\}\) for \(k\ne r\); then

$$
p_k(t)=\frac{q_k(t)}{\sum_{\ell=1}^{K}q_\ell(t)}.
$$

**API:** `alr_transform()`, `inverse_alr()`, `fit_compositional_fpca()`.

## Landmark registration { #registration }

For curve \(i\), `register_to_landmarks()` constructs a monotone piecewise-linear warp \(h_i(t)\) that maps reference landmark times to observed landmark times and evaluates

$$
\mathbf G_i^{\mathrm{reg}}(t)
=
\mathbf G_i\{h_i(t)\}.
$$

Phase displacement is retained as

$$
\Delta_i(t)=h_i(t)-t.
$$

**API:** `register_to_landmarks()`, `warping_displacement()`, `phase_summary()`.

## Simultaneous functional mean band { #mean-band }

Let \(\mathbf X_i(t_m)\) denote the independent inferential units: either curves or equal-weight participant-average curves. The mean and pointwise standard error are

$$
\overline{\mathbf X}(t_m)
=
\frac{1}{n}\sum_{i=1}^{n}\mathbf X_i(t_m),
\qquad
\widehat{\mathrm{SE}}_d(t_m)
=
\frac{\widehat\sigma_d(t_m)}{\sqrt n}.
$$

For multiplier replicate \(b\), with \(e_i^{(b)}\stackrel{\mathrm{iid}}{\sim}N(0,1)\),

$$
Z_d^{(b)}(t_m)
=
\frac{
n^{-1/2}
\sum_{i=1}^{n}
e_i^{(b)}
\{X_{id}(t_m)-\overline X_d(t_m)\}
}{
\widehat\sigma_d(t_m)
},
$$

and

$$
M^{(b)}
=
\max_{m,d}
\left|Z_d^{(b)}(t_m)\right|.
$$

With \(c_{1-\alpha}\) the empirical \((1-\alpha)\)-quantile of \(M^{(b)}\), the observed-grid simultaneous band is

$$
\overline X_d(t_m)
\pm
c_{1-\alpha}\widehat{\mathrm{SE}}_d(t_m).
$$

**API:** `multiplier_functional_mean_band()`; `windowed_rqa_functional_mean_band()` reuses this calibration after constructing the declared RQA-derived functional trajectories.

## Functional mixed-effects regression { #functional-mixed-effects }

Version 0.36 introduces a deliberately narrow functional mixed-effects model
for repeated common-grid trajectories. For participant \(i\), trial \(j\), and
one selected response dimension,

$
Y_{ij}(t)
=
\mathbf x_{ij}^{\top}\boldsymbol\beta(t)
+
b_i(t)
+
\varepsilon_{ij}(t),
$

where the participant-specific functional random intercept is

$
b_i(t)
=
\mathbf B_r(t)^{\top}\mathbf u_i.
$

Each fixed coefficient function is represented in a declared clamped B-spline
basis,

$
\beta_p(t)
=
\mathbf B_f(t)^{\top}\boldsymbol\theta_p.
$

The random basis coefficients follow

$
\mathbf u_i
\sim
N(\mathbf 0,\boldsymbol\Psi),
$

with one unstructured covariance matrix \(\boldsymbol\Psi\) shared across
participants. Conditional residual errors are

$
\varepsilon_{ij}(t_m)
\sim
N(0,\sigma^2),
$

independently over the stacked grid once the fixed and participant random
effects are conditioned upon.

For the stacked observations of participant \(i\), the marginal covariance
under the implemented model is

$
\operatorname{Cov}(\mathbf Y_i\mid\mathbf X_i)
=
\mathbf Z_i\boldsymbol\Psi\mathbf Z_i^\top
+
\sigma^2\mathbf I.
$

The fixed-effect design is formed by tensoring each scalar design column with
the fixed B-spline basis. The participant random-effect design uses the random
B-spline basis for every curve belonging to the participant. For the historical
participant-only model, all curve-by-time observations are fitted in **one**
Gaussian linear mixed model using `statsmodels.MixedLM`; there is no separate
mixed-model fit at each time point.

### Version 0.48 nested trial functional random intercept

When explicitly requested, version 0.48 extends the conditional mean to

$
Y_{ij}(t)
=
\mathbf x_{ij}^{\top}\boldsymbol\beta(t)
+
b_i(t)
+
u_{ij}(t)
+
\varepsilon_{ij}(t),
$

where

$
u_{ij}(t)=\mathbf B_u(t)^\top\mathbf v_{ij},
\qquad
\mathbf v_{ij}\sim
N(\mathbf 0,\boldsymbol\Psi_{trial}).
$

One unstructured \(\boldsymbol\Psi_{trial}\) is shared across nested trials.
It is distinct from the participant covariance and is not replaced by an
independent scalar variance-component approximation.

For participant \(i\), the marginal covariance is

$
\mathbf V_i
=
\mathbf Z_i\boldsymbol\Psi_p\mathbf Z_i^\top
+
\sum_j
\mathbf W_{ij}\boldsymbol\Psi_{trial}\mathbf W_{ij}^\top
+
\sigma^2\mathbf I.
$

The participant and trial covariance matrices are parameterized through
Cholesky factors. For every covariance-parameter evaluation, the fixed B-spline
coefficients are profiled by generalized least squares. This explicit nested
backend is used only when
`trial_random_effect="functional_intercept"`; participant-only fits preserve
the established MixedLM implementation.

Version 0.48 requires an explicit trial identifier, unique participant/trial
pairs, at least two observed trials per participant, an analyst-declared trial
basis size, and more nested trials than free parameters in the unstructured
trial covariance. Those requirements are conservative identifiability/
complexity guards rather than guarantees of precise covariance estimation.

Participant and trial random coefficients are independent in the 0.48 model:
no participant–trial cross-covariance is estimated. Trial covariance
eigenvalues, condition number, boundary/singularity diagnostics, trial BLUP
coefficients, and reconstructed trial functions are retained.

### Version 0.49 explicit residual covariance

Version 0.49 replaces the iid residual block only when an analyst explicitly
declares a serial family. For each source curve/trial,

\[
\boldsymbol\varepsilon_{ij}
\sim
N(\mathbf 0,\sigma^2\mathbf R_\theta).
\]

The physical-time exponential family is

\[
R_\phi(t,s)
=
\exp\!\left(-\frac{|t-s|}{\phi}\right),
\qquad \phi>0,
\]

with \(\phi=\exp(\eta_\phi)\). The parameter \(\phi\) is therefore in the same
physical time unit as the trajectory grid and remains meaningful on an
unequally spaced common grid.

For a verified equally spaced common grid, AR(1) is

\[
R_{\rho,rs}
=
\rho^{|r-s|},
\qquad
-1<\rho<1,
\]

with \(\rho=\tanh(\eta_\rho)\). This is an index-step model. Negative
\(\rho\) is supported; continuous-time exponential correlation is not treated
as an equivalent parameterization when \(\rho<0\).

The participant marginal covariance becomes

\[
\mathbf V_i
=
\mathbf Z_i\boldsymbol\Psi_P\mathbf Z_i^\top
+
\sum_j
\mathbf W_{ij}\boldsymbol\Psi_T\mathbf W_{ij}^\top
+
\sigma^2\operatorname{blockdiag}_j\{\mathbf R_\theta\}.
\]

Residual correlation therefore never crosses source-curve/trial boundaries.
The trial term is omitted when no trial functional random effect is declared,
and \(\mathbf R_\theta=\mathbf I\) under the iid model.

For diagnostic whitening,

\[
\sigma^2\mathbf R_\theta=\mathbf L\mathbf L^\top,
\qquad
\mathbf e_{ij}^{(w)}=\mathbf L^{-1}\mathbf e_{ij}.
\]

A serial model is not judged by requiring the raw residual ACF to vanish:
correlation is expected in the raw residual scale under the fitted model.
The whitened residual ACF/variogram instead diagnose remaining serial
structure after applying the declared residual covariance. Numerical
optimizer bounds and boundary proximity are retained rather than hidden.

### Trial-varying predictors

Unlike the 0.35 participant-aggregation route, trial-varying scalar predictors
are allowed because all trials remain in the stacked likelihood and
participant clustering is represented by \(b_i(t)\). Thus a within-participant
condition can enter \(\mathbf x_{ij}\) directly.

### Basis and covariance boundary

Version 0.36 does not choose the number of fixed or random basis functions.
The analyst supplies `fixed_basis_size`, `random_basis_size`, and
`spline_degree`. No smoothing penalty is estimated automatically.

The participant random-basis covariance is unstructured. Fits with an
estimated covariance eigenvalue at or near the numerical boundary are retained
but flagged in the result rather than silently interpreted as regular fits.

### Inferential boundary

The base 0.36 fit propagates the fitted fixed-parameter covariance through the
declared basis and exposes 95% **pointwise Wald intervals**. Those pointwise
intervals do not themselves provide whole-function coverage.

Version 0.44 adds a separate participant-cluster bootstrap layer for
observed-grid simultaneous fixed-coefficient bands. That layer re-estimates
fixed coefficients under whole-participant resampling while conditioning on the
reference random-effect covariance, residual variance, and declared bases.
The fixed-covariance bootstrap does not claim variance-component
uncertainty, basis-selection uncertainty, or continuous-between-grid coverage.
When a serial residual model is declared, it conditions on that fitted residual
covariance as well as the participant/trial covariance terms. Version 0.45
supports exactly one guarded participant random functional slope, version 0.46
adds a full-refit participant bootstrap, version 0.48 adds one nested trial
functional random intercept, and version 0.49 adds explicit exponential/AR(1)
within-trial residual covariance plus diagnostic whitening. The full-refit
bootstrap re-estimates every declared covariance parameter, including phi/rho,
without changing the predeclared covariance family. Multiple participant/trial
random effects, generalized/non-Gaussian responses, and joint cross-dimension
covariance remain outside the current model.

A non-converged optimizer result raises rather than being returned as a valid
scientific fit.

**API:** `fit_functional_mixed_effects_regression()`,
`functional_mixed_effects_coefficient_frame()`,
`functional_mixed_effects_whitened_residuals()`;
for whole-function observed-grid inference see
`bootstrap_functional_mixed_effects_coefficients()` and
`functional_mixed_effects_simultaneous_bands()`.

## Covariance-structure sensitivity { #functional-mixed-effects-covariance-sensitivity }

Version 0.50 compares already fitted, predeclared covariance structures against
one analyst-declared reference. It does not fit covariance combinations or
select a preferred model.

For model \(m\) relative to reference \(r\),

\[
\Delta\beta_m(t)
=
\widehat\beta_m(t)-\widehat\beta_r(t).
\]

The two retained coefficient-robustness summaries are

\[
D_{\infty,m}
=
\sup_t |\Delta\beta_m(t)|
\]

and

\[
D_{2,m}
=
\left[
\int
\{\Delta\beta_m(t)\}^2\,dt
\right]^{1/2},
\]

with the latter evaluated by trapezoidal integration on the observed time grid.

Covariance matrices are also mapped back to interpretable functional scales.
For the participant random intercept and optional trial random intercept,

\[
v_{P0}(t)
=
\mathbf B_P(t)^\top
\boldsymbol\Psi_{P0}
\mathbf B_P(t),
\qquad
v_T(t)
=
\mathbf B_T(t)^\top
\boldsymbol\Psi_T
\mathbf B_T(t),
\]

while the pointwise residual marginal variance is

\[
v_\varepsilon(t)=\sigma^2.
\]

When a participant random slope is present, its variance function and the
intercept/slope cross-covariance function are retained separately rather than
collapsed into one percentage.

Information criteria are descriptive. Under ML,

\[
k_{\mathrm{ML}}
=
k_{\mathrm{fixed}}+k_{\mathrm{covariance}},
\]

whereas under REML with identical fixed design/basis the recorded restricted
likelihood convention uses

\[
k_{\mathrm{REML}}
=
k_{\mathrm{covariance}}.
\]

The reported criteria are

\[
\mathrm{AIC}_m=-2\ell_m+2k_m,
\qquad
\mathrm{BIC}_m=-2\ell_m+k_m\log n,
\]

with the explicit BIC convention

\[
n=n_{\mathrm{curves}}n_{\mathrm{time}}.
\]

That observation count is a transparent calculation convention rather than a
claim about a unique effective sample size for clustered functional data.

Successful models are compared only when observations, fixed design/basis,
participant mapping/basis, response dimension, time grid/unit, spline degree,
and ML/REML mode match. Matching trial identities/bases are also required when
both models contain trial functional effects. Failed predeclared models remain
visible with their failure reasons and NaN numerical comparisons.

Raw and whitened residual diagnostics are retained side by side. Simultaneous
band-width ratios are available only when supplied bands use the same
confidence/scope/bootstrap contract and identical participant bootstrap draws.
No model ranking, automatic covariance selection, or likelihood-ratio p-values
are produced.

**API:** `functional_mixed_effects_covariance_sensitivity()`,
`functional_mixed_effects_variance_decomposition()`.

## One participant random functional slope { #functional-mixed-effects-random-slope }

Version 0.45 adds exactly one analyst-declared participant random functional
slope to the existing random functional intercept model:

$$
Y_{ij}(t)
=
\mathbf x_{ij}^{\top}\boldsymbol\beta(t)
+
b_{0i}(t)
+
X_{ij,q}b_{1i}(t)
+
\varepsilon_{ij}(t).
$$

The random intercept and random slope are represented as

$$
b_{0i}(t)
=
\mathbf B_r(t)^{\top}\mathbf u_{0i},
\qquad
b_{1i}(t)
=
\mathbf B_r(t)^{\top}\mathbf u_{1i}.
$$

Version 0.45 deliberately uses the same declared `random_basis_size=q` for
both functions. The stacked random coefficient vector satisfies

$$
\begin{bmatrix}
\mathbf u_{0i}\\
\mathbf u_{1i}
\end{bmatrix}
\sim
N\!\left(
\mathbf 0,
\boldsymbol\Psi_{2q}
\right),
$$

with one full unstructured covariance. Therefore,

$$
p_{\Psi}
=
\frac{(2q)(2q+1)}{2}.
$$

For the default $q=4$, the random-effect dimension is 8 and the covariance
contains 36 free parameters. The guarded 0.45 implementation requires
$n_{\mathrm{participants}}>p_{\Psi}$, so that default slope specification
requires at least 37 participants.

The slope predictor must be one of the declared fixed predictors and must vary
within every participant. No automatic random-slope choice or fallback to an
intercept-only model occurs.

The result retains the full random-effect design matrix, full covariance,
intercept/intercept block, slope/slope block, intercept/slope cross-covariance,
eigenvalues, covariance condition number, covariance parameter count,
boundary/singularity diagnostics, participant BLUP coefficient matrices, and
the reconstructed participant random-intercept and random-slope functions.

The 0.44 simultaneous-band bootstrap remains available. With a random slope,
it conditions on the fitted full intercept/slope covariance exactly as it
conditions on the random-intercept covariance in the simpler model; it does not
refit variance components.

**API:** `fit_functional_mixed_effects_regression()`,
`functional_random_effect_frame()`,
`plot_functional_random_effects()`.

## Full-refit participant bootstrap for functional mixed-effects models { #functional-mixed-effects-full-refit-bootstrap }

Version 0.46 adds whole-participant resampling with complete parameter refitting
under the already-declared mixed-effects specification.

For bootstrap replicate \(b\),

$
I_1^{*(b)},\ldots,I_n^{*(b)}
\overset{\mathrm{iid}}{\sim}
\{1,\ldots,n\}.
$

Each occurrence of a sampled source participant receives a distinct bootstrap
group identity. This prevents repeated draws of one participant from being
merged into one random-effect group by the mixed-model backend.

The bootstrap sample is refitted to obtain

$
\mathcal D^{*(b)}
\longrightarrow
\left\{
\widehat{\boldsymbol\beta}^{*(b)}(t),
\widehat{\boldsymbol\Psi}^{*(b)},
\widehat{\sigma}^{2*(b)}
\right\}.
$

Thus, unlike the 0.44 fixed-covariance participant bootstrap, 0.46 re-estimates
the complete random-effect covariance and residual variance in every replicate.

The declared model specification remains fixed: preprocessing, response
dimension, predictor set, fixed/random basis sizes, spline degree,
random-slope structure, REML/ML choice, optimizer, and optimizer iteration
limit are not reselected.

For direct sensitivity comparison,

$
R_p(t_m)
=
\frac{
W_{p,\mathrm{full}}(t_m)
}{
W_{p,\mathrm{fixed}}(t_m)
},
$

where \(W_{p,\mathrm{full}}(t_m)\) and
\(W_{p,\mathrm{fixed}}(t_m)\) are simultaneous-band widths at coefficient
\(p\) and observed time \(t_m\).

Values substantially different from one indicate that variance-component
re-estimation changes fixed-effect uncertainty under the declared model. The
ratio is descriptive rather than a formal model-comparison statistic.

The full-refit result retains every covariance matrix, covariance eigenvalues
and condition numbers, boundary/singularity flags, residual variances, log
likelihoods, convergence states, backend warnings, source participant IDs, and
bootstrap participant IDs.

**API:** `bootstrap_functional_mixed_effects_full_refit()`,
`functional_mixed_effects_full_refit_audit_frame()`,
`functional_mixed_effects_variance_bootstrap_frame()`,
`compare_functional_mixed_effects_bootstraps()`.

## Participant-cluster simultaneous mixed-effects coefficient bands { #functional-mixed-effects-simultaneous }

Version 0.44 adds whole-function observed-grid inference for the fixed
coefficient functions from the 0.36 joint functional mixed-effects model.

For participant \(i\), the fitted marginal covariance is

$$
\mathbf V_i
=
\mathbf Z_i\widehat{\boldsymbol\Psi}\mathbf Z_i^\top
+
\widehat\sigma^2\mathbf I.
$$

With participant-level fixed-effect design \(\mathbf X_i\) and stacked
functional response \(\mathbf y_i\), define

$$
\mathbf A_i
=
\mathbf X_i^\top\mathbf V_i^{-1}\mathbf X_i,
\qquad
\mathbf s_i
=
\mathbf X_i^\top\mathbf V_i^{-1}\mathbf y_i.
$$

A bootstrap replicate samples \(n\) participant indices with replacement,
\(I_1^{(b)},\ldots,I_n^{(b)}\). Every selected participant contributes the
complete set of that participant's trial-by-time observations. The fixed basis
coefficients are then re-estimated conditionally on the fitted covariance model:

$$
\widehat{\boldsymbol\theta}^{*(b)}
=
\left[
\sum_{r=1}^{n}
\mathbf A_{I_r^{(b)}}
\right]^{-1}
\sum_{r=1}^{n}
\mathbf s_{I_r^{(b)}}.
$$

For coefficient \(p\), the bootstrap pointwise standard deviation is used to
studentize the centered bootstrap coefficient process,

$$
M_p^{*(b)}
=
\max_m
\left|
\frac{
\widehat\beta_p^{*(b)}(t_m)
-
\overline{\widehat\beta_p^*}(t_m)
}{
\widehat{\mathrm{SE}}_p^*(t_m)
}
\right|.
$$

The empirical \(1-\alpha\) quantile \(c_{p,1-\alpha}\) gives

$$
\widehat\beta_p(t_m)
\pm
c_{p,1-\alpha}
\widehat{\mathrm{SE}}_p^*(t_m).
$$

With `simultaneous_scope="family"`, the maximum is instead taken jointly over
all fixed coefficients and observed time points before calibration.

This is a **participant-cluster case bootstrap conditional on the fitted
covariance model and declared bases**. It does not refit
\(\widehat{\boldsymbol\Psi}\), \(\widehat\sigma^2\), basis sizes, spline
degree, preprocessing, or model specification inside resamples. The coverage
claim is simultaneous over the observed time grid only, not every point of the
continuous B-spline domain.

**API:** `bootstrap_functional_mixed_effects_coefficients()`,
`functional_mixed_effects_simultaneous_bands()`.

## Marginal generalized function-on-scalar regression { #generalized-function-on-scalar }

Version 0.51 models repeated non-Gaussian functional responses through a
population-averaged generalized estimating equation. For participant \(i\),
trial \(j\), and observed time \(t\),

\[
g\{\mu_{ij}(t)\}
=
\mathbf x_{ij}^{\top}\boldsymbol\beta(t),
\qquad
\mu_{ij}(t)
=
E\{Y_{ij}(t)\mid\mathbf x_{ij}\}.
\]

Each coefficient function is represented by a fixed analyst-declared B-spline
basis,

\[
\beta_k(t)
=
\mathbf B(t)^\top\boldsymbol\theta_k.
\]

For Bernoulli responses, \(g\) is the logit link and observations must be coded
exactly as 0/1. For Poisson responses, \(g\) is the log link and observations
must be non-negative integer counts.

Participants are the independent GEE clusters. Trial-varying scalar predictors
remain in the design; trials are not averaged before fitting. Version 0.51
fixes the working dependence structure to independence and uses the robust
cluster sandwich covariance,

\[
\widehat{\operatorname{Var}}_{\mathrm{robust}}
(\widehat{\boldsymbol\theta})
=
\mathbf A^{-1}
\mathbf B_{\mathrm{sand}}
\mathbf A^{-1}.
\]

Pointwise coefficient-function standard errors are obtained by mapping the
robust covariance of the basis coefficients through \(\mathbf B(t)\).

If there are \(K\) scalar coefficients including the intercept and \(q\) basis
functions per coefficient, the expanded parameter vector has \(Kq\) entries.
The implementation requires

\[
n_{\mathrm{participants}}>Kq.
\]

This is a minimum structural guard, not an adequacy theorem for robust sandwich
inference.

Whole-participant case bootstrap refits resample complete participant bundles.
Duplicate source-participant draws receive distinct bootstrap cluster
identities. For coefficient \(k\),

\[
M_k^{*(b)}
=
\max_m
\left|
\frac{
\widehat\beta_k^{*(b)}(t_m)-\widehat\beta_k(t_m)
}{
\widehat{\mathrm{SE}}\{\widehat\beta_k(t_m)\}
}
\right|.
\]

The resulting observed-grid simultaneous band is calibrated on the link scale.
A familywise option takes the maximum across all declared coefficient functions
and observed time points.

The coefficients are marginal / population averaged. They are not conditional
generalized mixed-model coefficients. No family, link, basis dimension, working
correlation, smoothing penalty or model is selected automatically.

**API:** `fit_generalized_function_on_scalar_regression()`,
`bootstrap_generalized_function_on_scalar_coefficients()`,
`generalized_function_on_scalar_simultaneous_bands()`.

## Function-on-scalar regression { #function-on-scalar }

Let \(Y_{id}(t_m)\) be functional response dimension \(d\) for independent inference unit \(i\), and let \(\mathbf x_i\) contain an intercept and the analyst-declared scalar predictors. At each observed time and selected response dimension,

$
Y_{id}(t_m)
=
\mathbf x_i^\top\boldsymbol\beta_d(t_m)
+
\varepsilon_{id}(t_m).
$

Stacking inference units gives

$
\mathbf Y_d(t_m)
=
\mathbf X\boldsymbol\beta_d(t_m)
+
\boldsymbol\varepsilon_d(t_m),
$

with full-rank observed-grid OLS estimator

$
\widehat{\boldsymbol\beta}_d(t_m)
=
(\mathbf X^\top\mathbf X)^{-1}
\mathbf X^\top\mathbf Y_d(t_m).
$

The package does not smooth the coefficient functions or expand them in a basis in version 0.35. Each coefficient curve is therefore the sequence of observed-grid OLS estimates under one shared design matrix.

### HC1 pointwise sandwich standard errors

Let

$
\mathbf A
=
\mathbf X(\mathbf X^\top\mathbf X)^{-1},
$

and let \(\widehat\varepsilon_{id}(t_m)\) be the fitted residual. For coefficient \(j\), the diagonal HC1 variance estimate is

$
\widehat V_{j,d}(t_m)
=
\frac{n}{n-p}
\sum_{i=1}^{n}
\left[
A_{ij}\widehat\varepsilon_{id}(t_m)
\right]^2,
$

where \(p=\operatorname{rank}(\mathbf X)\). The reported pointwise standard error is \(\sqrt{\widehat V_{j,d}(t_m)}\).

### Fixed-design wild bootstrap

For bootstrap replicate \(b\), one multiplier is drawn per independent inference unit and the complete residual function is multiplied as a unit:

$
Y_{id}^{*(b)}(t_m)
=
\widehat Y_{id}(t_m)
+
W_i^{(b)}\widehat\varepsilon_{id}(t_m).
$

Version 0.35 supports Rademacher or standard-normal multipliers. The design matrix is held fixed, so a declared full-rank design does not become rank deficient because of bootstrap row resampling.

For coefficient-specific simultaneous calibration,

$
M_j^{*(b)}
=
\max_{m,d}
\left|
\frac{
\widehat\beta_{j,d}^{*(b)}(t_m)
-
\widehat\beta_{j,d}(t_m)
}{
\widehat{\mathrm{SE}}\{\widehat\beta_{j,d}(t_m)\}
}
\right|.
$

If \(c_{j,1-\alpha}\) is the empirical \((1-\alpha)\)-quantile of these maxima, the observed-grid simultaneous band is

$
\widehat\beta_{j,d}(t_m)
\pm
c_{j,1-\alpha}
\widehat{\mathrm{SE}}\{\widehat\beta_{j,d}(t_m)\}.
$

With `simultaneous_scope="family"`, one maximum is taken over coefficient, time, and selected functional dimensions, producing one shared critical value for the declared coefficient family.

### Repeated-trial boundary

With `unit="curve"`, source curves are explicitly treated as independent inference units. With `unit="participant"`, version 0.35 first averages the selected response trajectories within participant and requires every declared predictor to be constant within participant. The resulting estimand is an equal-weight participant-average functional response conditional on participant-level predictors.

This is not a functional mixed-effects model. Within-participant condition effects, trial-varying covariates, random functional intercepts/slopes, and participant-by-time covariance are deferred to the repeated-measures functional-regression tranche rather than approximated by independent pointwise mixed models.

**API:** `fit_function_on_scalar_regression()`, `bootstrap_function_on_scalar_coefficients()`, `function_on_scalar_simultaneous_bands()`, `function_on_scalar_coefficient_frame()`.

## Scalar-on-function regression through FPC scores { #fpcr }

The Gaussian score-space approximation is

$$
Y_i
=
\beta_0
+
\sum_{k=1}^{K}\beta_k\xi_{ik}
+
\mathbf z_i^\top\boldsymbol\gamma
+
\varepsilon_i.
$$

For binomial outcomes the same linear predictor is passed through the logit link,

$$
\operatorname{logit}\{\Pr(Y_i=1)\}
=
\beta_0
+
\sum_{k=1}^{K}\beta_k\xi_{ik}
+
\mathbf z_i^\top\boldsymbol\gamma.
$$

**API:** `fit_scalar_on_function_regression()`.

## Heteroscedastic Gaussian FPCR wild bootstrap { #wild-bootstrap }

For retained score matrix \(\boldsymbol\Xi_h\), the fitted score regression uses

$$
\mathbf X_h=[\mathbf 1,\boldsymbol\Xi_h].
$$

Residual estimation uses \(k\) components, the bootstrap pseudo-truth uses \(g=k\), and inference uses \(h\ge g\).

For replicate \(b\),

$$
Y_i^{*(b)}
=
\widehat Y_{i,k}
+
\widehat\varepsilon_{i,k}W_i^{(b)},
$$

where \(W_i\) is either standard normal or the implemented mean-zero, unit-variance Mammen two-point multiplier.

For the \(h\)-score covariance,

$$
\widehat{\boldsymbol\Gamma}_h
=
\frac{1}{n}
\boldsymbol\Xi_h^\top\boldsymbol\Xi_h.
$$

Writing
\(\mathbf q_i=\boldsymbol\xi_{i,h}\widehat\varepsilon_{i,k}\) and
\(\overline{\mathbf q}=n^{-1}\sum_i\mathbf q_i\), the heteroscedastic score-residual covariance is

$$
\widehat{\boldsymbol\Lambda}_h
=
\frac{1}{n-1}
\sum_{i=1}^{n}
(\mathbf q_i-\overline{\mathbf q})
(\mathbf q_i-\overline{\mathbf q})^\top.
$$

For fixed target score vector \(\boldsymbol\xi_{0,h}\), define

$$
\mathbf d_0
=
\widehat{\boldsymbol\Gamma}_h^{-1}\boldsymbol\xi_{0,h}.
$$

The target-specific heteroscedastic standard error is

$$
\widehat{\mathrm{SE}}_0
=
\left[
\frac{1}{n}
\mathbf d_0^\top
\widehat{\boldsymbol\Lambda}_h
\mathbf d_0
\right]^{1/2}.
$$

The reference centered projection is

$$
\widehat\theta_{0,h}
=
\boldsymbol\xi_{0,h}^\top\widehat{\boldsymbol\beta}_h,
$$

while the bootstrap pseudo-truth is

$$
\widehat\theta_{0,g}
=
\boldsymbol\xi_{0,g}^\top\widehat{\boldsymbol\beta}_g.
$$

The studentized bootstrap root is

$$
T_0^{*(b)}
=
\frac{
\widehat\theta_{0,h}^{*(b)}
-
\widehat\theta_{0,g}
}{
\widehat{\mathrm{SE}}_0^{*(b)}
}.
$$

If \(c_{0,1-\alpha}\) is the empirical quantile of \(|T_0^{*(b)}|\), the target-wise interval is

$$
\widehat\theta_{0,h}
\pm
c_{0,1-\alpha}\widehat{\mathrm{SE}}_0.
$$

**API:** `wild_bootstrap_fpca_projection()`.

## Simultaneous fixed-target calibration { #simultaneous-wild-bootstrap }

For a predeclared family \(j=1,\ldots,J\), each replicate contributes

$$
M^{*(b)}
=
\max_{1\le j\le J}
|T_j^{*(b)}|.
$$

A single empirical quantile of \(M^{*(b)}\) calibrates all fixed targets.

**API:** `fpca_wild_bootstrap_projection_simultaneous_interval()`.

## Fixed-family wild-bootstrap tests { #family-tests }

For supplied null value \(\theta_{0j}\),

$$
T_j
=
\frac{\widehat\theta_j-\theta_{0j}}
{\widehat{\mathrm{SE}}_j}.
$$

The target-wise exceedance count is

$$
r_j
=
\sum_{b=1}^{B}
\mathbb I\left(
|T_j^{*(b)}|\ge |T_j|
\right).
$$

The default finite-resampling p-value is

$$
p_j
=
\frac{r_j+1}{B+1}.
$$

For single-step max-\(|t|\) adjustment,

$$
r_j^{\max}
=
\sum_{b=1}^{B}
\mathbb I\left(
M^{*(b)}\ge |T_j|
\right),
\qquad
p_j^{\max}
=
\frac{r_j^{\max}+1}{B+1}.
$$

The complete-family global statistic is

$$
T_{\mathrm{global}}
=
\max_j |T_j|.
$$

**API:** `fpca_wild_bootstrap_projection_family_test()`.

## Finite-bootstrap Monte Carlo precision { #monte-carlo }

For any retained exceedance count \(r\) out of \(B\),

$$
\widehat q=\frac{r}{B},
\qquad
\widehat{\mathrm{MCSE}}
=
\sqrt{
\frac{\widehat q(1-\widehat q)}{B}
}.
$$

The exact Clopper-Pearson interval at diagnostic level \(1-\gamma\) is

$$
L=
\begin{cases}
0,&r=0,\\
F_{\mathrm{Beta}}^{-1}
\!\left(
\frac{\gamma}{2};r,B-r+1
\right),&r>0,
\end{cases}
$$

$$
U=
\begin{cases}
1,&r=B,\\
F_{\mathrm{Beta}}^{-1}
\!\left(
1-\frac{\gamma}{2};r+1,B-r
\right),&r<B.
\end{cases}
$$

These limits quantify **simulation precision of the bootstrap tail probability**, not uncertainty in the scientific effect.

**API:** `fpca_wild_bootstrap_family_test_monte_carlo_diagnostics()`.

## Split-conformal FPCA anomaly review { #conformal }

Let \(A_1,\ldots,A_m\) be calibration nonconformity scores and \(A_\mathrm{new}\) the target score. The implemented conservative p-value is

$$
p_{\mathrm{conf}}
=
\frac{
1+
\sum_{i=1}^{m}
\mathbb I(A_i\ge A_{\mathrm{new}})
}{
m+1
}.
$$

For reconstruction-RMSE nonconformity,

$$
A(\mathbf G)
=
\left[
\frac{
\sum_{m=1}^{M}
w_m
\sum_{d=1}^{D}
\{\widehat G_d(t_m)-G_d(t_m)\}^2
}{
D\sum_{m=1}^{M}w_m
}
\right]^{1/2}.
$$

**API:** `split_conformal_fpca_anomaly()`.

## Contract boundaries { #boundaries }

The equations above describe what the software computes; they do not enlarge the scientific scope of the underlying method. In particular:

- observed-grid bands do not imply continuous-domain coverage between grid points;
- fixed-target wild bootstrap currently requires independent curve rows;
- the single-step max-\(|t|\) layer does not claim strong FWER for arbitrary subset nulls without additional theory;
- finite-bootstrap precision intervals are Monte Carlo diagnostics, not effect-size confidence intervals;
- multilevel FPCA is the explicit two-level decomposition above, not a full likelihood/Bayesian functional mixed model;
- compositional FPCA is performed in ALR coordinates and depends on the declared reference component and zero-replacement \(\epsilon\).

See the [assumptions](assumptions.md), [limitations](limitations.md), and [API reference](../reference/api.md) for the operational contracts.

## Delay-coordinate reconstruction and embedding diagnostics { #delay-embedding }

For a multivariate gaze state \(\mathbf G(t)\), embedding dimension \(m\), and delay \(\tau\),

$$
\mathbf z_t=
[
\mathbf G(t),
\mathbf G(t-\tau),
\ldots,
\mathbf G(t-(m-1)\tau)
].
$$

The package does not choose \(m\) or \(\tau\) silently. `embedding_delay_diagnostics()` reports autocorrelation and Fraser–Swinney-style average mutual information,

$$
I(\tau)
=
\sum_{a,b}
p_{ab}(\tau)
\log
\frac{
p_{ab}(\tau)
}{
p_a p_b
},
$$

while `embedding_dimension_diagnostics()` reports Kennel-style false-nearest-neighbor fractions across analyst-requested dimensions. The diagnostic marks a first AMI local minimum when present but does not turn that mark into an analysis setting automatically.

**API:** `delay_embed_trajectory()`, `embedding_delay_diagnostics()`, `embedding_dimension_diagnostics()`.

## Sparse recurrence and recurrence quantification { #recurrence }

For observed or reconstructed state vectors and a declared \(p\)-norm radius \(\varepsilon\),

$$
R_{ij}
=
\mathbb I
\left[
\|\mathbf z_i-\mathbf z_j\|_p
\le
\varepsilon
\right].
$$

For auto-recurrence, the line of identity and every pair within the declared Theiler window are excluded. With \(N_{\mathrm{eligible}}\) eligible unordered pairs,

$$
\mathrm{RR}
=
\frac{
\sum_{i<j}R_{ij}
}{
N_{\mathrm{eligible}}
}.
$$

If \(P_d(\ell)\) denotes the number of diagonal recurrence lines of length \(\ell\),

$$
\mathrm{DET}
=
\frac{
\sum_{\ell\ge\ell_{\min}}
\ell P_d(\ell)
}{
\sum_{\ell\ge1}
\ell P_d(\ell)
}.
$$

For vertical lines,

$$
\mathrm{LAM}
=
\frac{
\sum_{v\ge v_{\min}}
v P_v(v)
}{
\sum_{v\ge1}
v P_v(v)
},
\qquad
\mathrm{TT}
=
\frac{
\sum_{v\ge v_{\min}}
vP_v(v)
}{
\sum_{v\ge v_{\min}}
P_v(v)
}.
$$

The auto-recurrence center-of-recurrence-mass diagnostic is

$$
\mathrm{CORM}
=
100
\frac{
\sum_{i<j}(j-i)R_{ij}
}{
(N-1)
\sum_{i<j}R_{ij}
}.
$$

The matrix is stored sparsely. Exactly one radius policy is allowed: a fixed \(\varepsilon\), or an explicit target recurrence rate from which \(\varepsilon\) is solved numerically.

**API:** `recurrence_matrix()`, `recurrence_radius_profile()`, `rqa_metrics()`, `rqa_parameter_sensitivity()`, `windowed_rqa()`, `cross_recurrence_matrix()`, `cross_rqa_metrics()`. The radius-profile API evaluates the same RR equation over a declared radius grid, while the sensitivity API evaluates the broader recurrence/RQA contract over a predeclared parameter grid without automatic selection.

## Synchronized joint recurrence and JRQA { #joint-recurrence }

Joint recurrence addresses a different question from cross-recurrence. A
cross-recurrence plot asks whether a state of system A resembles a state of
system B. A joint recurrence plot instead asks whether all declared systems
**individually recur at the same pair of time indices**.

For binary auto-recurrence matrices \(R^{(s)}\),

$
JR_{ij}
=
\prod_{s=1}^{S}R_{ij}^{(s)},
$

which is equivalent to an elementwise logical AND. Each subsystem may have its
own state representation, dimension, metric, and threshold/radius policy.

Version 0.39 requires all component recurrence matrices to have:

- the same square shape;
- the exact same time grid on both axes;
- the same Theiler exclusion;
- auto-recurrence semantics.

No lag shifting, synchronization, interpolation, resampling, or threshold
harmonization is performed inside the joint-recurrence function.

With \(N_{\mathrm{eligible}}\) unique off-diagonal time pairs outside the
shared Theiler window,

$
\mathrm{JRR}
=
\frac{\sum_{i<j}JR_{ij}}{N_{\mathrm{eligible}}}.
$

Line-based JRQA then applies the existing auto-RQA conventions to the joint
matrix:

$
\mathrm{JDET}
=
\frac{\sum_{\ell\ge\ell_{\min}}\ell P_{d,J}(\ell)}
{\sum_{\ell\ge1}\ell P_{d,J}(\ell)},
$

and

$
\mathrm{JLAM}
=
\frac{\sum_{v\ge v_{\min}}v P_{v,J}(v)}
{\sum_{v\ge1}v P_{v,J}(v)}.
$

Because line statistics rely on comparable index increments, the same
approximately regular-grid requirement used by `rqa_metrics()` applies to
`joint_rqa_metrics()`. Spatial joint recurrence itself can still be
constructed before that line-metric check.

### Interpretation boundary

A high JRR means that the declared component systems often return
simultaneously to their own previously visited neighborhoods. It is not a
cross-system state distance, a direction-of-influence statistic, transfer
entropy, or evidence of causal coupling.

**API:** `joint_recurrence_matrix()`,
`joint_recurrence_component_frame()`, `joint_rqa_metrics()`.

## Sparse recurrence-network topology { #recurrence-network }

Recurrence networks reinterpret one symmetric auto-recurrence plot as an
undirected simple graph. Every recurrence-state/time index is a node and every
retained off-diagonal recurrence pair is an edge:

$
A_{ij}=R_{ij},\quad i\ne j,\qquad A_{ii}=0.
$

Node degree is

$
k_i=\sum_j A_{ij},
$

with normalized degree \(k_i/(N-1)\).

If \(T_i\) denotes the number of graph triangles incident to node \(i\), local
clustering is

$
C_i=\frac{2T_i}{k_i(k_i-1)}.
$

Version 0.40 uses the standard computational convention \(C_i=0\) for nodes
with degree below two. Mean local clustering averages those node-wise values
over all nodes.

Global transitivity is

$
\mathcal T=\frac{3N_{\triangle}}{N_{\mathrm{triples}}},
$

where \(N_{\mathrm{triples}}=\sum_i {k_i\choose2}\). If there are no connected
triples, transitivity remains explicit `NaN` rather than being silently set to
zero.

Standard graph density is

$
\rho_G=\frac{2E}{N(N-1)}.
$

This denominator includes all unordered node pairs. It is therefore distinct
from the package recurrence-rate denominator when a Theiler exclusion removes
temporally near pairs. Both quantities are retained rather than relabeled as
the same estimand.

Connected components are computed from the sparse adjacency matrix. The result
reports the number of components, largest-component fraction, and isolated-node
fraction. Version 0.40 deliberately does not compute dense all-pairs shortest
paths, optimize communities, infer a fractal/transitivity dimension, or choose
a recurrence threshold from the resulting graph topology.

### Interpretation boundary

Recurrence-network topology describes the geometry induced by the **declared**
recurrence relation. Changing state variables, coordinate scaling, embedding,
metric, recurrence radius/target-RR policy, Theiler window, or sampling design
can change the graph. A high clustering coefficient or transitivity is not by
itself evidence of low-dimensional deterministic chaos.

**API:** `recurrence_network()`, `recurrence_network_node_frame()`,
`recurrence_network_summary_frame()`.

## Discrete transfer entropy and circular-shift surrogate testing { #discrete-transfer-entropy }

For discrete source states \(X_t\) and target states \(Y_t\), version 0.41
implements the empirical plug-in conditional mutual information

$
T_{X\to Y}(k,l,d)
=
I\!\left(X_{t-d}^{(l)};Y_t\mid Y_{t-1}^{(k)}\right).
$

Equivalently,

$
T_{X\to Y}
=
\sum p(y_t,\mathbf y,\mathbf x)
\log_2
\frac{p(y_t\mid\mathbf y,\mathbf x)}
     {p(y_t\mid\mathbf y)}.
$

The state codes, target history \(k\), source history \(l\), and source lag
\(d\) are analyst supplied. The implementation uses base-2 logarithms and
returns local contributions plus observed-history support diagnostics. It does
not bin continuous observations or select history/lag values.

For a declared set of \(B\) circular source shifts, the package reports

$
p_+
=
\frac{1+\sum_{b=1}^{B}I(T_b^*\ge T_{obs})}{B+1}.
$

The circular-shift null preserves the source marginal and circular ordering but
requires the analyst to defend wrap-around/stationarity. A positive TE estimate
or a small surrogate p-value is not treated as standalone causal evidence.

**API:** `discrete_transfer_entropy()`,
`transfer_entropy_circular_shift_test()`,
`transfer_entropy_local_frame()`.

## Conditional transfer entropy and source-shift surrogate testing { #conditional-transfer-entropy }

For source \(X\), target \(Y\), and explicitly supplied conditioning process
\(Z\), the 0.43 estimand is

$$
T_{X\to Y\mid Z}(k,l,m,d,c)
=
I\!\left(
X_{t-d}^{(l)};
Y_t
\mid
Y_{t-1}^{(k)},
Z_{t-c}^{(m)}
\right).
$$

For observed histories
\(\mathbf y=Y_{t-1}^{(k)}\),
\(\mathbf x=X_{t-d}^{(l)}\), and
\(\mathbf z=Z_{t-c}^{(m)}\),

$$
T_{X\to Y\mid Z}
=
\sum
p(y_t,\mathbf y,\mathbf x,\mathbf z)
\log_2
\frac{
p(y_t\mid\mathbf y,\mathbf x,\mathbf z)
}{
p(y_t\mid\mathbf y,\mathbf z)
}.
$$

The empirical implementation uses observed contingency counts and reports the
mean local log-ratio over the exact effective transitions implied by the five
declared history/lag settings.

For \(B\) analyst-declared circular shifts of the source only,

$$
p_+
=
\frac{
1+
\sum_{b=1}^{B}
I(T_{b}^{*,cond}\ge T_{obs}^{cond})
}{
B+1
}.
$$

The target and conditioning process remain fixed. The result therefore tests
additional directed predictive information under the declared conditioning
process and shift null. It does not establish causal influence or guarantee
adjustment for unmeasured common drivers.

**API:** `conditional_transfer_entropy()`,
`conditional_transfer_entropy_local_frame()`,
`conditional_transfer_entropy_circular_shift_test()`,
`plot_conditional_transfer_entropy_circular_shift_test()`.

## Transfer-entropy specification sensitivity { #transfer-entropy-sensitivity }

Let \(\mathcal K\), \(\mathcal L\), and \(\mathcal D\) be analyst-declared
sets of target-history lengths, source-history lengths, and source lags. Version
0.42 evaluates the complete Cartesian design

$
\Theta
=
\mathcal K\times\mathcal L\times\mathcal D.
$

For every \(\theta=(k,l,d)\in\Theta\),

$
T_{\theta}
=
I\!\left(
X_{t-d}^{(l)};
Y_t
\mid
Y_{t-1}^{(k)}
\right)
$

is estimated with the same empirical discrete-state plug-in contract as the
0.41 base estimator.

If one common set of \(B\) circular source shifts is supplied, every
specification additionally retains

$
\Delta T_{\theta}
=
T_{\theta,obs}
-
B^{-1}
\sum_{b=1}^{B}
T_{\theta,b}^{*}.
$

The table also retains finite empirical-support diagnostics for every
specification. Invalid declared combinations abort the complete sensitivity
analysis. The summaries are descriptive across \(\Theta\): no parameter
ranking, winner selection, hidden averaging, posterior interpretation, or
causal identification is introduced.

**API:** `transfer_entropy_parameter_sensitivity()`,
`plot_transfer_entropy_sensitivity()`,
`transfer_entropy_parameter_sensitivity_reporting_text()`.

## Population mean bootstrap for curve-level RQA metrics { #rqa-population-bootstrap }

For source curve $i$ and selected RQA metric $q$, let

$$
M_{iq}=Q_q\{R_i(\theta)\},
$$

where $\theta$ is one fixed, fully declared recurrence/RQA specification.

With curve-level inference, the independent units are $M_{iq}$ directly. With repeated trials nested in participant $p$, participant mode first forms

$$
U_{pq}
=
\frac{1}{m_p}
\sum_{j=1}^{m_p}
M_{pjq},
$$

so each participant receives equal inferential weight regardless of trial count.

For bootstrap replicate $b$, resample the $n$ independent unit indices with replacement and compute

$$
\overline U_q^{*(b)}
=
\frac{1}{n}
\sum_{r=1}^{n}
U_{I_r^{(b)}q}.
$$

The implemented percentile interval is

$$
CI_{1-\alpha}
=
\left[
Q_{\alpha/2}\{\overline U_q^*\},
Q_{1-\alpha/2}\{\overline U_q^*\}
\right].
$$

This estimates between-unit population sampling uncertainty in the mean of fixed-specification curve-level RQA summaries. Curve-level RQA values are deterministic summaries of the observed curves under the declared contract and are therefore computed once before unit resampling. The procedure does **not** implement Schinkel-style within-single-series recurrence-line resampling, a moving/block bootstrap, hierarchical trial resampling, or parameter-selection uncertainty.

Under target-recurrence-rate mode, recurrence density is controlled by design and recurrence_rate is not accepted as a bootstrap outcome.

**API:** bootstrap_rqa_metric_means(), plot_rqa_metric_mean_bootstrap(), and rqa_metric_mean_bootstrap_reporting_text().

## Windowed RQA as functional trajectories { #functional-rqa-trajectories }

Let window $w$ span source samples from $t_{w,\mathrm{start}}$ to $t_{w,\mathrm{end}}$, with center

$
c_w=
\frac{
t_{w,\mathrm{start}}+t_{w,\mathrm{end}}
}{2}.
$

For source curve $i$ and selected RQA metric $q$, the derived functional value is

$
F_{iq}(c_w)=M_q\left\{R_i^{(w)}\right\},
$

where $R_i^{(w)}$ is the recurrence matrix computed under the same declared recurrence contract inside window $w$.

For window length $W$ samples and step $S$ samples, explicit source-sample overlap is

$
\omega=
\frac{\max(0,W-S)}{W}.
$

This overlap is recorded as provenance. It is not converted into an independence assumption. Even when $\omega=0$, serial dependence in the source process may remain.

When target recurrence rate determines the radius, RR is controlled by construction and is therefore not accepted as a downstream functional outcome. Undefined selected metrics fail closed by default; an explicit keep policy preserves them as `NaN` without imputation.

**API:** `windowed_rqa_trajectory_set()`, `windowed_rqa_sensitivity()`, `plot_windowed_rqa_trajectories()`, `plot_windowed_rqa_sensitivity()`, `windowed_rqa_functional_reporting_text()`, and `windowed_rqa_sensitivity_reporting_text()`. The sensitivity API evaluates the same functionalization contract across a predeclared window/step grid without automatic selection or interpolation.
## Rosenstein local divergence and largest Lyapunov estimate { #local-divergence }

For reconstructed state \(i\), let \(j(i)\) be its nearest positive-distance neighbor outside the declared Theiler window. Forward separation is

$$
d_i(k)
=
\|
\mathbf z_{i+k}
-
\mathbf z_{j(i)+k}
\|_2.
$$

The package reports

$$
D(k)
=
\frac{1}{N_k}
\sum_i
\log d_i(k),
$$

including the number of usable pairs and any zero-distance events at every horizon. Zero distances are not replaced by an arbitrary epsilon.

The analyst then declares the linear fit interval. Within that interval,

$$
D(k)
\approx
a+
\lambda_{\max}
k\Delta t.
$$

The fitted slope is the Rosenstein-style largest-Lyapunov estimate. A positive estimate is evidence of local exponential separation under the declared reconstruction, not standalone proof that behavioral gaze is generated by a deterministic chaotic attractor.

**API:** `local_divergence_curve()`, `estimate_largest_lyapunov_rosenstein()`, `lyapunov_parameter_sensitivity()`. The sensitivity API reuses the same divergence and linear-fit equations across analyst-declared reconstruction, Theiler, and fit-interval specifications.

## Kantz neighborhood divergence and largest Lyapunov estimate { #kantz-local-divergence }

For reconstructed state $i$, define a fixed-radius neighborhood after the declared Theiler exclusion,

$$
\mathcal N_i(\varepsilon)
=
\left\{
j:
\|\mathbf z_i-\mathbf z_j\|_2\le\varepsilon,
\ |i-j|>w
\right\}.
$$

For horizon $k$, only neighbors whose forward states remain observed are retained. A reference contributes only when at least the declared minimum number of neighbors remains. Its mean forward separation is computed first, then logged, and the logs are averaged across contributing references:

$$
S(\varepsilon,k)
=
\frac{1}{N_k}
\sum_i
\log
\left[
\frac{1}{|\mathcal N_i(k)|}
\sum_{j\in\mathcal N_i(k)}
\|\mathbf z_{i+k}-\mathbf z_{j+k}\|_2
\right].
$$

Over an analyst-declared linear region,

$$
S(\varepsilon,k)
\approx
a+\lambda_{\max}k\Delta t.
$$

The radius and minimum-neighbor count are explicit inputs. The package does not expand the neighborhood automatically when a reference has too few neighbors. Reference counts, pair counts, zero-mean-neighborhood counts, and each reference state's initial neighbor count are retained for audit.

The fitted slope is a Kantz-style maximal-Lyapunov estimate. It is a conditional local-divergence estimate under the declared reconstruction, radius, Theiler window, minimum-neighbor rule, and fit interval; a positive slope is not standalone evidence of deterministic chaos.

**API:** `kantz_divergence_curve()`, `estimate_largest_lyapunov_kantz()`, and `kantz_parameter_sensitivity()`. The sensitivity API reuses the same neighborhood-divergence and linear-fit equations across the complete analyst-declared reconstruction, radius, minimum-neighbor, Theiler, and fit-interval grid without selecting a preferred specification.

## Multivariate IAAFT surrogates { #multivariate-iaaft }

For simultaneously observed dimensions \(k=1,\ldots,K\),

$
F_k(\omega)=A_k(\omega)e^{i\phi_k(\omega)}.
$

A multivariate surrogate should retain between-channel linear dependence rather
than generate each channel independently. Relative to an explicitly declared
reference dimension \(r\),

$
\Delta\phi_{kr}(\omega)=\phi_k(\omega)-\phi_r(\omega).
$

During one Fourier-adjustment step, the current surrogate reference phase
\(\psi_r^*(\omega)\) is combined with the original phase offset,

$
F_k^*(\omega)
=
A_k(\omega)e^{i[\psi_r^*(\omega)+\Delta\phi_{kr}(\omega)]}.
$

This jointly targets each channel's original Fourier amplitude and the original
complex cross-spectrum

$
C_{k\ell}(\omega)=F_k(\omega)F_\ell(\omega)^*.
$

The inverse transform is rank-remapped channel by channel to the exact observed
empirical marginal distribution. The Fourier and rank constraints are iterated
until the declared convergence tolerance is met or the rank ordering becomes
stable.

### Exact versus approximate preservation

The returned surrogate has the exact observed marginal value set in each
dimension. The final power spectrum and cross-spectrum are not claimed to be
exact because the final rank-remapping step perturbs Fourier coefficients.
Version 0.37 therefore retains relative per-channel spectrum errors and
per-pair complex cross-spectrum errors for every surrogate.

### Reference-dimension boundary

The update is reference-anchored. The reference dimension is a finite-sample
algorithm choice and is required explicitly through `reference_dimension`.
It is never selected by the package.

### Nonlinearity testing

The same multichannel embedding and nonlinear statistic settings are used for
the observed trajectory and all surrogates. For a greater-than alternative,

$
p
=
\frac{1+\sum_{b=1}^{B}\mathbb I(T_b^*\ge T_{\mathrm{obs}})}{B+1}.
$

The current public statistic is multichannel Rosenstein
largest-Lyapunov estimation. Rejection is evidence against the declared
multivariate linear-stochastic surrogate null under the retained marginal and
spectral constraints. It is not proof of deterministic chaos or a unique
nonlinear mechanism.

**API:** `generate_multivariate_iaaft_surrogates()`,
`multivariate_iaaft_diagnostics_frame()`,
`multivariate_surrogate_nonlinearity_test()`.

## IAAFT surrogate nonlinearity test { #surrogate-nonlinearity }

Version 0.23 uses iterative amplitude-adjusted Fourier transform surrogates for the explicitly supported largest-Lyapunov statistic. Every surrogate is analyzed with exactly the same embedding, Theiler window, divergence horizon, and fit interval as the observed signal.

For the greater-than alternative,

$$
p
=
\frac{
1+
\sum_{b=1}^{B}
\mathbb I
\left(
T_b^*
\ge
T_{\mathrm{obs}}
\right)
}{
B+1
}.
$$

The plus-one correction prevents zero Monte Carlo p-values. Two-sided testing is centered on the surrogate median. A failed surrogate aborts the procedure rather than being discarded or redrawn silently.

Rejecting the surrogate null is evidence against the declared linear-stochastic surrogate model. It does not identify a unique nonlinear mechanism and does not prove chaos.

**API:** `surrogate_nonlinearity_test()`.

## Empirical Poincare return-map stability { #return-map-stability }

For an explicitly declared scalar section,

$$
h(\mathbf z)=0,
$$

`poincare_crossings()` linearly interpolates successive crossing states. The section, crossing direction, and returned state dimensions are all explicit.

Within an analyst-declared reference and neighborhood, `fit_local_return_map()` estimates

$$
\mathbf z_{n+1}
=
\mathbf a
+
\mathbf J
(
\mathbf z_n-\mathbf z_0
)
+
\boldsymbol\varepsilon_n.
$$

The local empirical contraction/expansion summary is

$$
\rho(\mathbf J)
=
\max_j
|
\lambda_j(\mathbf J)
|.
$$

With tolerance \(\delta\), the package labels \(\rho<1-\delta\) as contracting, \(\rho>1+\delta\) as expanding, and values inside the tolerance band as near-neutral.

**API:** `poincare_crossings()`, `fit_local_return_map()`, `return_map_stability()`.

!!! warning "Not Floquet analysis"
    The fitted \(\mathbf J\) is an empirical local return-map Jacobian. It is not obtained by integrating variational equations around a known periodic orbit, so it must not be reported as a classical monodromy matrix or as a Floquet-multiplier calculation. Classical model-based Floquet and numerical-continuation APIs remain outside the 0.23 raw-gaze contract.
