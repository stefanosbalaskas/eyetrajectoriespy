# Quick start

## 1. Build a canonical trajectory set

```python
from eyetrajectoriespy import from_long_dataframe

gaze = from_long_dataframe(
    samples,
    curve_columns=["participant_id", "trial_id"],
    time_column="time_s",
    value_columns=["x", "y"],
    metadata_columns=["condition", "stimulus_id"],
    coordinate_system="normalized",
    time_unit="s",
)
```

The constructor does **not** smooth, interpolate, normalize time, or average duplicate timestamps.

## 2. Inspect the representation

```python
from eyetrajectoriespy import summarise_trajectory_set
print(summarise_trajectory_set(gaze))
```

## Sparse irregular data: do not manufacture a dense curve

If interpolation would create much of the analyzed trajectory, keep the native
`IrregularTrajectorySet` and use the optional sparse backend:

```python
summary = sparse_dimension_summary(
    irregular,
    dimension="x",
)

sparse_fit = fit_sparse_fpca_fdapy(
    irregular,
    dimension="x",
    n_components=3,
    fit_smoothing="PS",
    score_smoothing="LP",
    tol=1e-4,
)
```

Install FDApy interoperability with `pip install -e ".[sparse]"`. Under the
currently validated FDApy/NumPy dependency line this optional extra is enabled
for Python 3.11–3.12, while the eyetrajectoriespy core remains Python 3.11–3.13.

This is **univariate sparse PACE** for the selected dimension. Separate x(t)
and y(t) fits are not joint planar MFPCA.

## 3. Fit joint x/y MFPCA

```python
from eyetrajectoriespy import fit_mfpca, summarise_fpca

fit = fit_mfpca(gaze, n_components=0.95, scaling="dimension_sd")
print(summarise_fpca(fit))
```

## 4. Interpret functions, not only scores

```python
from eyetrajectoriespy import plot_fpca_component
plot_fpca_component(fit, component=0, dimension="x")
plot_fpca_component(fit, component=0, dimension="y")
```

!!! warning
    Do not call an FPC “attention,” “verification,” or another psychological construct solely because its geometry looks plausible. Interpret against the experimental design and, when possible, validate against external behavior.


## 5. Select dimension without leakage

For repeated trials, keep each participant in one held-out fold:

    cv = cross_validate_fpca_reconstruction(
        gaze,
        candidate_components=(1, 2, 3, 4, 5),
        n_splits=5,
        scaling="dimension_sd",
        cv_unit="group",
        group_column="participant_id",
    )

    selected = select_fpca_components_cv(cv, rule="one_se")

The FPCA basis is re-estimated inside each training fold. The one-SE rule is a parsimony heuristic rather than a significance test.

## 6. Tune FPC count for an external outcome

When prediction is the goal, tune the ordinary FPC regression inside folds rather than reusing the reconstruction-selected count:

    predictive = cross_validate_fpca_regression(
        gaze,
        outcome,
        candidate_components=(1, 2, 3, 4),
        loss="rmse",
        cv_unit="group",
        group_column="participant_id",
    )

    selected_for_prediction = select_fpca_regression_components(
        predictive,
        rule="one_se",
    )

Use nested_cross_validate_fpca_regression() when predictive performance itself will be reported.

## 7. Validate before labeling components

For repeated trials, use participant-level bootstrap:

    stability = bootstrap_fpca_stability(
        gaze,
        n_bootstrap=200,
        n_components=3,
        scaling="dimension_sd",
        resample_unit="participant",
        participant_column="participant_id",
        random_state=2026,
    )

    print(summarise_fpca_stability(stability))

Use the stability result to qualify component interpretation rather than to create a new significance test.

## If your trials are irregularly sampled

Do not force them through <code>from_long_dataframe()</code>. Start with <code>from_irregular_long_dataframe_native()</code>, inspect the native sampling, and only then choose the common-grid projection.


## 8. Diagnose near-tied component blocks

If adjacent FPCs swap or rotate across resamples:

    gaps = fpca_eigenvalue_gap_table(fit)

    subspace = bootstrap_fpca_subspace_stability(
        gaze,
        start_component=0,
        n_components=2,
        n_bootstrap=200,
        scaling="dimension_sd",
        resample_unit="participant",
        participant_column="participant_id",
        random_state=2026,
    )

Interpret a stable block as a reproducible functional span, not as proof that the individual axes inside it are uniquely identifiable.

## 9. Review functional anomalies and influence without deleting data

    review = diagnose_fpca_outliers(
        fit,
        gaze,
        n_components=3,
        random_state=2026,
    )

    influence = leave_one_group_out_fpca_influence(
        gaze,
        group_column="participant_id",
        n_components=3,
        scaling="dimension_sd",
    )

A review flag or influential participant is a prompt to inspect the functional data and metadata. It is not an exclusion command.


## Simultaneous uncertainty for an FPC shape

