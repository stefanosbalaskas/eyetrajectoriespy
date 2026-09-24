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
