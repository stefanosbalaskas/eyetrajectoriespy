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
