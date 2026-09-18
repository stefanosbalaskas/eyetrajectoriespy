# Sparse irregular FPCA: when projection is not enough

Irregular sampling and sparse sampling are related but different problems.

## Dense irregular trajectories

A trial may have many observations but at slightly different times than other trials.

In that case, preserving the native grids and then applying a documented common-grid projection can be reasonable:

    irregular = from_irregular_long_dataframe_native(...)
    grid = make_common_grid(irregular, n_time=121, domain="overlap")
    gaze = resample_irregular_to_grid(
        irregular,
        grid,
        max_gap=0.10,
    )

## Sparse irregular trajectories

A sparse trajectory may contain only a small number of observations over the full trial window.

For those data, ordinary interpolation can fabricate a large fraction of the curve. The scientific problem is no longer simply “choose a common grid.”

Sparse functional methods instead estimate population mean/covariance structure from pooled irregular observations and recover subject/curve scores conditionally.

PACE is a canonical example.

## Package boundary

`eyetrajectoriespy` currently preserves sparse/irregular observations through `IrregularTrajectorySet`, but it does **not** silently convert sparse data into dense FPCA input.

General FDA packages provide specialist sparse-FPCA implementations. FDApy, for example, documents sparse UFPCA workflows and PACE score estimation.

This separation is intentional:

- eye-tracking semantics, provenance, timing, and coordinate contracts remain in `eyetrajectoriespy`;
- specialist sparse covariance estimation remains in a specialist FDA backend until interoperability can be validated against the package's supported Python/runtime matrix.

## When common-grid projection is reasonable

Common-grid projection is most defensible when trajectories are densely observed, native time support overlaps substantially, and interpolation fills relatively small gaps rather than constructing most of the curve.

## When a sparse functional estimator is preferable

Prefer a specialist sparse-FDA estimator when observation counts are low, time support differs strongly across curves, measurement error is material, or interpolation would create a substantial fraction of the analyzed function.

## Decision rule

Ask:

**Do I have enough actual observations per trajectory that interpolation is a minor representation step, or would interpolation create most of the curve?**

If interpolation is doing most of the work, use a sparse functional estimator rather than pretending the trajectory was densely observed.

## Report

For sparse functional analyses report:

- observations per curve;
- native time-domain coverage;
- measurement-error assumption;
- mean/covariance smoothing method;
- smoothing/bandwidth parameters;
- score-recovery method;
- number of retained components;
- sensitivity to estimator tuning.


## Related API and guidance

- [Native irregular trajectory API](../reference/api.md#native-and-common-grid-import)
- [Native irregular trajectories guide](irregular-trajectories.md)
- [Worked irregular-sampling example](../examples/native-irregular.md)
- [Assumptions and diagnostics](../methods/assumptions.md)
