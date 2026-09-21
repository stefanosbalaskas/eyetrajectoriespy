# Simultaneous uncertainty bands for FPC shapes

Functional principal components are estimated functions. A pointwise bootstrap envelope can show local variation, but it does not calibrate the probability of an excursion somewhere along the full curve.

Use <code>bootstrap_fpca_component_bands()</code> when the scientific statement concerns the whole observed FPC function.

## What the method does

For every bootstrap replicate, eyetrajectoriespy:

1. resamples curves or participants;
2. refits FPCA using the same explicit scaling rule;
3. matches replicate FPCs to the full-sample reference by maximum absolute functional similarity;
4. sign-aligns each matched FPC;
5. estimates pointwise bootstrap standard errors;
6. computes the maximum absolute studentized deviation over the observed time × functional-dimension grid;
7. calibrates the requested simultaneous band from the empirical maximum distribution.

## Component-wise versus familywise calibration

Component-wise calibration gives each FPC its own whole-grid critical value:

    bands = bootstrap_fpca_component_bands(
        gaze,
        n_bootstrap=1000,
        n_components=3,
        confidence_level=0.95,
        simultaneous_scope="component",
        random_state=2026,
    )

Familywise calibration takes the maximum over the requested FPC set as well as the observed grid:

    family = bootstrap_fpca_component_bands(
        gaze,
        n_bootstrap=1000,
        n_components=3,
        confidence_level=0.95,
        simultaneous_scope="family",
        random_state=2026,
    )

The scope is part of the estimand and should be pre-specified and reported.

## Repeated trials: resample participants when participants are independent

    bands = bootstrap_fpca_component_bands(
        gaze,
        n_bootstrap=1000,
        n_components=2,
        scaling="dimension_sd",
        resample_unit="participant",
        participant_column="participant_id",
        confidence_level=0.95,
        simultaneous_scope="component",
        random_state=2026,
    )

Participant bootstrap resamples whole participant trial bundles rather than silently treating repeated trials as independent participants.

## Near-tied eigenvalues require an identification decision

Simultaneous uncertainty around an individual FPC axis is only scientifically useful when that axis is sufficiently identifiable.

The package does not impose a universal eigengap threshold. If a study pre-specifies one, pass it explicitly:

    bands = bootstrap_fpca_component_bands(
        gaze,
        n_bootstrap=1000,
        n_components=2,
        relative_gap_threshold=0.05,
        on_near_tie="error",
        random_state=2026,
    )

The screen fits one additional component so the retention boundary can be inspected. For each requested FPC it records the smallest adjacent relative eigengap.

Available actions are <code>error</code>, <code>warn</code>, and <code>ignore</code>. The default action is <code>error</code> when a threshold is supplied.

If no threshold is supplied, no numerical near-tie classification is made.

## Why matching is necessary but not sufficient

Matching and sign alignment prevent arbitrary sign flips and ordinary component swaps from contaminating bootstrap summaries.

They do not make a population eigenfunction uniquely identifiable when adjacent eigenvalues are nearly equal. In that case, use <code>fpca_eigenvalue_gap_table()</code>, <code>compare_fpca_subspaces()</code>, and <code>bootstrap_fpca_subspace_stability()</code>.

A stable eigenspace with unstable individual axes should be interpreted as a stable span, not as precise evidence for named FPC1/FPC2 directions.

## Observed-grid semantics

The maximum is calibrated over the finite time × dimension grid supplied to FPCA. The implementation does not by itself support a continuous-domain coverage statement between sampled time points.

## Degenerate grid cells

If bootstrap FPC estimates have essentially zero variability at a grid cell and agree with the reference, the band width there is zero. If variability is numerically zero but the bootstrap estimates have a non-negligible discrepancy from the reference, the function fails explicitly rather than adding an arbitrary epsilon.

## Interpretation

A narrow band suggests low resampling variability for the chosen FPC orientation under the specified sample, scaling, bootstrap unit, and calibration scope.

It does not establish causality, construct validity, preprocessing invariance, unique FPC identity under near-tied eigenvalues, exact finite-sample coverage, or coverage between sampled time points.

## Reporting example

> FPC-shape uncertainty was evaluated using 1,000 participant-level bootstrap resamples. Bootstrap FPCs were matched and sign-aligned to the full-sample reference. Ninety-five-percent studentized maximum-deviation bands were calibrated separately for each requested FPC over the observed time × x/y grid. A pre-specified relative-eigengap threshold of 0.05 was used as an identification screen; components meeting this criterion were interpreted at the eigenspace rather than individual-axis level.

## API links

- <code>bootstrap_fpca_component_bands()</code>
- <code>FPCAComponentBandResult</code>
- <code>fpca_component_band_frame()</code>
- <code>plot_fpca_component_band()</code>
- <code>fpca_component_band_reporting_text()</code>
- <code>bootstrap_fpca_component_envelopes()</code>
- <code>fpca_eigenvalue_gap_table()</code>
- <code>bootstrap_fpca_subspace_stability()</code>

## Methodological context

Hall and Hosseini-Nasab (2006) show that eigenvalue spacing has a first-order effect on eigenfunction estimation and discuss bootstrap simultaneous confidence regions for eigensystem quantities. Cai and Hu (2024) develop asymptotically correct simultaneous eigenfunction bands for dense functional data using B-spline smoothing.

The eyetrajectoriespy implementation is deliberately different: it uses matched/sign-aligned nonparametric resampling and an observed-grid studentized maximum. It should therefore be described by its actual algorithm rather than as an implementation of the Cai-Hu spline estimator.

See [References](../methods/references.md).
