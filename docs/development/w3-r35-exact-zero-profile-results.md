# R35 — original exact-zero random-slope REML profiles: boundary likelihood geometry

**Research-only identifiability/optimizer reference, NOT a variance-component likelihood-ratio confidence interval and NOT a functional-effect CI.** [Draft PR #337](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/337) and original [scientific run #38808537658](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/38808537658) passed both independently cross-checked Gaussian restricted-likelihood contracts and complete constrained source execution. New master seed `202610163535`, **four genuinely independently generated original Gaussian source blocks**, n24 and only predictor-dependent Gaussian covariance, original irregular gaze/trial structure, ordinary and x=(3,−2.5) extreme predictor leverage; correctly matched predictor-scaled nuisance model. **Eight original source/profile cases; 56/56 independently optimized fixed-slope profile points, ZERO source, base REML, or constrained-optimizer failures.** Each source block appears in ordinary and extreme predictor cases, so these are **not eight independent source experiments**.

The original [case ledger artifact #12006882680](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/38808537658/artifacts/12006882680) retains all eight original source rows, seven constrained likelihood points per row, original source-checkout SHA, independent summary and SHA256SUMS. All three original source entries passed SHA256 manifest verification.

## Mathematical cross-check, including exactly zero

An independently coded Gaussian restricted negative loglikelihood accepts `participant_slope variance = 0` **as an exact mathematical zero**, while the other three covariance components are reoptimized under the original positive log-variance bounds. The nuisance objective and three free-parameter analytic gradients were independently compared with R25's analytically and numerically validated four-component REML objective/gradient at *positive* slope variance, and tested by independent central finite differences at **exactly zero**. Both reference tests passed.

Seven prespecified `slope_variance / observed_residual_variance_reference` points are **0, 1e−6, 1e−4, .01, .1, 1, 10**. These are a **finite, prespecified diagnostic grid**; its best evaluated point must not be represented as a global restricted-likelihood optimum. The 2×restricted negative-loglikelihood difference displayed below is calculated against the best of those seven evaluated points, NOT a calibrated test statistic, chi-square mixture or significance threshold.

## Eight original source cases and likelihood shape

| Independent generating block | Original source leverage | Original REML slope near boundary? | Best *evaluated* slope/reference grid point | Twice restricted negative loglikelihood: exactly zero vs best evaluated | Exactly zero likelihood lower than prior bounded R25 REML? |
|---|---|---|---:|---:|---|
| 0 | Ordinary | No | 0.1 | 0.1072 | No |
| 0 | Extreme | Yes | **0** | **0.0000** | **Yes** |
| 1 | Ordinary | No | 1 | 1.2214 | No |
| 1 | Extreme | Yes | **0** | **0.0000** | No |
| 2 | Ordinary | No | 0.1 | 0.0784 | No |
| 2 | Extreme | No | 0.1 | 0.4540 | No |
| 3 | Ordinary | No | 1 | 0.7622 | No |
| 3 | Extreme | No | 0.1 | 0.8337 | No |

In **two of four extreme-leverage source blocks**, exactly zero random-slope variance was the lowest negative restricted Gaussian loglikelihood among the seven evaluated grid points, versus zero of four ordinary-leverage blocks. A zero profile point returned an even smaller negative likelihood than the R25 bounded positive-variance fit in **one extreme-leverage block** (block 0). This shows why the original bounded `log(theta)` optimizer and regular observed Hessian cannot reliably represent nonregular boundary geometry. It does not prove the true generating random-slope variance was zero (it was generated positive), nor prove a population frequency of boundary maxima. Source-block noise and predictor structure can make zero comparatively favorable in the sample.

The locally flat near-zero segments also matter: in block 0 extreme, 2∆negative-loglikelihood is 0.0000 at 1e−6 times reference and only 0.0007 at 1e−4; in block 1 extreme, the same values are approximately 0.0000 and 0.0004. A small likelihood gap means the data provide little distinction across a neighborhood near zero at the tested scale; that is **not** a validated variance-component confidence region.

## Interpretation and protected gates

R34's 10/16 refused regular nuisance-Hessian inversions were correctly guarded; R35 independently demonstrates that exactly-zero covariance parameter values can form competitive constrained likelihood profiles and therefore should not be replaced with arbitrary floors or interpreted through naive regular asymptotic standard errors. This result is conditional on the Gaussian source, one observed mean basis, fixed native trajectory design and only four independent source blocks.

A likelihood profile is an **identifiability diagnostic**, not an automatic boundary mixture test. No chi-square(1), chi-bar-square or other reference distribution was applied, and no slope-variance confidence interval was qualified. More source blocks and independent calibrations would be needed before boundary-aware covariance uncertainty could be used in a functional coefficient interval procedure. The working covariance family is deliberately matched here; misspecification, missing observations, non-Gaussian sensor errors and simultaneous whole-function inference remain distinct unresolved problems.

`exact_zero_boundary_profile_numerically_supported=true`, `profile_optimizer_complete=56/56`, `boundary_asymptotic_reference_validated=false`, `estimated_target_functional_CI_qualified=false`, `simultaneous_bands_qualified=false`, `release_authorized=false`. Keep issues [#289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289) and [#296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296) OPEN, preserve original R20 41/256 failures, R22 32 numerical refusals, R33 4 paired inclusion disagreements and R34 10 boundary-based information refusals. Draft research only: protected main, stable API, version 1.2 release tag and PyPI untouched.
