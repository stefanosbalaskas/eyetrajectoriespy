# R18 — independent Gaussian-oracle replication results

**Original science:** [workflow #38619203614](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/38619203614), source head `18701edf9f1fa80f3e6588788c9711f43da0d5ae`, [draft PR #319](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/319). Original-source execution and dedicated numerical contract both successful: **768/768 cases complete; 0 failed; 0 missing**. Source seed `202610142621` differs from all earlier R16/R17 seeds. This is **192 independent new generating blocks**, reused in a paired way across two source covariance mechanisms and two fixed mean bases, not 768 independent datasets.

The experiment intentionally focuses on **n=96 ordinary predictor support**, the setting where the original R17 simulation-known Gaussian oracle showed 90% pointwise inclusion shortfalls. Both original continuous-time midpoint truth and conditional weighted-basis projection are retained and never redefined. The normal oracle is theoretically appropriate for *known* covariance under Gaussian innovations; t(95) is displayed solely as the original R17 reference.

## All prespecified original-source cells

Every coverage fraction has 192 independent source blocks as denominator. Wilson 95% Monte Carlo intervals are reported for the fixed design; between-condition comparison must account for paired common source blocks.

| Source covariance | Basis | Normal oracle truth coverage | Wilson 95% MC interval | t(95) oracle truth coverage | Wilson 95% MC interval | SD of (point−projection)/known SE | Mean square standardized error | Max oracle variance delta |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| ordinary_independent | legendre5 | 163/192 (84.9%) | 79.1%–89.3% | 164/192 (85.4%) | 79.7%–89.7% | 1.088 | 1.178 | 4.17e-18 |
| ordinary_independent | cubic_spline13 | 168/192 (87.5%) | 82.1%–91.5% | 170/192 (88.5%) | 83.3%–92.3% | 1.090 | 1.182 | 3.74e-18 |
| ordinary_dependent | legendre5 | 167/192 (87.0%) | 81.5%–91.0% | 167/192 (87.0%) | 81.5%–91.0% | 1.075 | 1.149 | 3.63e-18 |
| ordinary_dependent | cubic_spline13 | 170/192 (88.5%) | 83.3%–92.3% | 170/192 (88.5%) | 83.3%–92.3% | 1.088 | 1.178 | 3.90e-18 |

## Methodological interpretation

1. The replication again shows some **low inclusion** and standardized-error sample SD above 1.0. However, the four cells are highly related: two fixed basis fits share source innovations and independent/dependent covariance settings share a seeded source block, so their patterns **must not be treated as four independent confirmations**. Each estimated probability is subject to binomial Monte Carlo uncertainty; 90% lies outside the individual Wilson interval for the independent/Legendre **normal** reference by a small margin, but this individual interval is not multiplicity-adjusted.
2. A direct alternative covariance calculation based on original within-participant covariance blocks and WLS contrast loading matched the R16 oracle variance **to within 4.2×10⁻¹⁸ in the tested cases**. This checks algebra, not by itself the distribution of the generating random variables or the implementation's Gaussian independence assumptions.
3. The finite-basis mean projection differs negligibly from the original truth and had identical inclusion counts in all four cells. This mirrors R17's 24-cell original-source diagnostic. It excludes substantive projection displacement as the explanation in these particular designs.
4. Under an actually Gaussian linear generating process with the stipulated independent innovations and known conditional covariance, `(point−conditional projection)/oracle_se` is exactly standard normal *conditional on the observed design*. Persistent deviation would imply a mismatch in assumptions, source implementation, or chance fluctuations; a second fixed-design source-innovation reconstruction is warranted **before** claiming the known-covariance oracle is wrong.

## Next diagnostic gate

In a new isolated research draft, freeze selected native R18 design matrices, participant trial maps and original generating innovations. Express the fitted focal contrast error as a **linear sum of primitive random intercept, random slope, trial and sensor innovations** and independently compute the variance by summing their squared weights. Verify exact per-original-source reconstruction of the realized contrast error and its variance; then use separately seeded conditional Gaussian draws at these frozen designs for numerical distribution checks. Do **not** repair, discard, relabel or change the 768 original R18 outcomes. Preserve the original source experiment and report conditional simulation variability without pooling its Monte Carlo draws as independent reproductions of the 192-block source experiment.

`general_empirical_coverage_qualified=false`, `simultaneous_inference_qualified=false`, `production_release_ready=false`. Scientific issues #289/#296 remain open; no public API, main merge, release tag or PyPI publication.
