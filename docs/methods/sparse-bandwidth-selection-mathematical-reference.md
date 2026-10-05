# Mathematical reference: audited sparse-FPCA bandwidth selection

This page defines the first 1.1 bandwidth-selection contract for the native univariate sparse-FPCA estimator. It is a tuning procedure around `fit_sparse_fpca()`; it does not change that estimator's scientific definition or defaults.

## Training-fold population model

Let fold $f$ contain training curves $\mathcal T_f$ and validation curves $\mathcal V_f$. For candidate bandwidth tuple

$$
h=(h_\mu,h_G,h_\epsilon),
$$

where $h_\epsilon$ is present only for diagonal-difference noise estimation, the native sparse-FPCA population objects are refitted using **training curves only**:

$$
\widehat\mu_{-f,h}(t),
\qquad
\widehat G_{-f,h}(s,t),
\qquad
\widehat\sigma^2_{\epsilon,-f,h}.
$$

No observation from $\mathcal V_f$ is used in those estimates.

If measurement-error variance is externally fixed, $h_\epsilon$ is absent and the declared fixed variance is retained in every training fold. If diagonal-difference noise estimation is used, the noise smoother and declared `noise_support` are applied within each training fold.

## Held-out whole-curve Gaussian loss

For validation curve $i\in\mathcal V_f$ observed at native times

$$
T_i=(t_{i1},\ldots,t_{im_i}),
$$

write

$$
\mathbf y_i=
\begin{bmatrix}
Y_i(t_{i1}) & \cdots & Y_i(t_{im_i})
\end{bmatrix}^{\top},
$$

and evaluate the training-fold population model at those native times:

$$
\widehat{\boldsymbol\mu}_{i,-f,h}
=
\widehat\mu_{-f,h}(T_i),
$$

$$
\widehat\Sigma_{i,-f,h}
=
\widehat G_{-f,h}(T_i,T_i)
+
\widehat\sigma^2_{\epsilon,-f,h}I_{m_i}.
$$

The candidate loss for curve $i$ is the Gaussian negative log predictive density normalized by the number of observed samples:

$$
\ell_{i,f}(h)
=
\frac{1}{2m_i}
\left[
\log\left|\widehat\Sigma_{i,-f,h}\right|
+
(\mathbf y_i-\widehat{\boldsymbol\mu}_{i,-f,h})^{\top}
\widehat\Sigma_{i,-f,h}^{-1}
(\mathbf y_i-\widehat{\boldsymbol\mu}_{i,-f,h})
+
m_i\log(2\pi)
\right].
$$

The implementation uses stable linear solves. A held-out covariance matrix that is not positive definite or exceeds the declared predictive condition-number limit fails explicitly.

The fold criterion is

$$
L_f(h)
=
\frac{1}{|\mathcal V_f|}
\sum_{i\in\mathcal V_f}\ell_{i,f}(h).
$$

Thus validation **curves** receive equal weight at the fold-aggregation stage; the criterion is not an observation-level iid loss.

Across valid folds, the aggregate criterion is

$$
\overline L(h)
=
\frac{1}{F_h}
\sum_{f\in\mathcal F_h}L_f(h),
$$

where $\mathcal F_h$ is the set of folds for which candidate $h$ completed successfully and $F_h=|\mathcal F_h|$.

## Eligibility and failures

A candidate is eligible only when

$$
F_h\ge F_{\min},
$$

where `min_valid_folds` defines $F_{\min}$. The default is

$$
F_{\min}=K,
$$

for $K$-fold cross-validation, so every fold must be valid by default.

Failed folds remain in the audit table with a failure code and message. They are not silently removed, replaced by another bandwidth, or converted to a finite loss.

## Selection rule

Among eligible finite candidates,

$$
\widehat h
=
\operatorname*{arg\,min}_{h}\overline L(h).
$$

Ties are resolved deterministically by preferring larger mean, covariance, and noise bandwidths lexicographically, then by `candidate_id`. The tie-break is an implementation rule for reproducibility; it is not an inferential statement about optimal smoothing.

The first tranche does **not** implement a one-standard-error rule. A multidimensional bandwidth tuple does not currently have a prespecified scalar complexity ordering analogous to retaining fewer principal components. A 1-SE selector would require such an ordering to be defined scientifically before implementation.

## Resampling unit

Two resampling units are supported:

- `resampling_unit="curve"`: whole curves are assigned to folds;
- `resampling_unit="group"`: all curves sharing the declared `group_column` are assigned to the same validation fold.

For repeated participant/trial data, group resampling is the leakage-safe route when participant-level generalization is intended.

Observation-level random splitting is not part of this method.

## Distinction from PACE scoring

The validation loss uses

$$
\widehat G_{-f,h}(T_i,T_i)
+
\widehat\sigma^2_{\epsilon,-f,h}I,
$$

not the PACE score system with `score_ridge`, and validation observations are not used to estimate held-out PACE scores before computing the criterion.

This separation is intentional: the first bandwidth selector tunes the training-fold population observation model rather than a downstream score reconstruction.

## Scope of the selected bandwidth

$\widehat h$ is the minimizer of the declared criterion over the declared candidate set and fold design. It is not a universal population parameter and should not be described as recovery of a unique "true bandwidth".

Bandwidth choice depends on, among other things:

- sample size;
- native observation density/design;
- measurement noise;
- smoothing family and kernel;
- analysis support;
- candidate grid;
- resampling unit; and
- validation criterion.

## API and audit objects

**Selector:** `eyetrajectoriespy.sparse_bandwidth_selection.select_sparse_fpca_bandwidths()`.

**Result:** `SparseFPCABandwidthSelectionResult`, retaining assignments, candidate grid, candidate-fold results, held-out curve losses, aggregate candidate summaries, selected bandwidths, status, and provenance.

**Reporting helper:** `sparse_fpca_bandwidth_selection_reporting_text()`.

The selected numeric values are not applied automatically. They must be supplied explicitly to a later `fit_sparse_fpca()` call, which continues to record `automatic_bandwidth_selection_performed=False`.

See the [user guide](../guides/sparse-bandwidth-selection.md) and the [native sparse FPCA/PACE guide](../guides/sparse-irregular-fpca.md).
