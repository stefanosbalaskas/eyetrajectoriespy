# Sparse partial-trajectory prediction

The 1.1 development line adds a dedicated prediction layer for a **new partially observed univariate sparse trajectory**. It is designed for the situation where a native sparse history has already been observed and the scientific target is the future segment of the same functional process.

This capability is additive. It does not change `fit_sparse_fpca()`, does not add names to the frozen 1.0 root namespace, and does not interpolate the raw sparse history onto a common grid.

## Two distinct uncertainty targets

The workflow deliberately separates two objects.

### 1. Conditional latent future trajectory

Given fitted sparse-FPCA population objects, native observed history times $T_o$, observed values $Y_o$, and a declared future target grid $T_f$, the model-based predictor is

$$
\widehat\mu_{f\mid o}
=
\widehat\mu(T_f)
+
\widehat C(T_f,T_o)
\widehat\Sigma_{oo}^{-1}
\{Y_o-\widehat\mu(T_o)\},
$$

where

$$
\widehat\Sigma_{oo}
=
\widehat C(T_o,T_o)
+
\widehat\sigma_\epsilon^2 I
+
\gamma I.
$$

The conditional latent covariance is

$$
\widehat C_{f\mid o}
=
\widehat C(T_f,T_f)
-
\widehat C(T_f,T_o)
\widehat\Sigma_{oo}^{-1}
\widehat C(T_o,T_f).
$$

The calculation uses the **full fitted/repaired covariance surface**, not a rank-$K$ reconstruction. Linear solves are used instead of an explicit inverse.

The numerical history ridge $\gamma$ stabilizes the conditioning system only. It is not re-labelled as measurement error and is not added to future measurement noise.

### 2. Future observed measurements on a finite grid

For a future observed measurement, the model-based predictive covariance additionally contains the fitted measurement-error variance:

$$
\widehat C^{\mathrm{obs}}_{f\mid o}
=
\widehat C_{f\mid o}
+
\widehat\sigma_\epsilon^2 I.
$$

This is the scale used by the optional conformal layer.

## Base prediction

Import the development API from its dedicated module:

```python
import numpy as np
from eyetrajectoriespy.sparse_partial_prediction import (
    sparse_fpca_partial_trajectory_prediction,
    sparse_fpca_partial_prediction_frame,
    sparse_fpca_partial_prediction_reporting_text,
)

prediction = sparse_fpca_partial_trajectory_prediction(
    sparse_fit,
    one_target_curve,
    history_cutoff=0.60,
    prediction_grid=np.array([0.75, 0.85, 0.95]),
)

print(sparse_fpca_partial_prediction_frame(prediction))
print(sparse_fpca_partial_prediction_reporting_text(prediction))
```

The target must contain exactly one curve. Only actual observations at or before `history_cutoff` are used. Values after the cutoff may be present in the object for later validation, but they do **not** enter the conditional predictor.

The prediction grid must be strictly after the cutoff and remain inside the fitted population support.

## What the model-based uncertainty does and does not include

`latent_covariance` and `latent_standard_errors` are conditional on the fitted sparse population mean, covariance surface, measurement-error variance and declared numerical regularization.

They do **not** propagate uncertainty from estimating:

- the population mean;
- the covariance surface;
- the eigensystem;
- measurement-error variance;
- smoothing bandwidths; or
- PSD repair decisions.

Therefore the base prediction object carries **no frequentist coverage claim** by itself.

## Participant-aware split conformal calibration

The optional conformal layer targets **future observed measurements on one declared finite future grid**.

```python
from eyetrajectoriespy.sparse_partial_conformal import (
    calibrate_sparse_fpca_partial_prediction_conformal,
    sparse_fpca_conformal_prediction_band,
    sparse_fpca_conformal_band_frame,
    sparse_fpca_conformal_band_reporting_text,
)

calibration = calibrate_sparse_fpca_partial_prediction_conformal(
    sparse_fit,
    calibration_curves,
    history_cutoff=0.60,
    prediction_grid=np.array([0.75, 0.85, 0.95]),
    alpha=0.10,
    group_column="participant_id",
)

band = sparse_fpca_conformal_prediction_band(
    calibration,
    one_new_target_curve,
)
```

