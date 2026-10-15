# R38 — two-basin REML profile geometry and projected-score audit

**Research-only diagnostic protocol; reuses the original R37 Gaussian source.** This experiment is **not** an independent Monte Carlo replication, not a new variance-component significance test, not a certified global optimum, and not a covariance-estimation-adjusted CR2 confidence interval.

## Why a numerical gate is necessary

[R37](w3-r37-continuous-boundary-reml-results.md) found two important cases in its four-independent-block source: both were **block 2, true-positive random-slope variance**, one with ordinary and one with extreme leverage. Every one of their four continuous bounded L-BFGS-B starts declared success, but the 10-times slope-variance starts converged at worse restricted negative likelihoods. The original objective excesses were **1.822897** (ordinary) and **1.395040** (extreme). A solver success flag does not establish that the covariance-likelihood maximum has been found.

R38 does not discard these cases, reinitialize their Gaussian primitives, or relabel the previously failed numerical criterion as successful. It characterizes why purportedly converged solutions disagree.

## Fixed, reproducible protocol

- **Source:** reuse the exact R37 seed `202610163737`, original generating **block 2 only**, n=24. Four *paired* conditions cross ordinary/extreme predictor support with true-zero/positive slope innovations. **Zero new independent generating blocks** are claimed.
- **One-dimensional profile grid:** 20 ratios of participant-slope variance to the observed-only residual variance reference: `0, .001, .01, .05, .1, .2, .4, .6, .7, .75, 1, 1.5, 1.75, 2, 2.5, 3, 3.5, 4, 6, 10`. This includes **exact zero** and neighborhoods of the two known problematic 10-times-start endpoints, about 1.732 and 3.554. The values are frozen before R38 original execution; this is not an adaptive post-hoc redefinition.
- **Independent nuisance reoptimizations:** at every grid point, call the independently implemented R35 exact-fixed-slope restricted Gaussian likelihood with analytic free-component derivatives. Fit from TWO nuisance initializations inherited from the best and worst R37 continuous outcomes. They are **not** independent source draws. Four paired cases × 20 grid points × 2 starts = **160 planned constrained three-dimensional fits**.
- **KKT diagnostics:** reconstruct each R37 continuous solution and recalculate the objective, analytic four-coordinate score and **projected box-constrained first-order residual**. The random-slope derivative is evaluated directly at zero. A tolerance of `1e-4` is a numerical diagnostic only, not an inferential acceptance cutoff.
- **Independent objective crosscheck:** at each constrained nuisance optimum, recompute the corresponding R37 four-parameter objective and direct slope derivative (envelope score) to check implementation consistency. Preserve nuisance lower/upper numerical-bound activity.
- **Failure-inclusive retention:** record every optimizer flag, exception, nonconvergence, missing profile point, and objective disagreement. A difference of **more than .001** between successful dual-seed nuisance fits is a diagnostic warning. A fixed-profile minimum below R37's selected four-start best objective by **more than .0001** is additional evidence that the original optimizer failed to locate the best investigated basin.

An optimization may satisfy a local first-order projected score and still be suboptimal relative to another basin; conversely, an apparent `success` may have a large projected score. Thus separate **optimizer completion**, **first-order stationarity**, **agreement among starts**, and **global-optimality claims** in every interpretation. This discrete one-dimensional diagnostic does not certify global nuisance minima between grid points or establish the number of all stationary points.

## Gates and permitted claims

The CI workflow should verify the exact-zero gradient identity, objective consistency, the predeclared case/grid dimensions and scientific execution with an auditable JSON case ledger and SHA256SUMS. Original science may produce negative diagnostic findings even when the workflow completes. Any incomplete case or missing grid count is a hard source-integrity failure; optimizer failures are reported, never silently omitted from denominators.

**No p-values, chi-square or mixture likelihood-ratio cutoffs, type-I error/power estimates, estimated-covariance-corrected Satterthwaite degrees of freedom, pointwise functional 90% coverage or simultaneous bands** are authorized from these four paired cases. Follow-on calibration requires genuinely new independent source blocks and independently prespecified continuous-profile inference rules after numerical reliability is established.

Retain scientific blockers [#289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289) and [#296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296) as open, and all original R20/R22/R33/R34/R35/R36/R37 negative results. Research draft only; **no protected-main merge, stable API promotion, tag, PyPI release or claim that version 1.2 has completed qualification**.