Use simultaneous FPC bands when the scientific statement concerns the whole observed FPC curve rather than isolated time points.

    from eyetrajectoriespy import bootstrap_fpca_component_bands

    bands = bootstrap_fpca_component_bands(
        gaze,
        n_bootstrap=500,
        n_components=2,
        scaling="dimension_sd",
        resample_unit="participant",
        participant_column="participant_id",
        confidence_level=0.95,
        simultaneous_scope="component",
        random_state=2026,
    )

For a joint familywise statement across all requested FPCs, set <code>simultaneous_scope="family"</code>. If the study pre-specifies a descriptive near-tie threshold, pass it through <code>relative_gap_threshold</code>; the default action is to stop rather than silently interpret a weakly identified individual axis.

See [Simultaneous FPC-shape bands](guides/simultaneous-fpc-bands.md).


## Quantify uncertainty in the FPCA spectrum

Use spectrum uncertainty when eigenvalues or variance-explained summaries are being interpreted rather than treated as fixed sample quantities.

    from eyetrajectoriespy import bootstrap_fpca_spectrum_uncertainty

    spectrum = bootstrap_fpca_spectrum_uncertainty(
        gaze,
        n_bootstrap=1000,
        n_components=3,
        scaling="dimension_sd",
        resample_unit="participant",
        participant_column="participant_id",
        confidence_level=0.95,
        simultaneous_scope="family",
        random_state=2026,
    )

Individual eigenvalues and per-component explained-variance ratios are attached to matched reference-FPC identities. Cumulative explained variance deliberately stays in descending eigenvalue rank so that “top k components explain …” keeps its conventional meaning.

Familywise calibration is across the requested components separately within each spectrum metric; it is not one joint guarantee spanning eigenvalues, explained-variance ratios, and cumulative ratios.

See [FPCA spectrum uncertainty](guides/spectrum-uncertainty.md).


## Quantify sensitivity of FPC scores to basis estimation

Use score uncertainty when individual FPC scores are scientifically interpreted or passed to a downstream analysis and you need to know how much they move when the FPCA basis is re-estimated.

    from eyetrajectoriespy import bootstrap_fpca_score_uncertainty

    score_uncertainty = bootstrap_fpca_score_uncertainty(
        gaze,
        targets=gaze.subset([0, 1, 2, 3]),
        n_bootstrap=1000,
        n_components=2,
        scaling="dimension_sd",
        resample_unit="participant",
        participant_column="participant_id",
        level=0.95,
        random_state=2026,
    )

The target curves stay fixed. Only the training sample used to estimate the FPCA basis is resampled. Bootstrap components are matched and sign-aligned before the same targets are projected into each basis.

The returned percentile envelopes therefore describe **basis-resampling uncertainty**, not full uncertainty in a latent score. They do not include measurement error, future-curve variability, preprocessing uncertainty, or full propagation through a downstream regression.

See [FPC score basis uncertainty](guides/score-uncertainty.md).


## Propagate FPCA estimation through Gaussian scalar regression

Use the paired FPCR bootstrap when a scalar outcome is modeled from continuous gaze and the functional slope or fitted mean response needs uncertainty that reflects re-estimation of the FPCA basis.

    from eyetrajectoriespy import bootstrap_fpca_regression_uncertainty

    inference = bootstrap_fpca_regression_uncertainty(
        gaze,
        outcome,
        targets=gaze.subset([0, 1, 2, 3]),
        n_bootstrap=1000,
        n_components=2,
        scaling="dimension_sd",
        resample_unit="participant",
        participant_column="participant_id",
        level=0.95,
        random_state=2026,
    )

Each bootstrap replicate resamples the independent unit together with its scalar outcome, refits FPCA/MFPCA, refits the Gaussian score regression, reconstructs the slope, and predicts the same fixed targets.

The slope envelope is pointwise. Target intervals describe uncertainty in the fitted **conditional mean response** and are not prediction intervals for a future noisy outcome.

The component count is kept fixed across bootstrap replicates. If the number of components was selected from data, report that selection procedure separately.

See [Gaussian FPCR bootstrap uncertainty](guides/fpcr-bootstrap-inference.md).


## Calibrate simultaneous uncertainty for the Gaussian FPCR slope

After fitting the paired-bootstrap FPCR uncertainty object, reuse its exact slope replicates to obtain a simultaneous band over the sampled slope grid.

    from eyetrajectoriespy import fpca_regression_slope_simultaneous_band

    band = fpca_regression_slope_simultaneous_band(
        inference,
        confidence_level=0.95,
        simultaneous_scope="global",
    )

With <code>simultaneous_scope="global"</code>, one studentized maximum is taken over all sampled time points and functional dimensions.

With <code>simultaneous_scope="dimension"</code>, each functional dimension gets its own maximum over sampled time.

