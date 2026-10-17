# W3 R57-A — independent immutable-original exact-zero nested Gaussian REML evidence audit

**Read-only research-only evidence verification.** This audit does not import the R57 scientific likelihood runner, generate or modify Gaussian sources, fit Gaussian nuisance variance parameters, change covariance kernels, compute valid boundary-null p-values or qualify any fixed-effect confidence interval.

## Authoritative immutable source

The full original Gaussian restricted-likelihood study is [R57 science workflow #39023712112](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39023712112), which completed **6/6 dedicated jobs** successfully and retained [original aggregate artifact #12098250313](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39023712112/artifacts/12098250313). Its original Actions **PR merge checkout `d120e5f48978dc7a86e6e400ac402dc42d2a3a59`** differs from subsequent documentation commits.

The independent checker downloads the original archive by **original run ID**, verifies its three SHA256 checksums, original checkout and exact source content identity (original cases `4b0acd21512579513ca904d61d0f74912855807f6ac46e4961af706e30ebc726`, summary `0ef577b86ded44343f18e2c345afbbea47e260883a510fd8393490bdfac7ea4b`), and refuses altered/missing/duplicated original evidence.

## Independently reconstructed contracts

The separate `scripts/audit_w3_r57_original_nested_zero_independent.py` reads only the original immutable JSON; it does **not** import the R35/R37 Gaussian likelihood estimator or the R57 generator. It independently validates every case identity against **8 source blocks×2 support regimes×2 true-zero/positive generating states**, retaining source grouping as paired rather than reporting 32 independent primitive innovations.

For all **32 source variants**, the audit checks: exact-zero null fit with three nuisance ratios, genuinely nested nonnegative slope-variance alternative with four variance ratios including **zero**, **two original null numerical starts** and **four alternative numerical starts**, accepted candidate optimizer-success flags, reconstructed independent NLL, numerical reconstruction error within **10⁻⁶**, **physical variance-ratio projected KKT≤0.001**, and selected candidate NLL within **0.001** of the best originally observed candidate. The physical KKT score is recomputed directly from archived analytic physical scores and selected variance-ratio bounds; in particular, at slope ratio zero, a *negative slope NLL derivative* is **not** incorrectly accepted as a valid lower-bound KKT condition.

The audit reconstructs the exact raw signed nested gap `2(NLL_H0−NLL_H1)`, checks that the observed alternative is numerically not worse than the exact-zero null by more than the frozen **−10⁻⁵ deviance** tolerance, verifies the separately labeled descriptive `max(0,raw)`, and insists that **p-values and hypothesis-rejection fields are null**. It rechecks every H1 exact-zero selection and the original leverage-by-generating-state median deviance calculations. A valid numerical deviance is **not** a statistically calibrated null-hypothesis test.

The audit explicitly cannot verify the random-slope-generating term's exact subtraction from the **raw native gaze trajectories**, because the immutable original case JSON does not include all raw `y` vectors or latent primitive innovation arrays. That property is checked in the **separate original scientific R57 source-contract tests**, and should not be attributed to the read-only archive checker.

The audit has fixed tests on Python 3.11–3.13 for strict one-sided slope-zero KKT, false optimizer start selection, likelihood reconstruction and immutable SHA256 tampering; a fourth GitHub Actions job downloads the original scientific archive and saves a separate derived JSON report for independent verification.

## Scientific restrictions

Even if all 32 original comparisons and 192 original optimizer starts are reproduced, the audit does **not** establish global REML optimum, the appropriate finite-sample or asymptotic zero-random-slope variance likelihood-ratio sampling law, Type-I error/power, corrected 90% pointwise CR2 fixed-effect confidence intervals or simultaneously valid whole-function bands. A structurally zero covariance likelihood null and a valid fixed-effect inferential method are separate scientific questions. The original source has only **eight genuinely independent Gaussian innovation blocks**, with all leverage/generating variants paired.

Keep scientific issues [#289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289) and [#296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296) **OPEN**, preserve the earlier negative R20/R22/R33–R56 results, and do not merge protected main, promote a stable inference API, tag eyetrajectoriespy 1.2 or publish PyPI.
