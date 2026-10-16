# W3 R43 — fresh-source numerical stress of size, anchored point dropout and covariance-family misspecification

**Research-only prespecified numerical robustness study.** This experiment follows the new independent-source R42 numerical gate without promoting numerical optimizer success into a statistically calibrated inference method or a supported public API. The R43 design, numerical thresholds and case denominator were frozen before original R43 CI results were inspected.

## Why R43 is distinct

[R42](w3-r42-independent-kkt-results.md) generated eight new Gaussian primitive blocks (n=24), retained all **576** numerical solver stages, and found **192/192** source/start fits near the best observed likelihood and compliant with projected physical KKT under a stricter L-BFGS-B restart. R42 used *complete trajectories* and the Gaussian working covariance family matching the source, without participant-count or missing-observation stress. Its numerical-only gate does **not** establish a globally optimal covariance estimator, Type-I-calibrated boundary test, or correct CR2 confidence interval coverage.

R43 tests whether the **same predeclared raw physical-nuisance positive-variance L-BFGS-B and stricter physical-gradient restart** behave under independently generated Gaussian primitive blocks in a limited factorial stress study. Model likelihood and nuisance variance bounds remain unchanged.

## Frozen source and factorial numerical design

Use original independent primitive master seed **202610164343** and independent interior loss-mask seed **202610164344**, distinct from R37–R42. Generate **4 genuinely independent primitive Gaussian source blocks**, with nested participant prefixes **n=24 and n=48** per block (not eight independent source draws). Cross ordinary/extreme predictor support and generating exact-zero/positive participant random-slope states as **paired variants of the same primitive innovations**. For a generating zero slope, reconstruct actual observations after explicitly deleting the Gaussian participant-slope innovation; do not simply attach a label to positive-slope observations.

Two prespecified observation processes:

- **Complete native irregular trials**: original native time grid and outcomes.
- **Anchored independent interior point dropout**: independently retain each interior native time point with probability **0.70**, always retain the first and last original trial timestamps, and deterministically rescue sufficient interior points to keep at least four native time points per trial. Masks are generated independently of the observed response, and coupled identically across zero/positive slope states and nested n24/n48 prefixes. This is **design-constrained independent dropout**, not unconditional MCAR across endpoints and **not response-dependent MAR/MNAR loss**. Refit weights on *retained observations*. No interpolation or hidden source-truth substitution.

Two fitted covariance working families over **the same observed data**:

- **Matched predictor-scaled participant slope** working kernel, identical in structural family to the Gaussian source design.
- **Deliberately misspecified shared/unscaled participant slope** kernel, replacing the predictor-dependent slope kernel with a predictor-independent slope kernel. It is a *working covariance misspecification*, not a second independently simulated generating process. When the generating slope variance is exactly zero, the generating covariance cannot diagnose this slope-family difference, but the candidate fixed positive-slope profile still differs.

At original fixed participant-slope variance ratios **0 and 0.75** relative to each source's observed-only residual reference, optimize the three strictly positive nuisance variance ratios from the **single predeclared difficult initialization** (intercept near positive lower bound, trial 0.5, sensor 1). Retaining this one difficult start allows the pilot to stress count, dropout and working-family effects without selecting on R43 optimizer results. It does *not* imply numerical robustness over all initializers.

For each source/working/profile case, run exactly **two** solver stages, same Gaussian restricted negative loglikelihood and analytic physical ratio derivative/bounds:

1. The original R40 raw positive linear-nuisance ratio L-BFGS-B candidate (maxiter 250, ftol 1e-12, gtol 1e-8, maxls 45).
2. The frozen R41 stricter physical-variance-ratio L-BFGS-B restart from the baseline endpoint (maxiter 450, ftol 0, gtol 1e-10, maxls 80, maxfun 2200).

**Prespecified denominator:** 4 independent primitive blocks × 2 nested sizes × 2 supports × 2 generating slope states × 2 observation conditions = **64 paired source evaluations**; × 2 working covariance families × 2 fixed profile ratios = **256 source/working/profile numerical cells**; × 2 stages = **512 planned original numeric optimizer records**. Only the four primitive source blocks are statistically independent experimental units. Downstream restart slots must be retained and explicitly marked **not attempted** if the original solver fails.

## Frozen gates and interpretation

Original R40–R42 **physical linear-ratio projected KKT tolerance 0.001** and **within-cell best-observed NLL gap tolerance 0.001** remain unchanged. Evaluate the latter *within the same source, size, support, slope state, loss process, fitted working model and fixed slope ratio* across the two stages. These stage comparisons are numerical; **NLL values from different working covariance specifications are not compared to claim a statistically superior scientific model**.

Report all solver nonconvergences, failures, incomplete source cases, near-best observed NLL disagreements, KKT exceedances, by-stage overall counts and fully stratified outcomes across matched/misspecified working covariance × complete/anchored dropout. Qualify a method's **within-experiment numerical-only gate** only if all 64 source cases and 512 planned stage records exist, no sources or stages fail, no optimizer success remains at an inferior NLL more than 0.001, and no successful fit exceeds physical projected KKT 0.001. Do not alter these thresholds after inspecting the results. Numerical success cannot certify global Gaussian REML optimization.

This **four-block factorial pilot** cannot establish inferential reliability under arbitrary n, realistic gaze loss, MNAR, covariance misspecification, or cross-device eye tracking. In particular, optimization of an intentionally wrong covariance family can be numerically reliable while its resulting covariance and CR2 uncertainty are statistically wrong. Distinguish this numerical analysis from new variance-boundary test null calibration and the separate nominal **90% pointwise and simultaneous functional CI** validation programme.

Scientific blockers [#289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289) and [#296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296) remain **OPEN**; preserve the historical R20/R22/R33–R42 scientific failures. No supported eyetrajectoriespy 1.2 inference claim, protected-main merge, release tag, or PyPI publication is authorized.
