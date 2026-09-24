# Choose a representation

The most important choice is the **functional object**, not the PCA backend.

| Research object | Functional form | Use |
|---|---|---|
| Screen-space gaze | $G_i(t)=[x_i(t),y_i(t)]^\\top$ | `fit_mfpca()` |
| One continuous derived variable | $X_i(t)$ | `fit_fpca()` |
| Functional response explained by scalar predictors | $Y_i(t)=x_i^\top\beta(t)+\epsilon_i(t)$ | `fit_function_on_scalar_regression()` |
| Repeated functional response with trial-level predictors | $Y_{ij}(t)=x_{ij}^\top\beta(t)+b_i(t)+\epsilon_{ij}(t)$ | `fit_functional_mixed_effects_regression()` |
| Repeated trials per participant | $G_{ij}(t)$ | `fit_multilevel_fpca()` |
| AOI probability vector | $P_i(t)$, $\\sum_k p_{ik}(t)=1$ | `fit_compositional_fpca()` |
| Same path at different rates | amplitude + phase | `register_to_landmarks()` / elastic analysis |
| Ordered point-sequence similarity | $P=(p_1,\ldots,p_m)$ | `discrete_frechet_distance()` / `dynamic_time_warping_distance()` |

## Functional response regression

Use function-on-scalar regression when the scientific object is a continuous response trajectory and the predictors are scalar experimental or participant variables. Examples include condition effects on x(t), speed(t), curvature(t), or RQA-derived DET(t).

Version 0.35 fits the coefficient functions directly on the observed common grid. It does not smooth them or infer a spline basis automatically. The scalar design must therefore be encoded explicitly before fitting.

Repeated-trial support is deliberately restricted: participant mode first averages response functions within participant and requires every declared predictor to be participant-constant. Within-participant trial-varying predictors belong to the planned repeated-measures functional regression layer.

## Ordered point-sequence similarity

Discrete Fréchet and DTW operate on the supplied ordered points rather than on recorded elapsed timestamps. Fréchet minimizes the worst coupled separation; DTW minimizes a cumulative local alignment cost. DTW exposes the step-weighting rule explicitly: the backward-compatible symmetric1 raw-cost contract and the normalizable symmetric2 rule with optional N+M normalization. An optional Sakoe-Chiba band constrains sample-index displacement.

These are similarity representations, not substitutes for registration/phase analysis when timing deformation itself is a scientific outcome. Coordinate scaling, selected dimensions, upstream resampling, DTW step pattern, normalization choice, and the DTW band remain explicit analysis decisions.

When more than one similarity representation is defensible, version 0.38 can retain all declared L2, Fréchet, and DTW distance matrices and compare pair-order plus local-neighbor structure. This sensitivity layer does not collapse different representations into a common metric or erase their different scientific meanings.

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

For surrogate testing, the representation determines the null. Scalar IAAFT
targets one declared signal dimension. Multivariate IAAFT treats selected
simultaneous dimensions jointly, restoring each empirical marginal while
targeting their auto- and cross-spectral linear structure. Independent
surrogate generation of x and y is therefore not equivalent to a planar-gaze
multivariate surrogate null.

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
## Recurrence-network representation

A recurrence network reinterprets one auto-recurrence matrix as an undirected
graph. Nodes are state/time indices and edges are retained recurrence pairs.

This representation is useful when the scientific object is the topology of
recurrence neighborhoods rather than diagonal/vertical line structure. The
graph remains conditional on the same recurrence state space, threshold, metric,
Theiler exclusion, and sampling decisions as the underlying recurrence plot.

## Joint recurrence representation

A joint recurrence plot is not a pooled multivariate state space. Each
subsystem first defines its own auto-recurrence matrix, potentially with a
different state dimension, metric, and threshold. The joint plot then records
where all component recurrence matrices are simultaneously true.

This preserves modality-specific geometry while requiring a common synchronized
time index. It answers a simultaneity-of-recurrence question and should not be
substituted for cross-recurrence or a directional coupling model.

## RQA-metric functional trajectories

`windowed_rqa_trajectory_set()` creates a derived `TrajectorySet` with `coordinate_system="rqa_metrics"`. Its dimensions are explicitly selected recurrence summaries such as RR, DET, LAM, line lengths, entropy, or CORM, and its time grid is the sequence of complete-window centers.

This label distinguishes derived nonlinear summaries from screen-space coordinates. Per-metric units remain explicit in provenance because the dimensions are heterogeneous: proportions, state-step counts, nats, and percentages must not be silently treated as having common physical units.

Overlapping windows remain within-curve dependent. Functionalization changes representation; it does not create new observational units.

## Discrete states for transfer entropy

Transfer entropy in 0.41 starts from an explicit sequence of integer-coded
states. The codes may represent scientifically defined AOIs, behavioral states,
quantized motion states, or another preregistered symbolic representation, but
`eyetrajectoriespy` does not choose that representation.

Raw continuous \([x(t),y(t)]\) gaze, pupil diameter, or head rotation should
not be passed to the discrete TE API unless the analyst has explicitly
constructed and justified the states upstream. Changing the state definition
changes the empirical probability model and therefore the TE estimand.

### Sensitivity does not change the discrete state representation

The 0.42 TE sensitivity multiverse varies declared history and lag settings
only. The integer-coded source and target state sequences are held fixed across
all rows. If alternative state definitions or discretizations are scientifically
plausible, treat that as a separate representation sensitivity problem rather
than allowing the history/lag multiverse to silently change states.

### Conditional TE keeps all three state representations explicit

Version 0.43 requires explicit integer-coded source, target, and conditioning
series. The estimator varies none of those state definitions internally.
Changing the conditioning-process discretization, source state definition, or
target state definition changes the scientific estimand and should be treated
as a separate representation decision rather than hidden inside the CTE call.
