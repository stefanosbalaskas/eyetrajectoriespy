---
title: Observation-process diagnostics
---

# Observation-process diagnostics

Sparse eye-tracking data can be irregular for scientifically different reasons. A sample may be absent because the design never scheduled it, because the device failed to retain it, because quality control removed it, or because retention itself depends on time, task state, participant/trial structure, or prior gaze history. Those cases should not be collapsed into the same object.

The 1.1 A3 observation-process workflow is a **diagnostic-only** layer for asking whether the supplied retention process shows descriptive structure that challenges a simple non-informative-observation assumption. It does not alter sparse FPCA/MFPCA, classify the process as MAR or MNAR, impute missing gaze, or apply inverse-probability/intensity correction.

## The denominator is the scientific object

`IrregularTrajectorySet` contains retained samples. That is not enough to study retention because the rows that could have been observed are absent.

A3 therefore requires an explicit candidate-sample denominator: one row per scheduled/candidate sample, including at least

- curve/trial identifier;
- candidate time;
- binary retained/observed indicator;
- optional participant/group identifier;
- optional predictors available for **every** candidate row.

The package does **not** reconstruct candidate rows from timestamp gaps or a nominal sampling frequency. If the experiment/device protocol defines the schedule, supply that schedule explicitly.

```python
import pandas as pd

from eyetrajectoriespy.observation_process import (
    diagnose_observation_process,
    observation_process_data,
    observation_process_frame,
    observation_process_reporting_text,
)

candidate = pd.DataFrame(
    {
        "trial_id": ["t1"] * 6,
        "participant_id": ["p1"] * 6,
        "time": [0, 1, 2, 3, 4, 5],
        "retained": [1, 1, 0, 0, 1, 1],
        "condition": ["control"] * 6,
        "x": [0.40, 0.43, None, None, 0.52, 0.55],
        "y": [0.55, 0.54, None, None, 0.50, 0.48],
    }
)

process = observation_process_data(
    candidate,
    curve_column="trial_id",
    time_column="time",
    observed_column="retained",
    group_column="participant_id",
    candidate_predictors=("condition",),
    predictor_sources={"condition": "design"},
    coordinate_columns=("x", "y"),
    time_unit="s",
    coordinate_system="normalized",
)
```

The constructor validates uniqueness and increasing candidate time within curve, binary retention coding, predictor availability, and raw-coordinate semantics. When raw gaze coordinates are supplied, they must be finite on retained rows and missing on unretained rows.

## Candidate-time predictors versus gaze history

The distinction is deliberate.

### Candidate-time predictors

These are defined on every candidate row before knowing whether gaze was retained. Examples include candidate time, condition, stimulus state, trial metadata, device/status flags, and externally supplied geometry.

Declare their provenance with `predictor_sources`. A source is one of:

- `"candidate_time"`;
- `"design"`;
- `"external_candidate_time"`.

A complete externally supplied state variable may be used, but it should not be presented as a gaze value recovered from missing samples.

### History predictors

These are derived only from information observed **before** the current candidate sample. A3 can derive:

- `previous_observed_x`;
- `previous_observed_y`;
- `previous_observed_eccentricity`;
- `previous_observed_speed`;
- `time_since_last_observed`;
- `preceding_observed_run_length`;
- `preceding_missing_run_length`.

For eccentricity, the reference must be declared explicitly. No current/future gaze value is carried backward or interpolated into an unretained row.

```python
result = diagnose_observation_process(
    process,
    predictors=("condition",),
    history_predictors=(
        "previous_observed_x",
        "previous_observed_speed",
        "time_since_last_observed",
    ),
    eccentricity_reference=(0.5, 0.5),
    time_basis="linear",
    time_bins=4,
    association_bins=4,
)
```

## What is reported

### Denominator and support

The result retains exact candidate, observed, and missing counts/fractions globally and by curve/group, candidate versus retained support, candidate versus retained median sampling interval, and longest observed/missing runs.

