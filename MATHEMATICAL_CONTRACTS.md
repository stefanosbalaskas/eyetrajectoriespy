# Mathematical contracts

This repository keeps the main mathematical definitions in LaTeX alongside the implementation. GitHub renders the expressions in this Markdown file with MathJax, while the documentation site contains the expanded version with assumptions and API links.

Website: https://stefanosbalaskas.github.io/eyetrajectoriespy/methods/mathematical-reference/

## Quadrature-weighted FPCA

For grid weights \(w_m\), mean \(\widehat{\boldsymbol\mu}(t_m)\), and optional functional-dimension scale \(s_d\),

$$
Z_{i,m,d}
=
\frac{G_{id}(t_m)-\widehat\mu_d(t_m)}{s_d}\sqrt{w_m}.
$$

The implementation performs PCA on flattened \(Z_i\) and maps Euclidean loading \(v_{k,m,d}\) back to

$$
\widehat\phi_{k,d}(t_m)
=
\frac{v_{k,m,d}}{\sqrt{w_m}}\,s_d.
$$

Reconstruction is

$$
\widehat{\mathbf G}^{(K)}_i(t)
=
\widehat{\boldsymbol\mu}(t)
+
\sum_{k=1}^{K}\widehat\xi_{ik}\widehat{\boldsymbol\phi}_k(t).
$$

Implemented by `fit_fpca()`, `fit_mfpca()`, `transform_fpca()`, and `reconstruct_fpca()`.

## Functional distance

$$
d_{L^2}(\mathbf a,\mathbf b)
=
\left[
\sum_m w_m\sum_d\omega_d\{a_d(t_m)-b_d(t_m)\}^2
\right]^{1/2}.
$$

Implemented by `functional_l2_distance()`.

## Discrete Fréchet trajectory distance

For ordered point sequences \(P\) and \(Q\),

$$
d_w(\mathbf p_i,\mathbf q_j)=\left[\sum_r \omega_r(p_{ir}-q_{jr})^2\right]^{1/2},
$$

$$
D_{i,j}=\max\left\{d_w(\mathbf p_i,\mathbf q_j),\min(D_{i-1,j},D_{i-1,j-1},D_{i,j-1})\right\}.
$$

The discrete Fréchet distance is

$$
\delta_{dF}(P,Q)=D_{m,n}.
$$

Implemented by `discrete_frechet_distance()` and `pairwise_discrete_frechet_distances()`. Couplings preserve sequence order without backtracking; elapsed time is not used and no hidden preprocessing is introduced.

## Dynamic time warping trajectory distance

For ordered point sequences \(P\) and \(Q\), define the optional weighted Euclidean local cost

$$
d_w(\mathbf p_i,\mathbf q_j)
=
\left[
\sum_r \omega_r(p_{ir}-q_{jr})^2
\right]^{1/2}.
$$

The backward-compatible symmetric1 recursion is

$$
C^{(s1)}_{i,j}
=
d_w(\mathbf p_i,\mathbf q_j)
+
\min(C_{i-1,j-1},C_{i-1,j},C_{i,j-1}).
$$

The normalizable symmetric2 recursion weights a diagonal advance by two local-cost units,

$$
C^{(s2)}_{i,j}
=
\min\left\{
C_{i-1,j-1}+2d_w,
C_{i-1,j}+d_w,
C_{i,j-1}+d_w
\right\}.
$$

For global symmetric2 alignment,

$$
d^{(s2)}_{\mathrm{norm}}(P,Q)
=
\frac{C^{(s2)}_{m,n}}{m+n}.
$$

Implemented by dynamic_time_warping_distance() and pairwise_dynamic_time_warping_distances(). The 0.33 symmetric1 raw cumulative-cost behavior remains the default for backward compatibility. symmetric2 can be requested explicitly, and normalize=True is accepted only for symmetric2. The optional Sakoe-Chiba radius is measured in sample indices, not physical elapsed time. No hidden interpolation, resampling, smoothing, coordinate normalization, path simplification, missing-value deletion, step-pattern selection, window selection, or normalization rule is introduced automatically.


