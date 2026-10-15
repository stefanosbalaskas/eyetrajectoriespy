# R34 — local REML nuisance-information and conditional CR2 interval-width sensitivity

**Original research-only evidence, not an uncertainty-corrected functional CI.** [Draft PR #336](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/336), [original scientific run #38807507865](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/38807507865), frozen pre-results branch head `a5e1ff9d244f974ff57f7a467015b44a5075bb8e`. Both the native-numerical-contract job and complete original-source job **passed**, but the *scientific result includes ten prespecified refusals*. New source seed **202610163434**, **four** genuinely independent Gaussian source blocks, n24, ordinary versus extreme predictor support under **predictor-dependent** generating covariance and both matched predictor-scaled versus deliberately wrong shared-slope *fitted* covariance families: **16/16 paired model cases recorded; zero source failures, zero REML optimizer failures, zero CR2 finite-difference refusal cases**.

The [original scientific ledger artifact #12007256193](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/38807507865/artifacts/12007256193) includes case-level analytical gradients, fitted component boundary flags, source SHA, summary and SHA256SUMS. All **three** named source artifact files passed independent SHA256 verification.

## Scientific distinction: conditional interval derivatives versus regular nuisance information

For each fitted four-component Gaussian REML nuisance vector, log variance components were perturbed **±0.02 and ±0.01** individually; working covariance rebuilt from the original observed time/trial/participant/predictor kernels; and original R22 numerically guarded CR2/Satterthwaite **90%-nominal interval half-width** recalculated. The derivative of log half-width with respect to log variance components was numerically stable in all 16 fitted models, with no CR2 refusal. Conditional df derivatives were also obtained for all 16. These computations quantify **sensitivity to a specified change of working covariance**—they do not integrate the sampling uncertainty of the fitted covariance into an inferential procedure.

The original R25 analytic restricted Gaussian negative-loglikelihood gradient was independently finite-differenced to calculate an observed log-component Hessian, with symmetry and derivative-step stability checked. A candidate local asymptotic nuisance delta sensitivity `sqrt(g' H⁻¹ g)`, where `g` is the interval log half-width derivative, was **only permitted when the fitted variance vector was interior and all four components away from near-zero/bounded behavior, with a stable SPD observed Hessian**. It is a diagnostic for the estimated **half-width**, not a revised confidence interval or correction to Satterthwaite df.

## Full four predeclared model × source groups

| Original Gaussian source | Fitted covariance family | Matched? | Original cases | Stable CR2 width derivatives | Regular observed-information accepted | Explicit curvature refusals | Median max absolute conditional df derivative | Median diagnostic SD of log CI half-width, accepted only |
|---|---|---|---:|---:|---:|---:|---:|---:|
| Ordinary predictor support | Shared slope | No | 4 | 4 | 1 | 3 | 0.0464 | 0.000099 |
| Ordinary predictor support | Predictor-scaled slope | Yes | 4 | 4 | 3 | 1 | 0.6514 | 0.02180 |
| Extreme leverage | Shared slope | No | 4 | 4 | 2 | 2 | 0.0131 | 0.000201 |
| Extreme leverage | Predictor-scaled slope | Yes | 4 | 4 | **0** | **4** | 0.0154 | Not computed |

**Total: 16/16 conditional interval derivatives evaluated; 6/16 observed-information delta diagnostics accepted, 10/16 explicitly refused.** All ten refusals were triggered by **a near-boundary variance component**, rather than a CR2 Cholesky failure, Hessian non-SPD condition or a failed REML optimizer. Nine refused cases had near-boundary **participant random-slope variance**; one had near-boundary intercept variance. **Four** random-slope cases also reached the active numerical lower bound. The code records Hessian diagnostics even for refused fits but does not invert or regularize the boundary Hessian to force a positive scientific conclusion.

The apparently tiny local width sensitivity in some **wrong-family** accepted cases must not be interpreted as statistical accuracy or as evidence that a misspecified model gives safer intervals. Wrong-family working covariance can have superficially stable width conditional on an incorrect variance structure, as demonstrated by R33's substantive width differences from the Gaussian oracle.

## Research decision and next method gate

This new independent pilot reinforces the earlier R26–R28 practical information finding: random-slope covariance components frequently approach the boundary even when the Gaussian REML optimizer converges and CR2 computes reliably. High leverage can change the **conditional** Satterthwaite reference strongly (R33), but in this R34 source all four high-leverage correctly specified REML fits were **nonregular at the component boundary** and were properly refused by the nuisance-curvature gate.

**A regular inverse-Hessian delta approximation is not a defensible general answer to estimated covariance uncertainty.** The next scientifically justified investigation should use explicitly boundary-aware nuisance inference—e.g. constrained restricted-likelihood profiles for the random-slope variance with the other variance components reoptimized—and establish numerical reference/likelihood geometry before another nominal functional-effect CI calibration. It must keep boundary mass, one-sided/profile behavior, nonidentifiability and all refused source cases. Even successful nuisance profiling does not on its own deliver valid fitted-target CR2/Satterthwaite confidence intervals.

Only **four independent generating blocks** were studied, so neither fraction accepted nor curvature distribution is a precise population result. **No source-based coefficient truth-inclusion/coverage calculation, no simultaneous confidence band, no estimated-nuisance-adjusted Satterthwaite reference and no public inference API are qualified.**

Original R20 **41/256 failures**, R22 **32 explicit numerical refusals**, R33 four high-leverage inclusion disagreements and all earlier scientific source records remain unchanged. Scientific blockers [#289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289) and [#296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296) remain **OPEN**. All research PRs remain drafts; protected main, supported public API, 1.2 release tag and PyPI are unchanged.
