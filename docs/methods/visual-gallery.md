---
title: Visual gallery
---

# Visual gallery

These figures are regenerated from deterministic synthetic data during the documentation workflow. The gallery is therefore part of the tested documentation build rather than a collection of manually exported screenshots.

<div class="grid cards et-gallery" markdown>

-   **Continuous planar trajectories**

    ![Synthetic planar gaze trajectories](../assets/gallery/planar-trajectories.svg)

    Whole-path inspection before dimensional reduction.

    **API:** `simulate_planar_trajectories()`, `plot_planar_trajectories()`

    [Worked example](../examples/evidence-inspection.md) · [Mathematics](mathematical-reference.md#fpca)

-   **FPC interpretation curve**

    ![First functional principal component](../assets/gallery/fpca-component.svg)

    Mean and score-SD perturbations for one functional dimension.

    **API:** `fit_mfpca()`, `plot_fpca_component()`

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

    **API:** `multiplier_functional_mean_band()`, `plot_functional_mean_band()`

    [Worked example](../examples/functional-mean-bands.md) · [Mathematics](mathematical-reference.md#mean-band)

-   **Heteroscedastic FPCR target intervals**

    ![Wild bootstrap fixed target intervals](../assets/gallery/wild-bootstrap-projections.svg)

    Studentized fixed-regressor wild-bootstrap intervals for centered target projections.

    **API:** `wild_bootstrap_fpca_projection()`, `plot_fpca_wild_bootstrap_projection()`

    [Worked example](../examples/fpcr-wild-bootstrap.md) · [Mathematics](mathematical-reference.md#wild-bootstrap)

-   **Fixed-family wild-bootstrap tests**

    ![Target-wise and maxT adjusted wild-bootstrap p-values](../assets/gallery/wild-bootstrap-family-test.svg)

    Target-wise and single-step max-(|t|) probabilities for one declared family.

    **API:** `fpca_wild_bootstrap_projection_family_test()`, `plot_fpca_wild_bootstrap_family_test()`

    [Worked example](../examples/fpcr-wild-bootstrap-family-tests.md) · [Mathematics](mathematical-reference.md#family-tests)

-   **Finite-bootstrap precision**

    ![Monte Carlo precision diagnostics](../assets/gallery/monte-carlo-precision.svg)

    Exact binomial intervals around retained bootstrap exceedance probabilities.

    **API:** `fpca_wild_bootstrap_family_test_monte_carlo_diagnostics()`, `plot_fpca_wild_bootstrap_monte_carlo_diagnostics()`

    [Worked example](../examples/fpcr-wild-bootstrap-monte-carlo.md) · [Mathematics](mathematical-reference.md#monte-carlo)


-   **Continuous signed curvature**

    ![Signed curvature over time for a smooth planar trajectory](../assets/gallery/trajectory-curvature.svg)

    Continuous local path curvature computed from the observed planar trajectory without hidden smoothing, interpolation, or denominator stabilization.

    **API:** `signed_curvature_function()`, `plot_trajectory_overlay()`

    [Worked example](../examples/trajectory-geometry.md) · [Method guide](trajectory-geometry.md) · [Mathematics](mathematical-reference.md#trajectory-geometry)

-   **Audited dynamic time warping alignment**

    ![Dynamic time warping alignment path](../assets/gallery/dtw-alignment.svg)

    A normalizable symmetric2 alignment with an explicit Sakoe-Chiba sample-index band, shown against the same-index diagonal.

    **API:** `dynamic_time_warping_distance()`, `plot_dynamic_time_warping_alignment()`

    [Worked example](../examples/dynamic-time-warping.md) · [Method guide](dynamic-time-warping.md) · [Mathematics](mathematical-reference.md#dynamic-time-warping)

-   **Sparse recurrence structure**

    ![Sparse recurrence plot](../assets/gallery/recurrence-plot.svg)

    Recurrent reconstructed states under an explicit target recurrence rate and Theiler exclusion.

    **API:** `delay_embed_trajectory()`, `recurrence_matrix()`, `plot_recurrence()`

    [Worked example](../examples/nonlinear-dynamics.md) · [Mathematics](mathematical-reference.md#recurrence)

-   **Recurrence threshold profile**

    ![Recurrence rate over an analyst-declared radius grid](../assets/gallery/recurrence-radius-profile.svg)

    Exact RR(radius) diagnostics and pair-distance threshold sensitivity without automatic radius selection.

    **API:** `recurrence_radius_profile()`, `plot_recurrence_rate_curve()`

    [Worked example](../examples/recurrence-threshold-diagnostics.md) · [Method guide](recurrence-threshold-diagnostics.md) · [Mathematics](mathematical-reference.md#recurrence)

-   **Population uncertainty for RQA summaries**

    ![Participant-level bootstrap intervals for population-average RQA metrics](../assets/gallery/rqa-population-bootstrap.svg)

    Percentile-bootstrap uncertainty for fixed-specification curve-level RQA metrics using equal-weight participant inference units.

    **API:** `bootstrap_rqa_metric_means()`, `plot_rqa_metric_mean_bootstrap()`

    [Worked example](../examples/rqa-population-bootstrap.md) · [Method guide](rqa-population-bootstrap.md) · [Mathematics](mathematical-reference.md#rqa-population-bootstrap)

-   **Time-varying RQA**

    ![Windowed recurrence quantification](../assets/gallery/windowed-rqa.svg)

    Full-window recurrence rate, determinism, and laminarity retained over trial time.

    **API:** `windowed_rqa()`, `plot_windowed_rqa()`

    [Nonlinear guide](../guides/nonlinear-dynamics.md) · [Mathematics](mathematical-reference.md#recurrence)

-   **RQA-derived functional trajectories**

    ![Windowed RQA recurrence-rate trajectories across source curves](../assets/gallery/functional-rqa-trajectories.svg)

    Sliding-window recurrence summaries promoted to a native functional representation while retaining overlap, edge/tail, and radius-policy provenance.

    **API:** `windowed_rqa_trajectory_set()`, `plot_windowed_rqa_trajectories()`

    [Worked example](../examples/rqa-functional-trajectories.md) · [Mathematics](mathematical-reference.md#functional-rqa-trajectories)
-   **Local divergence / Rosenstein LLE**

    ![Local divergence with declared Lyapunov fit interval](../assets/gallery/local-divergence.svg)

    Mean nearest-neighbor log divergence and the explicitly declared linear fit interval.

    **API:** `local_divergence_curve()`, `estimate_largest_lyapunov_rosenstein()`, `plot_local_divergence()`

    [Worked example](../examples/nonlinear-dynamics.md) · [Mathematics](mathematical-reference.md#local-divergence)

-   **Kantz neighborhood divergence**

    ![Kantz fixed-radius neighborhood divergence with declared LLE fit](../assets/gallery/kantz-divergence.svg)

    Fixed-radius local-neighborhood divergence with explicit minimum-neighbor support and analyst-declared fit interval.

    **API:** `kantz_divergence_curve()`, `estimate_largest_lyapunov_kantz()`, `plot_local_divergence()`

    [Worked comparison](../examples/kantz-lle.md) · [Method guide](kantz-lle.md) · [Mathematics](mathematical-reference.md#kantz-local-divergence)

-   **Kantz radius sensitivity**

    ![Kantz largest-Lyapunov estimate over a declared radius grid](../assets/gallery/kantz-sensitivity.svg)

    Exponent sensitivity over a predeclared fixed-radius grid with reconstruction, minimum-neighbor, Theiler, and fit settings held explicit.

    **API:** `kantz_parameter_sensitivity()`, `plot_kantz_sensitivity()`

    [Worked example](../examples/nonlinear-parameter-sensitivity.md) · [Sensitivity guide](nonlinear-parameter-sensitivity.md) · [Mathematics](mathematical-reference.md#kantz-local-divergence)

-   **Experimental empirical return map**

    ![Empirical Poincare return map](../assets/gallery/return-map.svg)

    Successive section crossings and a local affine return map for a deterministic synthetic contracting cycle.

    **API:** `poincare_crossings()`, `fit_local_return_map()`, `return_map_stability()`, `plot_poincare_return_map()`

    [Worked example](../examples/return-map-stability.md) · [Mathematics](mathematical-reference.md#return-map-stability)

</div>

## Reproduce the gallery

Run:

```bash
python scripts/generate_docs_gallery.py
```

The generator uses the package itself, fixed random seeds, the non-interactive Matplotlib backend, deterministic SVG hashing, and timestamp-free SVG metadata.

## Plot → method → equation

=== "FPCA"

    `plot_fpca_component()` visualizes

    $$
    \widehat{\boldsymbol\mu}(t)
    +a\sqrt{\widehat\lambda_k}\widehat{\boldsymbol\phi}_k(t).
    $$

=== "Mean band"

    `plot_functional_mean_band()` visualizes

    $$
    \overline X_d(t_m)
    \pm
    c_{1-\alpha}\widehat{\mathrm{SE}}_d(t_m).
    $$

=== "Wild bootstrap"

    `plot_fpca_wild_bootstrap_projection()` visualizes

    $$
    \widehat\theta_{0,h}
    \pm
    c_{0,1-\alpha}\widehat{\mathrm{SE}}_0.
    $$

=== "DTW alignment"

    `plot_dynamic_time_warping_alignment()` visualizes the selected monotone index path. For symmetric2, the raw path cost uses step weights 2 for diagonal moves and 1 for horizontal/vertical moves; the optional normalized distance divides the complete global cost by \(N+M\).

=== "Recurrence"

    `plot_recurrence()` visualizes sparse entries satisfying

    $
    R_{ij}=\mathbb I\{\|\mathbf z_i-\mathbf z_j\|_p\le\varepsilon\}.
    $

=== "Local divergence"

    `plot_local_divergence()` visualizes

    $
    D(k)=\frac{1}{N_k}\sum_i\log d_i(k),
    $

    with the analyst-declared LLE fit interval when an estimate is supplied.

=== "Return map"

    `plot_poincare_return_map()` visualizes successive crossings under

    $
    \mathbf z_{n+1}\approx
    \mathbf a+\mathbf J(\mathbf z_n-\mathbf z_0).
    $

=== "Monte Carlo precision"

    `plot_fpca_wild_bootstrap_monte_carlo_diagnostics()` visualizes the raw retained tail estimate and exact binomial precision limits, where

    $$
    \widehat q=\frac{r}{B}.
    $$

## Gallery contract

The docs workflow regenerates all nineteen assets before the strict MkDocs build and runs `scripts/validate_docs_contracts.py`. A missing image, stale generated equation index, broken nav target, undefined mathematical deep link, missing mathematical API contract, stale MathJax hook, or unresolved documented public symbol fails the documentation job.
