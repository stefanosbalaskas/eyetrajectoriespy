# W3 R42 — fresh-source end-to-end physical-KKT refinement and independent solver cross-check

**Prespecified research-only numerical replication.** This protocol freezes the algorithm, numerical gates, all starting configurations, and source seed before any R42 original-source result is inspected. Do not equate optimizer success, numerical KKT, globally certified REML covariance recovery, variance-component test calibration, or estimated-covariance functional CR2 interval coverage.

## Motivating scientific gap

[R40](w3-r40-fresh-source-nuisance-results.md) reproduced 58 success-flagged but materially inferior log-variance optimization endpoints over eight new generating blocks; raw positive linear nuisance coordinates found near-best observed likelihood for 192/192 frozen starts but had **18/192 physical projected-KKT residuals greater than 0.001**. [R41](w3-r41-targeted-kkt-refinement-results.md), on **outcome-selected old R40 data**, restored the original 18 KKT exceptions to the frozen threshold under either stricter L-BFGS-B or an independent SLSQP restart, without material NLL change. However, R41 generated zero independent blocks and only examined selected exceptions; it cannot qualify the full method.

## New generating block design (frozen)

Original master seed **202610164242**, different from the prior R37–R41 sources; **8 genuinely independent participant-level Gaussian primitive generating blocks**, each with **24 participants**, native irregular repeated trials and original Gaussian innovations. Within each independent primitive block, generate paired **ordinary/extreme predictor support × genuine zero/positive participant random-slope** sources; the exact-zero state reconstructs observations with the slope innovation actually removed while the remaining primitive innovations, time grids and participant/trial labels remain fixed. There are **32 support/state condition evaluations but only 8 independent primitive blocks**.

Across the **32** paired source cases, evaluate **both frozen random-slope variance ratios 0 and 0.75** relative to the same observed-only residual reference, with the three *observed-data-blind* R40 nuisance starts: interior ratios (0.2, 0.2, 1), near-bound participant intercept (exp(-13.8) × 1.01, 0.5, 1) and near-bound trial (0.5, exp(-13.8) × 1.01, 1). Optimize nuisance participant-intercept/trial/sensor variances inside the original strictly positive physical box [exp(-13.8), exp(7)].

For **every** frozen source/fixed-ratio/start, fit and retain **all three** stages, without selecting on baseline numerical outcome:

1. Original R40 **raw Gaussian NLL direct positive linear variance-ratio L-BFGS-B**, with original settings maxiter 250, ftol 1e-12, gtol 1e-8 and maxls 45.
2. Frozen R41 **stricter L-BFGS-B restart** from the baseline endpoint, same Gaussian likelihood/analytic physical-ratio gradient and bounds, maxiter 450, ftol 0, gtol 1e-10, maxls 80, maxfun 2200.
3. Frozen R41 **independent SLSQP restart** from the *same baseline endpoint*, same objective/analytic gradient and bounds, maxiter 450, ftol 1e-11.

Thus **8 independent primitive blocks × 2 support variants × 2 true slope states × 2 fixed slope ratios × 3 fixed nuisance starts = 192 prespecified starting cases**, with **3 numerical stages per start = 576 original-source optimizer records**. If the baseline fails, preserve the baseline's failure and explicitly mark **both downstream stages not attempted**, rather than omitting them from the planned denominator. All source/refusal states, optimizer messages, restricted NLLs, reference likelihood recomputation, physical coordinate projected-KKT residuals and full fitted nuisance ratios are retained in the original SHA256-matched ledger.

## Predeclared diagnostics and qualification boundary

Original physical projected KKT tolerance **0.001**, NLL within-source/fixed-ratio numerical agreement tolerance **0.001**, objective reconstruction tolerance **1e-6**. Compare stages against the lowest *successful observed* restricted NLL across all fixed nuisance starts and stages in the same source/fixed-slope profile. This baseline is **not a mathematically certified global optimum**. Summarize by stage and generating block, retaining worst-case failures, nonconvergences and gradient violations. Also report paired restart-minus-baseline objective differences greater than 0.001 in either direction.

**Numerical-only all-start gate**, calculated **separately for each stage** and unalterable after result inspection, requires: complete 32 source cases and 576 planned stage slots; zero source failures; no numerical failures/nonconvergences/refusals for that stage; no successful endpoints more than 0.001 above the best *observed* within-profile NLL; and zero stage endpoints exceeding 0.001 physical KKT. The integrity script refuses missing/source-incomplete cases while leaving ordinary numerical failures visible as scientific results. Passing the stage gate **would only qualify this prespecified numerical experiment's first-order diagnostic within these eight source blocks**, not the method globally or statistical inference.

No estimated-working-covariance CR2 coefficient confidence intervals, finite-sample Satterthwaite degrees of freedom, simultaneous whole-function bands, likelihood-ratio null/positive type-I error or power, real eye-tracking performance or missingness robustness can be deduced from these optimization studies. Additional fresh data, model/covariance misspecification and incomplete-observation stress would remain necessary.

Keep scientific blockers [#289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289) and [#296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296) **OPEN**, preserve the original R20/R22/R33–R41 negative evidence, and prohibit a protected-main merge, public API promotion, v1.2 release tag or PyPI upload.
