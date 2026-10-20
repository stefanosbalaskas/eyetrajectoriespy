# W3 R74-A — independent original weighted-slope HC2/HC3 source and maximum-statistic audit

**Research-only. Not a nominal-90% simultaneous confidence-band validation.** Stacked on the frozen prospectively specified [R74 study](w3-r74-prospective-weighted-slope-HC2-HC3-protocol.md); both [#289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289) and [#296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296) remain unresolved.

## Original scientifically completed source experiment (before R74-A)

Original [R74 draft PR #396](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/396) achieved **25/25 exact-head CI workflows** and original [scientific workflow #39315676669](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39315676669) **12/12 successful jobs** (three Python-version algebra/OLS bootstrap contracts, eight four-independent-block Gaussian source shards, exact-source SHA256 aggregate). Immutable complete [original evidence #12217916622](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39315676669/artifacts/12217916622) pinned to original GitHub Actions scientific source PR-merge checkout `4031d3dbe5cfc5617bd939c8ea9cd00d17376bd9`.

R74 generated **32 truly NEW independent primitive Gaussian generating blocks**, four disjoint size/unit configurations (36 or 72 independent curves; 24 or 36 participants, three trials each), ordinary versus artificial extreme support and constant versus predictor-dependent Gaussian unit error SD `1+0.75|x_i|`, holding matched primitive source innovations fixed within support/variance pairs. Exactly **512/512 original source cases completed**, zero numerical refusals. Source unit variance is known only in the simulator. Source-specific reference methods: unchanged W3 wild-HC1, unchanged R72 **pooled** HC2 Gaussian, **weighted-slope HC2 Gaussian**, **weighted-slope HC3 Gaussian**, plus simulation-known heterogeneous Gaussian slope reference. All three estimated Gaussian references reuse the same 999 unit Gaussian draws per case; original W3 wild uses separate 999 Rademacher unit multipliers. At most **32 independent generating blocks per configuration/support/variance**, not 512 independent coverage units for any one condition.

## Complete original nominal-90% full-grid slope truth-inclusion matrix

Each numerator out of 32 independent primitive source blocks. Extreme predictor support overwrites two predictor values as −4 and +4, making their Gaussian error SD 4× normal baseline in the predictor-dependent regime. These are **descriptive Monte Carlo source observations**, not calibrated method coverage.

| Source configuration | Support / source variance | Original wild-HC1 | Pooled HC2 Gaussian | Weighted-slope HC2 | Weighted-slope HC3 | Known Gaussian |
|---|---|---:|---:|---:|---:|---:|
| 36 curves | ordinary / constant | 16 | 29 | 23 | 24 | 32 |
| 36 curves | ordinary / predictor-dependent | 13 | 18 | 20 | 23 | 30 |
| 36 curves | extreme / constant | 1 | 22 | 5 | 8 | 28 |
| 36 curves | **extreme / predictor-dependent** | **0** | **0** | **0** | **0** | **30** |
| 72 curves | ordinary / constant | 23 | 29 | 29 | 29 | 31 |
| 72 curves | ordinary / predictor-dependent | 24 | 23 | 27 | 29 | 31 |
| 72 curves | extreme / constant | 5 | 27 | 9 | 10 | 27 |
| 72 curves | **extreme / predictor-dependent** | **0** | **0** | **0** | **0** | **31** |
| 24 participants ×3 | ordinary / constant | 25 | 27 | 26 | 27 | 30 |
| 24 participants ×3 | ordinary / predictor-dependent | 24 | 26 | 27 | 27 | 30 |
| 24 participants ×3 | extreme / constant | 12 | 29 | 15 | 18 | 31 |
| 24 participants ×3 | **extreme / predictor-dependent** | **5** | **4** | **7** | **9** | **31** |
| 36 participants ×3 | ordinary / constant | 25 | 26 | 27 | 29 | 30 |
| 36 participants ×3 | ordinary / predictor-dependent | 24 | 24 | 27 | 29 | 29 |
| 36 participants ×3 | extreme / constant | 11 | 24 | 16 | 18 | 28 |
| 36 participants ×3 | **extreme / predictor-dependent** | **5** | **4** | **6** | **10** | **27** |

### Variance-scaling and simultaneous-reference distinction

In the **extreme predictor-dependent** conditions, the original mean weighted-slope HC3 **estimated-to-simulation-true marginal slope SE** ratios were **1.013** (36 curves), **0.982** (72 curves), **1.073** (24 participants) and **1.029** (36 participants). The corresponding weighted HC2 ratios were **0.791, 0.834, 0.801, 0.807**, versus **0.440, 0.461, 0.453, 0.455** for pooled HC2.

**Yet both curve designs gave 0/32 full-grid inclusion even under weighted-slope HC3.** This establishes that correcting the **average marginal SE scale** does not establish the distribution of the **joint maximum statistic**. The separate independent-source numerical audit must inspect and independently reconstruct the observed source-specific Gaussian critical values and full-grid pivot, including possible concentration of fitted factor loadings on a small number of high-leverage units. Until that inspection, one must not claim a particular causal critical-value mechanism or recommend a new multiplier.

In the two participant designs, HC3 increased extreme heteroskedastic truth inclusion from the pooled 4/32 to 9/32 and 10/32, but still far below the nominal 90% target. The 32-block Monte Carlo intervals remain wide, and the eight within-source condition combinations must not be treated as independent repeated experiments.

## Actual-original independent numerical audit contract

An independently authored `scripts/audit_w3_r74_independent_original_weighted_slope.py` **never imports** R74's original source generator/OLS/W3 package estimator, original R72 HC2 implementation or source aggregator. Its actual immutable-artifact job must:

- Require the exact original PR-merge source checkout `4031d3dbe5cfc5617bd939c8ea9cd00d17376bd9` and **three matching original SHA256 archive members** (`cases.json`, `summary.json`, `source-commit.txt`).
- Independently regenerate **all original 512 synthetic source predictor X and independent-unit Y arrays** from frozen NumPy Gaussian innovations, unit scale factors and real source-seed domains, then reconstruct least-squares coefficient curve, exact source truth error, HC1 SE, HC2/HC3 leverage factors and the analytically true heterogeneous slope standard error.
- Independently resimulate from the original fixed Gaussian and Rademacher streams all **511,488 archived raw W3 wild maximum-statistic draws**, and **1,534,464 derived estimated Gaussian maximum-statistic values** spanning pooled HC2, weighted HC2 and weighted HC3; verify each raw maximum sequence, all **2,048** source-specific 90% higher critical values and the source-known analytic Gaussian law reference.
- Independently reclassify **all 2,560 source/method truth-inclusion events**, all 16 full 32-generating-block coverage tables, three matched source-paired method comparisons per condition, full-denominator refusal bounds, Wilson 95% Monte Carlo intervals and SE-scale ratios.
- Refuse wrong original checkout, forged SHA, duplicated/missing case, altered original Gaussian X/Y, numeric discrepancy in any wild/HC2/HC3 maximum array, fake accepted failures or promotion of `release_authorized` or `no_90pct_simultaneous_band_calibration`.

**This independent work must pass against the ACTUAL immutable original R74 archive, not just synthetic regression fixtures.** The original R74 source contains full synthetic X/Y and both underlying source covariance regime/scale vectors, enabling stronger numerical replays than R71, but the data are still **synthetic from the same frozen source law**, not an external dataset.

## Scientific/release boundaries

R74 can falsify a candidate or motivate an additional experiment on the **joint dependence/critical-value reference**, but no estimated slope-weighted HC2/HC3 candidate has achieved general nominal-90% functional coverage. A candidate with approximately correct pointwise variance but observed 0/32 full-grid inclusion under extreme predictor-dependent noise is clearly not ready for inferential exposure in the public API. These fully observed Gaussian complete-grid results say nothing decisive about actual response-dependent gaze loss, missing trials, non-Gaussian tails or continuously indexed functional coverage. #289/#296 OPEN; stable v1.1.0 and protected main unchanged, 1.2 unreleased, no API, merge/tag/PyPI.
