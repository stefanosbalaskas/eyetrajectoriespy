# Functional outliers and FPCA influence

![Illustrative FPCA review diagnostic scatter](../assets/outlier-influence.svg)

*Illustrative synthetic diagnostic geometry. A review flag identifies a trajectory to inspect; it is not an exclusion command.*


Functional trajectories can be unusual for several different reasons:

- a genuine but rare viewing strategy;
- stimulus/layout mismatch;
- tracker failure or preprocessing artifact;
- an influential participant whose curves strongly shape the FPCA basis;
- ordinary tail variation.

These are not interchangeable. **An outlier flag is not an exclusion rule.**

## Two complementary FPCA diagnostics

`diagnose_fpca_outliers()` combines two views of the same fitted sample.

### Reconstruction behavior

The fitted FPC basis is used to reconstruct each trajectory. Integrated reconstruction RMSE is converted to a robust modified-z score.

A large reconstruction error means the retained basis represents that trajectory poorly.

### Score-space behavior

Retained FPC scores are evaluated with squared Mahalanobis distance. The default covariance estimate is Minimum Covariance Determinant, which is more resistant to extreme score vectors than the ordinary empirical covariance.

A trajectory can have a small reconstruction error but still be extreme in score space because the FPCA basis itself may have adapted to it.

That is why the package reports both diagnostics.

    result = diagnose_fpca_outliers(
        fit,
        gaze,
        n_components=4,
        reconstruction_z_threshold=3.5,
        score_alpha=0.99,
        score_covariance="robust",
        random_state=2026,
    )

    result.diagnostics

The output contains separate `reconstruction_flag`, `score_flag`, and combined `review_flag` columns.

!!! danger
    `review_flag=True` means **inspect this trajectory**. It does not mean delete it.

## Participant-aware influence

Repeated eye-tracking trials make curve-level leave-one-out analysis misleading when many curves come from the same participant.

Use:

    influence = leave_one_group_out_fpca_influence(
        gaze,
        group_column="participant_id",
        n_components=3,
        scaling="dimension_sd",
    )

Every participant is omitted as a block and FPCA is refitted.

The refitted components are matched to the full-sample reference components by maximum absolute functional similarity.

The summary reports:

- minimum matched component similarity;
- mean matched component similarity;
- maximum absolute explained-variance change;
- mean absolute explained-variance change;
- a descriptive influence score, defined as one minus the minimum matched similarity.

## When influence matters

A participant can be influential without being invalid.

Large influence can indicate:

- a genuine rare strategy;
- a subgroup not represented elsewhere;
- condition imbalance;
- stimulus-specific behavior;
- processing failure;
- insufficient sample size for a stable covariance estimate.

Inspect the trajectory and study metadata before drawing conclusions.

## Optional functional-depth backends

The `fda` optional dependency exposes scikit-fda functional outlier methods:

    result = detect_functional_outliers_skfda(
        gaze,
        dimension="x",
        method="boxplot",
        factor=1.5,
    )

Available wrappers are:

- `method="boxplot"`: functional boxplot screening;
- `method="msplot"`: magnitude-shape directional-outlyingness screening.

These methods answer a different question from FPCA score-space diagnostics and can be used as sensitivity analyses.

## Recommended manuscript workflow

1. Apply acquisition/QC exclusions using rules defined independently of the functional results.
2. Fit the planned FPCA.
3. Inspect reconstruction and score-space review diagnostics.
4. Run participant-level influence when trials are repeated within people.
5. Investigate flagged/influential cases using raw/preprocessed data and metadata.
6. Refit only as a documented sensitivity analysis if exclusion is scientifically justified.
7. Report whether substantive conclusions changed.

## What not to do

Do not:

- remove every curve flagged by an algorithm;
- tune thresholds until a desired condition effect appears;
- treat a rare trajectory as measurement error without evidence;
- run curve-level omission when participant-level dependence is the relevant unit;
- call a robust-distance cutoff a formal hypothesis test.


## Reporting example

> Functional trajectory diagnostics were conducted after the pre-specified acquisition/QC rules and did not determine exclusions. Using four retained FPCs, trajectories were screened with integrated reconstruction error and robust Mahalanobis distance in FPC-score space. Flagged trajectories were reviewed against the preprocessed gaze data and study metadata. Participant-level leave-one-out refits were then used to assess influence on the matched FPC structure. Any sensitivity exclusion was reported separately together with its independent substantive or quality justification.

Report the actual component count, covariance estimator, review thresholds, number of review flags, omission unit, and whether substantive conclusions changed.

## Related API and guidance

- [Functional outlier and influence API](../reference/api.md#functional-outliers-and-influence)
- [Worked anomaly/influence example](../examples/outlier-influence.md)
- [Reporting checklist](../methods/reporting.md)
- [Pre-registration checklist](../methods/preregistration.md)


## Split-conformal anomaly review for genuinely new curves

The original FPCA outlier diagnostics answer an **in-sample review** question: which curves in the fitted sample look unusual?

Split conformal inference answers a different question: is a **new target curve** unusual relative to a reference population?

Use three disjoint objects:

    result = split_conformal_fpca_anomaly(
        proper_training,
        calibration,
        targets,
        n_components=3,
        scaling="dimension_sd",
        nonconformity="reconstruction_rmse",
        alpha=0.05,
    )

The reference FPCA is estimated only from <code>proper_training</code>.

Calibration and target curves are scored through that fixed reference.

### Reconstruction nonconformity

<code>nonconformity="reconstruction_rmse"</code> uses integrated reconstruction RMSE under the retained FPC span.

It is useful for shape or structure that the proper-training basis represents poorly.

### Score-space Mahalanobis nonconformity

For a curve that lies inside the retained FPC span but has an unusually extreme score combination, use:

    result = split_conformal_fpca_anomaly(
        proper_training,
        calibration,
        targets,
        n_components=3,
        nonconformity="score_mahalanobis",
        mahalanobis_covariance="robust",
        random_state=2026,
    )

The covariance estimator must be chosen explicitly as <code>"empirical"</code> or <code>"robust"</code>. The package does not choose one silently.

### Marginal conformal p-values

For each target score \(s(X^*)\),

\[
\hat p(X^*) =
\frac{1 + |\{i \in I_{\mathrm{calib}}: s(X_i) \ge s(X^*)\}|}
{n_{\mathrm{calib}}+1}.
\]

The minimum attainable p-value is therefore (1/(n_{calib}+1)).

Small calibration sets can make conventional alpha levels unattainable.

### Review, never automatic deletion

<code>review_flag=True</code> means only that the marginal conformal p-value is at or below the requested alpha threshold.

It does not authorize removal from a scientific dataset.

### Exchangeability boundary

The marginal conformal guarantee assumes exchangeable inlier curves relative to the calibration population.

Repeated trials from the same participant are not made independent by calling this function.

For participant-clustered designs, do not claim curve-level conformal validity without a defensible independent-unit construction.

See [Conformal FPCA anomaly review](conformal-fpca-anomaly.md).
