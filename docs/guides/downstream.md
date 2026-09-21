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
