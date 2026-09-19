# Selecting the number of FPCs

Choosing the retained dimension is a **model-selection decision**, not a cosmetic plotting choice.

A cumulative-variance threshold answers:

> How many fitted components summarize a chosen fraction of in-sample functional variance?

Held-out reconstruction cross-validation answers a different question:

> How many components are useful for reconstructing trajectories that were not used to estimate the FPCA basis?

Both can be reported. They should not be treated as interchangeable.

## Leakage-safe reconstruction CV

`cross_validate_fpca_reconstruction()` refits FPCA inside every training fold, projects held-out trajectories into that training basis, reconstructs them with each candidate component count, and evaluates integrated RMSE.

```python
cv = cross_validate_fpca_reconstruction(
    gaze,
    candidate_components=(1, 2, 3, 4, 5, 6),
    n_splits=5,
    scaling="dimension_sd",
    cv_unit="group",
    group_column="participant_id",
)
```

The full dataset is **not** used to estimate the basis before folds are created.

!!! warning "Do not fit once and score folds afterwards"
    Fitting FPCA on the full sample before evaluating held-out curves leaks information about the test trajectories into the mean, scaling, and eigenfunctions.

## Repeated trials: group the participant

When a participant contributes multiple trials, curve-level K-fold CV can place some of that participant's trials in training and others in testing.

Use grouped CV instead:

```python
cv_unit="group"
group_column="participant_id"
```

Every participant then belongs to one test fold only.

Use curve-level CV only when curves are genuinely independent at the level relevant to the scientific question.

## Inspect before selecting

```python
summary = summarise_fpca_cross_validation(cv)
print(summary)
plot_fpca_cross_validation(cv)
```

The summary contains:

- candidate component count;
- mean fold-level held-out integrated RMSE;
- SD across folds;
- SE across folds;
- number of folds.

The result also retains the curve-to-fold assignments so grouping can be audited.

## Selection rules are explicit

### Minimum RMSE

```python
k = select_fpca_components_cv(cv, rule="minimum")
```

This selects the candidate with the smallest mean held-out reconstruction error.

### One-standard-error heuristic

```python
k = select_fpca_components_cv(cv, rule="one_se")
```

This selects the smallest candidate whose mean error is no worse than one standard error above the minimum-error candidate.

The one-SE rule is a **parsimony heuristic**. It is not a hypothesis test and does not guarantee the scientifically correct dimension.

## Cross-validation is not the only criterion

A useful component count should also be considered against:

- cumulative variance explained;
- bootstrap component stability;
- reconstruction curves;
- component interpretability;
- sensitivity to registration and preprocessing;
- the sample size available for stable eigenfunction estimation.

A component can slightly improve reconstruction but remain unstable or scientifically uninterpretable.

## Candidate range

Do not search arbitrarily large component counts.

Within each training fold, the centered sample covariance has at most `n_train - 1` non-zero sample directions. The API rejects candidate counts above that fold-specific maximum instead of fitting a degenerate direction.

## When not to use this workflow

Do not use ordinary common-grid reconstruction CV as a substitute for:

- sparse-FPCA methods when interpolation creates most of each curve;
- supervised dimension selection when the scientific target is prediction of an external outcome;
- phase-aware model selection when timing variation should first be modeled separately;
- participant-independent CV when repeated trials are clustered within participants.

## Interpretation

Lower held-out RMSE indicates better out-of-sample reconstruction under the stated representation, scaling, fold definition, and candidate set.

It does **not** prove that:

- the selected components are causally meaningful;
- every selected FPC is stable;
- a different preprocessing or registration choice would select the same dimension;
- the selected dimension is optimal for a downstream regression outcome.

## Reporting example

> The retained FPCA dimension was evaluated using five-fold participant-grouped reconstruction cross-validation. FPCA, including the training-fold mean and dimension scaling, was re-estimated within each fold. Candidate dimensions of one through six FPCs were compared using held-out integrated RMSE. The pre-specified one-standard-error heuristic selected three FPCs; the minimum-RMSE solution retained four. Component stability and interpretation were examined separately.

Use `fpca_cross_validation_reporting_text()` for a compact reproducible starting point.

## API links

- `cross_validate_fpca_reconstruction()`
- `summarise_fpca_cross_validation()`
- `select_fpca_components_cv()`
- `plot_fpca_cross_validation()`
- `fpca_cross_validation_reporting_text()`

## Methodological context

Li, Wang, and Carroll (2013) emphasize that selecting the number of functional principal components is a distinct methodological problem rather than something resolved automatically by FPCA. The implementation here is intentionally a transparent held-out reconstruction diagnostic; it does not claim to reproduce their information-criterion estimator.

- Li Y, Wang N, Carroll RJ. *Selecting the Number of Principal Components in Functional Data*. Journal of the American Statistical Association. 2013;108(504). doi:10.1080/01621459.2013.788980.