## Trajectory-distance specification sensitivity

For distance specification \(s\), let \(D^{(s)}\) be the complete pairwise
distance matrix over the same \(n\) trajectories. Its upper triangle is

$
\mathbf v^{(s)}
=
\{D_{ij}^{(s)}:1\le i<j\le n\}.
$

Global ordering agreement between two specifications \(s\) and \(r\) is
described by the Spearman correlation of the pair-distance ranks,

$
\rho_S(s,r)
=
\operatorname{corr}
\left(
\operatorname{rank}\mathbf v^{(s)},
\operatorname{rank}\mathbf v^{(r)}
\right).
$

For curve \(i\), let \(\mathcal N_k^{(s)}(i)\) denote its \(k\) nearest
neighbors under specification \(s\). Local agreement is described by

$
J_k^{(s,r)}(i)
=
\frac{
|\mathcal N_k^{(s)}(i)\cap\mathcal N_k^{(r)}(i)|
}{
|\mathcal N_k^{(s)}(i)\cup\mathcal N_k^{(r)}(i)|
}.
$

Nearest-neighbor identity agreement is

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

Implemented by `trajectory_distance_sensitivity()`. Raw distance matrices
remain on their native scales. The package does not standardize the matrices,
average them into a consensus distance, compute p-values for dependent
upper-triangle entries, or select a preferred metric.

## Continuous planar trajectory geometry

For a declared planar path \(\mathbf G(t)=[x(t),y(t)]^\top\),

$$
\theta(t)
=
\operatorname{atan2}\{y'(t),x'(t)\},
$$

$$
\kappa(t)
=
\frac{x'(t)y''(t)-y'(t)x''(t)}
{\{x'(t)^2+y'(t)^2\}^{3/2}},
$$

and

$$
\omega(t)
=
\frac{x'(t)y''(t)-y'(t)x''(t)}
{x'(t)^2+y'(t)^2}
=
\kappa(t)\|\mathbf G'(t)\|.
$$

Observed-path tortuosity is

$$
T
=
\frac{
\sum_{m=1}^{M-1}
\|\mathbf G(t_{m+1})-\mathbf G(t_m)\|_2
}{
\|\mathbf G(t_M)-\mathbf G(t_1)\|_2
}.
$$

Implemented by `heading_function()`, `signed_curvature_function()`, `turning_rate_function()`, and `trajectory_tortuosity()`.

No smoothing, interpolation, axis inversion, coordinate rescaling, or denominator epsilon is introduced automatically. Low-speed and zero-displacement undefinedness remains explicit.

## Multilevel decomposition

$$
\mathbf G_{ij}(t)
=
\boldsymbol\mu(t)+\mathbf U_i(t)+\mathbf V_{ij}(t).
$$

Implemented by `fit_multilevel_fpca()`.

## Compositional AOI transform

For reference AOI \(r\),

$$
z_k(t)=\log\frac{p_k^\epsilon(t)}{p_r^\epsilon(t)},\qquad k\ne r,
$$

followed by the inverse normalization

$$
p_k(t)=\frac{q_k(t)}{\sum_{\ell=1}^{K}q_\ell(t)}.
$$

Implemented by `alr_transform()`, `inverse_alr()`, and `fit_compositional_fpca()`.

## Landmark registration

$$
\mathbf G_i^{\mathrm{reg}}(t)=\mathbf G_i\{h_i(t)\},
\qquad
\Delta_i(t)=h_i(t)-t.
$$

Implemented by `register_to_landmarks()`.

## Functional mean multiplier band

$$
M^{(b)}
=
\max_{m,d}
\left|
\frac{
n^{-1/2}\sum_i e_i^{(b)}\{X_{id}(t_m)-\overline X_d(t_m)\}
}{
\widehat\sigma_d(t_m)
}
\right|.
$$

The simultaneous band is

