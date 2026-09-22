# AOI probability functions

At each time point, AOI probabilities satisfy

$
p_k(t)\ge 0,
\qquad
\sum_{k=1}^{K}p_k(t)=1.
$

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


## Mathematical contract

After explicit zero replacement and renormalization, the additive log-ratio coordinate relative to reference AOI \(r\) is

$$
z_k(t)
=
\log\frac{p_k^\epsilon(t)}{p_r^\epsilon(t)},
\qquad k\ne r.
$$

The inverse transformation normalizes \(q_r(t)=1\) and \(q_k(t)=\exp\{z_k(t)\}\):

$$
p_k(t)
=
\frac{q_k(t)}
{\sum_{\ell=1}^{K}q_\ell(t)}.
$$

See the [mathematical reference](../methods/mathematical-reference.md#compositional).
