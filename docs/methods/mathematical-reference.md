---
title: Mathematical reference
---

# Mathematical contracts

This page records the equations implemented by \`eyetrajectoriespy\`. It is a **software contract reference**: each equation is paired with the public API that implements it and with the scope limits that matter for interpretation.

!!! note "Notation"
    \(i\) indexes trajectories or independent units, \(t_m\) the observed common grid, \(d\) functional dimensions, and \(k\) retained functional principal components. Bold symbols denote vectors or matrices.

## Quadrature on the observed grid

For strictly increasing grid points \(t_1,\ldots,t_M\), \`functional_trapezoid_weights()\` uses trapezoidal weights

$$
w_1=\frac{t_2-t_1}{2},\qquad
w_M=\frac{t_M-t_{M-1}}{2},
$$

and for \(m=2,\ldots,M-1\),

$$
w_m=\frac{(t_m-t_{m-1})+(t_{m+1}-t_m)}{2}.
$$

When \`normalize=True\`,

$$
\widetilde w_m=\frac{w_m}{\sum_{\ell=1}^{M}w_\ell}.
$$

**API:** \`functional_trapezoid_weights()\`.

## Quadrature-weighted FPCA / MFPCA

Let \(\mathbf G_i(t_m)\in\mathbb R^D\) and

$$
\widehat{\boldsymbol\mu}(t_m)
=
\frac{1}{n}\sum_{i=1}^{n}\mathbf G_i(t_m).
$$

With \`scaling="dimension_sd"\`, dimension \(d\) is scaled by the square root of its mean integrated variance,

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

For \`scaling="none"\`, \(s_d=1\).

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

The interpretation curves from \`component_trajectories()\` are

$$
\widehat{\boldsymbol\mu}(t)
+
a\sqrt{\widehat\lambda_k}\,
\widehat{\boldsymbol\phi}_k(t),
$$

where \(a\) is an analyst-selected score-SD multiplier.

**API:** \`fit_fpca()\`, \`fit_mfpca()\`, \`transform_fpca()\`, \`reconstruct_fpca()\`, \`component_trajectories()\`.

## Integrated functional \(L^2\) distance

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

**API:** \`functional_l2_distance()\`, \`pairwise_functional_distances()\`.

## Two-level functional decomposition

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

**API:** \`fit_multilevel_fpca()\`.

## Compositional AOI trajectories

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

**API:** \`alr_transform()\`, \`inverse_alr()\`, \`fit_compositional_fpca()\`.

## Landmark registration

For curve \(i\), \`register_to_landmarks()\` constructs a monotone piecewise-linear warp \(h_i(t)\) that maps reference landmark times to observed landmark times and evaluates

$$
\mathbf G_i^{\mathrm{reg}}(t)
=
\mathbf G_i\{h_i(t)\}.
$$

Phase displacement is retained as

$$
\Delta_i(t)=h_i(t)-t.
$$

**API:** \`register_to_landmarks()\`, \`warping_displacement()\`, \`phase_summary()\`.

## Simultaneous functional mean band

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

**API:** \`multiplier_functional_mean_band()\`.

## Scalar-on-function regression through FPC scores

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

**API:** \`fit_scalar_on_function_regression()\`.

## Heteroscedastic Gaussian FPCR wild bootstrap

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

**API:** \`wild_bootstrap_fpca_projection()\`.

## Simultaneous fixed-target calibration

For a predeclared family \(j=1,\ldots,J\), each replicate contributes

$$
M^{*(b)}
=
\max_{1\le j\le J}
|T_j^{*(b)}|.
$$

A single empirical quantile of \(M^{*(b)}\) calibrates all fixed targets.

**API:** \`fpca_wild_bootstrap_projection_simultaneous_interval()\`.

## Fixed-family wild-bootstrap tests

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

**API:** \`fpca_wild_bootstrap_projection_family_test()\`.

## Finite-bootstrap Monte Carlo precision

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

**API:** \`fpca_wild_bootstrap_family_test_monte_carlo_diagnostics()\`.

## Split-conformal FPCA anomaly review

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

**API:** \`split_conformal_fpca_anomaly()\`.

## Contract boundaries

The equations above describe what the software computes; they do not enlarge the scientific scope of the underlying method. In particular:

- observed-grid bands do not imply continuous-domain coverage between grid points;
- fixed-target wild bootstrap currently requires independent curve rows;
- the single-step max-\(|t|\) layer does not claim strong FWER for arbitrary subset nulls without additional theory;
- finite-bootstrap precision intervals are Monte Carlo diagnostics, not effect-size confidence intervals;
- multilevel FPCA is the explicit two-level decomposition above, not a full likelihood/Bayesian functional mixed model;
- compositional FPCA is performed in ALR coordinates and depends on the declared reference component and zero-replacement \(\epsilon\).

See the [assumptions](assumptions.md), [limitations](limitations.md), and [API reference](../reference/api.md) for the operational contracts.
