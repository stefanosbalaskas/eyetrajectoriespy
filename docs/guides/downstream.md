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
