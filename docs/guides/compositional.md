# AOI probability functions

At each time point, AOI probabilities satisfy

[
p_1(t)+cdots+p_K(t)=1.
]

That constraint means the channels are not ordinary unconstrained Euclidean variables.

`fit_compositional_fpca()` verifies the simplex, applies explicit zero replacement, transforms to additive log-ratio coordinates, fits MFPCA, and reconstructs valid probabilities.

```python
fit = fit_compositional_fpca(
    aoi_probabilities,
    reference_dimension=3,
    epsilon=1e-8,
    n_components=0.95,
)
```

Report how probabilities were built, the reference AOI, zero-replacement epsilon, retained components, and interpretation on the original probability scale.
