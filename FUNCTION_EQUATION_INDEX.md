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

## Discrete Fréchet trajectory distance

**Functions:** `discrete_frechet_distance()`, `pairwise_discrete_frechet_distances()`

$$
d_w(\mathbf p_i,\mathbf q_j)=\left[\sum_r\omega_r(p_{ir}-q_{jr})^2\right]^{1/2}
$$

$$
D_{i,j}=\max\left\{d_w(\mathbf p_i,\mathbf q_j),\min(D_{i-1,j},D_{i-1,j-1},D_{i,j-1})\right\}
$$

$$
\delta_{dF}(P,Q)=D_{m,n}
$$

**Scope:** Ordered complete point sequences with monotone coupling and no backtracking; elapsed time is not part of the recurrence, and no interpolation, resampling, normalization, or path simplification is introduced automatically.

Expanded reference: https://stefanosbalaskas.github.io/eyetrajectoriespy/methods/mathematical-reference/#discrete-frechet

## Dynamic time warping trajectory distance

**Functions:** `dynamic_time_warping_distance()`, `pairwise_dynamic_time_warping_distances()`

$$
d_w(\mathbf p_i,\mathbf q_j)=\left[\sum_r\omega_r(p_{ir}-q_{jr})^2\right]^{1/2}
$$

$$
C^{(s1)}_{i,j}=d_w(\mathbf p_i,\mathbf q_j)+\min(C_{i-1,j-1},C_{i-1,j},C_{i,j-1})
$$

$$
C^{(s2)}_{i,j}=\min\{C_{i-1,j-1}+2d_w,C_{i-1,j}+d_w,C_{i,j-1}+d_w\}
$$

$$
d^{(s2)}_{\mathrm{norm}}(P,Q)=\frac{C^{(s2)}_{m,n}}{m+n}
$$

**Scope:** Complete ordered point sequences with explicit symmetric1 or normalizable symmetric2 step weighting and optional Sakoe-Chiba sample-index constraint; the 0.33 symmetric1 raw-cost default is preserved, elapsed time is not used, and no hidden preprocessing or automatic specification selection is introduced.

Expanded reference: https://stefanosbalaskas.github.io/eyetrajectoriespy/methods/mathematical-reference/#dynamic-time-warping

## Trajectory-distance specification sensitivity

**Functions:** `trajectory_distance_sensitivity()`

$$
\mathbf v^{(s)}=\{D_{ij}^{(s)}:1\le i<j\le n\}
$$

$$
\rho_S(s,r)=\operatorname{corr}\left(\operatorname{rank}\mathbf v^{(s)},\operatorname{rank}\mathbf v^{(r)}\right)
$$

$$
J_k^{(s,r)}(i)=\frac{|\mathcal N_k^{(s)}(i)\cap\mathcal N_k^{(r)}(i)|}{|\mathcal N_k^{(s)}(i)\cup\mathcal N_k^{(r)}(i)|}
$$

$$
A_1^{(s,r)}=\frac{1}{n}\sum_{i=1}^{n}\mathbb I\{\mathcal N_1^{(s)}(i)=\mathcal N_1^{(r)}(i)\}
$$

**Scope:** Descriptive comparison of at least two analyst-declared L2, discrete-Frechet, and/or DTW specifications on the same complete trajectories. Raw distance matrices remain on native scales; no standardization, consensus metric, p-value, or preferred distance is constructed automatically.

Expanded reference: https://stefanosbalaskas.github.io/eyetrajectoriespy/methods/mathematical-reference/#trajectory-distance-sensitivity

## Continuous planar trajectory geometry

**Functions:** `heading_function()`, `signed_curvature_function()`, `turning_rate_function()`, `trajectory_tortuosity()`

$$
\theta(t)=\operatorname{atan2}\{y'(t),x'(t)\}
$$

