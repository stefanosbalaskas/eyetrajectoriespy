# W3 missing gaze and irregular sampling: fail-closed workflow contract

!!! warning "Source-data integrity, not an inferred missingness correction"
    The unpublished W3 observed-grid function-on-scalar regression
    requires *finite, complete trajectories on a common time grid*.
    The package may represent missing gaze with `np.nan` or native
    curve-specific times with `IrregularTrajectorySet`, but merely
    representing those data does **not** make W3 complete-grid OLS
    statistically valid for them.

## Why this matters in real eye-tracking studies

Missing gaze arises from blinks, off-screen periods, track loss, sensor
geometry, calibration problems and task behavior. Timing can also
differ between participants or trials. Automatically interpolating
through missing observations—or silently dropping affected trials—
can change an estimand and may induce systematic selection bias.
The appropriate response depends on the observed-data mechanism,
measurement quality and scientific question, not only whether
interpolation is computationally possible.

The W3 workflow therefore **does not silently interpolate, impute,
regrid, zero-fill, smooth or exclude** trajectories.

## Explicit input behavior

- **Complete finite `TrajectorySet`:** the existing W3 function-on-scalar
  workflow proceeds without extra preprocessing or model selection.
- **Common grid with any `nan` or infinite value:** fail early
  with a `ValueError` that reports the number of non-finite source
  values. All original curves and metadata remain unchanged.
- **`IrregularTrajectorySet`:** fail early with an explicit `TypeError`
  naming the unsupported layout and the need for a *separately
  qualified* sparse/irregular workflow. No regridding occurs.
- **Other inputs:** preserve the original documented `TrajectorySet`
  type contract.

Use the already supported descriptive audit:

```python
from eyetrajectoriespy.workflows.experimental import workflow_preflight

audit = workflow_preflight(
    gaze,
    participant_column="participant_id",
    trial_column="trial_id",
    required_dimensions=("x", "y"),
    require_common_grid=True,
)
print(audit.summary)
print(audit.curve_support)
print(audit.warnings)
print(audit.blocking_issues)
```

The preflight reports support/missingness and records
`input_modified=False`, `automatic_exclusions=False`.
**Preflight `ready=True` is not a certification of statistical
identification, complete-case validity, nominal uncertainty coverage
or W3 function-on-scalar eligibility.** A common-grid object may
still contain `np.nan` and be rejected by W3.

A researcher may consider a scientifically justified sensitivity
analysis using a preprocessed common-grid dataset, or choose a
separately qualified sparse/irregular scientific method appropriate
for the estimand. Neither option is automatically chosen or
validated by W3. The underlying *published* 1.1 estimator remains
unchanged; this is a clearer workflow-level error contract.

## Evidence and inference restrictions

Dedicated negative and positive tests verify `nan`, `+inf`,
`-inf`, irregular native times, unchanged input values and curve
counts, descriptive preflight semantics, and exact continued success
on finite common-grid data.

This is a **functional usability and measurement-integrity
improvement**, not a missing-data estimator, a MAR/MNAR identification
claim, or interval calibration. The [independent W3 uncertainty
programme](w3-fresh-192-block-confirmation-results.md) found a
specific limitation in the original fixed-HC1 simultaneous bands.
Scientific blocker [#289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289)
must remain OPEN regardless of success of these fail-closed tests.

Published stable **1.1.0** remains available. Unreleased 1.2 source
is still **`1.2.0rc2.dev0`** with
`production_release_ready=false`. No literal RC, release tag,
or PyPI action follows.
