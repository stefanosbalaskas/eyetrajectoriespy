# Multilevel FPCA

Repeated experiments naturally have participant → trial → time structure:

$$
\mathbf G_{ij}(t)
=
\boldsymbol\mu(t)
+
\mathbf U_i(t)
+
\mathbf V_{ij}(t).
$$

`U_i(t)` represents participant-level deviation and `V_{ij}(t)` within-participant trial deviation.

```python
result = fit_multilevel_fpca(
    gaze,
    participant_column="participant_id",
    participant_components=0.90,
    trial_components=0.90,
    scaling="dimension_sd",
)
```

Participant FPCs characterize stable between-person functional differences. Trial FPCs characterize deviations around each participant's own mean trajectory.

!!! note
    The stable dense implementation is a transparent two-level functional ANOVA decomposition followed by separate FPCAs, not a full probabilistic functional mixed model.

The actual dense/common-grid decomposition used before the two separate FPCAs is

$$
\mathbf U_i(t)
=
\overline{\mathbf G}_{i\cdot}(t)-\boldsymbol\mu(t),
\qquad
\mathbf V_{ij}(t)
=
\mathbf G_{ij}(t)-\overline{\mathbf G}_{i\cdot}(t).
$$

## Sparse/irregular repeated trials

Do **not** manufacture participant mean curves by interpolating genuinely sparse raw trials onto a common grid merely to use the dense decomposition above. The 1.1 development line provides a separate [native sparse multilevel FPCA](sparse-multilevel-fpca.md) workflow. It estimates hierarchical covariance operators from native-time residual products and recovers participant/trial scores jointly by Gaussian BLUP using the full fitted hierarchy.

The sparse route has a deliberately narrower first contract: univariate trajectories, exchangeable repeated trials after any required condition/visit effects are handled upstream, observation/raw-pair weighting, and explicit support/PSD/identifiability diagnostics. See its [known-truth qualification](../validation/sparse-multilevel-fpca.md).

See the [mathematical reference](../methods/mathematical-reference.md#multilevel) for the stable dense decomposition.