$$
\overline X_d(t_m)
\pm
c_{1-\alpha}\frac{\widehat\sigma_d(t_m)}{\sqrt n}.
$$

Implemented by `multiplier_functional_mean_band()`.

## Functional mixed-effects regression

For repeated functional responses from participant \(i\), trial \(j\), and
observed grid location \(t_m\),

$
Y_{ij}(t)
=
\mathbf x_{ij}^{\top}\boldsymbol\beta(t)
+
\mathbf B_r(t)^{\top}\mathbf u_i
+
\varepsilon_{ij}(t).
$

Each fixed coefficient function is represented as

$
\beta_p(t)
=
\mathbf B_f(t)^{\top}\boldsymbol\theta_p,
$

while participant random-basis coefficients satisfy

$
\mathbf u_i
\sim
N(\mathbf 0,\boldsymbol\Psi),
\qquad
\varepsilon_{ij}(t_m)
\sim
N(0,\sigma^2).
$

For all stacked observations from participant \(i\), the historical
participant-only model has

$
\operatorname{Cov}(\mathbf Y_i\mid\mathbf X_i)
=
\mathbf Z_i\boldsymbol\Psi_p\mathbf Z_i^\top
+
\sigma^2\mathbf I.
$

Version 0.48 optionally adds a nested trial functional random intercept,

$
u_{ij}(t)
=
\mathbf B_u(t)^\top\mathbf v_{ij},
\qquad
\mathbf v_{ij}\sim N(\mathbf 0,\boldsymbol\Psi_{trial}),
$

with one shared unstructured trial-basis covariance. The participant-block
marginal covariance then becomes

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

Implemented by `fit_functional_mixed_effects_regression()`. Participant-only
fits retain the established `statsmodels.MixedLM` backend. The explicit 0.48
participant→trial extension uses a profiled Gaussian marginal likelihood with
separate Cholesky-parameterized participant and trial covariance matrices.
Both routes use explicitly sized B-spline bases and conditionally iid
grid-level residual errors after the declared random effects. Neither is a
collection of independent pointwise mixed models.

## One participant random functional slope

Version 0.45 extends the participant functional random-intercept model with one
explicitly declared random functional slope predictor $X_{ij,q}$:

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

The participant random intercept and random slope use the same declared
$q$-dimensional B-spline basis in 0.45:

$$
b_{0i}(t)
=
\mathbf B_r(t)^{\top}\mathbf u_{0i},
\qquad
b_{1i}(t)
=
\mathbf B_r(t)^{\top}\mathbf u_{1i}.
$$

The stacked random-basis coefficient vector is

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

where the full unstructured covariance has

$$
p_{\Psi}
=
\frac{(2q)(2q+1)}{2}
$$

free covariance parameters. The 0.45 package guard requires the participant
count to exceed $p_{\Psi}$ before fitting the random-slope model. The named
slope predictor must also vary within every participant. These are explicit
package safeguards against an over-parameterized or unidentified random-slope
fit; they are not automatic model-selection rules.

Implemented by `fit_functional_mixed_effects_regression(...,
random_slope_predictor=...)`. Participant BLUP intercept and slope functions
are exported by `functional_random_effect_frame()`.

## Full-refit participant bootstrap for functional mixed-effects models

For bootstrap replicate \(b\), sample participant indices independently with
replacement,

$
I_1^{*(b)},\ldots,I_n^{*(b)}
\overset{\mathrm{iid}}{\sim}
\{1,\ldots,n\}.
$

Every occurrence of a sampled participant is assigned a distinct bootstrap
mixed-model group identity. Thus a source draw such as

$
(3,7,7,12,\ldots)
$

creates two independent bootstrap groups corresponding to source participant 7.

The complete declared mixed model is then refitted:

$
\mathcal D^{*(b)}
\longrightarrow
\left\{
\widehat{\boldsymbol\beta}^{*(b)}(t),
\widehat{\boldsymbol\Psi}^{*(b)},
\widehat{\sigma}^{2*(b)}
\right\}.
$

