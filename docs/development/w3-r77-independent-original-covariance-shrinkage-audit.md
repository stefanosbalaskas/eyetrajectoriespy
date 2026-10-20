# W3 R77-A — mandatory independent original-source covariance regularization audit

**Research only.** Original R77 source [draft PR #405](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/405) prospectively froze two source-observable HC3 covariance shrinkages (lambda 0.25, 0.50; seven-time within-coordinate diagonal smoothing) before drawing new experimental outcomes. No product estimator, calibration claim or API is accepted.

Original [R77 scientific workflow #39403101425](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39403101425) completed **12/12 scientific jobs**: 3 numerical contracts, 8 four-block new-source shards and 1 immutable SHA256 aggregate, with **256/256 source cases complete, 0 refusals**; exact original source checkout **`7bf404844078361339d593f27db0d70aeca3de2b`**. Source Gaussian seed 202610207770, reference seed 202610207771, wild seed 202610207772 and fixed regularized candidate seeds 202610207773/774. There are **32 independently generated primitive blocks per condition**, not 256 independent replicates per condition.

## Original adverse-condition results before independent audit

The primary adversarial mechanism is Gaussian unit SD `1+0.75|x|` with only two independent x=±4 observations. The 90% **whole 31×2 slope function** truth-inclusion counts, out of 32 independent generated source blocks each, were:

| Candidate/reference | 72 independent curves | 36 independent participants ×3 trials |
|---|---:|---:|
| Original package wild-HC1 | **0/32** | **4/32** |
| Original data-estimated slope HC3 SE + HC3 correlation | **1/32** | **9/32** |
| Frozen data-estimated covariance λ=.25 | **22/32** | **23/32** |
| Frozen data-estimated covariance λ=.50 | **24/32** | **24/32** |
| Source-known generating Gaussian SE+correlation (simulation-only oracle) | **27/32** | **29/32** |

Under 16 independent extreme predictors in the same noise regime, baseline HC3 / λ=.25 / λ=.50 / known Gaussian were curves **28/32, 28/32, 30/32, 30/32** and participants **27/32, 30/32, 30/32, 29/32**. Constant-variance source conditions remain prespecified falsification comparators; no method selection or arbitrary acceptance threshold is inferred from these observed counts.

The regularized covariance changes **both marginal variance and maximum-statistic reference correlation**. With two independent extreme anchors in the adverse condition, average candidate criticals curves **2.746 (baseline), 2.988 (λ=.25), 3.056 (λ=.50)**; participants **2.305, 2.837, 3.016**. The source-wise 10th percentile of HC3/true SE ratios averages curves **0.445 → 0.619 → 0.719**, participants **0.457 → 0.517 → 0.560**. This decomposition is original-source descriptive evidence only and does not demonstrate general nominal 90% calibration. Regularization imposes a strong time-diagonal structural restriction on a very particular Gaussian source law.

## Independent replay acceptance gates

1. Audit the **actual original immutable R77 aggregate** (not fixture-only): three checked SHA256 member files, exact original source PR merge checkout, all **256 new independent Gaussian source X/Y datasets** and true noise scales, slope errors, HC1/HC3, analytic source-known SE and effective variance concentration.
2. Independently construct the two positive-definite regularized 62×62 covariances as `(1-λ) F.T@F + λ diag(K7 diag(F.T@F))`, not importing the original R77 function; verify both covariance diagonals and estimated-vs-known marginal SE summaries, the original Cholesky-generated reference draws and their empirical higher 90% maxima.
3. Independently reconstruct **five original reference arrays of 999 maximum statistics per accepted source** (**1,278,720 numerical values total**), their quantiles, each source-wise observed maximum pivot, five full-grid truth-inclusion classifications and all 32-block Wilson intervals and source-paired differences. Preserve genuine numerical refusals in source denominators.
4. Require Python 3.11/3.12/3.13 fixture/numerical/tamper gates followed by a fourth **mandatory actual original artifact replay**, and archive results. Passing numerical reconstruction alone does not prove statistical calibration.

**Scientific inference remains unqualified.** Source law is fully Gaussian/observed with fixed time grid, and the time-diagonal smoothing target may be materially misspecified for other within-participant covariances. No participant dropout, MNAR loss, authentic sensor recordings, non-Gaussian errors or unknown temporal structure is tested. **W3 issues #289/#296 stay open; version 1.2 and PyPI HOLD; no protected-main estimator changes.**

**Audit status:** The independently implemented R77-A source checker and mandatory original-artifact workflow have been prepared; original outcomes above are not independently verified until the fourth audit job succeeds.