$$
\kappa(t)=\frac{x'(t)y''(t)-y'(t)x''(t)}{\{x'(t)^2+y'(t)^2\}^{3/2}}
$$

$$
\omega(t)=\frac{x'(t)y''(t)-y'(t)x''(t)}{x'(t)^2+y'(t)^2}=\kappa(t)\|\mathbf G'(t)\|
$$

$$
T=\frac{\sum_{m=1}^{M-1}\|\mathbf G(t_{m+1})-\mathbf G(t_m)\|_2}{\|\mathbf G(t_M)-\mathbf G(t_1)\|_2}
$$

**Scope:** Complete declared planar coordinates with numerical derivatives computed without hidden smoothing; low-speed and zero-displacement undefinedness is explicit, and geometric interpretation remains conditional on source coordinate scaling and axis orientation.

Expanded reference: https://stefanosbalaskas.github.io/eyetrajectoriespy/methods/mathematical-reference/#trajectory-geometry

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

## Joint functional mixed-effects regression

**Functions:** `fit_functional_mixed_effects_regression()`, `functional_mixed_effects_whitened_residuals()`

$$
Y_{ij}(t)=\mathbf x_{ij}^{\top}\boldsymbol\beta(t)+\mathbf B_r(t)^{\top}\mathbf u_i+u_{ij}(t)+\varepsilon_{ij}(t)
$$

$$
\beta_p(t)=\mathbf B_f(t)^{\top}\boldsymbol\theta_p
$$

$$
\mathbf u_i\sim N(\mathbf 0,\boldsymbol\Psi_{P})
$$

$$
u_{ij}(t)=\mathbf B_u(t)^\top\mathbf v_{ij},\qquad \mathbf v_{ij}\sim N(\mathbf 0,\boldsymbol\Psi_{T})
$$

$$
\operatorname{Cov}\{\boldsymbol\varepsilon_{ij}\}=\sigma^2\mathbf R_\theta
$$

$$
R_\phi(t,s)=\exp\{-|t-s|/\phi\},\qquad \phi>0
$$

$$
R_{\rho,rs}=\rho^{|r-s|},\qquad -1<\rho<1
$$

$$
\mathbf V_i=\mathbf Z_i\boldsymbol\Psi_P\mathbf Z_i^\top+\sum_j\mathbf W_{ij}\boldsymbol\Psi_T\mathbf W_{ij}^\top+\sigma^2\operatorname{blockdiag}_j\{\mathbf R_\theta\}
$$

$$
\sigma^2\mathbf R_\theta=\mathbf L\mathbf L^\top,\qquad \mathbf e_{ij}^{(w)}=\mathbf L^{-1}\mathbf e_{ij}
$$

**Scope:** One selected Gaussian functional response dimension on a common grid with explicit B-spline fixed effects and participant functional random effects. Version 0.48 optionally adds one nested trial functional random intercept with a shared unstructured basis-coefficient covariance. Version 0.49 optionally adds an analyst-declared within-trial residual covariance: physical-time exponential correlation on arbitrary strictly increasing common grids or signed index-step AR(1) on verified regular grids. Residual covariance is block diagonal across trials; phi/rho is estimated jointly and whitening uses the fitted residual covariance. No automatic basis, trial-effect, or residual-correlation-family selection, multiple trial random effects, or multivariate cross-dimension covariance is claimed.

Expanded reference: https://stefanosbalaskas.github.io/eyetrajectoriespy/methods/mathematical-reference/#functional-mixed-effects

## Predeclared functional mixed-effects covariance sensitivity

