---
title: Function → equation index
---

# Function → equation index

Generated from the public mathematical-contract registry in `eyetrajectoriespy.mathematical_contracts`.

The equations below are implementation contracts, not claims of methodological novelty. See the linked expanded reference for assumptions, derivations, and scope limits.

## Observed-grid trapezoidal quadrature

**Functions:** `functional_trapezoid_weights()`

$$
w_1=\frac{t_2-t_1}{2},\quad w_M=\frac{t_M-t_{M-1}}{2},\quad w_m=\frac{(t_m-t_{m-1})+(t_{m+1}-t_m)}{2}
$$

**Scope:** Strictly increasing observed grids; optional normalization only rescales the weights to sum to one.

[Expanded mathematical reference](../methods/mathematical-reference.md#quadrature)

## Quadrature-weighted FPCA / MFPCA

**Functions:** `fit_fpca()`, `fit_mfpca()`, `transform_fpca()`, `reconstruct_fpca()`, `component_trajectories()`

$$
Z_{i,m,d}=\frac{G_{id}(t_m)-\widehat\mu_d(t_m)}{s_d}\sqrt{w_m}
$$

$$
\widehat{\mathbf G}^{(K)}_i(t)=\widehat{\boldsymbol\mu}(t)+\sum_{k=1}^{K}\widehat\xi_{ik}\widehat{\boldsymbol\phi}_k(t)
$$

**Scope:** Common-grid functional PCA with explicit channel scaling; retained-component interpretation is conditional on the fitted basis.

[Expanded mathematical reference](../methods/mathematical-reference.md#fpca)

## Integrated functional L2 distance

**Functions:** `functional_l2_distance()`, `pairwise_functional_distances()`

$$
d_{L^2}(\mathbf a,\mathbf b)=\left[\sum_m w_m\sum_d\omega_d\{a_d(t_m)-b_d(t_m)\}^2\right]^{1/2}
$$

**Scope:** Complete trajectories on a common grid; optional dimension weights must be non-negative.

[Expanded mathematical reference](../methods/mathematical-reference.md#functional-l2)

## Two-level participant / trial decomposition

**Functions:** `fit_multilevel_fpca()`

$$
\mathbf G_{ij}(t)=\boldsymbol\mu(t)+\mathbf U_i(t)+\mathbf V_{ij}(t)
$$

$$
\mathbf U_i(t)=\overline{\mathbf G}_{i\cdot}(t)-\boldsymbol\mu(t),\quad \mathbf V_{ij}(t)=\mathbf G_{ij}(t)-\overline{\mathbf G}_{i\cdot}(t)
$$

**Scope:** Transparent two-level functional ANOVA followed by separate FPCAs; not a full probabilistic functional mixed model.

[Expanded mathematical reference](../methods/mathematical-reference.md#multilevel)

## Compositional AOI additive log-ratio transform

**Functions:** `alr_transform()`, `inverse_alr()`, `fit_compositional_fpca()`, `reconstruct_compositional_fpca()`

$$
z_k(t)=\log\frac{p_k^\epsilon(t)}{p_r^\epsilon(t)},\quad k\ne r
$$

$$
p_k(t)=\frac{q_k(t)}{\sum_{\ell=1}^{K}q_\ell(t)}
$$

**Scope:** Simplex-valued AOI probabilities with explicit reference component and zero-replacement epsilon.

[Expanded mathematical reference](../methods/mathematical-reference.md#compositional)

## Landmark registration and phase displacement

**Functions:** `register_to_landmarks()`, `warping_displacement()`, `phase_summary()`

$$
\mathbf G_i^{\mathrm{reg}}(t)=\mathbf G_i\{h_i(t)\}
$$

$$
\Delta_i(t)=h_i(t)-t
$$

**Scope:** Monotone piecewise-linear landmark warping; phase is retained rather than silently discarded.

[Expanded mathematical reference](../methods/mathematical-reference.md#registration)

## Simultaneous functional mean multiplier band

**Functions:** `multiplier_functional_mean_band()`

$$
M^{(b)}=\max_{m,d}\left|\frac{n^{-1/2}\sum_i e_i^{(b)}\{X_{id}(t_m)-\overline X_d(t_m)\}}{\widehat\sigma_d(t_m)}\right|
$$

$$
\overline X_d(t_m)\pm c_{1-\alpha}\frac{\widehat\sigma_d(t_m)}{\sqrt n}
$$

**Scope:** Simultaneous calibration over the observed time-by-dimension grid, with curve or equal-weight participant inference units.

[Expanded mathematical reference](../methods/mathematical-reference.md#mean-band)

## Scalar-on-function regression through FPC scores

**Functions:** `fit_scalar_on_function_regression()`

$$
Y_i=\beta_0+\sum_{k=1}^{K}\beta_k\xi_{ik}+\mathbf z_i^\top\boldsymbol\gamma+\varepsilon_i
$$

$$
\operatorname{logit}\{\Pr(Y_i=1)\}=\beta_0+\sum_{k=1}^{K}\beta_k\xi_{ik}+\mathbf z_i^\top\boldsymbol\gamma
$$

**Scope:** Score-space approximation; Gaussian and binomial fits have distinct inferential assumptions and no automatic component-selection uncertainty.

[Expanded mathematical reference](../methods/mathematical-reference.md#fpcr)

## Heteroscedastic Gaussian FPCR wild bootstrap

**Functions:** `wild_bootstrap_fpca_projection()`

$$
Y_i^*=\widehat Y_{i,k}+\widehat\varepsilon_{i,k}W_i
$$

$$
\widehat{\mathrm{SE}}_0=\left[\frac{1}{n}\mathbf d_0^\top\widehat{\boldsymbol\Lambda}_h\mathbf d_0\right]^{1/2}
$$

$$
T_0^*=\frac{\widehat\theta_{0,h}^*-\widehat\theta_{0,g}}{\widehat{\mathrm{SE}}_0^*},\quad g=k,\ h\ge g
$$

**Scope:** Fixed-regressor Gaussian FPCR with independent curve rows; not clustered wild bootstrap or future-outcome prediction.

[Expanded mathematical reference](../methods/mathematical-reference.md#wild-bootstrap)

## Simultaneous fixed-target wild-bootstrap calibration

**Functions:** `fpca_wild_bootstrap_projection_simultaneous_interval()`

$$
M^{*(b)}=\max_{1\le j\le J}|T_j^{*(b)}|
$$

**Scope:** One predeclared fixed-target family using the stored joint root matrix; no adaptive target-family guarantee.

[Expanded mathematical reference](../methods/mathematical-reference.md#simultaneous-wild-bootstrap)

## Fixed-family wild-bootstrap hypothesis tests

**Functions:** `fpca_wild_bootstrap_projection_family_test()`

$$
T_j=\frac{\widehat\theta_j-\theta_{0j}}{\widehat{\mathrm{SE}}_j}
$$

$$
p_j=\frac{1+\sum_{b=1}^{B}\mathbb I(|T_j^{*(b)}|\ge |T_j|)}{B+1}
$$

$$
p_j^{\max}=\frac{1+\sum_{b=1}^{B}\mathbb I(M^{*(b)}\ge |T_j|)}{B+1}
$$

**Scope:** Two-sided post-processing tests for a declared fixed family; strong FWER for arbitrary subsets is not claimed without additional theory.

[Expanded mathematical reference](../methods/mathematical-reference.md#family-tests)

## Finite-bootstrap Monte Carlo precision

**Functions:** `fpca_wild_bootstrap_family_test_monte_carlo_diagnostics()`

$$
\widehat q=\frac{r}{B}
$$

$$
\widehat{\mathrm{MCSE}}=\sqrt{\frac{\widehat q(1-\widehat q)}{B}}
$$

**Scope:** Simulation precision of retained bootstrap tail probabilities; not scientific-effect uncertainty and not sequential-stopping inference.

[Expanded mathematical reference](../methods/mathematical-reference.md#monte-carlo)

## Split-conformal FPCA anomaly p-value

**Functions:** `split_conformal_fpca_anomaly()`

$$
p_{\mathrm{conf}}=\frac{1+\sum_{i=1}^{m}\mathbb I(A_i\ge A_{\mathrm{new}})}{m+1}
$$

**Scope:** Marginal curve-level split-conformal interpretation under exchangeability; review flags are never automatic exclusions.

[Expanded mathematical reference](../methods/mathematical-reference.md#conformal)
