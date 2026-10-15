# R36 — held-out exact-zero slope variance: finite-grid restricted likelihood diagnostics

**Research-only original-source held-out experiment, NOT statistical type-I or likelihood-ratio-test qualification.** [Draft PR #338](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/338), [original science workflow #38811379572](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/38811379572), preregistered source seed `202610163636`; original science source head `e1485b4a158295b015d64a9285734770792a551f` and original GitHub Actions checkout `b4e79f8fc17ce7b150333292189af92980f4a527` (**pull-request merge SHA**). Both true-zero primitive-source integrity contracts and full 48-case/336-point scientific execution **passed**. No previously published scientific results were altered.

The full [original artifact #12009130612](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/38811379572/artifacts/12009130612) contains original `case-ledger.json`, `summary.json`, `source-commit.txt`, and `SHA256SUMS`. All three original named source files were independently checked against SHA256SUMS after downloading the artifact. The case ledger is authoritative for individual source block outcomes.

## Frozen source and split

Exactly **16 genuinely independent primitive Gaussian generating blocks**, with original native irregular repeated-trial gaze timestamps and 24 participants, crossed with ordinary and high-leverage predictor support under predictor-dependent Gaussian covariance. **Blocks 0–7** were reserved exclusively for true-zero null calibration, and **blocks 8–15** exclusively for held-out evaluation. Each of the eight held-out primitive blocks generated *both* a true-zero source and a paired positive-random-slope-variance source, reusing original participant intercept, trial and sensor innovations and observation times.

The true-zero source was rebuilt by setting primitive participant-slope innovations to **exactly zero**, not by merely passing a zero variance label to a positive-variance response. The positive source retained original generating variance **0.002025**. Test contracts verified that positive minus null observed outcomes equal the original participant random-slope contribution at every original native timestamp. Neither source truth nor latent Gaussian innovations were provided to observed-only REML nuisance fitting.

**48/48 prespecified source/state evaluations recorded, 336/336 constrained profile points optimized, zero source failures, zero base-REML failures, zero constrained-profile failures, zero missing records or refused calibration thresholds.** These 48 cases are paired/repeated configurations of only 16 independent generating blocks, not 48 independent source experiments.

## Seven-point empirical profile rule

For every source, the nuisance Gaussian REML model was fitted to observed original native trajectories; the other three covariance components were reoptimized at each frozen random-slope variance ratio to the observed-only residual reference: **0, 1e−6, 1e−4, 0.01, 0.1, 1, 10**.

The *finite-grid* statistic was defined prior to source outcomes as `T_grid = max(0, 2[restricted_NLL(slope_variance=0) − lowest_restricted_NLL_among_seven_grid_points])`. Exactly-zero is a valid constrained point. **This is NOT the continuous nonnegative-variance likelihood-ratio statistic**; its grid minimum is not a global MLE and its discrete zero mass may be substantial. No chi-square(1), chi-bar-square or other parametric cutoff was applied.

Per source-support condition, the eight **independent** calibration-null statistics were sorted, with the prespecified higher empirical 90th percentile (the **maximum of eight** values) frozen before held-out evaluation. Rejection is strictly `T_heldout > cutoff`. With only eight training null cases, this provides neither a well-resolved 90th-percentile estimate nor precise finite-sample nominal type-I error.

## Prespecified held-out results

| Generating source support | Empirical null-calibration cutoff | Held-out true-zero strict-tail rejections | Held-out positive-variance strict-tail rejections | True-zero rejection Wilson 95% | Positive rejection Wilson 95% |
|---|---:|---:|---:|---|---|
| Ordinary dependent | **1.588387** | **0/8 (0%)** | **0/8 (0%)** | [0, 0.324] | [0, 0.324] |
| Extreme dependent | **0.415556** | **2/8 (25%)** | **2/8 (25%)** | [0.071, 0.591] | [0.071, 0.591] |

All 8/8 held-out null and 8/8 held-out positive cases per support completed their seven constrained profile points. No failed case was omitted from an accepted-only denominator. The **joint numerical-success-and-rejection** rates equal those reported above only because numerical success was complete in this seed, not as a general policy.

### Held-out original generating blocks, paired null and positive statistic

Each cell below gives `T_grid(null), T_grid(positive)`. Extreme and ordinary leverage designs share primitive source block identities and **must not be treated as independent experiments**.

| Original block | Ordinary predictor support: null / positive | Extreme predictor support: null / positive |
|---|---|---|
| 8 | 0.000000 / 0.080444 | 0.000000 / 0.000000 |
| 9 | 0.041584 / 0.175085 | 0.000000 / 0.000000 |
| 10 | 0.445124 / 1.010727 | **0.790893 / 0.874327** |
| 11 | 0.000000 / 0.000000 | 0.000000 / 0.000000 |
| 12 | 0.000002 / 0.115127 | **0.781820 / 0.005109** |
| 13 | 0.000000 / 0.000000 | 0.000000 / **5.849386** |
| 14 | 0.000000 / 0.000000 | 0.000000 / 0.000000 |
| 15 | 0.000000 / 0.000000 | 0.000000 / 0.256015 |

With the frozen cutoff, extreme block **10** triggers a rejection under both true-zero and positive Gaussian source, extreme block **12** only under the true-zero source, and extreme block **13** only under the positive source. The evidence is therefore not a claim of useful null-versus-alternative discrimination. The eight held-out positive cases had a **finite-grid exact-zero minimum** in four source blocks under **both** ordinary and extreme support, despite strictly positive generating slope variance. The null source had exact-zero minima in five ordinary and six extreme blocks.

## Scientific interpretation and failure policy

R36 establishes that the **exact-zero source generator, constrained profile objective, fixed finite-grid empirical threshold and independent held-out source split can be executed reproducibly**. It does **not** show that this provisional test is calibrated near a 10% false-positive rate or that it has worthwhile power at generating slope variance 0.002025. The observed 25% held-out null rejection under extreme leverage is concerning, but **2/8** has a very wide Wilson interval and cannot by itself establish population overrejection. The simultaneous 2/8 positive rejections do not provide discriminatory evidence. Under ordinary leverage, 0/8 both null and alternative leaves the procedure uninformative in this small sample. Multiple support conditions, source pairing, threshold discreteness, finite-grid approximation and boundary likelihood mass all limit interpretation.

This stage also differs sharply from R34: it does not invert a nonregular observed nuisance Hessian to force an interval variance correction. It tests a *fixed, source-calibrated, finite-grid nuisance variance hypothesis statistic* against actual zero and positive Gaussian generator states. The source calibration itself is extremely small, and Gaussian source matching does not demonstrate robustness to wrong covariance, missing observations, or real eye-tracker data.

**No fitted-covariance Satterthwaite correction, regression coefficient confidence interval, function-wide simultaneous band or version 1.2 release qualification was produced.** A defensible later stage would predefine either (a) a continuously optimized nonnegative-variance profile statistic with independently verified boundary optimizer, plus appropriately calibrated reference, or (b) a constrained parametric bootstrap with nuisance re-estimation, and repeat calibration across much larger independent blocks with failure-inclusive source accounting. The present 16-block feasibility experiment **does not select either inferential procedure**.

`source_null_reconstruction_verified=true`; `finite_grid_numerical_execution_complete=true`; `heldout_null_calibration_qualified=false`; `variance_component_test_qualified=false`; `nuisance_adjusted_coefficient_CI_qualified=false`; `pointwise_or_simultaneous_bands_qualified=false`; `release_authorized=false`. Preserve historical R20 **41/256** failures, R22 **32** numerical refusals, R33 **four** high-leverage inclusion disagreements, R34 **10** regular-curvature refusals and R35 positive-source exact-zero grid minima unchanged. Keep blockers [#289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289) and [#296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296) OPEN; all research PRs draft, no protected-main merge, supported API promotion, version 1.2 tags or PyPI publication.
