# Fixed-family FPCR wild-bootstrap hypothesis tests

Version 0.19 adds explicit two-sided hypothesis testing for the same predeclared fixed-target families used by the heteroscedastic Gaussian FPCR wild-bootstrap interval workflow.

## Scientific question

For each fixed target trajectory j, define a null centered projection value m0_j.

The target-wise hypotheses are:

    H0_j: centered FPCR projection_j = m0_j

The default null value is zero, but a scalar null can be broadcast to every target or one finite null value can be supplied per target.

## Reuse the certified wild-bootstrap roots

Start with the 0.16 fixed-regressor wild-bootstrap result:

    base = wild_bootstrap_fpca_projection(
        trajectories,
        outcome,
        targets=declared_targets,
        n_bootstrap=1000,
        residual_components=k,
        inference_components=h,
        multiplier="normal",
        random_state=2029,
    )

Then test the complete family:

    tests = fpca_wild_bootstrap_projection_family_test(
        base,
        null_values=0.0,
        significance_level=0.05,
        pvalue_correction="plus_one",
    )

No FPCA fit, score regression, residual estimate, multiplier draw, or bootstrap replicate is recomputed.

## Observed studentized statistics

For target j, the observed statistic is the null discrepancy divided by the stored heteroscedastic reference standard error:

    T_j = (reference_projection_j - null_j) / reference_se_j

A zero standard error is accepted only when the null discrepancy is also numerically zero. A non-zero discrepancy with zero standard error fails explicitly instead of producing an infinite test statistic.

## Target-wise bootstrap p-values

For each target, the marginal bootstrap tail probability compares |T_j| with the absolute studentized roots already stored for that target.

With the default plus-one correction:

    p_j = (1 + number of bootstrap |T*_bj| >= |T_j|) / (B + 1)

This prevents a finite Monte Carlo run from returning p=0.

## Single-step maxT adjustment

For each bootstrap replicate b, compute:

    M_b = max_j |T*_bj|

The adjusted probability for target j compares |T_j| with the joint bootstrap distribution of M_b.

This is the same max-statistic geometry used by the 0.18 simultaneous interval calibration, now exposed as explicit hypothesis-test evidence.

## Complete-family global test

The global observed statistic is:

    T_global = max_j |T_j|

Its bootstrap p-value uses the M_b distribution.

The global null is that every declared target projection equals its supplied null value.

## Multiplicity claim boundary

The package calls these single-step maxT-adjusted bootstrap probabilities for the complete declared family.

It does not assert strong family-wise error control for every possible subset of null hypotheses. Such a claim generally needs additional conditions such as subset pivotality or a dedicated closed/step-down procedure.

The stored provenance therefore records:

- bootstrap roots reused: yes;
- null-enforced bootstrap: no;
- single-step familywise adjustment: yes;
- strong FWER for arbitrary subset nulls claimed: no;
- subset pivotality assumed by package: no.

## Plus-one versus uncorrected empirical tails

The default `pvalue_correction="plus_one"` uses `(r+1)/(B+1)`.

The explicit `pvalue_correction="none"` option reports the raw empirical exceedance fraction `r/B`. That option can produce zero with finite B and should be described as such.

## Monte Carlo precision of the finite bootstrap run

Version 0.20 can audit the finite-replicate precision of these target-wise, maxT-adjusted, and global bootstrap probabilities without changing the 0.19 test result.

Use:

    diagnostics = fpca_wild_bootstrap_family_test_monte_carlo_diagnostics(
        tests,
        confidence_level=0.95,
    )

The diagnostic reports exceedance counts, raw r/B fractions, plug-in binomial MCSEs, Clopper-Pearson exact intervals, and conservative decision-stability flags. The configured plus-one/raw p-values and rejection indicators remain unchanged.

See **Wild-bootstrap Monte Carlo precision** for the full contract, interpretation, optional-stopping boundary, reporting guidance, and worked example.

## What remains outside the contract

The 0.19 tests do not cover:

- future observed scalar outcomes;
- targets not included in the base result;
- repeated-participant or clustered wild-bootstrap dependence;
- target measurement error;
- preprocessing uncertainty;
- data-driven target-family selection;
- automatic propagation of k/h component-selection uncertainty;
- strong subset-wise FWER without additional assumptions;
- non-Gaussian/binomial functional regression.

## Reporting checklist

Report the target family, null values, two-sided alternative, alpha, bootstrap replicate count, k/g/h truncations, multiplier family, independent sampling unit, p-value correction, target-wise and maxT-adjusted probabilities, global max statistic/p-value, and the limitations above.

The full target statistic, plus-one tail probability, max-|t| adjustment, and global statistic are given in the [mathematical reference](../methods/mathematical-reference.md#fixed-family-wild-bootstrap-tests).

## API links

- `fpca_wild_bootstrap_projection_family_test()`
- `FPCAWildBootstrapFamilyTestResult`
- `fpca_wild_bootstrap_family_test_frame()`
- `plot_fpca_wild_bootstrap_family_test()`
- `fpca_wild_bootstrap_family_test_reporting_text()`
- `wild_bootstrap_fpca_projection()`
- `fpca_wild_bootstrap_projection_simultaneous_interval()`

See also [Simultaneous fixed-target FPCR wild-bootstrap inference](fpcr-wild-bootstrap-simultaneous.md) and [References](../methods/references.md).