For calibration curve $i$, define the standardized future residual at target-grid point $t_j$ as

$$
r_{ij}
=
\frac{
|Y_i(t_j)-\widehat\mu_{i,f\mid o}(t_j)|
}{
\widehat s^{\mathrm{obs}}_{i,f\mid o}(t_j)
}.
$$

The curve-level nonconformity score is

$$
S_i=\max_j r_{ij}.
$$

If `group_column` is supplied, repeated curves/trials from participant $g$ are **not** treated as independent calibration units. Instead,

$$
S_g=\max_{i\in g} S_i,
$$

and the conformal order statistic is computed over participants/groups.

For $n$ calibration units and miscoverage level $\alpha$, the critical rank is

$$
k=\left\lceil(n+1)(1-\alpha)\right\rceil.
$$

The implementation fails if this rank exceeds $n$ rather than inventing an unattainable finite-sample quantile.

The final band is

$$
\widehat\mu_{f\mid o}(t_j)
\pm
q_{1-\alpha}\,
\widehat s^{\mathrm{obs}}_{f\mid o}(t_j).
$$

## No interpolation of calibration responses

Every calibration curve must contain an **actual retained observation at every declared future target-grid timestamp**. The first implementation uses exact timestamp equality and fails if one is absent or non-finite.

It does not:

- interpolate a nearby value;
- use nearest-neighbour matching;
- bin times;
- fill a missing future response; or
- move the target grid to match available calibration data.

This restriction is intentional: the coverage target should not silently change through preprocessing performed only for calibration.

## Coverage interpretation

Under the declared exchangeability/grouping contract, the conformal result is a simultaneous prediction band for **future observed measurements over the declared finite target grid**.

It is **not** claimed to provide:

- continuous-domain coverage between target-grid points;
- confidence coverage for the latent noise-free function;
- coverage conditional on the realized calibration set;
- validity under participant leakage; or
- automatic robustness to covariate shift or informative observation processes.

If repeated trials are present, use `group_column` so the participant/group is the exchangeability unit.

## Failure semantics

The workflow fails explicitly when, among other cases:

- the target dimension or units do not match the fit;
- history is too sparse;
- the cutoff or target grid lies outside fitted support;
- a target-grid point is not strictly future of the cutoff;
- the history covariance is non-positive-definite or exceeds the condition limit;
- proper-training, calibration or target curve IDs overlap;
- declared participant/group units overlap across partitions;
- the group column is absent;
- a calibration future-grid observation is absent or non-finite;
- predictive scales are non-positive/non-finite; or
- the requested $\alpha$ is below the finite-sample resolution of the calibration set.

## Qualification evidence

The known-truth qualification deliberately separates Gaussian conditional calibration from conformal calibration.

Across four oracle-population scenarios crossing history length and measurement noise, standardized latent/observed prediction errors had standard deviations from approximately **0.986 to 1.037**, while nominal 95% pointwise coverage ranged from approximately **0.936 to 0.950**. Increasing the history from 6 to 12 native observations reduced mean latent conditional variance from **0.0757 to 0.00120** in the low-noise design and from **0.3543 to 0.0176** in the higher-noise design.

The participant-aware conformal experiment used 60 calibration participants with two correlated trials each and 180 target participants with two trials each. At nominal 90% simultaneous coverage, participant-level coverage across **both trials and all three future target-grid points** was **0.9056**. Curve-level simultaneous coverage was **0.9528**. The critical value was **2.326**.

Deterministic replay passed. A missing calibration target-grid observation failed with `calibration_future_grid_observation_missing`, and deliberate proper-training/calibration leakage failed explicitly.

See [Sparse partial-prediction validation](../validation/sparse-partial-prediction.md) for the exact evidence boundary.

## Reporting

Report at least:

- fitted sparse dimension and units;
- history cutoff and retained history count;
- future target grid;
- fitted measurement-error variance;
- history ridge and condition limit;
- whether reported uncertainty is latent or future-observed predictive uncertainty;
- whether conformal calibration was applied;
- calibration alpha and number of calibration units;
- exchangeability unit and group column, if used;
- conformal critical value;
- exact-grid response requirement; and
- the explicit finite-grid observed-measurement coverage scope.
