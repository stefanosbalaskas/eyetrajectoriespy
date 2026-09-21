# Simultaneous bands for functional mean trajectories

A functional mean is a time-varying estimand:

\[
\mu(t) = E\{X(t)\}.
\]

For multivariate gaze trajectories, the package treats the observed functional object as all requested dimensions over the same sampled time grid. A simultaneous band should therefore account for multiplicity across **time and functional dimensions**, not only provide separate pointwise intervals.

## What eyetrajectoriespy estimates

\`multiplier_functional_mean_band()\` uses a studentized Gaussian multiplier bootstrap for the empirical mean process.

At each bootstrap replication, Gaussian multipliers are applied to centered inference-unit trajectories. The calibration statistic is the maximum absolute standardized deviation over the complete observed time × dimension grid.

The returned band is:

\[
\hat\mu(t,d)
\pm
c_{1-\alpha}
\, \widehat{\operatorname{SE}}\{\hat\mu(t,d)\},
\]

where \(c_{1-\alpha}\) is the multiplier quantile of the gridwise maximum statistic.

This is not the same as drawing independent 95% intervals at every time point.

## Choose the inference unit before fitting

### Independent curves

If every trajectory is an independent sampling unit:

\`\`\`python
band = multiplier_functional_mean_band(
    gaze,
    confidence_level=0.95,
    n_multiplier=5000,
    unit="curve",
    random_state=2026,
)
\`\`\`

The estimand is the equal-weight mean across curves.

### Repeated trials within participant

If participants contribute repeated trials, those curves are not independent population units.

Use:

\`\`\`python
band = multiplier_functional_mean_band(
    gaze,
    confidence_level=0.95,
    n_multiplier=5000,
    unit="participant",
    participant_column="participant_id",
    random_state=2026,
)
\`\`\`

The package first averages each participant's observed trajectories and then applies mean inference to those participant-average functions.

The estimand becomes:

> the equal-weight population mean of participant-average trajectories.

Participants with more observed trials do **not** receive larger inferential weight.

!!! warning "Do not use curve-level inference for repeated trials merely to increase n"
    Treating repeated curves as independent can severely overstate effective sample size. Use the sampling unit that corresponds to the population claim.

## The band is simultaneous over the observed grid

The current implementation controls the maximum multiplier statistic across:

- every sampled time point; and
- every functional dimension in the \`TrajectorySet\`.

For x(t), y(t), a single critical value is therefore calibrated over both channels.

However, the implementation does **not** claim continuous-domain coverage between sampled grid points.

That distinction is recorded in provenance:

\`\`\`python
band.provenance["functional_mean_band"][
    "continuous_between_grid_points"
]
# False
\`\`\`

If continuous-domain inference is scientifically essential, use a method whose theoretical target and smoothing assumptions explicitly establish that coverage.

## Why studentize?

Different portions of a gaze trajectory can have very different variability.

The multiplier process is standardized by the empirical pointwise standard deviation before the maximum is taken. The final band then rescales by the pointwise standard error.

This prevents highly variable regions from automatically dominating the calibration statistic only because of their scale.

## Zero-variance locations

Some coordinates can be structurally constant across all inference units.

At such grid points:

- pointwise SE is zero;
- the band has exactly zero width;
- the location is excluded from division in the standardized multiplier statistic.

No epsilon noise is added.

## Number of multiplier draws

The API requires at least 100 draws but this is only a computational floor.

For a final analysis, use enough multiplier draws for the desired quantile resolution. Values such as 2,000–10,000 are common practical choices depending on computational cost and the confidence level.

Report the exact number and random seed.

## Probability-simplex trajectories

Direct Euclidean bands are rejected for \`coordinate_system="probability_simplex"\`.

A lower or upper Euclidean band for AOI probabilities can violate non-negativity and sum-to-one constraints.

Use an explicitly chosen compositional/log-ratio representation first if that is the intended estimand. The package does not silently change geometry.

## Interpretation

If a 95% simultaneous observed-grid band is narrow around a feature of the mean trajectory, that feature is estimated precisely under:

- the chosen inference unit;
- the observed common grid;
- the specified coordinate system;
- the multiplier approximation;
- the study's sampling design.

The band does **not** establish:

- causal effects;
- simultaneous coverage between sampled grid points;
- validity under informative missingness;
- independence of repeated trials when \`unit="curve"\`;
- compositional validity for probability-simplex trajectories;
- coverage for a condition difference unless a dedicated difference-of-means procedure is used.

## Reporting example

> The mean two-dimensional gaze trajectory was estimated using participant-level functional inference. Trial trajectories were first averaged within participant so each participant contributed one equal-weight functional unit. A 95% simultaneous band was calibrated across the full sampled time × coordinate grid using 5,000 Gaussian multiplier replicates and the maximum absolute studentized mean-process statistic. The procedure therefore controls multiplicity across the observed x(t) and y(t) grid jointly. The band was interpreted as an observed-grid simultaneous band rather than a continuous-domain confidence band between sampled time points.

Use \`functional_mean_band_reporting_text()\` as a reproducible starting point.

## API links

- \`multiplier_functional_mean_band()\`
- \`functional_mean_band_frame()\`
- \`plot_functional_mean_band()\`
- \`functional_mean_band_reporting_text()\`
- \`FunctionalMeanBandResult\`

## Methodological context

Simultaneous inference for functional mean functions is well established, with bootstrap, Gaussian-process, and other approximations used to calibrate supremum-type statistics. The present implementation intentionally targets the observed common grid and uses a Gaussian multiplier approximation rather than claiming a generic continuous-domain theorem.

See the [references](../methods/references.md) and the [worked example](../examples/functional-mean-bands.md).
