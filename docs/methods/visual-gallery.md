---
title: Visual gallery
---

# Visual gallery

These figures are regenerated from deterministic synthetic data during the documentation workflow. The gallery is therefore part of the tested documentation build rather than a collection of manually exported screenshots.

<div class="grid cards et-gallery" markdown>

-   **Continuous planar trajectories**

    ![Synthetic planar gaze trajectories](../assets/gallery/planar-trajectories.svg)

    Whole-path inspection before dimensional reduction.

    **API:** \`simulate_planar_trajectories()\`, \`plot_planar_trajectories()\`

    [Worked example](../examples/evidence-inspection.md) · [Mathematics](mathematical-reference.md#fpca)

-   **FPC interpretation curve**

    ![First functional principal component](../assets/gallery/fpca-component.svg)

    Mean and score-SD perturbations for one functional dimension.

    **API:** \`fit_mfpca()\`, \`plot_fpca_component()\`

    [FPCA guide](../guides/fpca.md) · [Mathematics](mathematical-reference.md#fpca)

-   **Cumulative FPCA variance**

    ![Cumulative functional principal component variance](../assets/gallery/fpca-variance.svg)

    Retained functional variance across the fitted component sequence.

    **API:** `plot_fpca_variance()`

    [FPCA guide](../guides/fpca.md) · [Function → equation index](../reference/function-equation-index.md)

-   **Registration displacement**

    ![Landmark registration warping displacement](../assets/gallery/registration-warping.svg)

    The retained phase displacement (h_i(t)-t), rather than a hidden registration side effect.

    **API:** `register_to_landmarks()`, `plot_warping_functions()`

    [Registration guide](../guides/registration.md) · [Mathematics](mathematical-reference.md#registration)

-   **Simultaneous functional mean band**

    ![Functional mean simultaneous band](../assets/gallery/functional-mean-band.svg)

    Observed-grid Gaussian multiplier calibration.

    **API:** \`multiplier_functional_mean_band()\`, \`plot_functional_mean_band()\`

    [Worked example](../examples/functional-mean-bands.md) · [Mathematics](mathematical-reference.md#mean-band)

-   **Heteroscedastic FPCR target intervals**

    ![Wild bootstrap fixed target intervals](../assets/gallery/wild-bootstrap-projections.svg)

    Studentized fixed-regressor wild-bootstrap intervals for centered target projections.

    **API:** \`wild_bootstrap_fpca_projection()\`, \`plot_fpca_wild_bootstrap_projection()\`

    [Worked example](../examples/fpcr-wild-bootstrap.md) · [Mathematics](mathematical-reference.md#wild-bootstrap)

-   **Fixed-family wild-bootstrap tests**

    ![Target-wise and maxT adjusted wild-bootstrap p-values](../assets/gallery/wild-bootstrap-family-test.svg)

    Target-wise and single-step max-(|t|) probabilities for one declared family.

    **API:** `fpca_wild_bootstrap_projection_family_test()`, `plot_fpca_wild_bootstrap_family_test()`

    [Worked example](../examples/fpcr-wild-bootstrap-family-tests.md) · [Mathematics](mathematical-reference.md#family-tests)

-   **Finite-bootstrap precision**

    ![Monte Carlo precision diagnostics](../assets/gallery/monte-carlo-precision.svg)

    Exact binomial intervals around retained bootstrap exceedance probabilities.

    **API:** \`fpca_wild_bootstrap_family_test_monte_carlo_diagnostics()\`, \`plot_fpca_wild_bootstrap_monte_carlo_diagnostics()\`

    [Worked example](../examples/fpcr-wild-bootstrap-monte-carlo.md) · [Mathematics](mathematical-reference.md#monte-carlo)


-   **Sparse recurrence structure**

    ![Sparse recurrence plot](../assets/gallery/recurrence-plot.svg)

    Recurrent reconstructed states under an explicit target recurrence rate and Theiler exclusion.

    **API:** \`delay_embed_trajectory()\`, \`recurrence_matrix()\`, \`plot_recurrence()\`

    [Worked example](../examples/nonlinear-dynamics.md) · [Mathematics](mathematical-reference.md#recurrence)

-   **Time-varying RQA**

    ![Windowed recurrence quantification](../assets/gallery/windowed-rqa.svg)

    Full-window recurrence rate, determinism, and laminarity retained over trial time.

    **API:** \`windowed_rqa()\`, \`plot_windowed_rqa()\`

    [Nonlinear guide](../guides/nonlinear-dynamics.md) · [Mathematics](mathematical-reference.md#recurrence)

-   **Local divergence / Rosenstein LLE**

    ![Local divergence with declared Lyapunov fit interval](../assets/gallery/local-divergence.svg)

    Mean nearest-neighbor log divergence and the explicitly declared linear fit interval.

    **API:** \`local_divergence_curve()\`, \`estimate_largest_lyapunov_rosenstein()\`, \`plot_local_divergence()\`

    [Worked example](../examples/nonlinear-dynamics.md) · [Mathematics](mathematical-reference.md#local-divergence)

-   **Experimental empirical return map**

    ![Empirical Poincare return map](../assets/gallery/return-map.svg)

    Successive section crossings and a local affine return map for a deterministic synthetic contracting cycle.

    **API:** \`poincare_crossings()\`, \`fit_local_return_map()\`, \`return_map_stability()\`, \`plot_poincare_return_map()\`

    [Worked example](../examples/return-map-stability.md) · [Mathematics](mathematical-reference.md#return-map-stability)

</div>

## Reproduce the gallery

Run:

\`\`\`bash
python scripts/generate_docs_gallery.py
\`\`\`

The generator uses the package itself, fixed random seeds, the non-interactive Matplotlib backend, deterministic SVG hashing, and timestamp-free SVG metadata.

## Plot → method → equation

=== "FPCA"

    \`plot_fpca_component()\` visualizes

    $$
    \widehat{\boldsymbol\mu}(t)
    +a\sqrt{\widehat\lambda_k}\widehat{\boldsymbol\phi}_k(t).
    $$

=== "Mean band"

    \`plot_functional_mean_band()\` visualizes

    $$
    \overline X_d(t_m)
    \pm
    c_{1-\alpha}\widehat{\mathrm{SE}}_d(t_m).
    $$

=== "Wild bootstrap"

    \`plot_fpca_wild_bootstrap_projection()\` visualizes

    $$
    \widehat\theta_{0,h}
    \pm
    c_{0,1-\alpha}\widehat{\mathrm{SE}}_0.
    $$

=== "Recurrence"

    \`plot_recurrence()\` visualizes sparse entries satisfying

    $
    R_{ij}=\mathbb I\{\|\mathbf z_i-\mathbf z_j\|_p\le\varepsilon\}.
    $

=== "Local divergence"

    \`plot_local_divergence()\` visualizes

    $
    D(k)=\frac{1}{N_k}\sum_i\log d_i(k),
    $

    with the analyst-declared LLE fit interval when an estimate is supplied.

=== "Return map"

    \`plot_poincare_return_map()\` visualizes successive crossings under

    $
    \mathbf z_{n+1}\approx
    \mathbf a+\mathbf J(\mathbf z_n-\mathbf z_0).
    $

=== "Monte Carlo precision"

    \`plot_fpca_wild_bootstrap_monte_carlo_diagnostics()\` visualizes the raw retained tail estimate and exact binomial precision limits, where

    $$
    \widehat q=\frac{r}{B}.
    $$

## Gallery contract

The docs workflow regenerates all twelve assets before the strict MkDocs build and runs \`scripts/validate_docs_contracts.py\`. A missing image, stale generated equation index, broken nav target, undefined mathematical deep link, missing mathematical API contract, stale MathJax hook, or unresolved documented public symbol fails the documentation job.
