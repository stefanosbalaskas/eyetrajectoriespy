# Worked example: participant-level simultaneous mean bands

This example estimates a population mean gaze trajectory when each participant contributes repeated trials.

The important design decision is made before inference:

> participants, not trials, are the independent sampling units.

## Generate repeated-trial trajectories

\`\`\`python
from eyetrajectoriespy import simulate_planar_trajectories

gaze = simulate_planar_trajectories(
    n_participants=20,
    trials_per_participant=4,
    n_time=81,
    random_state=2026,
)
\`\`\`

The synthetic data contain x(t), y(t) trajectories on a common normalized screen coordinate system.

## Fit a participant-level simultaneous band

\`\`\`python
from eyetrajectoriespy import multiplier_functional_mean_band

band = multiplier_functional_mean_band(
    gaze,
    confidence_level=0.95,
    n_multiplier=5000,
    unit="participant",
    participant_column="participant_id",
    random_state=2026,
)
\`\`\`

The function first averages each participant's four trials.

The multiplier bootstrap therefore sees 20 independent participant-average functions, not 80 independent trials.

## Inspect the result contract

\`\`\`python
print(band.n_units)
print(band.critical_value)
print(
    band.provenance["functional_mean_band"]
)
\`\`\`

Important provenance fields include:

- inference unit;
- participant column;
- number of effective units;
- curves per participant;
- estimand;
- multiplier count and seed;
- number of zero-variance grid points;
- observed-grid coverage target.

## Convert to a tidy table

\`\`\`python
from eyetrajectoriespy import functional_mean_band_frame

frame = functional_mean_band_frame(band)
print(frame.head())
\`\`\`

The table contains:

- time;
- dimension;
- mean;
- pointwise SE;
- lower simultaneous bound;
- upper simultaneous bound.

## Plot x(t)

\`\`\`python
from eyetrajectoriespy import plot_functional_mean_band

plot_functional_mean_band(
    band,
    dimension="x",
)
\`\`\`

Repeat for y(t). The same critical value was calibrated jointly across both dimensions and all sampled times.

## Why participant weighting matters

Imagine participant A contributes three usable trials and participant B contributes one.

A curve-weighted mean gives participant A three times the contribution of participant B.

Participant-level inference instead computes:

\[
\frac{1}{2}
\left[
\frac{X_{A1}(t)+X_{A2}(t)+X_{A3}(t)}{3}
+
X_{B1}(t)
\right].
\]

This is the estimand used by \`unit="participant"\`.

It is not silently interchangeable with the curve-weighted mean.

## Higher confidence produces a wider calibration

With the same data, multiplier count, and random seed:

\`\`\`python
band_90 = multiplier_functional_mean_band(
    gaze,
    confidence_level=0.90,
    n_multiplier=5000,
    unit="participant",
    participant_column="participant_id",
    random_state=2026,
)

band_99 = multiplier_functional_mean_band(
    gaze,
    confidence_level=0.99,
    n_multiplier=5000,
    unit="participant",
    participant_column="participant_id",
    random_state=2026,
)

assert band_99.critical_value >= band_90.critical_value
\`\`\`

## Reporting helper

\`\`\`python
from eyetrajectoriespy import functional_mean_band_reporting_text

print(
    functional_mean_band_reporting_text(band)
)
\`\`\`

The generated wording includes the effective sampling unit, estimand, confidence level, multiplier count, critical value, and the observed-grid coverage limitation.

## Failure case: repeated trials treated as curves

This is syntactically valid:

\`\`\`python
curve_band = multiplier_functional_mean_band(
    gaze,
    unit="curve",
)
\`\`\`

But it answers a different inferential question and assumes curves are independent units.

For this repeated-trial design it should **not** be used for a participant-population claim.

The package does not infer independence from column names; the analyst must select the sampling unit explicitly.

## Failure case: simplex-valued trajectories

Direct Euclidean bands on AOI probability functions are rejected.

Move to an explicitly justified compositional/log-ratio representation before applying Euclidean functional inference.

## Next steps

- [Simultaneous mean-band guide](../guides/simultaneous-mean-bands.md)
- [Assumptions and diagnostics](../methods/assumptions.md)
- [Reporting checklist](../methods/reporting.md)
- [Pre-registration checklist](../methods/preregistration.md)
