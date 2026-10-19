# W3 R72 — prospective HC2-estimated covariance Gaussian slope bands

**Research only. No qualified 90% simultaneous band, public inference API, or release authorization.**

## Independently audited rationale

[R71 original PR #390](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/390) and [independent R71-A audit #391](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/391) establish that wild-HC1 observed-grid simultaneous slope bands substantially undercover relative to known-Gaussian-law reference bands in the tested new-source Gaussian experiment. Extreme predictor leverage: independent curves wild 2/32 vs known Gaussian 26/32; repeated-trial participants wild 13/32 vs known Gaussian 27/32. The independently reconstructed source reference is an **oracle** that uses simulation-known covariance, unavailable for actual gaze observations. Its large advantage motivates a separately source-NEW *estimated*-covariance experiment, not immediate production adoption.

## Source independence and fixed Gaussian generating law

- **32 new independent primitive Gaussian source blocks**, seed 202610197272, disjoint from the R71 sources. Two independent-unit designs per block: 72 independent curves, or 36 independent participants with three complete repeated trials; each is evaluated under paired ordinary or extreme predictor leverage, for **128 matched source cases, 32 independent blocks per cell**. The paired supports reuse original stochastic innovations with the design mean recomputed.
- Original W3 Gaussian law retained unchanged: 31 time points, 2 independent dimensions, original fixed coefficient truth, curve noise SD 0.04 or independent participant random intercept SD 0.065 scaled by (1+0.35×time) plus trial noise SD 0.04. No missing observations or source dropout.
- The original observed-source OLS/HC1 + W3 wild Rademacher reference is reproduced with **999** independent-unit multiplier draws/case, wild seed 202610197274 and higher empirical 90th percentile maximum-statistic quantile, with package output explicitly cross-checked.
- The known Gaussian-law reference from R71 is frozen as a separate benchmark arm: 32767 max-statistic draws per design from the true source law. The estimated-covariance candidate **must not access this true generating covariance**.

## Data-estimated HC2 covariance candidate

For each native source, work only with the **independent-unit mean response vectors** over all 62 observed time×dimension cells. From ordinary least-squares residuals r_i and unit leverages h_i, estimate common unit covariance using the prespecified HC2 residual correction:

$$
\widehat C_{\mathrm{HC2}} = \frac{1}{n}\sum_{i=1}^{n}
\frac{r_i r_i^\top}{1-h_i}.
$$

The conditional OLS slope variance estimate is g_11 × C_hat, with g_11 the slope diagonal of the inverse design Gram matrix. Under this *special common-covariance Gaussian model*, this corrected residual second moment is conditionally unbiased. It is not a general cluster-robust CR2 estimator or a consistent small-n guarantee under misspecification.

To avoid arbitrary ridge tuning and ill-conditioned inverses, generate Gaussian covariance draws using the rectangular n×62 factor of residuals divided by sqrt(n(1-h_i)); rank deficiency is allowed. Each case receives **999 new independent multivariate Gaussian reference draws** (seed 202610197273) whose standardized full-grid absolute maximum yields the frozen higher 90th-percentile estimated-Gaussian critical. Use the HC2 estimated diagonal slope standard errors to form the observed truth pivot and 90% simultaneous slope band. Refuse nonpositive estimated grid variances, h_i close to 1, singular fixed-design Gram, and any nonfinite draw. Do not select or tune methods after inspecting inclusion outcomes.

## Prespecified comparisons and full archive

The three method labels are: original_wild_HC1; estimated_HC2_Gaussian; known_Gaussian_law. Archive the per-case 999 wild and 999 estimated-Gaussian maximum-statistic draws, full original synthetic independent-unit X and Y (unlike the R71 archive), true slope, observed truth pivots, method critical values and inclusion decisions, estimated-to-known source SE ratios, estimated covariance trace and leverage diagnostics. Archive all original failures/refusals.

For each design×support cell compute complete-source and **full planned 32-block denominator** truth-inclusion counts, Wilson 95% Monte Carlo intervals and refusal-inclusive lower/upper bounds. For matched source cases, report candidate-minus-wild and oracle-minus-candidate differences, paired discordance and full-denominator conservative bounds. These comparisons are descriptive of algorithmic behavior and cannot establish real-world statistical calibration or a production method.

Use exactly **four independent original-source shards** of eight primitive blocks. Each shard retains SHA256 raw-byte digests, all original source IDs, seed domain, exact source checkout and source success/refusal classification. Require all shards in the aggregate, rejecting tampering, duplicate or mixed-sha cases. Aggregate produces cases.json, summary.json, source-commit.txt and SHA256SUMS. A **separate independent original-archive audit is required** after the source experiment completes; fixture-only test success is not a scientific result.

## Qualification and release boundaries

The new estimated covariance matrix has at most n−2 empirical rank, smaller than the 62-dimensional grid for the participant design. Its behavior under non-Gaussian errors, wrong covariances, heteroskedastic independent units, actual missing gaze, MNAR, and realistic physiological noise is unknown. R72 uses only the observed time grid and slope coefficient, not continuous-time or simultaneous intercept+slope confidence families.

With only 32 independent source blocks per design/support cell, even approximately 90% observed inclusion would have broad Monte Carlo uncertainty and could not justify an inferential calibration claim. The known-law oracle is *not* available in real data and is used strictly for benchmarking.

Keep scientific issues [#289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289) and [#296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296) open; version 1.2 release HOLD. No public inference API, protected-main merge, release tags or PyPI/TestPyPI.

**This design was frozen before inspecting R72 original source outcomes.**
