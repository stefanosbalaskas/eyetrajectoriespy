# Choose a representation

The most important choice is the **functional object**, not the PCA backend.

| Research object | Functional form | Use |
|---|---|---|
| Screen-space gaze | $G_i(t)=[x_i(t),y_i(t)]^\\top$ | `fit_mfpca()` |
| One continuous derived variable | $X_i(t)$ | `fit_fpca()` |
| Repeated trials per participant | $G_{ij}(t)$ | `fit_multilevel_fpca()` |
| AOI probability vector | $P_i(t)$, $\\sum_k p_{ik}(t)=1$ | `fit_compositional_fpca()` |
| Same path at different rates | amplitude + phase | `register_to_landmarks()` / elastic analysis |

## Absolute screen coordinates

Use when absolute position is meaningful and stimuli share the same layout.

## Stimulus-normalized coordinates

Use when layouts are geometrically comparable after scaling. This does **not** solve semantic layout differences.

## Landmark-relative coordinates

Use when the scientific object is location relative to a meaningful stimulus element. This can reduce irrelevant layout variation but should not be used merely to force different stimuli into alignment.

## Derived functions

Distance to evidence, speed, or cumulative path length can be useful univariate functions. Derivatives amplify noise; use them only when temporal resolution and preprocessing support the question.


### Sparse latent univariate process

Use `IrregularTrajectorySet` plus `fit_sparse_fpca_fdapy()` when one functional dimension is observed only at a small number of curve-specific times and a common-grid interpolation would fabricate a substantial portion of the function.

This representation targets a latent smooth process estimated from pooled sparse observations. It is distinct from a densely observed planar path and from joint x/y MFPCA.

## Dynamical state representations

Nonlinear analysis adds a second representation decision after the trajectory itself is scientifically interpretable.

Observed-state recurrence can use explicitly declared dimensions such as

$$
\mathbf z_t=[x(t),y(t)].
$$

Delay reconstruction instead uses explicit recent history,

$$
\mathbf z_t=
[\mathbf G(t),\mathbf G(t-\tau),\ldots,\mathbf G(t-(m-1)\tau)].
$$

These representations answer different questions and are never silently substituted for one another. Channel scaling is also not introduced automatically; distances inherit the declared coordinate/state units.
## RQA-metric functional trajectories

`windowed_rqa_trajectory_set()` creates a derived `TrajectorySet` with `coordinate_system="rqa_metrics"`. Its dimensions are explicitly selected recurrence summaries such as RR, DET, LAM, line lengths, entropy, or CORM, and its time grid is the sequence of complete-window centers.

This label distinguishes derived nonlinear summaries from screen-space coordinates. Per-metric units remain explicit in provenance because the dimensions are heterogeneous: proportions, state-step counts, nats, and percentages must not be silently treated as having common physical units.

Overlapping windows remain within-curve dependent. Functionalization changes representation; it does not create new observational units.
