# Functional regression and clustering

## FPCA-score regression

```python
model = fit_scalar_on_function_regression(
    fit,
    outcome,
    n_components=3,
    family="gaussian",
)
```

Report the retained component count because the downstream model depends on that dimension-reduction decision.

## Clustering

`cluster_fpca_scores()` performs deterministic K-means when `random_state` is supplied. Clusters are descriptive viewing-strategy groups, not latent psychological classes unless externally validated.

## Distances

`pairwise_functional_distances()` works in function space; `score_distance_matrix()` works in retained FPCA score space. They answer different questions.


## Select FPC count for prediction without leakage

When the retained FPC count is chosen using the scalar outcome, use the dedicated predictive-selection workflow rather than fitting FPCA once on the full sample. `cross_validate_fpca_regression()` estimates FPCA and the score regression inside every training fold; `nested_cross_validate_fpca_regression()` adds an untouched outer evaluation loop.

See [Outcome-tuned FPCA regression selection](predictive-component-selection.md).


## Gaussian scalar-on-function FPCR uncertainty

A fitted score regression conditions on an estimated FPCA basis. If the functional slope itself or fitted mean response is a scientific result, use <code>bootstrap_fpca_regression_uncertainty()</code> rather than treating the score matrix as error-free.

The bootstrap resamples the independent unit together with its scalar outcome and refits the entire FPCR pipeline:

1. resample curves or participant trial bundles;
2. refit FPCA/MFPCA using the fixed component count and scaling rule;
3. refit the Gaussian score regression;
4. reconstruct the functional slope in the original trajectory units;
5. re-project fixed target curves and obtain their fitted conditional means.

The implementation is intentionally Gaussian-only. The existing point-estimation helper supports binomial regression, but 0.12 does not generalize bootstrap inference to that model without dedicated methodological support.

The component count is fixed inside the bootstrap. Use reconstruction CV or predictive nested CV to choose the dimension separately, and report that selection step.

See [Gaussian FPCR bootstrap uncertainty](fpcr-bootstrap-inference.md).


## Simultaneous observed-grid FPCR slope bands

The 0.12 paired bootstrap stores every reconstructed slope replicate. The 0.13 calibration layer reuses those exact replicates:

    band = fpca_regression_slope_simultaneous_band(
        inference,
        confidence_level=0.95,
        simultaneous_scope="global",
    )

No second bootstrap is run.

Global scope uses one maximum over the complete sampled time-by-dimension slope grid. Dimension scope calibrates one maximum over time separately within each functional dimension.

The resulting band is a studentized bootstrap approximation over the **observed grid**. It does not establish continuous-domain coverage between samples and does not implement the operator-scaled FPCR significance test from recent asymptotic theory.

See [Gaussian FPCR simultaneous slope bands](fpcr-simultaneous-slope-band.md).


## Future observed outcomes versus conditional means

The 0.12 paired bootstrap estimates uncertainty in the fitted conditional mean response for a fixed target trajectory.

A future observed scalar outcome additionally contains response noise.

Use <code>fpca_regression_future_prediction_interval()</code> to combine:

1. the existing paired-bootstrap conditional-mean prediction for each fixed target;
2. an independent draw from the centered empirical residual distribution of the full-sample Gaussian FPCR fit.

The residual pool and the sampled residual used in every bootstrap/target draw are retained in the result object.

This is a residual-resampling predictive approximation. It assumes one exchangeable/common residual distribution across targets and therefore is not heteroscedasticity-robust.

The resulting intervals are marginal per target. They do not claim simultaneous coverage across several target trajectories and do not define a joint multivariate future-outcome distribution.

See [Gaussian FPCR future-outcome prediction](fpcr-future-prediction.md).


## Heteroscedastic Gaussian FPCR projection inference

The paired bootstrap and wild bootstrap answer related but different questions.

Use <code>bootstrap_fpca_regression_uncertainty()</code> when sampling uncertainty in the functional basis itself must be propagated by resampling independent units and refitting FPCA.

Use <code>wild_bootstrap_fpca_projection()</code> when the functional regressors are treated as fixed and the scientific target is a centered projection under possibly heterogeneous response errors.

The 0.16 wild-bootstrap contract is:

1. fit FPCA/MFPCA once and keep the functional regressors/basis fixed;
2. estimate residuals with k retained FPC scores;
3. use the same g=k truncation as the bootstrap pseudo-truth;
4. choose an explicit inference truncation h with h>=g;
5. generate pseudo-responses by multiplying k-truncation residuals by mean-zero, unit-variance multipliers;
6. refit the score regression on the fixed scores;
7. recompute the heteroscedastic studentization scale inside every pseudo-sample;
8. calibrate target-wise symmetrized intervals from the absolute studentized roots.

Standard-normal multipliers are the default; the mathematically mean-zero/unit-variance Mammen two-point distribution is also available.

The API currently assumes independent curve rows. Declared duplicated independent-unit IDs cause an explicit failure because clustered wild-bootstrap validity is outside this tranche.

See [Heteroscedastic FPCR wild bootstrap](fpcr-wild-bootstrap.md).
