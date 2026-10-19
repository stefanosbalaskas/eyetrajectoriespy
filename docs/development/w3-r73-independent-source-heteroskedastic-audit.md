# W3 R73-A — independent original predictor-heteroskedastic Gaussian source audit

**Failure-inclusive research-only source and numerical audit**, stacked on prospectively frozen [R73 original PR #394](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/394), developed for open inferential undercoverage [#289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289).

## The original adverse-condition result

Original R73 [scientific workflow #39310870157](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39310870157) passed **8/8 scientific jobs**: 3 Python 3.11–3.13 original numerical contracts, four new independent Gaussian source shards and one immutable SHA256 aggregate. Its complete original [source archive #12216120885](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39310870157/artifacts/12216120885) is pinned to the original source scientific pull-request merge checkout **`9d09b04ba49d6be34d16339c92eef457f71fcf31`**.

The prospectively fixed source seed 202610197373 generated **32 NEW independent primitive Gaussian source blocks** × two native independent-unit designs (72 curves or 36 participants each with three trials) × ordinary/extreme predictor supports × **constant versus predictor-dependent noise variance**. Exactly **256 original source cases completed, zero numerical refusals**. The heteroskedastic unit scale was **`1 + 0.75*abs(x_i)`** applied to both participant random effects and trial noise; in extreme support, the two ±4 predictors received **4× Gaussian SD**, i.e. **16× variance**. Original W3 wild-HC1 and R72 common-covariance HC2-estimated Gaussian procedures retained **999 unit-level wild or Gaussian reference draws per source**; 255,744 of each generated conditional-max draw type. The known-source benchmark used the **actual heterogeneous slope-weighted covariance** and the frozen independent Gaussian standardized reference (not passed into either estimated method).

### Complete original 90% simultaneous full-grid slope truth inclusion

Each denominator represents **32 independent primitive generating blocks within that specific design/support/variance condition**, not 256 independent replicates for any single method.

| Design and leverage | Noise law | W3 wild-HC1 | R72 estimated common HC2 Gaussian | Known heterogeneous Gaussian benchmark |
|---|---|---:|---:|---:|
| Curves, ordinary | Constant | 19/32 | 25/32 | 27/32 |
| Curves, ordinary | Predictor-dependent | 17/32 | 17/32 | 26/32 |
| Curves, extreme | Constant | 4/32 | 30/32 | 31/32 |
| Curves, extreme | **Predictor-dependent** | **0/32** | **0/32** | **27/32** |
| Participants, ordinary | Constant | 26/32 | 29/32 | 29/32 |
| Participants, ordinary | Predictor-dependent | 25/32 | 26/32 | 30/32 |
| Participants, extreme | Constant | 12/32 | 27/32 | 27/32 |
| Participants, extreme | **Predictor-dependent** | **0/32** | **2/32** | **27/32** |

Original extreme-support **predictor-heteroskedastic mean source HC2-to-true heterogeneous slope SE** ratios: **0.45830544** curves, **0.41891965** participants, vs source HC1-to-true ratios **0.71329058** curves, **0.55449560** participants. Thus the pooled HC2 reference is severely too small for the slope-weighted noise law under heteroskedastic high leverage. Source-validity must not be confused with constant-covariance R72 support, where the same HC2 procedure reached curve extreme 30/32 and participant extreme 27/32. These are original source-archive results; **independent verification is mandatory before calling them independently reproduced**.

## Independent original-data numerical contract

The separate `scripts/audit_w3_r73_independent_original_heteroskedastic.py` **does not import** the original R73 simulator, W3 estimator, R72 HC2 source implementation, its bootstrap code or source aggregator. The mandatory actual original source job downloads the unchanged full source archive and:

1. Verifies all three SHA256 archive members and exact pinned original PR-merge scientific checkout.
2. Independently regenerates all **256 original primitive Gaussian predictor/response `X` and native independent-unit `Y` mean arrays** with the frozen Gaussian RNG and predictor-dependent standard-deviation law; cross-checks all original source-level unit scale vectors and fixed functional truth curves. This is stronger than R71's archived-SE-shape-only numerical audit.
3. Independently recomputes original `np.linalg.lstsq` regression, HC1 sandwich slope SE, original full-grid slope error, leverage vector and pooled residual HC2 Gaussian factor; independently derives **true conditional heterogeneous slope SE `sqrt(sum_i [((X'X)^−1 X'_i)_{slope}]² * scale_i² * C_base_diag)`**, never obtained from a data-fitted method.
4. Replays **all 255,744 original Rademacher wild maximum-statistic draws** from unit multiplier vectors and **all 255,744 original pooled-HC2 Gaussian maximum-statistic draws** from the separate new source seeds; recomputes both 90% higher criticals, full-grid truth pivots, three truth-inclusion events per source and all independent-block Wilson 95% Monte Carlo intervals and paired known-versus-HC2 / HC2-versus-W3 discordance.
5. Rejects forged release/calibration flags, missing or duplicated original source IDs, original X/Y or noise-scale mismatches, altered raw 999 maximum arrays, wrong RNG provenance, false truth inclusion, incorrect original SHA256, or removal of numerical refusals from any original 32-source denominator.

**The audit must explicitly pass on the actual original archive.** Three Python-version fixture/contract jobs alone do not verify the real archived source evidence. The science allows the independently audited *negative robustness result* but does **not** authorize a fixed or releasable alternative.

## Independently executed original R73-A verification — PASS

[R73-A dedicated original-archive workflow #39312038641](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39312038641) **passed all 4/4 jobs**, including Python 3.11/3.12/3.13 source-level true heterogeneous covariance/wild-reference/tamper contracts and the **mandatory actual unchanged original R73 source archive** numerical-reconstruction job. Independent [evidence artifact #12216761586](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39312038641/artifacts/12216761586) verifies all three immutable SHA256 archive members, exact frozen original source checkout `9d09b04ba49d6be34d16339c92eef457f71fcf31`, independently regenerates **all 256 original predictor/response native-source X/Y arrays** from the prospective Gaussian RNG, confirms 256/256 accepted original cases and zero numerical refusals, and independently rederives every source truth/HC1/HC2 SE and pivot. It recomputes **255,744 original source wild maximum-statistic draws and 255,744 estimated HC2-Gaussian maximum-statistic draws**, their higher 90% criticals, all original source truth-inclusion events and complete fixed 32-block denominators, Wilson 95% Monte Carlo intervals and within-source candidate-vs-original/known-vs-candidate paired discordances.

The original R73 **fully observed Gaussian** extreme-leverage **predictor-dependent** evidence was independently reproduced, not inferred from the archived aggregate: **curves 0/32 original wild, 0/32 pooled common-covariance HC2, 27/32 known heterogeneous Gaussian**; **participants 0/32 original wild, 2/32 pooled HC2, 27/32 known heterogeneous Gaussian**. Mean `HC2/true_heteroskedastic_slope_SE` was **0.45830544** curves and **0.41891965** participants. Thus the common-covariance HC2 approach observed in R72 demonstrably **fails this prespecified high-leverage and predictor-dependent unequal variance stress**. This does NOT falsify all possible slope-specific leverage-adjusted covariance estimators; it falsifies only the frozen R72 **pooled** HC2 plug-in mechanism under this source DGP.

The independent audit reconstructs exact synthetic X/Y through the archived prospective seed and frozen Gaussian generating formula; this is a simulation-specific audit, not a second empirical dataset, nor a calibrated general 90% confidence band. Original 32 independent primitive blocks per condition provide exploratory source-level evidence with Wilson Monte Carlo uncertainty. Keep undercoverage #289 OPEN and observation-dependent gaze loss #296 OPEN; release HOLD.

## Interpretation and release boundary

The original R72 estimated HC2 Gaussian was a **common covariance** approximation. R73's unequal variance is Gaussian, independent across participant units, and intentionally correlated with predictors, including artificially extreme predictors. In this regime the correctly weighted heterogeneous slope SE can be many times greater than the **pooled** HC2 estimate. The observed result strongly suggests this simple R72 plug-in **does not solve general W3 simultaneous coverage**.

R73 does **not** test smaller independent samples, unequal numbers of repeated trials, non-proportional temporal covariance, true non-Gaussian tails, sensor anomalies or actual MAR/MNAR gaze missingness. One cannot infer that *all* HC2/cluster-robust or heteroskedasticity-aware Gaussian approaches fail; only the **frozen R72 common-covariance candidate** is stress-tested here.

Keep issue [#289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289) OPEN; keep response-dependent gaze-loss [#296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296) OPEN; stable 1.1.0, protected main, 1.2 unreleased, no inference API, no tags/PyPI.