**Functions:** \`functional_mixed_effects_covariance_sensitivity()\`, \`functional_mixed_effects_variance_decomposition()\`

$
\Delta\beta_m(t)=\widehat\beta_m(t)-\widehat\beta_r(t)
$

$
D_{\infty,m}=\sup_t|\Delta\beta_m(t)|
$

$
D_{2,m}=\left[\int\{\Delta\beta_m(t)\}^2dt\right]^{1/2}
$

$
v_{P0}(t)=\mathbf B_P(t)^\top\boldsymbol\Psi_{P0}\mathbf B_P(t)
$

$
v_T(t)=\mathbf B_T(t)^\top\boldsymbol\Psi_T\mathbf B_T(t)
$

$
v_\varepsilon(t)=\sigma^2
$

$
\mathrm{AIC}_m=-2\ell_m+2k_m,\qquad \mathrm{BIC}_m=-2\ell_m+k_m\log n
$

**Scope:** Descriptive comparison of already fitted, predeclared covariance structures against one analyst-declared reference. Successful fits must share observations, fixed design/basis, participant mapping, time grid, response dimension, and ML/REML mode. Failed declared structures remain visible. Coefficient changes, paired band-width changes, variance decomposition, raw/whitened residual diagnostics, and information criteria are reported without ranking, automatic selection, or likelihood-ratio p-values.

Expanded reference: https://stefanosbalaskas.github.io/eyetrajectoriespy/methods/mathematical-reference/#functional-mixed-effects-covariance-sensitivity

## One participant random functional slope

**Functions:** `functional_random_effect_frame()`

$$
Y_{ij}(t)=\mathbf x_{ij}^{\top}\boldsymbol\beta(t)+b_{0i}(t)+X_{ij,q}b_{1i}(t)+\varepsilon_{ij}(t)
$$

$$
b_{0i}(t)=\mathbf B_r(t)^{\top}\mathbf u_{0i},\qquad b_{1i}(t)=\mathbf B_r(t)^{\top}\mathbf u_{1i}
$$

$$
\begin{bmatrix}\mathbf u_{0i}\\\mathbf u_{1i}\end{bmatrix}\sim N\!\left(\mathbf 0,\boldsymbol\Psi_{2q}\right)
$$

$$
p_{\Psi}=\frac{(2q)(2q+1)}{2}
$$

**Scope:** Exactly one analyst-declared random functional slope predictor using the same q-dimensional B-spline basis size as the participant functional random intercept. The stacked 2q random coefficient vector has one unstructured covariance. Version 0.45 requires the slope predictor to vary within every participant and requires the participant count to exceed the number of free covariance parameters. No automatic random-slope selection or multiple random slopes is introduced. The slope may coexist with the separately declared 0.48 trial effect and 0.49 residual-correlation family.

Expanded reference: https://stefanosbalaskas.github.io/eyetrajectoriespy/methods/mathematical-reference/#functional-mixed-effects-random-slope

## Full-refit participant bootstrap for functional mixed-effects models

**Functions:** `bootstrap_functional_mixed_effects_full_refit()`, `compare_functional_mixed_effects_bootstraps()`

$$
I_1^{*(b)},\ldots,I_n^{*(b)}\overset{\mathrm{iid}}{\sim}\{1,\ldots,n\}
$$

$$
\mathcal D^{*(b)}\longrightarrow\left\{\widehat{\boldsymbol\beta}^{*(b)}(t),\widehat{\boldsymbol\Psi}_P^{*(b)},\widehat{\boldsymbol\Psi}_T^{*(b)},\widehat\sigma^{2*(b)},\widehat\theta^{*(b)}\right\}
$$

$$
R_p(t_m)=\frac{W_{p,\mathrm{full}}(t_m)}{W_{p,\mathrm{fixed}}(t_m)}
$$

**Scope:** Whole-participant case bootstrap with a complete declared mixed-model parameter refit in every replicate. Duplicate source-participant draws receive distinct bootstrap group identities. Fixed effects, participant covariance, optional trial covariance, residual variance, and any declared residual-correlation parameter are re-estimated; basis sizes, spline degree, preprocessing, predictor specification, random-slope structure, REML/ML choice, and optimizer remain fixed. Failed replicates raise and are not silently redrawn.

Expanded reference: https://stefanosbalaskas.github.io/eyetrajectoriespy/methods/mathematical-reference/#functional-mixed-effects-full-refit-bootstrap

## Participant-cluster simultaneous mixed-effects coefficient bands

**Functions:** `bootstrap_functional_mixed_effects_coefficients()`, `functional_mixed_effects_simultaneous_bands()`

$$
\mathbf V_i=\mathbf Z_i\widehat{\boldsymbol\Psi}_P\mathbf Z_i^\top+\sum_j\mathbf W_{ij}\widehat{\boldsymbol\Psi}_T\mathbf W_{ij}^\top+\widehat\sigma^2\operatorname{blockdiag}_j\{\widehat{\mathbf R}_\theta\}
$$

$$
\widehat{\boldsymbol\theta}^{*(b)}=\left[\sum_{r=1}^{n}\mathbf A_{I_r^{(b)}}\right]^{-1}\sum_{r=1}^{n}\mathbf s_{I_r^{(b)}},\quad \mathbf A_i=\mathbf X_i^\top\mathbf V_i^{-1}\mathbf X_i,\ \mathbf s_i=\mathbf X_i^\top\mathbf V_i^{-1}\mathbf y_i
$$

$$
M_p^{*(b)}=\max_m\left|\frac{\widehat\beta_p^{*(b)}(t_m)-\overline{\widehat\beta_p^*}(t_m)}{\widehat{\mathrm{SE}}_p^*(t_m)}\right|
$$

$$
\widehat\beta_p(t_m)\pm c_{p,1-\alpha}\widehat{\mathrm{SE}}_p^*(t_m)
$$

**Scope:** Whole-participant case bootstrap for fixed coefficient functions. Each resample re-estimates the fixed B-spline coefficients by GLS while conditioning on the reference participant covariance, optional trial covariance, residual variance, residual-correlation parameter, and declared bases. Bands are simultaneous over the observed time grid with coefficient or full fixed-effect-family scope; variance-component, basis-selection, and between-grid uncertainty are not included.

Expanded reference: https://stefanosbalaskas.github.io/eyetrajectoriespy/methods/mathematical-reference/#functional-mixed-effects-simultaneous

## Function-on-scalar regression and simultaneous coefficient bands

**Functions:** `fit_function_on_scalar_regression()`, `bootstrap_function_on_scalar_coefficients()`, `function_on_scalar_simultaneous_bands()`

$$
\mathbf Y(t)=\mathbf X\boldsymbol\beta(t)+\boldsymbol\varepsilon(t)
$$

$$
\widehat{\boldsymbol\beta}(t)=(\mathbf X^\top\mathbf X)^{-1}\mathbf X^\top\mathbf Y(t)
$$

$$
Y_i^{*(b)}(t)=\widehat Y_i(t)+W_i^{(b)}\widehat\varepsilon_i(t)
$$

$$
M_j^{*(b)}=\max_{m,d}\left|\frac{\widehat\beta_{j,d}^{*(b)}(t_m)-\widehat\beta_{j,d}(t_m)}{\widehat{\mathrm{SE}}\{\widehat\beta_{j,d}(t_m)\}}\right|
$$

$$
\widehat\beta_{j,d}(t_m)\pm c_{j,1-\alpha}\widehat{\mathrm{SE}}\{\widehat\beta_{j,d}(t_m)\}
$$

**Scope:** Observed-grid OLS for functional responses with explicit scalar design, HC1 pointwise sandwich standard errors, and fixed-design wild-bootstrap maxima. Repeated trials are supported only through equal-weight participant aggregation when all predictors are constant within participant; this is not a functional mixed model.

Expanded reference: https://stefanosbalaskas.github.io/eyetrajectoriespy/methods/mathematical-reference/#function-on-scalar

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

## Synchronized joint recurrence and JRQA

**Functions:** `joint_recurrence_matrix()`, `joint_rqa_metrics()`

$$
JR_{ij}=\prod_{s=1}^{S}R_{ij}^{(s)}
$$

$$
\mathrm{JRR}=\frac{\sum_{i<j}JR_{ij}}{N_{\mathrm{eligible}}}
$$

$$
\mathrm{JDET}=\frac{\sum_{\ell\ge\ell_{\min}}\ell P_{d,J}(\ell)}{\sum_{\ell\ge1}\ell P_{d,J}(\ell)}
$$

$$
\mathrm{JLAM}=\frac{\sum_{v\ge v_{\min}}v P_{v,J}(v)}{\sum_{v\ge1}v P_{v,J}(v)}
$$

**Scope:** Logical intersection of at least two synchronized auto-recurrence matrices on an exact common grid with one shared Theiler exclusion. Component state spaces, metrics, and thresholds may differ and remain explicit. No lag alignment, resampling, threshold harmonization, cross-recurrence interpretation, or causal-coupling claim is introduced.

Expanded reference: https://stefanosbalaskas.github.io/eyetrajectoriespy/methods/mathematical-reference/#joint-recurrence

## Sparse recurrence-network topology

**Functions:** `recurrence_network()`, `recurrence_network_node_frame()`, `recurrence_network_summary_frame()`

$$
A_{ij}=R_{ij},\quad i\ne j,\qquad A_{ii}=0
$$

$$
k_i=\sum_j A_{ij}
$$

$$
C_i=\frac{2T_i}{k_i(k_i-1)}
$$

$$
\mathcal T=\frac{3N_{\triangle}}{N_{\mathrm{triples}}}
$$

$$
\rho_G=\frac{2E}{N(N-1)}
$$

**Scope:** Undirected unweighted network induced by one declared symmetric auto-recurrence matrix. Network topology inherits the recurrence state representation, metric, threshold policy, Theiler exclusion, and sampling design. No threshold tuning, community optimization, edge weighting, or automatic dynamical-dimension interpretation is introduced.

Expanded reference: https://stefanosbalaskas.github.io/eyetrajectoriespy/methods/mathematical-reference/#recurrence-network

## Discrete transfer entropy and circular-shift surrogate testing

**Functions:** `discrete_transfer_entropy()`, `transfer_entropy_circular_shift_test()`

$$
T_{X\to Y}(k,l,d)=I\!\left(X_{t-d}^{(l)};Y_t\mid Y_{t-1}^{(k)}\right)
$$

$$
T_{X\to Y}=\sum p(y_t,\mathbf y,\mathbf x)\log_2\frac{p(y_t\mid\mathbf y,\mathbf x)}{p(y_t\mid\mathbf y)}
$$

$$
p_+=\frac{1+\sum_{b=1}^{B}I(T_b^*\ge T_{obs})}{B+1}
$$

**Scope:** Empirical plug-in conditional mutual information for analyst-supplied integer-coded states with explicit target/source histories and source lag. Circular-shift inference uses only analyst-declared shifts. No automatic discretization, lag/history selection, shift generation, or causal interpretation is introduced.

Expanded reference: https://stefanosbalaskas.github.io/eyetrajectoriespy/methods/mathematical-reference/#discrete-transfer-entropy

## Conditional transfer entropy and source-shift surrogate testing

**Functions:** `conditional_transfer_entropy()`, `conditional_transfer_entropy_circular_shift_test()`

$$
T_{X\to Y\mid Z}(k,l,m,d,c)=I\!\left(X_{t-d}^{(l)};Y_t\mid Y_{t-1}^{(k)},Z_{t-c}^{(m)}\right)
$$

$$
T_{X\to Y\mid Z}=\sum p(y_t,\mathbf y,\mathbf x,\mathbf z)\log_2\frac{p(y_t\mid\mathbf y,\mathbf x,\mathbf z)}{p(y_t\mid\mathbf y,\mathbf z)}
$$

$$
p_+=\frac{1+\sum_{b=1}^{B}I(T_{b}^{*,cond}\ge T_{obs}^{cond})}{B+1}
$$

**Scope:** Empirical plug-in conditional mutual information for analyst-supplied integer-coded source, target, and conditioning states with explicit target/source/conditioning histories and source/conditioning lags. Surrogate inference shifts only the source and holds target and conditioning processes fixed. Conditioning addresses only the explicitly supplied process and does not establish causal influence or guarantee adjustment for unmeasured common drivers.

Expanded reference: https://stefanosbalaskas.github.io/eyetrajectoriespy/methods/mathematical-reference/#conditional-transfer-entropy

## Transfer-entropy specification sensitivity

**Functions:** `transfer_entropy_parameter_sensitivity()`

$$
\Theta=\mathcal K\times\mathcal L\times\mathcal D
$$

$$
T_{\theta}=I\!\left(X_{t-d}^{(l)};Y_t\mid Y_{t-1}^{(k)}\right),\quad \theta=(k,l,d)\in\Theta
$$

$$
\Delta T_{\theta}=T_{\theta,obs}-B^{-1}\sum_{b=1}^{B}T_{\theta,b}^{*}
$$

**Scope:** Descriptive robustness analysis over the full analyst-declared Cartesian grid of target histories, source histories, and source lags. Optional surrogate-centered TE uses the identical declared circular-shift set for every specification. No failed row is discarded and no specification is ranked or selected automatically.

Expanded reference: https://stefanosbalaskas.github.io/eyetrajectoriespy/methods/mathematical-reference/#transfer-entropy-sensitivity

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

**Functions:** `kantz_divergence_curve()`, `estimate_largest_lyapunov_kantz()`, `kantz_parameter_sensitivity()`

$$
\mathcal N_i(\varepsilon)=\{j:\|\mathbf z_i-\mathbf z_j\|_2\le\varepsilon,\ |i-j|>w\}
$$

$$
S(\varepsilon,k)=\frac{1}{N_k}\sum_i\log\left[\frac{1}{|\mathcal N_i(k)|}\sum_{j\in\mathcal N_i(k)}\|\mathbf z_{i+k}-\mathbf z_{j+k}\|_2\right]
$$

$$
S(\varepsilon,k)\approx a+\lambda_{\max}k\Delta t
$$

**Scope:** Fixed-radius Kantz neighborhood divergence with explicit minimum neighbor count, Theiler exclusion, and analyst-declared fit interval; no automatic radius expansion or chaos classification.

Expanded reference: https://stefanosbalaskas.github.io/eyetrajectoriespy/methods/mathematical-reference/#kantz-local-divergence

## Cross-spectrum-aware multivariate IAAFT surrogates

**Functions:** `generate_multivariate_iaaft_surrogates()`, `multivariate_surrogate_nonlinearity_test()`

$$
F_k(\omega)=A_k(\omega)e^{i\phi_k(\omega)}
$$

$$
\Delta\phi_{kr}(\omega)=\phi_k(\omega)-\phi_r(\omega)
$$

$$
F_k^*(\omega)=A_k(\omega)e^{i[\psi_r^*(\omega)+\Delta\phi_{kr}(\omega)]}
$$

$$
C_{k\ell}(\omega)=F_k(\omega)F_\ell(\omega)^*
$$

$$
p=\frac{1+\sum_{b=1}^{B}\mathbb I(T_b^*\ge T_{\mathrm{obs}})}{B+1}
$$

**Scope:** Reference-anchored multivariate IAAFT with exact empirical marginal rank distributions and iterative targeting of each channel power spectrum plus original inter-channel Fourier phase differences. Final power/cross-spectrum preservation is approximate after rank remapping and retained diagnostically; the reference dimension is analyst-declared.

Expanded reference: https://stefanosbalaskas.github.io/eyetrajectoriespy/methods/mathematical-reference/#multivariate-iaaft

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
