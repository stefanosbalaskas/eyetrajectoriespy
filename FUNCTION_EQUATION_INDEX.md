# Function → equation index

Generated from the public mathematical-contract registry in `eyetrajectoriespy.mathematical_contracts`.

The equations below are implementation contracts, not claims of methodological novelty. See the linked expanded reference for assumptions, derivations, and scope limits.

## Observed-grid trapezoidal quadrature

**Functions:** `functional_trapezoid_weights()`

$$
w_1=\frac{t_2-t_1}{2},\quad w_M=\frac{t_M-t_{M-1}}{2},\quad w_m=\frac{(t_m-t_{m-1})+(t_{m+1}-t_m)}{2}
$$

**Scope:** Strictly increasing observed grids; optional normalization only rescales the weights to sum to one.

Expanded reference: https://stefanosbalaskas.github.io/eyetrajectoriespy/methods/mathematical-reference/#quadrature

## Quadrature-weighted FPCA / MFPCA

**Functions:** `fit_fpca()`, `fit_mfpca()`, `transform_fpca()`, `reconstruct_fpca()`, `component_trajectories()`

$$
Z_{i,m,d}=\frac{G_{id}(t_m)-\widehat\mu_d(t_m)}{s_d}\sqrt{w_m}
$$

$$
\widehat{\mathbf G}^{(K)}_i(t)=\widehat{\boldsymbol\mu}(t)+\sum_{k=1}^{K}\widehat\xi_{ik}\widehat{\boldsymbol\phi}_k(t)
$$

**Scope:** Common-grid functional PCA with explicit channel scaling; retained-component interpretation is conditional on the fitted basis.

Expanded reference: https://stefanosbalaskas.github.io/eyetrajectoriespy/methods/mathematical-reference/#fpca

## Integrated functional L2 distance

**Functions:** `functional_l2_distance()`, `pairwise_functional_distances()`

$$
d_{L^2}(\mathbf a,\mathbf b)=\left[\sum_m w_m\sum_d\omega_d\{a_d(t_m)-b_d(t_m)\}^2\right]^{1/2}
$$

**Scope:** Complete trajectories on a common grid; optional dimension weights must be non-negative.

Expanded reference: https://stefanosbalaskas.github.io/eyetrajectoriespy/methods/mathematical-reference/#functional-l2

## Two-level participant / trial decomposition

**Functions:** `fit_multilevel_fpca()`

$$
\mathbf G_{ij}(t)=\boldsymbol\mu(t)+\mathbf U_i(t)+\mathbf V_{ij}(t)
$$

$$
\mathbf U_i(t)=\overline{\mathbf G}_{i\cdot}(t)-\boldsymbol\mu(t),\quad \mathbf V_{ij}(t)=\mathbf G_{ij}(t)-\overline{\mathbf G}_{i\cdot}(t)
$$

**Scope:** Transparent two-level functional ANOVA followed by separate FPCAs; not a full probabilistic functional mixed model.

Expanded reference: https://stefanosbalaskas.github.io/eyetrajectoriespy/methods/mathematical-reference/#multilevel

## Compositional AOI additive log-ratio transform

**Functions:** `alr_transform()`, `inverse_alr()`, `fit_compositional_fpca()`, `reconstruct_compositional_fpca()`

$$
z_k(t)=\log\frac{p_k^\epsilon(t)}{p_r^\epsilon(t)},\quad k\ne r
$$

$$
p_k(t)=\frac{q_k(t)}{\sum_{\ell=1}^{K}q_\ell(t)}
$$

**Scope:** Simplex-valued AOI probabilities with explicit reference component and zero-replacement epsilon.

Expanded reference: https://stefanosbalaskas.github.io/eyetrajectoriespy/methods/mathematical-reference/#compositional

## Landmark registration and phase displacement

**Functions:** `register_to_landmarks()`, `warping_displacement()`, `phase_summary()`

$$
\mathbf G_i^{\mathrm{reg}}(t)=\mathbf G_i\{h_i(t)\}
$$

$$
\Delta_i(t)=h_i(t)-t
$$

**Scope:** Monotone piecewise-linear landmark warping; phase is retained rather than silently discarded.

Expanded reference: https://stefanosbalaskas.github.io/eyetrajectoriespy/methods/mathematical-reference/#registration

## Simultaneous functional mean multiplier band

**Functions:** `multiplier_functional_mean_band()`, `windowed_rqa_functional_mean_band()`

$$
M^{(b)}=\max_{m,d}\left|\frac{n^{-1/2}\sum_i e_i^{(b)}\{X_{id}(t_m)-\overline X_d(t_m)\}}{\widehat\sigma_d(t_m)}\right|
$$

$$
\overline X_d(t_m)\pm c_{1-\alpha}\frac{\widehat\sigma_d(t_m)}{\sqrt n}
$$

**Scope:** Simultaneous calibration over the observed time-by-dimension grid, with curve or equal-weight participant inference units.

