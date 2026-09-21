# Outcome-tuned FPCA regression selection

FPCA can be used for at least three different dimension-selection questions:

| Question | Criterion |
|---|---|
| How many components summarize the functional predictor? | cumulative variance explained |
| How many components reconstruct unseen trajectories? | held-out functional reconstruction loss |
| How many components predict an external scalar outcome? | held-out scalar prediction loss |

These are different estimands. A component that explains little gaze variance can still carry predictive information about an external outcome, while a component that improves trajectory reconstruction may add no useful predictive signal.

## Predictive FPCA regression

<code>cross_validate_fpca_regression()</code> tunes the number of retained ordinary FPCA components for scalar-outcome prediction.

FPCA remains unsupervised: the outcome does not alter the eigenfunctions. The outcome is used only to select how many of the training-fold FPC scores enter the scalar regression.

    cv = cross_validate_fpca_regression(
        gaze,
        outcome,
        candidate_components=(1, 2, 3, 4, 5),
        family="gaussian",
        loss="rmse",
        n_splits=5,
        scaling="dimension_sd",
        cv_unit="group",
        group_column="participant_id",
        random_state=2026,
    )

Every fold performs the complete sequence:

1. subset training trajectories;
2. estimate FPCA mean, scaling, and eigenfunctions using training curves only;
3. project held-out curves into the training-fold basis;
4. fit the scalar regression on training-fold FPC scores only;
5. predict the held-out outcome;
6. calculate the requested loss.

This avoids outcome or trajectory leakage through a full-sample FPCA fit.

## Repeated trials: group the participant

When participants contribute multiple trajectories, use participant-grouped folds:

    cv_unit="group"
    group_column="participant_id"

All trials from a participant are then assigned to one test fold.

!!! warning
    Grouped cross-validation prevents train/test leakage. It does not automatically model residual dependence between trials from the same participant and does not automatically equalize participant weights inside the curve-level scalar regression.

If the same participant-level outcome has simply been copied onto every trial, consider participant-level functional aggregation or a specialist grouped/mixed model instead of treating duplicated outcomes as independent observations.

## Gaussian outcomes

Supported loss functions are:

- <code>rmse</code> — default;
- <code>mae</code>.

    cv = cross_validate_fpca_regression(
        gaze,
        confidence,
        family="gaussian",
        loss="rmse",
        ...
    )

## Binary outcomes

Supported probability losses are:

- <code>log_loss</code> — default;
- <code>brier</code>.

    cv = cross_validate_fpca_regression(
        gaze,
        choice,
        family="binomial",
        loss="log_loss",
        ...
    )

The API evaluates probabilities rather than accuracy. Each binomial training fold must contain both classes. Perfect separation and non-convergence are treated as explicit failures rather than valid model fits.

## Covariates

Numeric, finite covariates can be supplied:

    cv = cross_validate_fpca_regression(
        gaze,
        outcome,
        covariates=design[["age_z", "baseline_score"]],
        ...
    )

Covariates are carried fold by fold. Rank-deficient regression designs are rejected.

Categorical predictors should be encoded explicitly before fitting. Column names cannot collide with the intercept or generated FPC score names.

## Inspect the loss curve

    summary = summarise_fpca_regression_cv(cv)
    print(summary)
    plot_fpca_regression_cv(cv)

The table reports mean, SD, and SE of fold-level predictive loss for every candidate component count.

## Explicit selection rules

Minimum loss:

    k = select_fpca_regression_components(
        cv,
        rule="minimum",
    )

One-standard-error heuristic:

    k = select_fpca_regression_components(
        cv,
        rule="one_se",
    )

The one-SE rule selects the smallest candidate within one estimated standard error of the minimum-loss model. It is a parsimony heuristic, not a significance test.

## Why nested CV matters

If component count is selected using cross-validation and the same minimum CV loss is then reported as final predictive performance, the performance estimate is optimistically selected.

Use nested CV when predictive performance itself is a scientific result:

    nested = nested_cross_validate_fpca_regression(
        gaze,
        outcome,
        candidate_components=(1, 2, 3, 4, 5),
        outer_splits=5,
        inner_splits=4,
        selection_rule="one_se",
        family="gaussian",
        loss="rmse",
        scaling="dimension_sd",
        cv_unit="group",
        group_column="participant_id",
        random_state=2026,
    )

The inner loop chooses the FPC count. The outer test fold is untouched by FPCA fitting, regression fitting, and component selection.

The result retains:

- each outer-fold selected component count;
- each outer-fold loss;
- all inner loss summaries;
- outer held-out predictions;
- group assignments where relevant.

## Interpretation

Predictive selection answers:

> How many ordinary training-fold FPC scores were useful for prediction under this model, loss, candidate set, and fold design?

It does not establish:

- that the retained FPCs are causal;
- that the selected FPCs are the most interpretable;
- that the same count optimizes trajectory reconstruction;
- that the FPC directions themselves are supervised by the outcome;
- that grouped folds solve within-participant residual dependence.

## Final model

After the selection protocol is complete, the final full-data FPCA/regression can be fitted with the existing <code>fit_scalar_on_function_regression()</code> workflow using the selected component count.

Do not use the final full-data refit to revise the pre-specified selection rule.

## Reporting example

> The number of FPC predictors was tuned using participant-grouped five-fold cross-validation. FPCA centering, dimension scaling, eigenfunctions, and the scalar regression were re-estimated within each training fold. Candidate models containing one through five FPC scores were compared by held-out RMSE, and the pre-specified one-standard-error rule selected two FPCs. Predictive performance was then evaluated using an outer five-fold participant-grouped loop, with component selection repeated entirely within each outer training set.

## API links

- <code>cross_validate_fpca_regression()</code>
- <code>summarise_fpca_regression_cv()</code>
- <code>select_fpca_regression_components()</code>
- <code>nested_cross_validate_fpca_regression()</code>
- <code>plot_fpca_regression_cv()</code>
- <code>plot_nested_fpca_regression_cv()</code>
- <code>fpca_regression_cv_reporting_text()</code>
- <code>fpca_nested_regression_cv_reporting_text()</code>
- <code>fit_scalar_on_function_regression()</code>

## Methodological context

Functional principal-component regression routinely treats component-number selection as part of prediction rather than as a variance-explained decision. Existing functional-regression software also provides cross-validation for choosing the number of FPC predictors.

For binary outcomes, probability losses such as log loss and the Brier score retain information discarded by thresholded accuracy.