The model specification itself is held fixed: preprocessing, response
dimension, fixed/random basis sizes, spline degree, predictor set,
random-slope structure, REML/ML choice, optimizer, and iteration limit are not
automatically reselected.

For sensitivity comparison with the fixed-covariance bootstrap, define the
observed-grid band-width ratio

$
R_p(t_m)
=
\frac{
W_{p,\mathrm{full}}(t_m)
}{
W_{p,\mathrm{fixed}}(t_m)
}.
$

The ratio is descriptive. It quantifies how much simultaneous fixed-effect band
width changes when variance components are re-estimated in participant
bootstrap samples; it is not a hypothesis test or automatic model-selection
criterion.

Implemented by `bootstrap_functional_mixed_effects_full_refit()`,
`functional_mixed_effects_variance_bootstrap_frame()`,
`compare_functional_mixed_effects_bootstraps()`, and the existing
`functional_mixed_effects_simultaneous_bands()`.

Failed replicates raise and are not silently replaced. The retained empirical
variance-component distributions are not automatically labelled calibrated
variance-component confidence intervals.

## Participant-cluster simultaneous mixed-effects coefficient bands

For participant \(i\), let the marginal covariance implied by the fitted
functional random intercept and residual model be

$$
\mathbf V_i
=
\mathbf Z_i\widehat{\boldsymbol\Psi}\mathbf Z_i^\top
+
\widehat\sigma^2\mathbf I.
$$

Define the participant-level fixed-effect information and score contributions

$$
\mathbf A_i
=
\mathbf X_i^\top\mathbf V_i^{-1}\mathbf X_i,
\qquad
\mathbf s_i
=
\mathbf X_i^\top\mathbf V_i^{-1}\mathbf y_i.
$$

For bootstrap replicate \(b\), draw \(n\) participant indices
\(I_1^{(b)},\ldots,I_n^{(b)}\) with replacement and re-estimate the fixed
basis coefficients by

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

The coefficient function replicate is reconstructed with the original fixed
basis. With bootstrap pointwise scale
\(\widehat{\mathrm{SE}}_p^*(t_m)\), coefficient-wise calibration uses

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
\right|,
$$

and the observed-grid simultaneous band is

$$
\widehat\beta_p(t_m)
\pm
c_{p,1-\alpha}
\widehat{\mathrm{SE}}_p^*(t_m).
$$

Implemented by `bootstrap_functional_mixed_effects_coefficients()` and
`functional_mixed_effects_simultaneous_bands()`. Whole participant trial
bundles are resampled. The random-effect covariance, residual variance, and
declared bases are held fixed at the reference fit; variance-component,
basis-selection, and between-grid uncertainty are not included.

## Function-on-scalar regression

For functional response vector \(\mathbf Y(t)\) and scalar design matrix \(\mathbf X\),

$
\mathbf Y(t)
=
\mathbf X\boldsymbol\beta(t)
+
\boldsymbol\varepsilon(t),
$

with observed-grid OLS coefficient function

$
\widehat{\boldsymbol\beta}(t)
=
(\mathbf X^\top\mathbf X)^{-1}
\mathbf X^\top\mathbf Y(t).
$

Pointwise standard errors use the HC1 diagonal sandwich estimator. Wild-bootstrap pseudo-functions are

$
Y_i^{*(b)}(t)
=
\widehat Y_i(t)
+
W_i^{(b)}\widehat\varepsilon_i(t).
$

For coefficient \(j\), the observed-grid studentized maximum is

$
M_j^{*(b)}
=
\max_{m,d}
\left|
\frac{
\widehat\beta_{j,d}^{*(b)}(t_m)-\widehat\beta_{j,d}(t_m)
}{
\widehat{\mathrm{SE}}\{\widehat\beta_{j,d}(t_m)\}
}
\right|,
$

yielding the simultaneous band

