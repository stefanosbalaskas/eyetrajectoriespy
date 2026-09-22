# Multilevel FPCA

Repeated experiments naturally have participant → trial → time structure:

$
\mathbf G_{ij}(t)
=
\boldsymbol\mu(t)
+
\mathbf U_i(t)
+
\mathbf V_{ij}(t).
$

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
    The first release is a transparent two-level functional ANOVA decomposition followed by separate FPCAs, not a full probabilistic functional mixed model.


The actual decomposition used before the two separate FPCAs is

$$
\mathbf U_i(t)
=
\overline{\mathbf G}_{i\cdot}(t)-\boldsymbol\mu(t),
\qquad
\mathbf V_{ij}(t)
=
\mathbf G_{ij}(t)-\overline{\mathbf G}_{i\cdot}(t).
$$

See the [mathematical reference](../methods/mathematical-reference.md#two-level-functional-decomposition).
