# Monte Carlo precision for fixed-family FPCR wild-bootstrap tests

Version 0.20 adds a diagnostic layer for the finite number of bootstrap replicates used by the 0.19 fixed-family hypothesis-test workflow.

The diagnostic answers a narrow computational question: if the fitted model, observed statistics, target family, bootstrap design, and retained bootstrap roots are held fixed, how precisely has the relevant bootstrap exceedance probability been estimated with the available number of replicates?

It does **not** add a new scientific sampling model, rerun the bootstrap, or strengthen the multiplicity guarantee.

## Why this matters

A bootstrap p-value is computed from a finite number of simulated replicates. With only B replicates, the observed number of exceedances is discrete and subject to Monte Carlo variability.

Version 0.19 defaults to the plus-one rule

    p = (r + 1) / (B + 1)

where r is the number of bootstrap statistics at least as extreme as the observed statistic. That rule remains the reported test probability and prevents a finite Monte Carlo run from returning zero.

Version 0.20 separately exposes the raw exceedance fraction

    q_hat = r / B

as a **Monte Carlo diagnostic quantity**. The diagnostic never substitutes q_hat for the reported plus-one p-value.

## Exact binomial precision interval

Conditional on the observed statistic and the fixed bootstrap design, the exceedance indicators across independently generated bootstrap replicates are treated as Bernoulli draws.

For each target-wise tail, each maxT-adjusted tail, and the complete-family global max statistic, the API reports:

- the exceedance count r;
- the raw exceedance fraction r/B;
- the plug-in binomial Monte Carlo standard error;
- a Clopper-Pearson exact binomial interval for the underlying exceedance probability.

The default diagnostic confidence level is 95%.

The Clopper-Pearson interval is intentionally conservative. It remains defined when the observed count is 0 or B, where the simple plug-in MCSE can be zero despite substantial finite-simulation uncertainty.

## Decision-stability diagnostic

The original 0.19 rejection indicator is never recomputed from the diagnostic interval.

Instead, version 0.20 reports whether finite-bootstrap Monte Carlo uncertainty is clearly on the same side of the declared alpha threshold as the **already reported** test decision.

A rejection is marked stable only when the entire exact binomial interval is below alpha. A non-rejection is marked stable only when the entire interval is above alpha. Otherwise the result is marked monte_carlo_sensitive.

This is deliberately conservative. A sensitive flag means that the available simulation size does not sharply separate the bootstrap tail probability from alpha at the requested diagnostic confidence level. It does not reverse the test decision.

## Workflow

Start from an existing fixed-family test result:

    family_test = fpca_wild_bootstrap_projection_family_test(
        base,
        null_values=0.0,
        significance_level=0.05,
        pvalue_correction="plus_one",
    )

Then diagnose finite-bootstrap precision:

    diagnostics = fpca_wild_bootstrap_family_test_monte_carlo_diagnostics(
        family_test,
        confidence_level=0.95,
    )

Create a target-level table:

    frame = fpca_wild_bootstrap_monte_carlo_diagnostic_frame(diagnostics)

Plot exact Monte Carlo intervals:

    ax = plot_fpca_wild_bootstrap_monte_carlo_diagnostics(
        diagnostics,
        show_targetwise=True,
    )

Generate reporting text:

    text = fpca_wild_bootstrap_monte_carlo_reporting_text(diagnostics)

No multiplier is redrawn and no FPCA, score regression, residual model, target projection, or studentized bootstrap root is recomputed.

## What to inspect

For confirmatory work, inspect at least:

1. the planned number of bootstrap replicates;
2. the plus-one minimum attainable p-value 1/(B+1);
3. target-wise and adjusted exceedance counts;
4. exact binomial interval widths;
5. which adjusted decisions are marked Monte-Carlo-sensitive;
6. the global max-statistic diagnostic interval.

A p-value numerically close to alpha deserves more bootstrap precision than a clearly separated value if the scientific conclusion depends on that threshold.

## Choosing the number of replicates

The package does not choose B automatically.

For confirmatory analyses, choose the bootstrap budget before inspecting whether additional replicates would change a preferred conclusion. The 0.20 API is a post hoc precision diagnostic for a completed finite run, not a sequential stopping algorithm.

If additional replicates are generated after reviewing the diagnostic, report that decision transparently. Version 0.20 does not implement always-valid sequential Monte Carlo p-values or optional-stopping guarantees.

## Interpretation

A narrow interval indicates that the finite bootstrap run estimated the relevant exceedance probability precisely under the fixed computational design.

A wide interval indicates Monte Carlo imprecision. This can happen even when the reported p-value itself appears numerically decisive.

The diagnostic concerns simulation error only. It says nothing about:

- uncertainty from sampling new participants;
- uncertainty from estimating the FPCA basis;
- preprocessing or registration choices;
- clustered/repeated-participant dependence;
- truncation/component-selection uncertainty;
- misspecification of the Gaussian functional regression;
- validity of strong FWER claims for arbitrary subsets of nulls.

## Reporting example

> Fixed-family Gaussian FPCR wild-bootstrap tests used 1,999 retained bootstrap replicates and the plus-one p-value rule. Finite-bootstrap Monte Carlo precision was assessed without additional resampling using raw exceedance counts, plug-in binomial MCSEs, and 95% Clopper-Pearson intervals. The adjusted decisions were reported together with Monte Carlo stability flags relative to alpha=.05. These intervals quantify simulation precision conditional on the fitted analysis and do not represent confidence intervals for the scientific estimand or additional family-wise error guarantees.

## Failure and boundary cases

The diagnostic fails explicitly when:

- the input is not an FPCAWildBootstrapFamilyTestResult;
- the diagnostic confidence level is non-numeric, non-finite, or outside (0, 1);
- retained studentized roots or maximum statistics have inconsistent shapes;
- retained roots, observed statistics, or maximum statistics contain non-finite values.

An exceedance count of zero is not treated as zero uncertainty. The exact interval still has positive width.

The MCSE and exact Clopper-Pearson limits are written explicitly in the [mathematical reference](../methods/mathematical-reference.md#monte-carlo).

## API links

- FPCAWildBootstrapMonteCarloDiagnosticResult
- fpca_wild_bootstrap_family_test_monte_carlo_diagnostics()
- fpca_wild_bootstrap_monte_carlo_diagnostic_frame()
- plot_fpca_wild_bootstrap_monte_carlo_diagnostics()
- fpca_wild_bootstrap_monte_carlo_reporting_text()
- FPCAWildBootstrapFamilyTestResult
- fpca_wild_bootstrap_projection_family_test()

## Methodological context

The plus-one finite-resampling correction follows the Monte Carlo testing literature summarized by North, Curtis & Sham (2002) and Phipson & Smyth (2010). The exact binomial precision treatment follows the standard view that finite Monte Carlo exceedance counts can be assessed as binomial counts. Recent work on sequential Monte Carlo p-values emphasizes that adaptive stopping requires its own validity theory; version 0.20 intentionally does not implement such a stopping procedure.