Expanded reference: https://stefanosbalaskas.github.io/eyetrajectoriespy/methods/mathematical-reference/#mean-band

## Scalar-on-function regression through FPC scores

**Functions:** `fit_scalar_on_function_regression()`

$$
Y_i=\beta_0+\sum_{k=1}^{K}\beta_k\xi_{ik}+\mathbf z_i^\top\boldsymbol\gamma+\varepsilon_i
$$

$$
\operatorname{logit}\{\Pr(Y_i=1)\}=\beta_0+\sum_{k=1}^{K}\beta_k\xi_{ik}+\mathbf z_i^\top\boldsymbol\gamma
$$

**Scope:** Score-space approximation; Gaussian and binomial fits have distinct inferential assumptions and no automatic component-selection uncertainty.

Expanded reference: https://stefanosbalaskas.github.io/eyetrajectoriespy/methods/mathematical-reference/#fpcr

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

Expanded reference: https://stefanosbalaskas.github.io/eyetrajectoriespy/methods/mathematical-reference/#wild-bootstrap

## Simultaneous fixed-target wild-bootstrap calibration

**Functions:** `fpca_wild_bootstrap_projection_simultaneous_interval()`

$$
M^{*(b)}=\max_{1\le j\le J}|T_j^{*(b)}|
$$

**Scope:** One predeclared fixed-target family using the stored joint root matrix; no adaptive target-family guarantee.

Expanded reference: https://stefanosbalaskas.github.io/eyetrajectoriespy/methods/mathematical-reference/#simultaneous-wild-bootstrap

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

Expanded reference: https://stefanosbalaskas.github.io/eyetrajectoriespy/methods/mathematical-reference/#family-tests

## Finite-bootstrap Monte Carlo precision

**Functions:** `fpca_wild_bootstrap_family_test_monte_carlo_diagnostics()`

$$
\widehat q=\frac{r}{B}
$$

$$
\widehat{\mathrm{MCSE}}=\sqrt{\frac{\widehat q(1-\widehat q)}{B}}
$$

**Scope:** Simulation precision of retained bootstrap tail probabilities; not scientific-effect uncertainty and not sequential-stopping inference.

Expanded reference: https://stefanosbalaskas.github.io/eyetrajectoriespy/methods/mathematical-reference/#monte-carlo

## Split-conformal FPCA anomaly p-value

**Functions:** `split_conformal_fpca_anomaly()`

$$
p_{\mathrm{conf}}=\frac{1+\sum_{i=1}^{m}\mathbb I(A_i\ge A_{\mathrm{new}})}{m+1}
$$

**Scope:** Marginal curve-level split-conformal interpretation under exchangeability; review flags are never automatic exclusions.

Expanded reference: https://stefanosbalaskas.github.io/eyetrajectoriespy/methods/mathematical-reference/#conformal

## Delay-coordinate reconstruction and embedding diagnostics

**Functions:** `delay_embed_trajectory()`, `embedding_delay_diagnostics()`, `embedding_dimension_diagnostics()`

$$
\mathbf z_t=[\mathbf G(t),\mathbf G(t-\tau),\ldots,\mathbf G(t-(m-1)\tau)]
$$

$$
I(\tau)=\sum_{a,b}p_{ab}(\tau)\log\frac{p_{ab}(\tau)}{p_a p_b}
$$

$$
\mathrm{FNN}_m=\frac{1}{N_m}\sum_i \mathbb I\{\text{neighbor }i\text{ fails the declared }R_{\mathrm{tol}}\text{ or }A_{\mathrm{tol}}\text{ criterion}\}
$$

**Scope:** Common-grid reconstruction only; delay and embedding dimension remain analyst-declared after diagnostics, with no silent smoothing, interpolation, or scaling.

Expanded reference: https://stefanosbalaskas.github.io/eyetrajectoriespy/methods/mathematical-reference/#delay-embedding

## Sparse recurrence and recurrence quantification

**Functions:** `recurrence_matrix()`, `recurrence_radius_profile()`, `rqa_metrics()`, `rqa_parameter_sensitivity()`, `windowed_rqa()`, `cross_recurrence_matrix()`, `cross_rqa_metrics()`

$$
R_{ij}=\mathbb I\{\|\mathbf z_i-\mathbf z_j\|_p\le\varepsilon\}
$$

$$
\mathrm{RR}=\frac{\sum_{i<j}R_{ij}}{N_{\mathrm{eligible}}}
$$

$$
\mathrm{DET}=\frac{\sum_{\ell\ge\ell_{\min}}\ell P_d(\ell)}{\sum_{\ell\ge1}\ell P_d(\ell)}
$$

$$
\mathrm{LAM}=\frac{\sum_{v\ge v_{\min}}v P_v(v)}{\sum_{v\ge1}v P_v(v)}
$$

**Scope:** Sparse observed-state or reconstructed-state recurrence with an explicit radius policy, metric, Theiler exclusion, and line-length thresholds.