$
\widehat\beta_{j,d}(t_m)
\pm
c_{j,1-\alpha}
\widehat{\mathrm{SE}}\{\widehat\beta_{j,d}(t_m)\}.
$

Implemented by `fit_function_on_scalar_regression()`, `bootstrap_function_on_scalar_coefficients()`, and `function_on_scalar_simultaneous_bands()`. Repeated trials are supported in 0.35 only through equal-weight participant aggregation when declared predictors are constant within participant. Trial-varying predictors require a repeated-measures functional model and are rejected rather than treated as independent.

## Heteroscedastic FPCR wild bootstrap

Pseudo-responses are

$$
Y_i^*
=
\widehat Y_{i,k}
+
\widehat\varepsilon_{i,k}W_i.
$$

With

$$
\widehat{\boldsymbol\Gamma}_h
=
n^{-1}\boldsymbol\Xi_h^\top\boldsymbol\Xi_h
$$

and centered score-residual covariance \(\widehat{\boldsymbol\Lambda}_h\), the target standard error is

$$
\widehat{\mathrm{SE}}_0
=
\left[
\frac{1}{n}
\mathbf d_0^\top
\widehat{\boldsymbol\Lambda}_h
\mathbf d_0
\right]^{1/2},
\qquad
\mathbf d_0
=
\widehat{\boldsymbol\Gamma}_h^{-1}\boldsymbol\xi_{0,h}.
$$

The studentized root is

$$
T_0^*
=
\frac{\widehat\theta_{0,h}^*-\widehat\theta_{0,g}}
{\widehat{\mathrm{SE}}_0^*},
\qquad g=k,\quad h\ge g.
$$

Implemented by `wild_bootstrap_fpca_projection()`.

## Fixed-family testing

For target \(j\),

$$
T_j=\frac{\widehat\theta_j-\theta_{0j}}{\widehat{\mathrm{SE}}_j},
$$

and the default plus-one p-value is

$$
p_j=\frac{1+\sum_{b=1}^{B}\mathbb I(|T_j^{*(b)}|\ge |T_j|)}{B+1}.
$$

Single-step family adjustment uses

$$
M^{*(b)}=\max_j|T_j^{*(b)}|.
$$

Implemented by `fpca_wild_bootstrap_projection_family_test()`.

## Finite-bootstrap precision

$$
\widehat q=\frac{r}{B},
\qquad
\widehat{\mathrm{MCSE}}
=
\sqrt{\frac{\widehat q(1-\widehat q)}{B}}.
$$

Exact Clopper-Pearson limits are used for the retained exceedance count \(r\). They quantify Monte Carlo simulation precision only and do not alter the scientific test.

Implemented by `fpca_wild_bootstrap_family_test_monte_carlo_diagnostics()`.

## Split conformal anomaly p-value

$$
p_{\mathrm{conf}}
=
\frac{
1+\sum_{i=1}^{m}\mathbb I(A_i\ge A_{\mathrm{new}})
}{
m+1
}.
$$

Implemented by `split_conformal_fpca_anomaly()`.

For the full mathematical reference, including exact quadrature weights, dimension scaling, reconstruction nonconformity, simultaneous calibration, boundary cases, assumptions, and API links, see the website page linked above.

## Delay-coordinate reconstruction

For embedding dimension \(m\) and delay \(\tau\),

$$
\mathbf z_t=
[
\mathbf G(t),
\mathbf G(t-\tau),
\ldots,
\mathbf G(t-(m-1)\tau)
].
$$

Average mutual information is

$$
I(\tau)
=
\sum_{a,b}
p_{ab}(\tau)
\log
\frac{p_{ab}(\tau)}
{p_a p_b}.
$$

False-nearest-neighbor diagnostics evaluate whether nearest neighbors in dimension \(m\) separate excessively when the next delayed coordinate is added.

Implemented by `delay_embed_trajectory()`, `embedding_delay_diagnostics()`, and `embedding_dimension_diagnostics()`.

## Sparse recurrence quantification

For reconstructed or observed state vectors,

