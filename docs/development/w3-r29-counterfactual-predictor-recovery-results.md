# R29 — new original-source Gaussian trajectories: predictor spread and covariance recovery

**Research-only original-source execution:** [draft PR #331](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/331), [scientific workflow #38782870723](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/38782870723), preregistered seed `202610152929`, original exact-head source `598320318cdb937bcabc30050240f29d45e93254`. Both **primitive Gaussian reconstruction contract** and the original-source 192-case numerical study **passed**. Twelve genuinely independent generating blocks; nested n24/96; ordinary-support predictor-independent/dependent source; fixed Legendre-5 mean, one structurally matching covariance family per source; predictor multipliers 0.5, 1, 2, 4. **192/192 paired cases recorded, zero original source failures, zero NNLS/REML estimator failures, zero missing**. Do not interpret the 192 paired cases as independent generating blocks.

The archived [complete original-source case ledger and manifest](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/38782870723/artifacts/11996123343) contains all 192 original case outcomes, source checkout SHA and `SHA256SUMS`; **all three source files passed independently checked SHA256 hashes**. The original R20 41/256 failures and R22 32 post-repair numerical refusals remain unchanged historical results on their own source seeds.

## Controlled primitive Gaussian counterfactual

The source experiment rebuilds every native original trajectory from the same participant intercept, participant random slope, trial and sensor primitive Gaussian innovations, the same jittered native times and trial IDs. The value `x_i` is rescaled and the underlying mean `mu(t,x_i)` recomputed. For predictor-dependent covariance, the participant random-slope Gaussian term is also multiplied by the new `x_i`, with its true random-slope variance parameter unchanged. For predictor-independent covariance, only the mean changes: subtracting the correct reconstructed mean leaves the exact same primitive noise. **Baseline 1× reconstruction was directly checked against original trajectory values and times**, and the counterfactual covariance identity tests passed.

Thus the independent-covariance source is a rigorous negative control against numerical artifacts from invertible fixed-effect scaling, whereas the dependent-covariance contrasts change the true Gaussian variance signal at the same variance parameter and fixed native observation design.

## Primary prespecified paired 2× versus 1× source result

Within every genuinely independent generating block, compare absolute relative slope-component error `|theta_hat / theta_true − 1|` at 2× versus the same original 1× source; use 2,000 bootstrap resamples over the **12 independent generating blocks**, never treating trial rows or multiplier variants as independent source samples. Negative mean error difference favors a broader predictor spread in this Gaussian simulation.

| Participant n | Covariance mode | Estimator | Mean error 2× minus 1× | 95% whole-block bootstrap interval |
|---|---|---|---:|---|
| 24 | independent | Original NNLS | 0.000 | -0.000 to 0.000 |
| 24 | independent | Gaussian REML | -0.000 | -0.000 to 0.000 |
| 24 | dependent | Original NNLS | -0.686 | -1.151 to -0.279 |
| 24 | dependent | Gaussian REML | -1.570 | -3.633 to -0.085 |
| 96 | independent | Original NNLS | 0.000 | -0.000 to 0.000 |
| 96 | independent | Gaussian REML | -0.000 | -0.000 to 0.000 |
| 96 | dependent | Original NNLS | -0.790 | -1.171 to -0.425 |
| 96 | dependent | Gaussian REML | -0.607 | -0.942 to -0.327 |

All eight paired bootstrap comparisons used **12 source blocks**, with no missing multiplier pair due to estimation failure. Independent-covariance comparisons were essentially invariant (estimated method error differences near zero, small optimizer precision noise). For predictor-dependent covariance, both methods showed improved **paired mean** random-slope component error under 2× spread at n24 and n96, with prespecified whole-block intervals below zero. The n24 Gaussian REML mean was more sensitive to extreme component recovery errors than its median, so the block result must not be described as a typical 12-block improvement at the median.

## All 16 source × spread cells: slope component median error and near-zero estimates

Each row has exactly 12 paired generating blocks as denominator. The 'near-zero' count uses the **same postfit criterion for both methods**, estimated slope variance below 5% of its positive source generating variance. This is a simulation diagnostic, not a procedure available on unknown empirical variance components.

| n | Covariance source | Spread | NNLS slope median relative error | REML slope median relative error | NNLS below 5%-truth /12 | REML below 5%-truth /12 |
|---|---|---:|---:|---:|---:|---:|
| 24 | independent | 0.5× | 1.000 | 1.000 | 7 | 7 |
| 24 | independent | 1.0× | 1.000 | 1.000 | 7 | 7 |
| 24 | independent | 2.0× | 1.000 | 1.000 | 7 | 7 |
| 24 | independent | 4.0× | 1.000 | 1.000 | 7 | 7 |
| 24 | dependent | 0.5× | 2.475 | 1.000 | 5 | 4 |
| 24 | dependent | 1.0× | 1.000 | 1.000 | 5 | 5 |
| 24 | dependent | 2.0× | 1.000 | 0.998 | 4 | 5 |
| 24 | dependent | 4.0× | 0.531 | 0.690 | 2 | 1 |
| 96 | independent | 0.5× | 1.000 | 0.941 | 5 | 2 |
| 96 | independent | 1.0× | 1.000 | 0.941 | 5 | 2 |
| 96 | independent | 2.0× | 1.000 | 0.941 | 5 | 2 |
| 96 | independent | 4.0× | 1.000 | 0.941 | 5 | 2 |
| 96 | dependent | 0.5× | 1.902 | 1.163 | 5 | 3 |
| 96 | dependent | 1.0× | 1.000 | 1.000 | 4 | 3 |
| 96 | dependent | 2.0× | 0.592 | 0.592 | 2 | 1 |
| 96 | dependent | 4.0× | 0.174 | 0.255 | 0 | 0 |

For the n96 predictor-dependent source, the Gaussian REML median slope absolute-relative error was approximately **1.000 at 1×**, **0.592 at 2×**, and **0.255 at 4×**. Original NNLS showed approximately **1.000, 0.592 and 0.174**, respectively. Near-zero matched Gaussian REML slope estimates declined from **3/12 at 1×** to **1/12 at 2×** and **0/12 at 4×**; the NNLS counterpart declined from **4/12** to **2/12** and **0/12**. At n24, 2× spread offered a mean error improvement but the median error remained near 1; a stronger median shift appeared only at the hypothetical 4× spread. These results underscore the variation across source blocks.

## Interpretation and remaining gates

The result is **consistent with** R28's oracle Fisher information pattern: physically increasing predictor spread *within a predictor-dependent Gaussian covariance generator* can make its variance component easier to recover from noisy finite-source outcomes. The independent covariance control demonstrates no false general improvement from merely increasing the numeric x range.

Nevertheless the spread multipliers are **artificial counterfactual interventions** on simulated data. The higher spread can imply unrealistic participant covariate values, altered leverage, changed mean extrapolation, or different conditional variance structures; finite-sample performance may depend on the assumed Gaussian generator and the predeclared covariance family. Twelve original independent blocks are insufficient to establish broad design optimality, let alone exact prospective power, model robustness or validity for human gaze recordings. The original primitive-noise pairing is intentional and must not be treated as independent samples across four multiplier levels.

**No fitted-target CR2 standard errors, Satterthwaite df, 90% pointwise confidence-interval inclusion, simultaneous bands or release qualification were evaluated.** Improved random-slope variance recovery is useful but does not yet account for estimating nuisance covariance from the very data used in a functional effect CI.

`original_source_regeneration_verified=true`; `paired_gaussian_recovery_diagnostic_complete=true`; `independent_covariance_negative_control_passed=true`; `empirical_study_design_qualified=false`; `estimated_target_inference_qualified=false`; `release_authorized=false`. Scientific blockers #289/#296 remain OPEN, draft research PRs isolated, protected main and supported public API unchanged, no version 1.2 tag or PyPI upload.
