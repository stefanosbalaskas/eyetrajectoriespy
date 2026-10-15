# R37 — continuous exact-zero Gaussian REML: analytic score, multistart and fixed-grid comparison

**Research-only original-source optimizer feasibility; not a certified global likelihood maximum, variance hypothesis test, or functional-effect confidence interval.** [Draft PR #339](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/339), original [science run #38812645212](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/38812645212), new source seed **202610163737**, original experiment source branch commit `46be8462787c9a9e0e908cf7c2a8d89a8385e11e`. GitHub Actions original source-checkout SHA `59f44816114c19f96d4f13e6b68f0770a4273ca3` is the **PR merge checkout**, not the research branch tip. Both independent R25 analytic-score cross-checks and complete new-source multistart scientific execution passed, **but two objective multistart disagreements remain negative numerical findings**.

The [original 16-case source artifact #12008947517](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/38812645212/artifacts/12008947517) preserves every optimizer start and all seven nuisance-reoptimized fixed-grid points/case, source SHA and SHA256SUMS. All three original source artifact entries independently passed SHA256 checks.

## Mathematical contract and actual source

An independent blockwise Gaussian negative restricted loglikelihood is parameterized by three **positive** nuisance log-variance ratios (participant intercept, trial, sensor) plus one **LINEAR nonnegative** participant random-slope variance ratio whose lower boundary is mathematical **zero**, not `exp(lower log variance)`. Its analytic score includes the direct one-sided slope-ratio derivative at exactly zero. The positive-slope objective and score were verified against the independent R25 original Gaussian REML likelihood, and the zero-boundary derivative against a numerical forward derivative.

New native Gaussian source has only **four genuinely independent generating blocks**, each with 24 participants and original irregular repeated trials. Ordinary and extreme predictor leverage were crossed with true random-slope variance **zero** versus original strictly positive source variance; paired source variants reuse all other primitive Gaussian intercept/trial/sensor innovations, predictor values and observation grids. Thus **16 paired source/condition evaluations** do **not** constitute 16 independent experiments.

The continuous four-parameter optimizer uses **four frozen starting slope ratios: 0, 0.01, 1 and 10**, each with R25 nuisance log-variance initializer and a disclosed numerical upper bound `slope_variance / observed_residual_reference <= 100`. In parallel, the original R35 exact-zero **seven-point grid** `0,1e−6,1e−4,0.01,0.1,1,10` was fitted with three nuisance components reoptimized at every grid point.

**Source numerical outcome:** all **16/16** original source cases, **64/64 continuous multistart optimizations**, and **112/112 fixed-profile grid fits** completed. Zero source failures, base REML failures, continuous-optimizer failures, fixed-grid optimization failures and best-solution hits at the upper bound. For each source the best of four continuous starts was no worse than the original separately evaluated finite-grid likelihood minimum within the prespecified tolerance. **This is not an external global-optimum certificate.**

## Full original source results

The table reports the best of four continuous-start slope variance ratios and the gap `2(best_grid_NLL - best_continuous_NLL)`. Positive improvement means that the continuous best fit achieved a lower negative restricted likelihood than the seven-point grid. 'Start discrepancy' means at least two **successfully converged** multistart runs ended at negative log-likelihood values separated by more than 0.001. The same original source block is repeated across the paired four source conditions.

| Generating block | Original predictor support | True slope variance | Best continuous slope variance / reference | Twice NLL improvement over frozen grid | Material between-start disagreement |
|---|---|---|---:|---:|---|
| 0 | Ordinary | Zero | 0.303831 | 0.126857 | No |
| 0 | Ordinary | Positive | 0.325695 | 0.132164 | No |
| 0 | Extreme | Zero | **0.000000** | 0.000000 | No |
| 0 | Extreme | Positive | 0.128815 | 0.012760 | No |
| 1 | Ordinary | Zero | 0.573626 | 0.174019 | No |
| 1 | Ordinary | Positive | 0.837898 | 0.026136 | No |
| 1 | Extreme | Zero | 0.013550 | 0.000557 | No |
| 1 | Extreme | Positive | 0.453207 | 0.328474 | No |
| 2 | Ordinary | Zero | **0.000000** | 0.000000 | No |
| 2 | Ordinary | Positive | 0.742823 | 0.059534 | **Yes** |
| 2 | Extreme | Zero | 0.063934 | 0.031959 | No |
| 2 | Extreme | Positive | 0.696190 | 0.194275 | **Yes** |
| 3 | Ordinary | Zero | **0.000000** | 0.000000 | No |
| 3 | Ordinary | Positive | 0.181430 | 0.016249 | No |
| 3 | Extreme | Zero | **0.000000** | 0.000000 | No |
| 3 | Extreme | Positive | 0.215728 | 0.311684 | No |

A zero-generating random slope variance does **not** force a finite-source maximum-likelihood slope estimate to zero: the ordinary null in blocks 0 and 1 had positive continuous fitted ratios, while the extreme null in block 2 also remained slightly positive. Conversely the exact-zero solution was selected in **two of four** null source blocks under ordinary support and **two of four** under extreme support; no positive-slope source block selected exactly zero in this *new seed*. These are descriptive counts from only four independent blocks; they cannot estimate test sensitivity, specificity, type-I error, or power.

## Two convergence-without-agreement warnings — retained

In **block 2**, under the true **positive** slope variance source, the continuous optimizer converged successfully from all four frozen starts, but the 10× starting ratio terminated in a poorer likelihood basin.

| Source | Best continuous slope ratio (three agreeing starts) | 10×-start fitted slope ratio | Extra negative loglikelihood of 10× start |
|---|---:|---:|---:|
| Ordinary, block 2, positive | 0.74282 | 3.55363 | **1.822897** |
| Extreme, block 2, positive | 0.69619 | 1.73204 | **1.395040** |

The other three starts (0, .01, 1) agreed closely in objective, and the selected best continuous likelihood was below the R35 best finite-grid likelihood in both cases. This does **not** prove that the selected best was a globally optimal likelihood solution; it shows that **single-start optimizer success is not a sufficient numerical contract** for a boundary-aware covariance estimator. The objective discrepancies are observable despite solver success and must not be silently averaged or discarded. A stronger next stage would independently certify one-dimensional profile geometry (e.g. dense/adaptive slope profiling, verified derivative signs and constrained nuisance-optimum checks), then separately test any candidate likelihood-ratio procedure with independent null and positive generators.

## Scientific boundaries and next gate

The R37 code establishes an independent and positive/zero-gradient-tested *continuous* objective, with explicit multistart diagnostics and original-case retention. The upper ratio bound at 100 is a numerical engineering constraint and no global likelihood theorem is claimed. The likelihood can be weakly identified or multimodal in this four-component repeated-trial setting, making naïve chi-square/chi-bar boundary references unsafe without further evidence.

A continuously optimized profile statistic would still require a separate **larger independently seeded null reference study** (or constrained bootstrap with full nuisance re-estimation), failure-inclusive Monte Carlo confidence and validation under high leverage/missingness/misspecified Gaussian covariance. R36's 0/8 vs 0/8 and 2/8 vs 2/8 negative held-out discrimination results continue to apply **to its own frozen seven-point statistic**, not automatically to this new continuous likelihood.

**No p-value, calibrated variance-component test, new nuisance-adjusted CR2 Satterthwaite reference, functional regression pointwise confidence interval, or simultaneous function-wide band is authorized from R37.** Keep scientific issues [#289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289) and [#296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296) OPEN. Preserve original R20 41/256 failures, R22 32 refused CR2 cases, R33 four paired inclusion disagreements, R34 10 nuisance-information refusals, and all R35/R36 results unchanged. All work remains draft research; protected main, stable APIs, version 1.2 release tags and PyPI untouched.