Run lengths are meaningful only when adjacency in the supplied candidate schedule has a scientific interpretation.

### Time dependence

With `time_basis="linear"`, A3 reports a descriptive rank association between candidate time and the binary retention indicator. User-declared `time_bins` provide observation fractions over time without silently selecting a smoother or spline complexity.

### Candidate-predictor dependence

Numeric predictors retain observed-versus-missing means, a standardized mean difference, and a rank association with retention. Categorical predictors retain observation fractions across levels and their range. Optional declared bins expose numeric profiles.

These are **descriptive association summaries**, not participant-level inferential tests.

### Past-history dependence

History variables can be evaluated over all candidate rows with sufficient prior history, or within an explicit next-sample risk set:

```python
next_sample = diagnose_observation_process(
    process,
    predictors=(),
    history_predictors=("time_since_last_observed", "previous_observed_speed"),
    risk_set="after_observed",
    time_basis=None,
    association_bins=4,
)
```

`risk_set="after_observed"` includes a candidate row only when the immediately preceding candidate row in that curve was retained. This makes the denominator for a next-sample retention/dropout diagnostic explicit.

## Failure semantics

A3 fails closed for malformed denominator contracts and retains explicit diagnostic failures when a requested descriptive summary is unavailable. Examples include

- duplicated/non-monotone candidate schedules;
- non-binary retention indicators;
- candidate predictors unavailable on missing rows;
- raw coordinates supplied on unretained rows;
- constant/non-finite predictors;
- history requests without sufficient prior observations;
- coordinate history without raw retained coordinates;
- eccentricity without a declared reference.

Use

```python
observation_process_frame(result, table="failures")
```

to inspect retained failures rather than silently dropping them.

Available tables are `global`, `curves`, `groups`, `time`, `associations`, `profiles`, `failures`, and `candidates`.

## Repeated data and inference boundary

Candidate samples within a curve are dependent, and repeated trials within a participant are dependent. A3 therefore does not report naive row-level standard errors or p-values. Participant/group identifiers are retained for audit and future separately qualified dependence-aware procedures.

An observed association with retention does **not** identify a Rubin MAR/MNAR mechanism. Conversely, failure to detect a descriptive association does not prove that observation is non-informative.

## Reporting

```python
print(observation_process_reporting_text(result))
```

The reporting helper names the explicit denominator, missing fraction, declared grouping, estimable predictors/failures, and the descriptive-only scope. Its final sentence explicitly states that A3 does not provide iid sample-level inference, MAR/MNAR classification, current-gaze imputation, or inverse-probability/intensity correction.

## Relationship to sparse FPCA/MFPCA

A3 is a diagnostic layer beside the sparse estimators, not a hidden preprocessing step. `fit_sparse_fpca()` and `fit_sparse_mfpca()` are unchanged. No diagnostic output is automatically converted to a weight, deletion rule, corrected score, or modified covariance estimate.

If these diagnostics show strong observation-process dependence, the appropriate response in A3 is to **report and sensitivity-audit that limitation**. A correction estimator would require a separate estimand, positivity/support assumptions, weight/truncation policy, known-truth recovery, and sensitivity qualification.

## Qualification scope

The dedicated `observation-process-validation` workflow checks three known-truth regimes:

1. MCAR/null retention, where time and past-state diagnostics should remain near null within Monte Carlo tolerance;
2. contiguous block loss, where per-curve missing-run structure should recover the known block exactly;
3. a simulation-only logistic candidate-time retention process with exact per-candidate retention probabilities, where diagnostics should recover the direction and time-bin pattern and empirical bin fractions should calibrate to the known probabilities.

The qualification also checks denominator identities, participant grouping, deterministic replay, absence of naive p-values, and that no sparse estimator, missing-gaze imputation, or correction procedure is activated.

See the [A3 validation record](../validation/observation-process-validation.md).