Expanded reference: https://stefanosbalaskas.github.io/eyetrajectoriespy/methods/mathematical-reference/#recurrence

## Population mean bootstrap for curve-level RQA metrics

**Functions:** `bootstrap_rqa_metric_means()`

$$
M_{iq}=Q_q\{R_i(\theta)\}
$$

$$
U_{pq}=m_p^{-1}\sum_{j=1}^{m_p}M_{pjq}
$$

$$
\overline U_q^{*(b)}=n^{-1}\sum_{r=1}^{n}U_{I_r^{(b)}q}
$$

$$
CI_{1-\alpha}=[Q_{\alpha/2}(\overline U_q^*),Q_{1-\alpha/2}(\overline U_q^*)]
$$

**Scope:** Percentile bootstrap for the between-unit population mean of fixed-specification curve-level RQA summaries; participant mode first averages curve metrics within participant. It does not estimate within-single-trajectory or parameter-selection uncertainty.

Expanded reference: https://stefanosbalaskas.github.io/eyetrajectoriespy/methods/mathematical-reference/#rqa-population-bootstrap

## Windowed RQA as functional trajectories

**Functions:** `windowed_rqa_trajectory_set()`, `windowed_rqa_sensitivity()`

$$
F_{iq}(c_w)=M_q\{R_i^{(w)}\},\quad c_w=\frac{t_{w,\mathrm{start}}+t_{w,\mathrm{end}}}{2}
$$

$$
\omega=\frac{\max(0,W-S)}{W}
$$

**Scope:** Derived functional summaries of declared sliding-window RQA; overlapping windows reuse source samples and are not independent observational units.

Expanded reference: https://stefanosbalaskas.github.io/eyetrajectoriespy/methods/mathematical-reference/#functional-rqa-trajectories

## Rosenstein local divergence and largest Lyapunov estimate

**Functions:** `local_divergence_curve()`, `estimate_largest_lyapunov_rosenstein()`, `lyapunov_parameter_sensitivity()`

$$
d_i(k)=\|\mathbf z_{i+k}-\mathbf z_{j(i)+k}\|_2
$$

$$
D(k)=\frac{1}{N_k}\sum_i\log d_i(k)
$$

$$
D(k)\approx a+\lambda_{\max}k\Delta t
$$

**Scope:** Nearest-neighbor local-divergence estimate with explicit Theiler window and analyst-declared linear fit interval; a positive estimate is not standalone evidence of deterministic chaos.

Expanded reference: https://stefanosbalaskas.github.io/eyetrajectoriespy/methods/mathematical-reference/#local-divergence

## Kantz neighborhood divergence and largest Lyapunov estimate

**Functions:** `kantz_divergence_curve()`, `estimate_largest_lyapunov_kantz()`

$
\mathcal N_i(\varepsilon)=\{j:\|\mathbf z_i-\mathbf z_j\|_2\le\varepsilon,\ |i-j|>w\}
$

$
S(\varepsilon,k)=\frac{1}{N_k}\sum_i\log\left[\frac{1}{|\mathcal N_i(k)|}\sum_{j\in\mathcal N_i(k)}\|\mathbf z_{i+k}-\mathbf z_{j+k}\|_2\right]
$

$
S(\varepsilon,k)\approx a+\lambda_{\max}k\Delta t
$

**Scope:** Fixed-radius Kantz neighborhood divergence with explicit minimum neighbor count, Theiler exclusion, and analyst-declared fit interval; no automatic radius expansion or chaos classification.

Expanded reference: https://stefanosbalaskas.github.io/eyetrajectoriespy/methods/mathematical-reference/#kantz-local-divergence

## IAAFT surrogate nonlinearity test

**Functions:** `surrogate_nonlinearity_test()`

$$
p=\frac{1+\sum_{b=1}^{B}\mathbb I(T_b^*\ge T_{\mathrm{obs}})}{B+1}
$$

**Scope:** Monte Carlo test against the declared IAAFT linear-stochastic surrogate null using identical statistic settings for observed and surrogate series.

Expanded reference: https://stefanosbalaskas.github.io/eyetrajectoriespy/methods/mathematical-reference/#surrogate-nonlinearity

## Empirical Poincare return-map stability

**Functions:** `poincare_crossings()`, `fit_local_return_map()`, `return_map_stability()`

$$
h(\mathbf z)=0,\qquad \mathbf z_n=\text{successive section crossings}
$$

$$
\mathbf z_{n+1}=\mathbf a+\mathbf J(\mathbf z_n-\mathbf z_0)+\boldsymbol\varepsilon_n
$$

$$
\rho(\mathbf J)=\max_j|\lambda_j(\mathbf J)|
$$

**Scope:** Experimental local affine cycle-to-cycle diagnostic; the empirical Jacobian is not a variational-equation monodromy matrix and its eigenvalues are not classical Floquet multipliers.

Expanded reference: https://stefanosbalaskas.github.io/eyetrajectoriespy/methods/mathematical-reference/#return-map-stability