$$
R_{ij}
=
\mathbb I
\left[
\|\mathbf z_i-\mathbf z_j\|_p
\le \varepsilon
\right],
$$

subject to the declared Theiler exclusion. Recurrence rate is

$$
\mathrm{RR}
=
\frac{
\sum_{i<j}R_{ij}
}{
N_{\mathrm{eligible}}
}.
$$

Determinism and laminarity use diagonal- and vertical-line length distributions:

$$
\mathrm{DET}
=
\frac{
\sum_{\ell\ge\ell_{\min}}
\ell P_d(\ell)
}{
\sum_{\ell\ge1}
\ell P_d(\ell)
},
\qquad
\mathrm{LAM}
=
\frac{
\sum_{v\ge v_{\min}}
v P_v(v)
}{
\sum_{v\ge1}
v P_v(v)
}.
$$

Implemented by `recurrence_matrix()`, `recurrence_radius_profile()`, `rqa_metrics()`, `rqa_parameter_sensitivity()`, `windowed_rqa()`, `cross_recurrence_matrix()`, and `cross_rqa_metrics()`.

## Synchronized joint recurrence and JRQA

For synchronized subsystem recurrence matrices \(R^{(s)}\), joint recurrence
requires recurrence in **every** declared subsystem at the same pair of time
indices:

$
JR_{ij}
=
\prod_{s=1}^{S}R_{ij}^{(s)}.
$

With one common Theiler exclusion and \(N_{\mathrm{eligible}}\) unique
off-diagonal pairs,

$
\mathrm{JRR}
=
\frac{\sum_{i<j}JR_{ij}}{N_{\mathrm{eligible}}}.
$

Joint determinism and laminarity use the same line-counting conventions as
ordinary auto-RQA, but on the joint recurrence matrix:

$
\mathrm{JDET}
=
\frac{\sum_{\ell\ge\ell_{\min}}\ell P_{d,J}(\ell)}
{\sum_{\ell\ge1}\ell P_{d,J}(\ell)},
$

$
\mathrm{JLAM}
=
\frac{\sum_{v\ge v_{\min}}v P_{v,J}(v)}
{\sum_{v\ge1}v P_{v,J}(v)}.
$

Implemented by `joint_recurrence_matrix()` and `joint_rqa_metrics()`.
Every component remains an independently declared auto-recurrence contract;
different state dimensions, metrics, and radii are allowed. The component
matrices must already share the exact time grid and Theiler exclusion.
Joint recurrence is not cross-recurrence and is not interpreted as causal
coupling.

## Sparse recurrence-network topology

A recurrence network treats each recurrence-state index as one node and each
retained off-diagonal recurrence pair as one undirected edge:

$
A_{ij}=R_{ij},\quad i\ne j,\qquad A_{ii}=0.
$

Node degree is

$
k_i=\sum_j A_{ij}.
$

If \(T_i\) is the number of graph triangles incident to node \(i\), local
clustering is

$
C_i=\frac{2T_i}{k_i(k_i-1)}.
$

The implementation uses \(C_i=0\) when \(k_i<2\). Global transitivity is

$
\mathcal T=\frac{3N_{\triangle}}{N_{\mathrm{triples}}},
$

and remains undefined when the graph contains no connected triples.

Standard graph density uses **all** unordered node pairs,

$
\rho_G=\frac{2E}{N(N-1)},
$

which can differ from the source recurrence rate when a Theiler window removes
eligible temporal neighbors.

Implemented by `recurrence_network()`,
`recurrence_network_node_frame()`, and
`recurrence_network_summary_frame()`. The network inherits the source
recurrence state representation, metric, threshold policy, Theiler exclusion,
and sampling design. No threshold tuning, community detection, edge weighting,
or automatic dimension interpretation is performed.

## Discrete transfer entropy and circular-shift surrogate testing

For discrete source and target states, the implemented transfer entropy is

