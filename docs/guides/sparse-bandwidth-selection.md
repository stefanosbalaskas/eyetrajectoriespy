# Audited bandwidth selection for native sparse FPCA

The 1.1 development line adds an **opt-in bandwidth selector** for the native univariate sparse-FPCA estimator. It is deliberately separate from `fit_sparse_fpca()`.

Use it when the scientific analysis requires data-driven smoothing choices but you still want the fitted estimator to receive explicit numeric bandwidths.

## What is selected

The first qualified selector tunes only:

- the local-linear mean bandwidth; and
- the local-linear latent covariance bandwidth.

It does **not** tune component count, score ridge, analysis support, PSD policy, the noise model, the diagonal-difference noise bandwidth, or any sparse-MFPCA parameter in this tranche.

When `noise_variance_method="diagonal_difference"` is used, `noise_bandwidth=` remains one explicitly declared scalar held fixed across all candidates and folds.

## Why noise-bandwidth CV is not included

An exploratory known-truth qualification initially allowed the same held-out marginal Gaussian criterion to tune the diagonal-difference noise bandwidth. The selected candidate reproduced total observation covariance well, but the resulting full-data noise estimate was about `0.183` when the simulated measurement-error variance was `0.0196`.

That result is informative: marginal predictive likelihood can fit the **sum** of latent and measurement-error covariance while allocating variance badly between the two components. It is therefore not sufficient, by itself, as a decomposition-specific criterion for selecting the diagonal-difference noise smoother.

A2 consequently does not promote noise-bandwidth CV. A future noise-bandwidth selector would require its own decomposition-aware criterion and qualification.

## Criterion

For validation curve $i$ with native observations $y_i$ at times $T_i$, a training fold supplies

$$
\widehat\mu_{-f}(T_i),
\qquad
\widehat\Sigma_{i,-f}
=
\widehat G_{-f}(T_i,T_i)
+
\widehat\sigma^2_{\epsilon,-f} I.
$$

The curve loss is the per-observation Gaussian negative log predictive density

$$
\ell_i
=
\frac{1}{2m_i}
\left[
\log|\widehat\Sigma_{i,-f}|
+
\{y_i-\widehat\mu_{-f}(T_i)\}^\top
\widehat\Sigma_{i,-f}^{-1}
\{y_i-\widehat\mu_{-f}(T_i)\}
+
m_i\log(2\pi)
\right].
$$

Fold loss is the mean of the held-out **curve** losses. Curves therefore receive equal weight at the fold-aggregation stage even when their native observation counts differ.

The validation observations are not used to estimate the fold mean, covariance surface, measurement-error variance, or PACE scores. This is a population predictive criterion, not a score-reconstruction criterion.

## Basic curve-level selection

```python
import numpy as np

from eyetrajectoriespy.sparse_bandwidth_selection import (
    select_sparse_fpca_bandwidths,
    sparse_fpca_bandwidth_selection_reporting_text,
)

selection = select_sparse_fpca_bandwidths(
    irregular,
    dimension="x",
    evaluation_grid=np.linspace(0.0, 1.0, 41),
    mean_bandwidths=(0.12, 0.20, 0.30),
    covariance_bandwidths=(0.20, 0.34, 0.50),
    noise_variance_method="fixed",
    measurement_error_variance=0.015,
    n_splits=5,
    resampling_unit="curve",
    random_state=2026,
    psd_action="project",
    failure_action="retain",
)

print(selection.candidate_summary)
print(selection.selected_bandwidths)
print(sparse_fpca_bandwidth_selection_reporting_text(selection))
```

The result retains:

- deterministic validation-fold assignments;
- every declared mean × covariance candidate;
- every candidate-fold status and loss;
- per-held-out-curve predictive losses and conditioning diagnostics;
- raw and effective post-support training/validation observation counts;
- fitted fold-level noise variances;
- failed candidate/fold evaluations and their codes/messages;
- aggregate candidate summaries;
- the declared minimum-valid-fold rule; and
- the selected minimum-loss candidate, if any candidate is eligible.

## Grouped resampling for repeated participants

If multiple curves belong to the same participant, keep the participant out of training whenever one of that participant's curves is in validation:

```python
selection = select_sparse_fpca_bandwidths(
    irregular,
    dimension="x",
    evaluation_grid=np.linspace(0.0, 1.0, 41),
    mean_bandwidths=(0.12, 0.20, 0.30),
    covariance_bandwidths=(0.20, 0.34, 0.50),
    noise_variance_method="fixed",
    measurement_error_variance=0.015,
    n_splits=5,
    resampling_unit="group",
    group_column="participant_id",
    psd_action="project",
)
```

`resampling_unit="group"` uses group-aware folds; every value of `group_column` appears in one validation fold only. Observation-level random splitting is not used.

## Using diagonal-difference noise estimation

