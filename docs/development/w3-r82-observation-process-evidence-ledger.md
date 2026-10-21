# W3 R82: actual original and independent MCAR/MAR/MNAR source evidence ledger

**Numerical source and plot provenance · 21 October 2026 · synthetic research only**

!!! danger "No missingness correction and no general 90% band qualification"
    The original public common-grid function-on-scalar regression continues to **reject NaN gaze**. R82's new pointwise available-case OLS is an exploratory separate calculation, **not** a supported estimator for MNAR or a confidence-band implementation. W3 #289/#296 OPEN, stable 1.1.0 unchanged, v1.2 RELEASE HOLD.

## Generating model and four paired observation processes

The [R82 original prospective protocol](https://github.com/stefanosbalaskas/eyetrajectoriespy/blob/research/w3-r82-observation-process-mcar-mar-mnar-20261021/docs/development/w3-r82-prospective-observation-process-decomposition.md) freezes **32 independent new primitive generating blocks** evaluated under 2 independent-unit configurations (72 separate curves or 36 participants each with three trials), 2 extreme-predictor support counts (2 and 16), and 2 unit-level variance laws (constant and predictor heteroskedastic). **256 true complete-source datasets** each have 4 paired masks (COMPLETE/MCAR/MAR/MNAR): **1,024 mechanism evaluations**, not 1,024 statistically independent replications.

The generating complete source is synthetic nonseparable Gaussian spatial/temporal noise with Student-t5 independent-unit radial shocks plus mean-zero rare asymmetric unit shocks. The observation laws are MCAR p=.12, MAR depending only on recorded predictor/time/trial, and MNAR also on the original subsequently missing response residual.

![The original analytic MCAR, MAR and MNAR selection laws](../assets/research/w3-r82-analytic-mcar-mar-mnar-loss-laws.svg)

*Figure 1.* Analytic simulation probabilities, not estimated empirical gaze-dropout probabilities.

## Main design: sample retention and refused grid locations

![Actual source retention and grid refusal under only two influential independent predictors](../assets/research/w3-r82-missingness-retention-and-grid-refusal.svg)

*Figure 2.* Primary adverse two-anchor predictor-heteroskedastic design, 32 independent primitive blocks/cell.

| Design | Law | Observed fraction | Mean refused of 62 grid positions | Stable native missing-data refusals |
|---|---|---:|---:|---:|
| Curves | COMPLETE | 1.0000 | 0.00 | 0/32 |
| Curves | MCAR | .8793 | 14.91 | 32/32 |
| Curves | MAR | .8428 | 31.84 | 32/32 |
| Curves | MNAR | .8310 | **33.56** | 32/32 |
| Participants | COMPLETE | 1.0000 | 0.00 | 0/32 |
| Participants | MCAR | .8809 | .25 | 32/32 |
| Participants | MAR | .8100 | 5.13 | 32/32 |
| Participants | MNAR | .7825 | **8.38** | 32/32 |

No grid position failing at least eight independent units, rank-two design and *both* ±4 independent-unit anchors receives an estimated slope. This is a **prespecified conservative support rule**, not an impossibility theorem for generic OLS. Every source under all missing-data laws preserved the stable native NaN rejection contract.

## All eight design/support/variance cells: observed fraction and grid refusal

Each cell below has 32 independent original primitive source blocks. Values list MCAR / MAR / MNAR.

| Independent design | Extreme units | Unit variance | Observed sample fractions | Refused positions, mean of 62 |
|---|---:|---|---|---|
| Curves | 2 | Constant | .8793 / .8432 / .8343 | 13.44 / 30.25 / 31.00 |
| Curves | 16 | Constant | .8819 / .8158 / .8071 | 0 / 0 / .03 |
| Curves | 2 | Heteroskedastic | .8793 / .8428 / .8310 | 14.91 / 31.84 / 33.56 |
| Curves | 16 | Heteroskedastic | .8816 / .8171 / .8040 | 0 / 0 / 0 |
| Participants | 2 | Constant | .8805 / .8099 / .7866 | .19 / 6.00 / 6.91 |
| Participants | 16 | Constant | .8791 / .7444 / .7235 | 0 / 0 / 0 |
| Participants | 2 | Heteroskedastic | .8809 / .8100 / .7825 | .25 / 5.13 / 8.38 |
| Participants | 16 | Heteroskedastic | .8789 / .7453 / .7140 | 0 / 0 / 0 |

The difference between curves and participants reflects the explicitly prespecified choice to average only **available trials per participant** before regressing. Neither masked trial observations nor 1,024 mechanism rows are pseudo-replicated into 1,024 independent units.

## Pointwise slope changes conditional on estimable positions

![R82 original source-complete to available-case absolute slope differences](../assets/research/w3-r82-available-case-slope-deviation.svg)

*Figure 3.* Original source-averaged absolute change in pointwise estimated slope between a missingness mask and that source's corresponding **complete** data, on masked-grid locations that passed the independent-unit/anchor support gate.

| Design | Extreme units | Predictor-dependent variance, MCAR / MAR / MNAR |
|---|---:|---|
| Curves | 2 | .00212 / .00260 / .00302 |
| Curves | 16 | .00325 / .00625 / .00654 |
| Participants | 2 | .00310 / .00642 / .00684 |
| Participants | 16 | .00199 / .00510 / .00690 |

These **selected-grid descriptive means are not MNAR causal effects or unbiased slope-bias estimates**: both the set of estimable positions and observed retention differ across masking mechanisms. The original source archive additionally preserves per-source signed/absolute error against generating slope truth, observed native-unit counts, exact per-coordinate refusal and support matrices, whole-curve/whole-unit survival, and source/mask checksums.

## Immutability and independent replication

| Contract | Verified original or independent source |
|---|---|
| Prospective original research | [Draft PR #420](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/420) |
| Actual original science workflow | [#39571308151](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39571308151), **12/12 dedicated jobs PASS** |
| Original source/mask evidence artifact | [#12331563201](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39571308151/artifacts/12331563201) |
| Original source checkout | 06d1bb888468f1f85eee3875ae14ee5070a12400 |
| Separate independently implemented audit | [Draft PR #421](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/421) |
| Actual original archive replay | [#39572315409](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39572315409), **4/4 dedicated jobs PASS** |
| Independent replay evidence | [#12332990886](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39572315409/artifacts/12332990886) |
| Original complete-source designs | **256**, from 32 new primitive blocks per fixed design/support/variance condition |
| Original paired observation-process evaluations | **1,024**, complete/MCAR/MAR/MNAR for each original source |
| Independently regenerated | All 256 source X/Y, 1,024 source/mask digests, pointwise 31×2 support/refusal and available-case diagnostics |
| Native public missing-data contract | Incomplete common-grid source trajectories rejected, not imputed |
| Inference qualification | **None**, no MNAR correction or nominal-90% simultaneous band |
| Release | Stable 1.1.0 unchanged, v1.2/PyPI RELEASE HOLD, issues #289/#296 OPEN |

R82-A independently reproduces **the original, actually archived source**, not just a synthetic fixture. It validates numerical agreement on this artificial data/observation generating mechanism. It does **not** establish that any real eye-tracker's loss follows these probabilities, that MAR is identified in field data, or that outcome-dependent missingness can be corrected from observed values alone.

[Read scientific R82 article](../articles/w3-response-dependent-gaze-loss-r82.md) · [Read methods companion](../articles/independent-gaze-loss-and-pointwise-feasibility.md) · [Previous fully observed R81 audit](w3-r81-skewed-unit-evidence-ledger.md)
