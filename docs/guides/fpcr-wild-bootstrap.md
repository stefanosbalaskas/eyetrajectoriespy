# Heteroscedastic Gaussian FPCR wild bootstrap

Gaussian scalar-on-function FPCR is often used after representing a gaze trajectory through retained FPC scores.

When response-error variance may change with the functional predictor, a homoscedastic residual bootstrap is not a safe default.

Version 0.16 provides a fixed-regressor multiplier wild bootstrap for **centered target projections** under possible heteroscedasticity.

## Scientific target

For a fixed target trajectory, the API estimates the centered functional projection associated with the fitted FPCR slope.

The target is defined relative to the training functional mean because the FPCA score coordinates are centered.

It is not a future observed response. Response-noise prediction remains a separate problem.

## Fixed-regressor bootstrap

The functional trajectories, their fitted FPCA/MFPCA basis, and their score coordinates stay fixed during wild resampling.

Only the scalar response is regenerated in the bootstrap world.

This differs intentionally from the paired FPCR bootstrap, which resamples independent units and refits the functional basis.

## Three truncation roles

The 2026 wild-bootstrap construction distinguishes three truncation levels:

- k: residual estimation;
- g: bootstrap pseudo-truth;
- h: target inference.

The 0.16 API follows the practical contract

    g = k
    h >= g

through:

    residual_components=k
    inference_components=h

The equality g=k is not hidden or estimated by the package.

## Pseudo-responses

First fit the k-component Gaussian score regression and obtain residuals.

For each bootstrap replicate:

    Y_star = fitted_k + residual_k * W

where W is a mean-zero, unit-variance multiplier.

The package supports:

- <code>multiplier="normal"</code>: standard normal multipliers;
- <code>multiplier="mammen"</code>: the conventional two-point Mammen distribution with exact mean zero and variance one.

The package does not silently switch multiplier families.

## Bootstrap-level studentization

A key methodological point is that heteroscedastic scaling is recomputed in every bootstrap pseudo-fit.

In score space, the package forms the empirical covariance of score × residual contributions, applies the inverse retained-score covariance, and obtains a target-specific heteroscedastic standard error.

The same construction is repeated using each pseudo-fit residual vector.

The bootstrap root is therefore:

    (bootstrap h-projection - g-pseudo-truth projection)
    / bootstrap heteroscedastic SE

The symmetrized target-wise interval uses the requested quantile of the absolute bootstrap roots multiplied by the full-sample heteroscedastic SE.

## Why not reuse the original SE inside every bootstrap root?

The 2026 methodology specifically emphasizes bootstrap-level studentization. Reusing only the original scaling can make performance more sensitive to the chosen multiplier distribution.

eyetrajectoriespy therefore recomputes the scale rather than taking a shortcut.

## Reference projection versus pseudo-truth

The final interval is centered on the full-sample h-component reference projection.

Bootstrap roots are centered against the g=k pseudo-truth projection.

Those can differ when h>g.

This difference is deliberate and records truncation bias rather than silently forcing the two approximations to be identical.

## Independent sampling units

The current implementation is an independent-curve wild bootstrap.

If <code>independent_unit_column</code> is supplied, every value must be unique.

Repeated participant IDs cause an explicit error.

For repeated trials, either:

- aggregate to a scientifically meaningful independent-unit functional trajectory before using this method; or
- use the participant-level paired FPCR bootstrap when basis/regression sampling uncertainty is the target.

A clustered wild-bootstrap extension would need a separate validity argument and is not approximated here.

## What is not included

The 0.16 method does not include:

- future observed-response noise;
- target functional measurement error;
- preprocessing uncertainty;
- component-selection uncertainty;
- FPCA basis resampling;
- clustered/repeated-participant wild resampling;
- simultaneous calibration across multiple targets;
- non-Gaussian/binomial functional regression.

## Relationship to Yeon, Dai & Nordman

Yeon, Dai & Nordman (2026) develop wild-bootstrap inference for mean-response projections in functional linear regression under heteroscedasticity.

Their construction keeps regressors fixed, uses multiplier-weighted residuals, separates k/g/h truncations, and emphasizes bootstrap-level studentization. Their companion BTSinFLRM implementation exposes normal, Mammen-type, and Härdle-Mammen multipliers and both individual and simultaneous procedures.

eyetrajectoriespy 0.16 implements a narrower score-space analogue for its common-grid Gaussian FPCR pipeline:

- g is fixed to k;
- h is explicit and must satisfy h>=k;
- normal and mathematically mean-zero/unit-variance Mammen multipliers are exposed;
- intervals are symmetrized and target-wise only;
- simultaneous target tests and null-enforced testing are not implemented.

## Reporting example

> Heteroscedastic uncertainty in centered Gaussian FPCR target projections was evaluated using 1,000 fixed-regressor multiplier wild-bootstrap replicates with standard-normal multipliers. Residual estimation and the bootstrap pseudo-truth used k=g=2 FPCs, while inference used h=3 FPCs. Each bootstrap projection root was studentized with a heteroscedastic score-covariance scale recomputed from the pseudo-fit residuals. Ninety-five-percent symmetrized intervals were reported separately for each fixed target trajectory. Curve rows were treated as independent sampling units; the analysis did not claim clustered wild-bootstrap validity, future-outcome prediction coverage, or simultaneous coverage across targets.

## API links

- <code>wild_bootstrap_fpca_projection()</code>
- <code>FPCAWildBootstrapProjectionResult</code>
- <code>fpca_wild_bootstrap_projection_frame()</code>
- <code>plot_fpca_wild_bootstrap_projection()</code>
- <code>fpca_wild_bootstrap_projection_reporting_text()</code>
- <code>bootstrap_fpca_regression_uncertainty()</code>
- <code>fpca_regression_future_prediction_interval()</code>

See [References](../methods/references.md).


## Selecting h instead of fixing it arbitrarily

Version 0.17 adds the stabilized-volatility strategy proposed with the 2026 wild-bootstrap method.

Conditional on a fixed residual truncation k and g=k, construct target-wise intervals over a consecutive candidate set H of h values.

For each adjacent transition h to h+1, define width stability and center stability by whether the absolute changes remain below analyst-declared thresholds.

A transition is stable only when both conditions hold.

The paper then selects the earliest h starting a run of r+1 stable transitions.

eyetrajectoriespy exposes this in two stages:

    scan = scan_wild_bootstrap_fpca_truncations(...)
    selected = select_fpca_wild_bootstrap_truncation(
        scan,
        width_threshold=...,
        center_threshold=...,
        stability_run=...,
    )

The scan deliberately reuses the same wild multiplier draws across all h candidates.

The package does not impose 0.01 as a default threshold. That value was used in the paper's numerical study, while an absolute threshold depends on the units and scale of the scalar outcome.

See [Stabilized-volatility FPCR truncation selection](fpcr-wild-bootstrap-selection.md).
