"""Programmatic mathematical contracts for public scientific APIs.

The registry is metadata: it does not execute estimators or change numerical
results. It provides one machine-readable source linking scientific functions to
implementation-matched LaTeX, documentation anchors, and scope statements.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True, slots=True)
class MathematicalContract:
    """Mathematical specification attached to one or more public APIs."""

    key: str
    title: str
    public_api: tuple[str, ...]
    equations: tuple[str, ...]
    site_anchor: str
    scope: str


_CONTRACTS = (
    MathematicalContract(
        key="quadrature",
        title="Observed-grid trapezoidal quadrature",
        public_api=("functional_trapezoid_weights",),
        equations=(
            r"w_1=\frac{t_2-t_1}{2},\quad "
            r"w_M=\frac{t_M-t_{M-1}}{2},\quad "
            r"w_m=\frac{(t_m-t_{m-1})+(t_{m+1}-t_m)}{2}",
        ),
        site_anchor="quadrature",
        scope="Strictly increasing observed grids; optional normalization only rescales the weights to sum to one.",
    ),
    MathematicalContract(
        key="fpca",
        title="Quadrature-weighted FPCA / MFPCA",
        public_api=(
            "fit_fpca",
            "fit_mfpca",
            "transform_fpca",
            "reconstruct_fpca",
            "component_trajectories",
        ),
        equations=(
            r"Z_{i,m,d}="
            r"\frac{G_{id}(t_m)-\widehat\mu_d(t_m)}{s_d}\sqrt{w_m}",
            r"\widehat{\mathbf G}^{(K)}_i(t)="
            r"\widehat{\boldsymbol\mu}(t)+"
            r"\sum_{k=1}^{K}\widehat\xi_{ik}\widehat{\boldsymbol\phi}_k(t)",
        ),
        site_anchor="fpca",
        scope="Common-grid functional PCA with explicit channel scaling; retained-component interpretation is conditional on the fitted basis.",
    ),
    MathematicalContract(
        key="functional-l2",
        title="Integrated functional L2 distance",
        public_api=("functional_l2_distance", "pairwise_functional_distances"),
        equations=(
            r"d_{L^2}(\mathbf a,\mathbf b)="
            r"\left[\sum_m w_m\sum_d\omega_d"
            r"\{a_d(t_m)-b_d(t_m)\}^2\right]^{1/2}",
        ),
        site_anchor="functional-l2",
        scope="Complete trajectories on a common grid; optional dimension weights must be non-negative.",
    ),
    MathematicalContract(
        key="discrete-frechet",
        title="Discrete Fréchet trajectory distance",
        public_api=(
            "discrete_frechet_distance",
            "pairwise_discrete_frechet_distances",
        ),
        equations=(
            r"d_w(\mathbf p_i,\mathbf q_j)="
            r"\left[\sum_r\omega_r(p_{ir}-q_{jr})^2\right]^{1/2}",
            r"D_{i,j}=\max\left\{d_w(\mathbf p_i,\mathbf q_j),"
            r"\min(D_{i-1,j},D_{i-1,j-1},D_{i,j-1})\right\}",
            r"\delta_{dF}(P,Q)=D_{m,n}",
        ),
        site_anchor="discrete-frechet",
        scope=(
            "Ordered complete point sequences with monotone coupling and no "
            "backtracking; elapsed time is not part of the recurrence, and no "
            "interpolation, resampling, normalization, or path simplification "
            "is introduced automatically."
        ),
    ),
    MathematicalContract(
        key="dynamic-time-warping",
        title="Dynamic time warping trajectory distance",
        public_api=(
            "dynamic_time_warping_distance",
            "pairwise_dynamic_time_warping_distances",
        ),
        equations=(
            r"d_w(\mathbf p_i,\mathbf q_j)="
            r"\left[\sum_r\omega_r(p_{ir}-q_{jr})^2\right]^{1/2}",
            r"C^{(s1)}_{i,j}=d_w(\mathbf p_i,\mathbf q_j)+"
            r"\min(C_{i-1,j-1},C_{i-1,j},C_{i,j-1})",
            r"C^{(s2)}_{i,j}=\min\{C_{i-1,j-1}+2d_w,"
            r"C_{i-1,j}+d_w,C_{i,j-1}+d_w\}",
            r"d^{(s2)}_{\mathrm{norm}}(P,Q)="
            r"\frac{C^{(s2)}_{m,n}}{m+n}",
        ),
        site_anchor="dynamic-time-warping",
        scope=(
            "Complete ordered point sequences with explicit symmetric1 or "
            "normalizable symmetric2 step weighting and optional Sakoe-Chiba "
            "sample-index constraint; the 0.33 symmetric1 raw-cost default is "
            "preserved, elapsed time is not used, and no hidden preprocessing "
            "or automatic specification selection is introduced."
        ),
    ),
    MathematicalContract(
        key="trajectory-distance-sensitivity",
        title="Trajectory-distance specification sensitivity",
        public_api=("trajectory_distance_sensitivity",),
        equations=(
            r"\mathbf v^{(s)}=\{D_{ij}^{(s)}:1\le i<j\le n\}",
            r"\rho_S(s,r)=\operatorname{corr}\left("
            r"\operatorname{rank}\mathbf v^{(s)},"
            r"\operatorname{rank}\mathbf v^{(r)}\right)",
            r"J_k^{(s,r)}(i)="
            r"\frac{|\mathcal N_k^{(s)}(i)\cap\mathcal N_k^{(r)}(i)|}"
            r"{|\mathcal N_k^{(s)}(i)\cup\mathcal N_k^{(r)}(i)|}",
            r"A_1^{(s,r)}=\frac{1}{n}\sum_{i=1}^{n}"
            r"\mathbb I\{\mathcal N_1^{(s)}(i)=\mathcal N_1^{(r)}(i)\}",
        ),
        site_anchor="trajectory-distance-sensitivity",
        scope=(
            "Descriptive comparison of at least two analyst-declared L2, "
            "discrete-Frechet, and/or DTW specifications on the same complete "
            "trajectories. Raw distance matrices remain on native scales; "
            "no standardization, consensus metric, p-value, or preferred "
            "distance is constructed automatically."
        ),
    ),
    MathematicalContract(
        key="trajectory-geometry",
        title="Continuous planar trajectory geometry",
        public_api=(
            "heading_function",
            "signed_curvature_function",
            "turning_rate_function",
            "trajectory_tortuosity",
        ),
        equations=(
            r"\theta(t)=\operatorname{atan2}\{y'(t),x'(t)\}",
            r"\kappa(t)=\frac{x'(t)y''(t)-y'(t)x''(t)}"
            r"{\{x'(t)^2+y'(t)^2\}^{3/2}}",
            r"\omega(t)=\frac{x'(t)y''(t)-y'(t)x''(t)}"
            r"{x'(t)^2+y'(t)^2}=\kappa(t)\|\mathbf G'(t)\|",
            r"T=\frac{\sum_{m=1}^{M-1}"
            r"\|\mathbf G(t_{m+1})-\mathbf G(t_m)\|_2}"
            r"{\|\mathbf G(t_M)-\mathbf G(t_1)\|_2}",
        ),
        site_anchor="trajectory-geometry",
        scope=(
            "Complete declared planar coordinates with numerical derivatives "
            "computed without hidden smoothing; low-speed and zero-displacement "
            "undefinedness is explicit, and geometric interpretation remains "
            "conditional on source coordinate scaling and axis orientation."
        ),
    ),
    MathematicalContract(
        key="multilevel",
        title="Two-level participant / trial decomposition",
        public_api=("fit_multilevel_fpca",),
        equations=(
            r"\mathbf G_{ij}(t)=\boldsymbol\mu(t)+\mathbf U_i(t)+\mathbf V_{ij}(t)",
            r"\mathbf U_i(t)=\overline{\mathbf G}_{i\cdot}(t)-\boldsymbol\mu(t),"
            r"\quad "
            r"\mathbf V_{ij}(t)=\mathbf G_{ij}(t)-\overline{\mathbf G}_{i\cdot}(t)",
        ),
        site_anchor="multilevel",
        scope="Transparent two-level functional ANOVA followed by separate FPCAs; not a full probabilistic functional mixed model.",
    ),
    MathematicalContract(
        key="compositional",
        title="Compositional AOI additive log-ratio transform",
        public_api=(
            "alr_transform",
            "inverse_alr",
            "fit_compositional_fpca",
            "reconstruct_compositional_fpca",
        ),
        equations=(
            r"z_k(t)=\log\frac{p_k^\epsilon(t)}{p_r^\epsilon(t)},\quad k\ne r",
            r"p_k(t)=\frac{q_k(t)}{\sum_{\ell=1}^{K}q_\ell(t)}",
        ),
        site_anchor="compositional",
        scope="Simplex-valued AOI probabilities with explicit reference component and zero-replacement epsilon.",
    ),
    MathematicalContract(
        key="registration",
        title="Landmark registration and phase displacement",
        public_api=("register_to_landmarks", "warping_displacement", "phase_summary"),
        equations=(
            r"\mathbf G_i^{\mathrm{reg}}(t)=\mathbf G_i\{h_i(t)\}",
            r"\Delta_i(t)=h_i(t)-t",
        ),
        site_anchor="registration",
        scope="Monotone piecewise-linear landmark warping; phase is retained rather than silently discarded.",
    ),
    MathematicalContract(
        key="mean-band",
        title="Simultaneous functional mean multiplier band",
        public_api=("multiplier_functional_mean_band", "windowed_rqa_functional_mean_band"),
        equations=(
            r"M^{(b)}=\max_{m,d}\left|"
            r"\frac{n^{-1/2}\sum_i e_i^{(b)}\{X_{id}(t_m)-\overline X_d(t_m)\}}"
            r"{\widehat\sigma_d(t_m)}\right|",
            r"\overline X_d(t_m)\pm "
            r"c_{1-\alpha}\frac{\widehat\sigma_d(t_m)}{\sqrt n}",
        ),
        site_anchor="mean-band",
        scope="Simultaneous calibration over the observed time-by-dimension grid, with curve or equal-weight participant inference units.",
    ),
    MathematicalContract(
        key="functional-mixed-effects",
        title="Joint functional mixed-effects regression",
        public_api=("fit_functional_mixed_effects_regression",),
        equations=(
            r"Y_{ij}(t)=\mathbf x_{ij}^{\top}\boldsymbol\beta(t)"
            r"+\mathbf B_r(t)^{\top}\mathbf u_i+\varepsilon_{ij}(t)",
            r"\beta_p(t)=\mathbf B_f(t)^{\top}\boldsymbol\theta_p",
            r"\mathbf u_i\sim N(\mathbf 0,\boldsymbol\Psi_{p}),\qquad "
            r"\varepsilon_{ij}(t_m)\sim N(0,\sigma^2)",
            r"\operatorname{Cov}(\mathbf Y_i\mid\mathbf X_i)="
            r"\mathbf Z_i\boldsymbol\Psi_p\mathbf Z_i^\top+\sigma^2\mathbf I",
            r"u_{ij}(t)=\mathbf B_u(t)^\top\mathbf v_{ij},\qquad "
            r"\mathbf v_{ij}\sim N(\mathbf 0,\boldsymbol\Psi_{trial})",
            r"\mathbf V_i=\mathbf Z_i\boldsymbol\Psi_p\mathbf Z_i^\top"
            r"+\sum_j\mathbf W_{ij}\boldsymbol\Psi_{trial}\mathbf W_{ij}^\top"
            r"+\sigma^2\mathbf I",
        ),
        site_anchor="functional-mixed-effects",
        scope=(
            "One selected Gaussian functional response dimension on a common "
            "grid with explicit B-spline fixed effects and participant "
            "functional random effects. Version 0.48 optionally adds one nested "
            "trial functional random intercept with its own shared unstructured "
            "basis-coefficient covariance. The trial extension is explicit, "
            "requires unique participant/trial pairs and at least two trials "
            "per participant, and retains conditionally iid grid residuals "
            "after the declared random effects. No automatic basis/covariance "
            "selection, residual serial-correlation model, multiple trial "
            "random effects, or multivariate cross-dimension covariance is claimed."
        ),
    ),
    MathematicalContract(
        key="functional-mixed-effects-random-slope",
        title="One participant random functional slope",
        public_api=("functional_random_effect_frame",),
        equations=(
            r"Y_{ij}(t)=\mathbf x_{ij}^{\top}\boldsymbol\beta(t)"
            r"+b_{0i}(t)+X_{ij,q}b_{1i}(t)+\varepsilon_{ij}(t)",
            r"b_{0i}(t)=\mathbf B_r(t)^{\top}\mathbf u_{0i},\qquad "
            r"b_{1i}(t)=\mathbf B_r(t)^{\top}\mathbf u_{1i}",
            r"\begin{bmatrix}\mathbf u_{0i}\\\mathbf u_{1i}\end{bmatrix}"
            r"\sim N\!\left(\mathbf 0,\boldsymbol\Psi_{2q}\right)",
            r"p_{\Psi}=\frac{(2q)(2q+1)}{2}",
        ),
        site_anchor="functional-mixed-effects-random-slope",
        scope=(
            "Exactly one analyst-declared random functional slope predictor "
            "using the same q-dimensional B-spline basis size as the participant "
            "functional random intercept. The stacked 2q random coefficient "
            "vector has one unstructured covariance. Version 0.45 requires the "
            "slope predictor to vary within every participant and requires the "
            "participant count to exceed the number of free covariance "
            "parameters. No automatic random-slope selection, multiple random "
            "slopes, residual serial-correlation model, or generalized response "
            "is introduced."
        ),
    ),
    MathematicalContract(
        key="functional-mixed-effects-full-refit-bootstrap",
        title="Full-refit participant bootstrap for functional mixed-effects models",
        public_api=(
            "bootstrap_functional_mixed_effects_full_refit",
            "compare_functional_mixed_effects_bootstraps",
        ),
        equations=(
            r"I_1^{*(b)},\ldots,I_n^{*(b)}"
            r"\overset{\mathrm{iid}}{\sim}\{1,\ldots,n\}",
            r"\mathcal D^{*(b)}\longrightarrow"
            r"\left\{\widehat{\boldsymbol\beta}^{*(b)}(t),"
            r"\widehat{\boldsymbol\Psi}^{*(b)},"
            r"\widehat\sigma^{2*(b)}\right\}",
            r"R_p(t_m)=\frac{W_{p,\mathrm{full}}(t_m)}"
            r"{W_{p,\mathrm{fixed}}(t_m)}",
        ),
        site_anchor="functional-mixed-effects-full-refit-bootstrap",
        scope=(
            "Whole-participant case bootstrap with a complete MixedLM parameter "
            "refit in every replicate. Duplicate source-participant draws receive "
            "distinct bootstrap group identities. Fixed effects, the complete "
            "random-effect covariance, and residual variance are re-estimated; "
            "basis sizes, spline degree, preprocessing, predictor specification, "
            "random-slope structure, REML/ML choice, and optimizer remain fixed. "
            "Failed replicates raise and are not silently redrawn."
        ),
    ),
    MathematicalContract(
        key="functional-mixed-effects-simultaneous",
        title="Participant-cluster simultaneous mixed-effects coefficient bands",
        public_api=(
            "bootstrap_functional_mixed_effects_coefficients",
            "functional_mixed_effects_simultaneous_bands",
        ),
        equations=(
            r"\mathbf V_i=\mathbf Z_i\widehat{\boldsymbol\Psi}\mathbf Z_i^\top+"
            r"\widehat\sigma^2\mathbf I",
            r"\widehat{\boldsymbol\theta}^{*(b)}="
            r"\left[\sum_{r=1}^{n}\mathbf A_{I_r^{(b)}}\right]^{-1}"
            r"\sum_{r=1}^{n}\mathbf s_{I_r^{(b)}},\quad "
            r"\mathbf A_i=\mathbf X_i^\top\mathbf V_i^{-1}\mathbf X_i,\ "
            r"\mathbf s_i=\mathbf X_i^\top\mathbf V_i^{-1}\mathbf y_i",
            r"M_p^{*(b)}=\max_m\left|"
            r"\frac{\widehat\beta_p^{*(b)}(t_m)-"
            r"\overline{\widehat\beta_p^*}(t_m)}"
            r"{\widehat{\mathrm{SE}}_p^*(t_m)}\right|",
            r"\widehat\beta_p(t_m)\pm c_{p,1-\alpha}"
            r"\widehat{\mathrm{SE}}_p^*(t_m)",
        ),
        site_anchor="functional-mixed-effects-simultaneous",
        scope=(
            "Whole-participant case bootstrap for fixed coefficient functions. "
            "Each resample re-estimates the fixed B-spline coefficients by GLS "
            "while conditioning on the reference random-effect covariance, "
            "residual variance, and declared bases. Bands are simultaneous over "
            "the observed time grid with coefficient or full fixed-effect-family "
            "scope; variance-component, basis-selection, and between-grid "
            "uncertainty are not included."
        ),
    ),
    MathematicalContract(
        key="function-on-scalar",
        title="Function-on-scalar regression and simultaneous coefficient bands",
        public_api=(
            "fit_function_on_scalar_regression",
            "bootstrap_function_on_scalar_coefficients",
            "function_on_scalar_simultaneous_bands",
        ),
        equations=(
            r"\mathbf Y(t)=\mathbf X\boldsymbol\beta(t)+\boldsymbol\varepsilon(t)",
            r"\widehat{\boldsymbol\beta}(t)="
            r"(\mathbf X^\top\mathbf X)^{-1}\mathbf X^\top\mathbf Y(t)",
            r"Y_i^{*(b)}(t)=\widehat Y_i(t)+W_i^{(b)}\widehat\varepsilon_i(t)",
            r"M_j^{*(b)}=\max_{m,d}\left|"
            r"\frac{\widehat\beta_{j,d}^{*(b)}(t_m)-"
            r"\widehat\beta_{j,d}(t_m)}"
            r"{\widehat{\mathrm{SE}}\{\widehat\beta_{j,d}(t_m)\}}"
            r"\right|",
            r"\widehat\beta_{j,d}(t_m)\pm "
            r"c_{j,1-\alpha}\widehat{\mathrm{SE}}"
            r"\{\widehat\beta_{j,d}(t_m)\}",
        ),
        site_anchor="function-on-scalar",
        scope=(
            "Observed-grid OLS for functional responses with explicit scalar "
            "design, HC1 pointwise sandwich standard errors, and fixed-design "
            "wild-bootstrap maxima. Repeated trials are supported only through "
            "equal-weight participant aggregation when all predictors are "
            "constant within participant; this is not a functional mixed model."
        ),
    ),
    MathematicalContract(
        key="fpcr",
        title="Scalar-on-function regression through FPC scores",
        public_api=("fit_scalar_on_function_regression",),
        equations=(
            r"Y_i=\beta_0+\sum_{k=1}^{K}\beta_k\xi_{ik}"
            r"+\mathbf z_i^\top\boldsymbol\gamma+\varepsilon_i",
            r"\operatorname{logit}\{\Pr(Y_i=1)\}="
            r"\beta_0+\sum_{k=1}^{K}\beta_k\xi_{ik}"
            r"+\mathbf z_i^\top\boldsymbol\gamma",
        ),
        site_anchor="fpcr",
        scope="Score-space approximation; Gaussian and binomial fits have distinct inferential assumptions and no automatic component-selection uncertainty.",
    ),
    MathematicalContract(
        key="wild-bootstrap",
        title="Heteroscedastic Gaussian FPCR wild bootstrap",
        public_api=("wild_bootstrap_fpca_projection",),
        equations=(
            r"Y_i^*=\widehat Y_{i,k}+\widehat\varepsilon_{i,k}W_i",
            r"\widehat{\mathrm{SE}}_0="
            r"\left[\frac{1}{n}\mathbf d_0^\top"
            r"\widehat{\boldsymbol\Lambda}_h\mathbf d_0\right]^{1/2}",
            r"T_0^*="
            r"\frac{\widehat\theta_{0,h}^*-\widehat\theta_{0,g}}"
            r"{\widehat{\mathrm{SE}}_0^*},\quad g=k,\ h\ge g",
        ),
        site_anchor="wild-bootstrap",
        scope="Fixed-regressor Gaussian FPCR with independent curve rows; not clustered wild bootstrap or future-outcome prediction.",
    ),
    MathematicalContract(
        key="simultaneous-wild-bootstrap",
        title="Simultaneous fixed-target wild-bootstrap calibration",
        public_api=("fpca_wild_bootstrap_projection_simultaneous_interval",),
        equations=(
            r"M^{*(b)}=\max_{1\le j\le J}|T_j^{*(b)}|",
        ),
        site_anchor="simultaneous-wild-bootstrap",
        scope="One predeclared fixed-target family using the stored joint root matrix; no adaptive target-family guarantee.",
    ),
    MathematicalContract(
        key="family-tests",
        title="Fixed-family wild-bootstrap hypothesis tests",
        public_api=("fpca_wild_bootstrap_projection_family_test",),
        equations=(
            r"T_j=\frac{\widehat\theta_j-\theta_{0j}}{\widehat{\mathrm{SE}}_j}",
            r"p_j=\frac{1+\sum_{b=1}^{B}"
            r"\mathbb I(|T_j^{*(b)}|\ge |T_j|)}{B+1}",
            r"p_j^{\max}=\frac{1+\sum_{b=1}^{B}"
            r"\mathbb I(M^{*(b)}\ge |T_j|)}{B+1}",
        ),
        site_anchor="family-tests",
        scope="Two-sided post-processing tests for a declared fixed family; strong FWER for arbitrary subsets is not claimed without additional theory.",
    ),
    MathematicalContract(
        key="monte-carlo",
        title="Finite-bootstrap Monte Carlo precision",
        public_api=("fpca_wild_bootstrap_family_test_monte_carlo_diagnostics",),
        equations=(
            r"\widehat q=\frac{r}{B}",
            r"\widehat{\mathrm{MCSE}}="
            r"\sqrt{\frac{\widehat q(1-\widehat q)}{B}}",
        ),
        site_anchor="monte-carlo",
        scope="Simulation precision of retained bootstrap tail probabilities; not scientific-effect uncertainty and not sequential-stopping inference.",
    ),
    MathematicalContract(
        key="conformal",
        title="Split-conformal FPCA anomaly p-value",
        public_api=("split_conformal_fpca_anomaly",),
        equations=(
            r"p_{\mathrm{conf}}="
            r"\frac{1+\sum_{i=1}^{m}\mathbb I(A_i\ge A_{\mathrm{new}})}{m+1}",
        ),
        site_anchor="conformal",
        scope="Marginal curve-level split-conformal interpretation under exchangeability; review flags are never automatic exclusions.",
    ),
    MathematicalContract(
        key="delay-embedding",
        title="Delay-coordinate reconstruction and embedding diagnostics",
        public_api=(
            "delay_embed_trajectory",
            "embedding_delay_diagnostics",
            "embedding_dimension_diagnostics",
        ),
        equations=(
            r"\mathbf z_t=[\mathbf G(t),\mathbf G(t-\tau),\ldots,"
            r"\mathbf G(t-(m-1)\tau)]",
            r"I(\tau)=\sum_{a,b}p_{ab}(\tau)"
            r"\log\frac{p_{ab}(\tau)}{p_a p_b}",
            r"\mathrm{FNN}_m=\frac{1}{N_m}\sum_i "
            r"\mathbb I\{\text{neighbor }i\text{ fails the declared }"
            r"R_{\mathrm{tol}}\text{ or }A_{\mathrm{tol}}\text{ criterion}\}",
        ),
        site_anchor="delay-embedding",
        scope="Common-grid reconstruction only; delay and embedding dimension remain analyst-declared after diagnostics, with no silent smoothing, interpolation, or scaling.",
    ),
    MathematicalContract(
        key="recurrence",
        title="Sparse recurrence and recurrence quantification",
        public_api=(
            "recurrence_matrix",
            "recurrence_radius_profile",
            "rqa_metrics",
            "rqa_parameter_sensitivity",
            "windowed_rqa",
            "cross_recurrence_matrix",
            "cross_rqa_metrics",
        ),
        equations=(
            r"R_{ij}=\mathbb I\{\|\mathbf z_i-\mathbf z_j\|_p\le\varepsilon\}",
            r"\mathrm{RR}=\frac{\sum_{i<j}R_{ij}}{N_{\mathrm{eligible}}}",
            r"\mathrm{DET}=\frac{\sum_{\ell\ge\ell_{\min}}\ell P_d(\ell)}"
            r"{\sum_{\ell\ge1}\ell P_d(\ell)}",
            r"\mathrm{LAM}=\frac{\sum_{v\ge v_{\min}}v P_v(v)}"
            r"{\sum_{v\ge1}v P_v(v)}",
        ),
        site_anchor="recurrence",
        scope="Sparse observed-state or reconstructed-state recurrence with an explicit radius policy, metric, Theiler exclusion, and line-length thresholds.",
    ),
    MathematicalContract(
        key="joint-recurrence",
        title="Synchronized joint recurrence and JRQA",
        public_api=(
            "joint_recurrence_matrix",
            "joint_rqa_metrics",
        ),
        equations=(
            r"JR_{ij}=\prod_{s=1}^{S}R_{ij}^{(s)}",
            r"\mathrm{JRR}="
            r"\frac{\sum_{i<j}JR_{ij}}{N_{\mathrm{eligible}}}",
            r"\mathrm{JDET}="
            r"\frac{\sum_{\ell\ge\ell_{\min}}\ell P_{d,J}(\ell)}"
            r"{\sum_{\ell\ge1}\ell P_{d,J}(\ell)}",
            r"\mathrm{JLAM}="
            r"\frac{\sum_{v\ge v_{\min}}v P_{v,J}(v)}"
            r"{\sum_{v\ge1}v P_{v,J}(v)}",
        ),
        site_anchor="joint-recurrence",
        scope=(
            "Logical intersection of at least two synchronized auto-recurrence "
            "matrices on an exact common grid with one shared Theiler "
            "exclusion. Component state spaces, metrics, and thresholds may "
            "differ and remain explicit. No lag alignment, resampling, "
            "threshold harmonization, cross-recurrence interpretation, or "
            "causal-coupling claim is introduced."
        ),
    ),
    MathematicalContract(
        key="recurrence-network",
        title="Sparse recurrence-network topology",
        public_api=(
            "recurrence_network",
            "recurrence_network_node_frame",
            "recurrence_network_summary_frame",
        ),
        equations=(
            r"A_{ij}=R_{ij},\quad i\ne j,\qquad A_{ii}=0",
            r"k_i=\sum_j A_{ij}",
            r"C_i=\frac{2T_i}{k_i(k_i-1)}",
            r"\mathcal T=\frac{3N_{\triangle}}{N_{\mathrm{triples}}}",
            r"\rho_G=\frac{2E}{N(N-1)}",
        ),
        site_anchor="recurrence-network",
        scope=(
            "Undirected unweighted network induced by one declared symmetric "
            "auto-recurrence matrix. Network topology inherits the recurrence "
            "state representation, metric, threshold policy, Theiler "
            "exclusion, and sampling design. No threshold tuning, community "
            "optimization, edge weighting, or automatic dynamical-dimension "
            "interpretation is introduced."
        ),
    ),
    MathematicalContract(
        key="discrete-transfer-entropy",
        title="Discrete transfer entropy and circular-shift surrogate testing",
        public_api=(
            "discrete_transfer_entropy",
            "transfer_entropy_circular_shift_test",
        ),
        equations=(
            r"T_{X\to Y}(k,l,d)=I\!\left(X_{t-d}^{(l)};Y_t\mid Y_{t-1}^{(k)}\right)",
            r"T_{X\to Y}=\sum p(y_t,\mathbf y,\mathbf x)"
            r"\log_2\frac{p(y_t\mid\mathbf y,\mathbf x)}{p(y_t\mid\mathbf y)}",
            r"p_+=\frac{1+\sum_{b=1}^{B}I(T_b^*\ge T_{obs})}{B+1}",
        ),
        site_anchor="discrete-transfer-entropy",
        scope=(
            "Empirical plug-in conditional mutual information for analyst-supplied "
            "integer-coded states with explicit target/source histories and source "
            "lag. Circular-shift inference uses only analyst-declared shifts. No "
            "automatic discretization, lag/history selection, shift generation, or "
            "causal interpretation is introduced."
        ),
    ),
    MathematicalContract(
        key="conditional-transfer-entropy",
        title="Conditional transfer entropy and source-shift surrogate testing",
        public_api=(
            "conditional_transfer_entropy",
            "conditional_transfer_entropy_circular_shift_test",
        ),
        equations=(
            r"T_{X\to Y\mid Z}(k,l,m,d,c)="
            r"I\!\left(X_{t-d}^{(l)};Y_t\mid "
            r"Y_{t-1}^{(k)},Z_{t-c}^{(m)}\right)",
            r"T_{X\to Y\mid Z}=\sum "
            r"p(y_t,\mathbf y,\mathbf x,\mathbf z)"
            r"\log_2\frac{p(y_t\mid\mathbf y,\mathbf x,\mathbf z)}"
            r"{p(y_t\mid\mathbf y,\mathbf z)}",
            r"p_+=\frac{1+\sum_{b=1}^{B}"
            r"I(T_{b}^{*,cond}\ge T_{obs}^{cond})}{B+1}",
        ),
        site_anchor="conditional-transfer-entropy",
        scope=(
            "Empirical plug-in conditional mutual information for analyst-supplied "
            "integer-coded source, target, and conditioning states with explicit "
            "target/source/conditioning histories and source/conditioning lags. "
            "Surrogate inference shifts only the source and holds target and "
            "conditioning processes fixed. Conditioning addresses only the explicitly "
            "supplied process and does not establish causal influence or guarantee "
            "adjustment for unmeasured common drivers."
        ),
    ),
    MathematicalContract(
        key="transfer-entropy-sensitivity",
        title="Transfer-entropy specification sensitivity",
        public_api=("transfer_entropy_parameter_sensitivity",),
        equations=(
            r"\Theta=\mathcal K\times\mathcal L\times\mathcal D",
            r"T_{\theta}=I\!\left(X_{t-d}^{(l)};Y_t\mid Y_{t-1}^{(k)}\right),"
            r"\quad \theta=(k,l,d)\in\Theta",
            r"\Delta T_{\theta}=T_{\theta,obs}-"
            r"B^{-1}\sum_{b=1}^{B}T_{\theta,b}^{*}",
        ),
        site_anchor="transfer-entropy-sensitivity",
        scope=(
            "Descriptive robustness analysis over the full analyst-declared "
            "Cartesian grid of target histories, source histories, and source "
            "lags. Optional surrogate-centered TE uses the identical declared "
            "circular-shift set for every specification. No failed row is "
            "discarded and no specification is ranked or selected automatically."
        ),
    ),
    MathematicalContract(
        key="rqa-population-bootstrap",
        title="Population mean bootstrap for curve-level RQA metrics",
        public_api=("bootstrap_rqa_metric_means",),
        equations=(
            r"M_{iq}=Q_q\{R_i(\theta)\}",
            r"U_{pq}=m_p^{-1}\sum_{j=1}^{m_p}M_{pjq}",
            r"\overline U_q^{*(b)}="
            r"n^{-1}\sum_{r=1}^{n}U_{I_r^{(b)}q}",
            r"CI_{1-\alpha}="
            r"[Q_{\alpha/2}(\overline U_q^*),"
            r"Q_{1-\alpha/2}(\overline U_q^*)]",
        ),
        site_anchor="rqa-population-bootstrap",
        scope=(
            "Percentile bootstrap for the between-unit population mean of "
            "fixed-specification curve-level RQA summaries; participant mode "
            "first averages curve metrics within participant. It does not "
            "estimate within-single-trajectory or parameter-selection uncertainty."
        ),
    ),
    MathematicalContract(
        key="functional-rqa-trajectories",
        title="Windowed RQA as functional trajectories",
        public_api=("windowed_rqa_trajectory_set", "windowed_rqa_sensitivity"),
        equations=(
            r"F_{iq}(c_w)=M_q\{R_i^{(w)}\},\quad "
            r"c_w=\frac{t_{w,\mathrm{start}}+t_{w,\mathrm{end}}}{2}",
            r"\omega=\frac{\max(0,W-S)}{W}",
        ),
        site_anchor="functional-rqa-trajectories",
        scope="Derived functional summaries of declared sliding-window RQA; overlapping windows reuse source samples and are not independent observational units.",
    ),
    MathematicalContract(
        key="local-divergence",
        title="Rosenstein local divergence and largest Lyapunov estimate",
        public_api=(
            "local_divergence_curve",
            "estimate_largest_lyapunov_rosenstein",
            "lyapunov_parameter_sensitivity",
        ),
        equations=(
            r"d_i(k)=\|\mathbf z_{i+k}-\mathbf z_{j(i)+k}\|_2",
            r"D(k)=\frac{1}{N_k}\sum_i\log d_i(k)",
            r"D(k)\approx a+\lambda_{\max}k\Delta t",
        ),
        site_anchor="local-divergence",
        scope="Nearest-neighbor local-divergence estimate with explicit Theiler window and analyst-declared linear fit interval; a positive estimate is not standalone evidence of deterministic chaos.",
    ),
    MathematicalContract(
        key="kantz-local-divergence",
        title="Kantz neighborhood divergence and largest Lyapunov estimate",
        public_api=(
            "kantz_divergence_curve",
            "estimate_largest_lyapunov_kantz",
            "kantz_parameter_sensitivity",
        ),
        equations=(
            r"\mathcal N_i(\varepsilon)=\{j:"
            r"\|\mathbf z_i-\mathbf z_j\|_2\le\varepsilon,"
            r"\ |i-j|>w\}",
            r"S(\varepsilon,k)=\frac{1}{N_k}\sum_i"
            r"\log\left[\frac{1}{|\mathcal N_i(k)|}"
            r"\sum_{j\in\mathcal N_i(k)}"
            r"\|\mathbf z_{i+k}-\mathbf z_{j+k}\|_2\right]",
            r"S(\varepsilon,k)\approx a+\lambda_{\max}k\Delta t",
        ),
        site_anchor="kantz-local-divergence",
        scope=(
            "Fixed-radius Kantz neighborhood divergence with explicit minimum "
            "neighbor count, Theiler exclusion, and analyst-declared fit "
            "interval; no automatic radius expansion or chaos classification."
        ),
    ),
    MathematicalContract(
        key="multivariate-iaaft",
        title="Cross-spectrum-aware multivariate IAAFT surrogates",
        public_api=(
            "generate_multivariate_iaaft_surrogates",
            "multivariate_surrogate_nonlinearity_test",
        ),
        equations=(
            r"F_k(\omega)=A_k(\omega)e^{i\phi_k(\omega)}",
            r"\Delta\phi_{kr}(\omega)=\phi_k(\omega)-\phi_r(\omega)",
            r"F_k^*(\omega)=A_k(\omega)"
            r"e^{i[\psi_r^*(\omega)+\Delta\phi_{kr}(\omega)]}",
            r"C_{k\ell}(\omega)=F_k(\omega)F_\ell(\omega)^*",
            r"p=\frac{1+\sum_{b=1}^{B}\mathbb I"
            r"(T_b^*\ge T_{\mathrm{obs}})}{B+1}",
        ),
        site_anchor="multivariate-iaaft",
        scope=(
            "Reference-anchored multivariate IAAFT with exact empirical "
            "marginal rank distributions and iterative targeting of each "
            "channel power spectrum plus original inter-channel Fourier "
            "phase differences. Final power/cross-spectrum preservation is "
            "approximate after rank remapping and retained diagnostically; "
            "the reference dimension is analyst-declared."
        ),
    ),
    MathematicalContract(
        key="surrogate-nonlinearity",
        title="IAAFT surrogate nonlinearity test",
        public_api=("surrogate_nonlinearity_test",),
        equations=(
            r"p=\frac{1+\sum_{b=1}^{B}\mathbb I(T_b^*\ge T_{\mathrm{obs}})}{B+1}",
        ),
        site_anchor="surrogate-nonlinearity",
        scope="Monte Carlo test against the declared IAAFT linear-stochastic surrogate null using identical statistic settings for observed and surrogate series.",
    ),
    MathematicalContract(
        key="return-map-stability",
        title="Empirical Poincare return-map stability",
        public_api=(
            "poincare_crossings",
            "fit_local_return_map",
            "return_map_stability",
        ),
        equations=(
            r"h(\mathbf z)=0,\qquad \mathbf z_n=\text{successive section crossings}",
            r"\mathbf z_{n+1}=\mathbf a+\mathbf J(\mathbf z_n-\mathbf z_0)"
            r"+\boldsymbol\varepsilon_n",
            r"\rho(\mathbf J)=\max_j|\lambda_j(\mathbf J)|",
        ),
        site_anchor="return-map-stability",
        scope="Experimental local affine cycle-to-cycle diagnostic; the empirical Jacobian is not a variational-equation monodromy matrix and its eigenvalues are not classical Floquet multipliers.",
    ),
)


def list_mathematical_contracts() -> tuple[MathematicalContract, ...]:
    """Return all mathematical contracts in stable documentation order."""

    return _CONTRACTS


def get_mathematical_contract(name: str) -> MathematicalContract:
    """Return a mathematical contract by key or registered public function."""

    if not isinstance(name, str):
        raise TypeError("name must be a string")
    for contract in _CONTRACTS:
        if name == contract.key or name in contract.public_api:
            return contract
    raise KeyError(f"No mathematical contract is registered for {name!r}")


def mathematical_contract_frame() -> pd.DataFrame:
    """Return one tidy row per registered public function and its LaTeX contract."""

    rows = []
    for contract in _CONTRACTS:
        latex = "\n\n".join(contract.equations)
        for function in contract.public_api:
            rows.append(
                {
                    "contract_key": contract.key,
                    "title": contract.title,
                    "function": function,
                    "latex": latex,
                    "site_anchor": contract.site_anchor,
                    "scope": contract.scope,
                }
            )
    return pd.DataFrame(rows)
