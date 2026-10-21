# W3 R85: secondary validation selection, full original-source evidence and figures

**Source and independent audit provenance · 21 October 2026 · synthetic research, not public inference**

!!! danger "No identification from ordinary gaze, no confidence bands"
    The R85 validation-stage mechanisms (independent, recorded-covariate selective, and latent-outcome selective) are **synthetic**. Exact hidden-outcome recovery weights require simulator-known generating mean and selection law. The experiment does **not** validate an actual technology for recovering lost gaze, observed-data MNAR identification, unbiased two-stage estimation, 90% simultaneous coverage or a released estimator. Stable 1.1.0 unchanged; version 1.2/PyPI HOLD; W3 #289/#296 OPEN.

## Original and independent numerical provenance

| Contract | Verified actual source |
|---|---|
| Prospectively frozen R85 source PR | [Draft PR #430](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/430) |
| Original dedicated scientific workflow | [#39629520741](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39629520741), **12/12 source jobs PASSED** |
| Original immutable SHA256 archive | [Artifact #12359490292](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39629520741/artifacts/12359490292) |
| Exact original science PR-merge checkout | `39ed0ed74d5eb23dfee316a8b5dcd73d498a4a9e` |
| Independently coded actual original audit | [Draft PR #431](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/431) |
| Actual original immutable archive replay | [#39630863879](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39630863879), **4/4 independent jobs PASSED** |
| Independent source/strategy reconstruction artifact | [#12359206531](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39630863879/artifacts/12359206531) |
| New source RNG seeds | Source **202610218580**, original missingness **202610218581**, external validation **202610218582** |
| True generating primitive blocks | **32 per fixed design/support/variance cell** |
| Complete synthetic X/Y source conditions | **256**, from 32 ×2 unit designs ×2 predictor supports ×2 noise scales |
| Paired first-stage MAR/MNAR masks | **512**, original generating δ=0 /+1.1 |
| Distinct recovery laws | Three: independent .25, recorded-input selective, latent-outcome selective |
| Strategies per source/mask | Five, including naïve/correct known recovery and privileged latent-oracle contrasts |
| Original strategy rows independently verified | **2,560**, not 2,560 independent generating blocks |
| Original public function-on-scalar behavior | Still **refuses missing gaze** |
| Interval and release qualification | **None**; no inferred confidence bands or valid general nominal-90% statement |

R85-A reconstructs **all original real archived source-level results**, rather than independently verifying only test fixtures. It uses centered-sufficient-statistic pilot OLS and independent Newton roots to compare against original trial-level least-squares and bounded bisection. Original X/Y, original masks, recovered masks, propensity arrays, pilot fits, final deltas, source-level error records and immutable hashes are independently verified for the entire factorial.

## Figure 1 — primary adverse MNAR source δ

![R85 original five external validation strategies and fitted original MNAR selection coefficient](../assets/research/w3-r85-selective-validation-mnar-delta.svg)

*Figure 1.* Two signed influential predictor units, predictor-dependent source variance; **32 independent blocks/design**, true first-stage MNAR δ=1.1.

| External recovery strategy | Independent curves, fitted δ | Repeated participants, fitted δ |
|---|---:|---:|
| Independent known .25 | 1.023421 | .965294 |
| Recorded-selective, naïve .25 | 1.285682 | 1.186202 |
| Recorded-selective, known recorded propensity | 1.030105 | .960964 |
| Latent-selective, naïve .25 | **1.670758** | **1.522912** |
| Latent-selective, simulator-known oracle propensity | 1.028327 | .950261 |

The MAR/MNAR first-stage generating truth is not used by fitting; the simulator-only recovery-propensity oracle uses true conditional mean only to calculate correct validation weights. These are **descriptive mean point estimates**, not inferential bounds.

## Figure 2 — full eight-cell latent-selective source error

![R85 full eight-cell outcome-selective external validation naive versus source-oracle weighted absolute delta error](../assets/research/w3-r85-eight-cell-oracle-versus-naive-errors.svg)

*Figure 2.* Mean source $|\widehat\delta-1.1|$ across 32 primitive independent source blocks/cell for actual original first-stage MNAR masks and **the same recovered samples** under both weighting strategies.

| Independent-unit design | Extreme signed units | Variance law | Naïve .25 mean absolute error | Privileged true-propensity error |
|---|---:|---|---:|---:|
| Curves | 2 | Constant | .6333 | .1301 |
| Curves | 2 | Heteroskedastic | .5708 | .1251 |
| Curves | 16 | Constant | .6081 | .1339 |
| Curves | 16 | Heteroskedastic | .4610 | .1635 |
| Participants | 2 | Constant | .5336 | .1048 |
| Participants | 2 | Heteroskedastic | .4288 | .1497 |
| Participants | 16 | Constant | .4811 | .1339 |
| Participants | 16 | Heteroskedastic | .3197 | .2267 |

The oracle's lower source-mean absolute errors in these eight cells are a **synthetic diagnostic**, not evidence that the oracle recovery propensity can be identified from actual observed gaze.

## Figure 3 — first-stage MAR, validation-stage MNAR produces a false coefficient

![R85 original MAR negative-control source fitted delta under latent-outcome-dependent external validation](../assets/research/w3-r85-mar-false-positive-validation-bias.svg)

*Figure 3.* First-stage generator true δ=0, 2-anchor heteroskedastic source, 32 new independent blocks/cell.

| Original MAR first-stage source | Independent known .25 | Recorded-selective naïve .25 | Recorded known propensity | Latent naïve .25 | Latent source oracle |
|---|---:|---:|---:|---:|---:|
| Independent curves | −.0063 | −.0396 | −.0091 | **+.6637** | −.0188 |
| Participants | +.0207 | +.0094 | +.0069 | **+.6304** | −.0051 |

The source with MAR original gaze selection does not become truly MNAR merely because a secondary validator preferentially recovers certain hidden residual values. Ignoring that second selection can nevertheless lead to a fitted positive original MNAR coefficient. These are **not formal significance tests or false-positive probabilities**.

## Qualifications of secondary observed-input weighting

The **recorded-selective corrected** strategy assumes the validation law is known, logged and governed by recorded predictor/time. It is not generally guaranteed to reduce *finite-sample* mean absolute first-stage δ error relative to an incorrectly constant recovery weight. For the adverse 2-anchor heteroskedastic original MNAR participants, source-mean absolute δ error was **.1189 under naïve** versus **.1390 under stipulated correct recorded-input recovery weights**, although source-mean signed fitted coefficients shifted from 1.1862 towards .9610 (truth 1.1). Error magnitudes and signed shifts address different criteria.

No source-independent uncertainty, estimated participant-cluster covariance, valid missingness-adjusted functional coefficient or calibrated whole-trajectory confidence band is computed here. The validation mechanism is itself a scientific object requiring independent information and measurement justification.

The [full R85 article](../articles/w3-biased-validation-mnar-r85.md) and [methods companion](../articles/secondary-validation-selection-and-mnar.md) explain the falsification and its limits. The original archived datasets, individual original source/mask/recovery hashes and all 2,560 source-strategy diagnostics remain available in the linked numerical evidence, not extrapolated to real eye-tracker behavior.

**Research source code stays draft, blockers #289/#296 OPEN, protected-main inference unchanged, version 1.2/PyPI RELEASE HOLD.**