$
T_{X\to Y}(k,l,d)
=
I\!\left(X_{t-d}^{(l)};Y_t\mid Y_{t-1}^{(k)}\right),
$

estimated by empirical counts and base-2 logarithms. The target history length
\(k\), source history length \(l\), and source lag \(d\) are all explicit
sample-index settings. Continuous observations are not discretized
automatically.

For analyst-declared circular source shifts, the upper-tail Monte Carlo
comparison uses

$
p_+
=
\frac{1+\sum_{b=1}^{B}I(T_b^*\ge T_{obs})}{B+1}.
$

Implemented by `discrete_transfer_entropy()` and
`transfer_entropy_circular_shift_test()`. The estimator retains empirical
history-support diagnostics; the surrogate test retains the complete declared
shift set and attainable p-value resolution. Neither API performs automatic
state construction, lag/history selection, or causal identification.

## Conditional transfer entropy and source-shift surrogate testing

For source \(X\), target \(Y\), and an explicitly supplied conditioning process
\(Z\),

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

With \(\mathbf y=Y_{t-1}^{(k)}\), \(\mathbf x=X_{t-d}^{(l)}\), and
\(\mathbf z=Z_{t-c}^{(m)}\), the empirical plug-in quantity is

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

For \(B\) analyst-declared source-only circular shifts,

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

Implemented by `conditional_transfer_entropy()` and
`conditional_transfer_entropy_circular_shift_test()`. Target and conditioning
processes stay fixed under the surrogate null. Conditioning is limited to the
explicitly supplied process and is not presented as causal identification or
complete adjustment for unmeasured common drivers.

## Transfer-entropy specification sensitivity

For declared target-history grid \(\mathcal K\), source-history grid
\(\mathcal L\), and source-lag grid \(\mathcal D\), the sensitivity
design is

$
\Theta
=
\mathcal K\times\mathcal L\times\mathcal D.
$

Each specification \(\theta=(k,l,d)\) evaluates the same discrete
transfer-entropy estimand,

$
T_{\theta}
=
I\!\left(
X_{t-d}^{(l)};
Y_t
\mid
Y_{t-1}^{(k)}
\right).
$

When one analyst-declared circular-shift set is supplied, the retained
surrogate-centered quantity is

$
\Delta T_{\theta}
=
T_{\theta,obs}
-
B^{-1}
\sum_{b=1}^{B}
T_{\theta,b}^{*}.
$

Implemented by `transfer_entropy_parameter_sensitivity()`. The full Cartesian
grid is retained, invalid specifications fail closed, and no history/lag
combination is ranked or selected automatically.

## Population mean bootstrap for curve-level RQA metrics

For one fixed recurrence/RQA specification $\theta$,

$$
M_{iq}
=
Q_q\{R_i(\theta)\}.
$$

If participant $p$ contributes $m_p$ curves, participant-level inference uses

$$
U_{pq}
=
m_p^{-1}
\sum_{j=1}^{m_p}
M_{pjq}.
$$

A bootstrap population-mean replicate is

$$
\overline U_q^{*(b)}
=
n^{-1}
\sum_{r=1}^{n}
U_{I_r^{(b)}q},
$$

and the implemented percentile interval is

$$
CI_{1-\alpha}
=
\left[
Q_{\alpha/2}(\overline U_q^*),
Q_{1-\alpha/2}(\overline U_q^*)
\right].
$$

Implemented by bootstrap_rqa_metric_means(). The bootstrap targets between-unit population sampling uncertainty conditional on the fixed RQA specification; it does not estimate within-single-trajectory or parameter-selection uncertainty.

## Windowed RQA as functional trajectories

For source curve $i$, window $w$, and selected RQA metric $q$,

$
F_{iq}(c_w)
=
M_q\left\{R_i^{(w)}\right\},
\qquad
c_w
=
\frac{t_{w,\mathrm{start}}+t_{w,\mathrm{end}}}{2}.
$

For a window of $W$ samples advanced by $S$ samples, the deterministic source-sample overlap is

