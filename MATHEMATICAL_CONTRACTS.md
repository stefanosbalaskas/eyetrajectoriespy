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

Implemented by \`fit_fpca()\`, \`fit_mfpca()\`, \`transform_fpca()\`, and \`reconstruct_fpca()\`.

## Functional distance

$$
d_{L^2}(\mathbf a,\mathbf b)
=
\left[
\sum_m w_m\sum_d\omega_d\{a_d(t_m)-b_d(t_m)\}^2
\right]^{1/2}.
$$

Implemented by \`functional_l2_distance()\`.

## Continuous planar trajectory geometry

For a declared planar path (mathbf G(t)=[x(t),y(t)]^\top),

$
\theta(t)
=
\operatorname{atan2}\{y'(t),x'(t)\},
$

$
\kappa(t)
=
\frac{x'(t)y''(t)-y'(t)x''(t)}
{\{x'(t)^2+y'(t)^2\}^{3/2}},
$

and

$
\omega(t)
=
\frac{x'(t)y''(t)-y'(t)x''(t)}
{x'(t)^2+y'(t)^2}
=
\kappa(t)\|\mathbf G'(t)\|.
$

Observed-path tortuosity is

$
T
=
\frac{
\sum_{m=1}^{M-1}
\|\mathbf G(t_{m+1})-\mathbf G(t_m)\|_2
}{
\|\mathbf G(t_M)-\mathbf G(t_1)\|_2
}.
$

Implemented by `heading_function()`, `signed_curvature_function()`, `turning_rate_function()`, and `trajectory_tortuosity()`.

No smoothing, interpolation, axis inversion, coordinate rescaling, or denominator epsilon is introduced automatically. Low-speed and zero-displacement undefinedness remains explicit.

## Multilevel decomposition

$$
\mathbf G_{ij}(t)
=
\boldsymbol\mu(t)+\mathbf U_i(t)+\mathbf V_{ij}(t).
$$

Implemented by \`fit_multilevel_fpca()\`.

## Compositional AOI transform

For reference AOI \(r\),

$$
z_k(t)=\log\frac{p_k^\epsilon(t)}{p_r^\epsilon(t)},\qquad k\ne r,
$$

followed by the inverse normalization

$$
p_k(t)=\frac{q_k(t)}{\sum_{\ell=1}^{K}q_\ell(t)}.
$$

Implemented by \`alr_transform()\`, \`inverse_alr()\`, and \`fit_compositional_fpca()\`.

## Landmark registration

$$
\mathbf G_i^{\mathrm{reg}}(t)=\mathbf G_i\{h_i(t)\},
\qquad
\Delta_i(t)=h_i(t)-t.
$$

Implemented by \`register_to_landmarks()\`.

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

Implemented by \`multiplier_functional_mean_band()\`.

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

Implemented by \`wild_bootstrap_fpca_projection()\`.

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

Implemented by \`fpca_wild_bootstrap_projection_family_test()\`.

## Finite-bootstrap precision

$$
\widehat q=\frac{r}{B},
\qquad
\widehat{\mathrm{MCSE}}
=
\sqrt{\frac{\widehat q(1-\widehat q)}{B}}.
$$

Exact Clopper-Pearson limits are used for the retained exceedance count \(r\). They quantify Monte Carlo simulation precision only and do not alter the scientific test.

Implemented by \`fpca_wild_bootstrap_family_test_monte_carlo_diagnostics()\`.

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

Implemented by \`split_conformal_fpca_anomaly()\`.

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

Implemented by \`delay_embed_trajectory()\`, \`embedding_delay_diagnostics()\`, and \`embedding_dimension_diagnostics()\`.

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

Implemented by \`recurrence_matrix()\`, \`recurrence_radius_profile()\`, \`rqa_metrics()\`, \`rqa_parameter_sensitivity()\`, \`windowed_rqa()\`, \`cross_recurrence_matrix()\`, and \`cross_rqa_metrics()\`.

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

Implemented by \`local_divergence_curve()\`, \`estimate_largest_lyapunov_rosenstein()\`, and \`lyapunov_parameter_sensitivity()\`.

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

Implemented by \`surrogate_nonlinearity_test()\`. The IAAFT procedure preserves the observed amplitude distribution exactly and iteratively matches the Fourier-amplitude spectrum.

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

Implemented by \`poincare_crossings()\`, \`fit_local_return_map()\`, and \`return_map_stability()\`.

These are empirical return-map diagnostics. \(\mathbf J\) is **not** a variational-equation monodromy matrix and its eigenvalues are **not** classical Floquet multipliers.