When measurement noise is estimated rather than externally fixed, declare one noise bandwidth and one noise-support interval before selection:

```python
selection = select_sparse_fpca_bandwidths(
    irregular,
    dimension="x",
    evaluation_grid=np.linspace(0.0, 1.0, 41),
    mean_bandwidths=(0.18, 0.24, 0.32),
    covariance_bandwidths=(0.30, 0.40, 0.52),
    noise_bandwidth=0.20,
    noise_variance_method="diagonal_difference",
    noise_support=(0.20, 0.80),
    n_splits=5,
    psd_action="project",
)
```

The declared `noise_bandwidth=0.20` is held fixed for every mean/covariance candidate and every training fold. Noise variance itself is still re-estimated from training data inside each fold. A fold-specific invalid noise estimate remains an explicit candidate-fold failure rather than being clipped or replaced.

## Failure semantics

The default `failure_action="retain"` treats failures as part of the audit record. A candidate can fail because of insufficient local support, invalid noise variance, PSD failure, or an invalid/ill-conditioned held-out predictive covariance.

A failed fold contributes no loss and is counted explicitly. By default `min_valid_folds` equals `n_splits`, so a candidate with any failed fold is ineligible for selection. You can relax `min_valid_folds` explicitly, but the missing folds remain visible in `fold_results` and `candidate_summary`.

Impossible fold designs fail before candidate evaluation; in particular, every native sparse-FPCA training fold must contain at least three curves.

Use `failure_action="error"` when any candidate/fold failure should stop the selector immediately.

The selector never silently:

- drops failed folds from the audit;
- reduces the number of folds;
- substitutes a nearby bandwidth;
- extrapolates unsupported smooths; or
- applies the selected values to the fitter.

## Selection rule and ties

The first tranche implements only the **minimum mean fold loss** rule.

When eligible candidates tie numerically, the deterministic tie-break prefers larger mean and covariance bandwidths lexicographically, then `candidate_id`. This tie-break is recorded in provenance.

A one-standard-error rule is intentionally **not** implemented yet. With a two-dimensional bandwidth tuple there is no scientifically predeclared one-dimensional "simpler model" ordering analogous to choosing fewer principal components. Adding a 1-SE rule without defining that ordering would make the result look more principled than it is.

## Fit explicitly after selection

Selection and estimation remain separate steps. With fixed measurement-error variance:

```python
from eyetrajectoriespy import fit_sparse_fpca

chosen = selection.selected_bandwidths
if chosen is None:
    raise RuntimeError("No bandwidth candidate satisfied the declared fold policy")

fit = fit_sparse_fpca(
    irregular,
    dimension="x",
    n_components=2,
    evaluation_grid=np.linspace(0.0, 1.0, 41),
    mean_bandwidth=chosen["mean_bandwidth"],
    covariance_bandwidth=chosen["covariance_bandwidth"],
    noise_variance_method="fixed",
    measurement_error_variance=0.015,
    psd_action="project",
)
```

If diagonal-difference noise estimation was used during selection, pass the **same predeclared** `noise_bandwidth` and `noise_support` to the final fit.

The stable fitter still records `automatic_bandwidth_selection_performed=False`. The selector never changes that contract.

## Interpretation

The selected mean/covariance bandwidth pair minimizes the declared cross-validated predictive criterion **within the supplied candidate set and resampling design**. It is not an estimate of a universal population "true bandwidth". The selected values depend on sample size, observation density, noise, candidate grid, analysis support, smoothing family, and validation criterion.

Use the qualification evidence as a recovery/stress check of the selector, not as proof that the same candidate grid is optimal for a different study.

## Reporting

Report at minimum:

- the criterion (`mean_curve_gaussian_nll`);
- the curve/group resampling unit and grouping column when applicable;
- fold count and random seed when curve folds are shuffled;
- mean/covariance candidate ranges;
- noise-variance policy and noise support;
- the fixed declared `noise_bandwidth` if diagonal-difference noise estimation was used;
- minimum-valid-fold rule;
- number of failed candidate-fold evaluations;
- selected mean/covariance bandwidths; and
- that the selected values were subsequently supplied explicitly to `fit_sparse_fpca()`.

Use `sparse_fpca_bandwidth_selection_reporting_text()` as a reproducible starting point.

## Public API

Import from the dedicated 1.1 module:

- `eyetrajectoriespy.sparse_bandwidth_selection.select_sparse_fpca_bandwidths()`
- `eyetrajectoriespy.sparse_bandwidth_selection.SparseFPCABandwidthSelectionResult`
- `eyetrajectoriespy.sparse_bandwidth_selection.sparse_fpca_bandwidth_selection_reporting_text()`

See also the [native sparse FPCA/PACE guide](sparse-irregular-fpca.md) and the [bandwidth-selection mathematical reference](../methods/sparse-bandwidth-selection-mathematical-reference.md).
