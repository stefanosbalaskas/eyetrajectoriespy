# Elastic trajectory analysis

The optional `fdasrsf` backend aligns multidimensional curves in the square-root velocity framework and supports shape PCA.

```python
fit = fit_elastic_fpca(
    gaze,
    n_components=3,
    rotation=False,
    scale_curves=False,
)
```

Rotation and scale invariance default to `False`: a screen-space path rotated or rescaled away from its stimulus often becomes scientifically meaningless.

Use elastic analysis when the question explicitly concerns geometric path shape versus traversal timing. Do not use it merely because aligned curves look cleaner.
