# Simultaneous fixed-target FPCR wild-bootstrap inference

Version 0.18 adds an explicit familywise calibration layer for a **predeclared set of fixed Gaussian FPCR target trajectories**.

It does not replace or alter the 0.16 heteroscedastic wild-bootstrap generator. Instead, it reuses the studentized roots already stored by `wild_bootstrap_fpca_projection()`.

## Scientific question

The base 0.16 method answers:

> What is a target-wise confidence interval for the centered FPCR projection of each fixed target trajectory under heterogeneous response errors?

The 0.18 layer answers the stronger familywise question:

> What common calibration protects the complete declared target family against at least one interval miss?

This is a fixed-target familywise statement. It is not a joint future-outcome prediction region.

## Start from a qualified base result

    base = wild_bootstrap_fpca_projection(
        trajectories,
        outcome,
        targets=declared_targets,
        n_bootstrap=1000,
        residual_components=k,
        inference_components=h,
        multiplier="normal",
        confidence_level=0.95,
        random_state=2028,
    )

The base result already contains one studentized root for every bootstrap replicate and target.

Version 0.18 does not regenerate those roots.

## Max-|t| post-calibration

Let `T[b, j]` denote the studentized bootstrap root for bootstrap replicate `b` and target `j`.

For each bootstrap replicate, compute

    M[b] = max_j |T[b, j]|

The familywise critical value is the requested empirical quantile of `M`, using the same conservative `method="higher"` convention as the base target-wise calibration.

The simultaneous interval for target `j` is

    reference_projection[j] ± critical_value * reference_se[j]

Because every target-wise absolute root is bounded by the replicate-wise maximum, the resulting simultaneous interval cannot be narrower than the corresponding same-level target-wise interval apart from floating-point tolerance.

For a family containing exactly one target, the simultaneous and target-wise calibrations are identical.

## Declare the family before inspecting results

The family is **exactly all target trajectories stored in the supplied base result**.

To analyze a different family, construct a base result with that target set and then post-calibrate it.

Do not inspect target-wise intervals, remove inconvenient targets, and then describe the remaining family as if it had been predeclared. Changing the family changes the calibration target.

## Why reuse the same bootstrap roots?

All targets must be evaluated under the same bootstrap replicate to preserve their empirical dependence structure.

Running a separate bootstrap for each target and combining marginal critical values afterward would discard that coupling.

The 0.18 implementation therefore:

- reuses the exact base studentized-root matrix;
- performs no new random-number generation;
- does not refit FPCA or score regressions;
- does not re-estimate residuals;
- does not rerun the wild bootstrap.

## Target-wise versus simultaneous output

The result retains both:

- same-level target-wise critical values recomputed from each target's absolute roots;
- one familywise max-|t| critical value shared by all targets.

This makes the multiplicity cost visible rather than hiding it.

## Interaction with truncation selection

The simultaneous layer is conditional on the `k=g` and `h` settings in the supplied base result.

If `h` was selected using data-driven stabilized-volatility rules, that selection uncertainty is not propagated automatically into the simultaneous interval.

For confirmatory work, define the target family and truncation strategy before inspecting final intervals.

## Assumptions inherited from the base wild bootstrap

All 0.16 assumptions remain in force:

- functional regressors and FPCA/MFPCA score geometry are fixed during wild resampling;
- curve rows are independent sampling units;
- the scalar response model is Gaussian FPCR;
- residual/pseudo-truth truncation is `k=g`;
- inference uses explicit `h>=g`;
- multiplier choice is explicit;
- heteroscedastic studentization is recomputed inside each bootstrap pseudo-sample.

## What simultaneity does and does not cover

The familywise statement covers only the fixed target projections included in the base result.

It does **not** provide simultaneous coverage for:

- future observed scalar outcomes;
- target trajectories not in the declared family;
- preprocessing choices;
- data-driven component-selection uncertainty;
- repeated-participant or clustered wild-bootstrap dependence;
- non-Gaussian/binomial functional regression.

## Reporting checklist

Report:

1. the number and scientific definition of targets in the family;
2. the confidence level;
3. `k`, `g=k`, and `h`;
4. multiplier family and bootstrap replicate count;
5. the independent sampling unit;
6. that the FPCA basis/regressors were fixed;
7. that bootstrap-level heteroscedastic studentization was used;
8. the familywise max-|t| critical value;
9. that the same root matrix was reused without a second bootstrap;
10. that simultaneity is restricted to the declared fixed targets.

## API links

- `wild_bootstrap_fpca_projection()`
- `FPCAWildBootstrapProjectionResult`
- `FPCAWildBootstrapSimultaneousResult`
- `fpca_wild_bootstrap_projection_simultaneous_interval()`
- `fpca_wild_bootstrap_simultaneous_frame()`
- `plot_fpca_wild_bootstrap_simultaneous_interval()`
- `fpca_wild_bootstrap_simultaneous_reporting_text()`

See also [Heteroscedastic FPCR wild bootstrap](fpcr-wild-bootstrap.md), [Stabilized-volatility FPCR selection](fpcr-wild-bootstrap-selection.md), and [References](../methods/references.md).

## From simultaneous intervals to explicit tests

Version 0.19 uses the same declared fixed-target family and the same stored studentized root matrix to report target-wise bootstrap probabilities, single-step maxT-adjusted probabilities, and a complete-family global maximum-statistic test.

This is a separate evidence layer rather than a new bootstrap generator. It also makes the strong-FWER boundary explicit: the package does not assume subset pivotality or claim a closed/step-down procedure for arbitrary subsets of null hypotheses.

See [Fixed-family FPCR wild-bootstrap hypothesis tests](fpcr-wild-bootstrap-family-tests.md).