The band is simultaneous only over the observed grid represented by the fit. It does not claim coverage between grid points and it is not the operator-scaled FPCR significance test from recent 2026 theory.

See [Gaussian FPCR simultaneous slope bands](guides/fpcr-simultaneous-slope-band.md).


## Predict a future observed scalar outcome

The 0.12 paired FPCR bootstrap returns uncertainty in the fitted conditional mean response. A future observed outcome also contains response noise.

Use the 0.14 predictive layer when that distinction is scientifically relevant:

    from eyetrajectoriespy import fpca_regression_future_prediction_interval

    future = fpca_regression_future_prediction_interval(
        inference,
        outcome,
        confidence_level=0.95,
        random_state=2026,
    )

The function reuses the exact paired-bootstrap conditional-mean predictions in <code>inference</code> and independently samples centered residuals from the full-sample Gaussian FPCR fit.

This assumes an exchangeable/common residual distribution. It is not heteroscedasticity-robust, and intervals are marginal per target rather than simultaneous or joint across several targets.

See [Gaussian FPCR future-outcome prediction](guides/fpcr-future-prediction.md).


## Review a genuinely new trajectory with split conformal inference

When the question is whether a **new** functional trajectory is unusual relative to a reference population, keep proper training and calibration separate:

    from eyetrajectoriespy import split_conformal_fpca_anomaly

    result = split_conformal_fpca_anomaly(
        proper_training,
        calibration,
        targets,
        n_components=3,
        scaling="dimension_sd",
        nonconformity="reconstruction_rmse",
        alpha=0.05,
    )

The FPCA/MFPCA basis is fitted only on <code>proper_training</code>. Calibration and target curves are scored without refitting that basis.

For a target score (s^*), the marginal conformal p-value is

[
hat p = rac{1 + #{s_i^{calib} ge s^*}}{n_{calib}+1}.
]

The greater-than-or-equal rule is intentionally conservative under ties.

A review flag is not an exclusion decision. This first conformal API does not apply calibration-conditional adjustment, BH/FDR correction, or repeated-participant clustering.

See [Conformal FPCA anomaly review](guides/conformal-fpca-anomaly.md).


## Heteroscedastic Gaussian FPCR projection inference

When the scientific target is the centered FPCR projection for fixed trajectories and response variance may depend on the functional predictor, use the fixed-regressor wild-bootstrap layer:

    from eyetrajectoriespy import wild_bootstrap_fpca_projection

    wild = wild_bootstrap_fpca_projection(
        gaze,
        outcome,
        targets=gaze.subset([0, 1, 2, 3]),
        n_bootstrap=1000,
        residual_components=2,
        inference_components=3,
        scaling="dimension_sd",
        multiplier="normal",
        confidence_level=0.95,
        independent_unit_column="participant_id",
        random_state=2026,
    )

The functional regressors and FPCA/MFPCA basis remain fixed. Residuals and the bootstrap pseudo-truth use k=g components; the target projection uses h components with h>=g.

Every bootstrap root is studentized using a heteroscedastic score-covariance scale recomputed from that pseudo-fit.

This API currently requires independent curve rows. If the declared independent-unit column contains duplicates, it stops rather than silently treating repeated trials as independent.

The interval targets the centered functional projection relative to the training functional mean. It is not a future-outcome prediction interval and is not simultaneous across targets.

See [Heteroscedastic FPCR wild bootstrap](guides/fpcr-wild-bootstrap.md).


## Select the wild-bootstrap inference truncation by stabilized volatility

When k has been fixed, for example from a prediction-oriented FPCR cross-validation analysis, scan a consecutive set of candidate h values using the same wild multiplier draws:

    from eyetrajectoriespy import (
        scan_wild_bootstrap_fpca_truncations,
        select_fpca_wild_bootstrap_truncation,
    )

    scan = scan_wild_bootstrap_fpca_truncations(
        gaze,
        outcome,
        targets=gaze.subset([0, 1, 2, 3]),
        candidate_components=(2, 3, 4, 5, 6),
        n_bootstrap=1000,
        residual_components=2,
        scaling="dimension_sd",
        multiplier="normal",
        confidence_level=0.95,
        independent_unit_column="participant_id",
        random_state=2027,
    )

    selected = select_fpca_wild_bootstrap_truncation(
        scan,
        width_threshold=0.15,
        center_threshold=0.10,
        stability_run=1,
    )

The selector compares the absolute change in interval width and center between adjacent h values. Both changes must remain below the declared thresholds.

The argument <code>stability_run</code> is the paper's r. Thus r=1 requires two consecutive stable transitions.

Thresholds are absolute and inherit the scalar outcome's units. eyetrajectoriespy therefore does not silently use the paper's simulation setting of 0.01.

If no qualifying run exists, selection fails by default rather than choosing the largest h.

See [Stabilized-volatility FPCR truncation selection](guides/fpcr-wild-bootstrap-selection.md).