$
\omega
=
\frac{\max(0,W-S)}{W}.
$

The overlap is provenance, not an independence assumption. Under target-recurrence-rate mode, recurrence rate is controlled by construction and is not accepted as a downstream functional outcome.

Implemented by `windowed_rqa_trajectory_set()`.
## Rosenstein local divergence

For each reconstructed state \(i\), let \(j(i)\) be the nearest temporally separated neighbor. Forward divergence is

$$
d_i(k)
=
\|
\mathbf z_{i+k}
-
\mathbf z_{j(i)+k}
\|_2.
$$

The mean log-divergence curve is

$$
D(k)
=
\frac{1}{N_k}
\sum_i
\log d_i(k).
$$

Over an analyst-declared linear region,

$$
D(k)
\approx
a+
\lambda_{\max}k\Delta t.
$$

Implemented by `local_divergence_curve()`, `estimate_largest_lyapunov_rosenstein()`, and `lyapunov_parameter_sensitivity()`.

## Kantz neighborhood divergence

For reconstructed state $i$, declare a fixed-radius neighborhood outside the Theiler window:

$$
\mathcal N_i(\varepsilon)
=
\{j:\|\mathbf z_i-\mathbf z_j\|_2\le\varepsilon,\ |i-j|>w\}.
$$

For horizon $k$, average forward distances inside each surviving neighborhood and then average their logarithms across reference states:

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

Implemented by `kantz_divergence_curve()`, `estimate_largest_lyapunov_kantz()`, and `kantz_parameter_sensitivity()`. Radius, minimum-neighbor count, Theiler exclusion, and fit interval remain explicit; the package does not enlarge neighborhoods or select a preferred sensitivity specification automatically.

## Multivariate IAAFT surrogates

For channel \(k\), write the discrete Fourier transform as

$
F_k(\omega)=A_k(\omega)e^{i\phi_k(\omega)}.
$

Relative to an explicitly declared reference channel \(r\), retain

$
\Delta\phi_{kr}(\omega)=\phi_k(\omega)-\phi_r(\omega).
$

At each Fourier-adjustment step,

$
F_k^*(\omega)
=
A_k(\omega)e^{i[\psi_r^*(\omega)+\Delta\phi_{kr}(\omega)]},
$

targeting the original cross-spectrum

$
C_{k\ell}(\omega)=F_k(\omega)F_\ell(\omega)^*.
$

Each inverse-transformed channel is then rank-remapped to its exact empirical
marginal distribution. Because rank remapping perturbs Fourier coefficients,
final power-spectrum and cross-spectrum preservation is approximate and the
relative mismatch is retained for every surrogate.

For a one-sided greater-than Monte Carlo test,

$
p
=
\frac{1+\sum_{b=1}^{B}\mathbb I(T_b^*\ge T_{\mathrm{obs}})}{B+1}.
$

Implemented by `generate_multivariate_iaaft_surrogates()` and
`multivariate_surrogate_nonlinearity_test()`. The reference dimension is
analyst-declared and never selected automatically.

## IAAFT surrogate testing

For a one-sided greater-than alternative and \(B\) surrogate statistics,

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

Implemented by `surrogate_nonlinearity_test()`. The IAAFT procedure preserves the observed amplitude distribution exactly and iteratively matches the Fourier-amplitude spectrum.

## Empirical Poincare return maps

A declared section defines successive crossing states

$$
h(\mathbf z)=0,
\qquad
\mathbf z_1,\mathbf z_2,\ldots.
$$

Within an explicitly declared local neighborhood, the package fits

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

The empirical contraction/expansion diagnostic is the spectral radius

$$
\rho(\mathbf J)
=
\max_j
|
\lambda_j(\mathbf J)
|.
$$

Implemented by `poincare_crossings()`, `fit_local_return_map()`, and `return_map_stability()`.

These are empirical return-map diagnostics. \(\mathbf J\) is **not** a variational-equation monodromy matrix and its eigenvalues are **not** classical Floquet multipliers.
