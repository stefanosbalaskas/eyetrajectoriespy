# R17 — 96 independent-block original source pointwise calibration results

**Original scientific source:** [GitHub Actions #38609764263](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/38609764263), exact source commit `376148eac71cf80ddc30bee364f0e8eee17c7578` of [draft research PR #317](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/317). Numerical contract and original-source jobs both successful. **4,608/4,608 source-model-target evaluations succeeded; zero failures and zero missing.** There are 96 independent source blocks (seed 202610142424), nested participant counts 24/48/96, four factorial generating conditions, two bases and two working covariance targets. Repeated cases sharing source blocks are **not independent replications**.

For each cell, observed inclusion is over 96 independent generating blocks, nominal **90% two-sided pointwise** functional-slope intervals. Columns: CR1/t(G−1), CR2/t(G−1), CR2/Satterthwaite, centered whole-participant CV3J/t(G−1), known Gaussian covariance oracle/t(G−1). The latter and correctly specified covariance target both use unavailable-in-practice known simulation parameters. The 'diagonal' target retains marginal variance but drops within-person covariance. Means of Satterthwaite df and CR2/oracle SE ratios are purely descriptive.

The case ledger and original summary, SHA and SHA256SUMS were uploaded by the original-source job; checking the archived artifact independently is a separate step.

## n = 24 participants — inclusion from 96 independent blocks per cell

| Source factor | Basis | Target | CR1 | CR2/t(G−1) | CR2/Satt. | CV3J | Oracle | Mean df | Mean CR2/oracle SE |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| ordinary_independent | legendre5 | known true | 87.5% | 90.6% | 90.6% | 90.6% | 89.6% | 11.61 | 0.96 |
| ordinary_independent | legendre5 | diagonal | 87.5% | 90.6% | 90.6% | 90.6% | 89.6% | 9.83 | 0.95 |
| ordinary_independent | cubic_spline13 | known true | 85.4% | 86.5% | 91.7% | 89.6% | 88.5% | 11.52 | 0.96 |
| ordinary_independent | cubic_spline13 | diagonal | 85.4% | 86.5% | 91.7% | 89.6% | 88.5% | 9.84 | 0.95 |
| ordinary_dependent | legendre5 | known true | 89.6% | 91.7% | 92.7% | 91.7% | 92.7% | 11.00 | 0.99 |
| ordinary_dependent | legendre5 | diagonal | 89.6% | 91.7% | 92.7% | 91.7% | 92.7% | 9.45 | 0.98 |
| ordinary_dependent | cubic_spline13 | known true | 89.6% | 90.6% | 91.7% | 90.6% | 91.7% | 10.94 | 0.98 |
| ordinary_dependent | cubic_spline13 | diagonal | 89.6% | 90.6% | 91.7% | 90.6% | 91.7% | 9.47 | 0.97 |
| extreme_independent | legendre5 | known true | 77.1% | 80.2% | 88.5% | 82.3% | 90.6% | 3.02 | 0.88 |
| extreme_independent | legendre5 | diagonal | 77.1% | 80.2% | 88.5% | 82.3% | 90.6% | 3.10 | 0.87 |
| extreme_independent | cubic_spline13 | known true | 77.1% | 79.2% | 88.5% | 83.3% | 90.6% | 3.03 | 0.88 |
| extreme_independent | cubic_spline13 | diagonal | 77.1% | 79.2% | 87.5% | 83.3% | 90.6% | 3.11 | 0.87 |
| extreme_dependent | legendre5 | known true | 71.9% | 81.3% | 96.9% | 83.3% | 91.7% | 1.74 | 0.92 |
| extreme_dependent | legendre5 | diagonal | 71.9% | 79.2% | 97.9% | 83.3% | 91.7% | 1.85 | 0.90 |
| extreme_dependent | cubic_spline13 | known true | 69.8% | 78.1% | 96.9% | 84.4% | 90.6% | 1.76 | 0.92 |
| extreme_dependent | cubic_spline13 | diagonal | 69.8% | 77.1% | 96.9% | 84.4% | 90.6% | 1.86 | 0.90 |

## n = 48 participants — inclusion from 96 independent blocks per cell

| Source factor | Basis | Target | CR1 | CR2/t(G−1) | CR2/Satt. | CV3J | Oracle | Mean df | Mean CR2/oracle SE |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| ordinary_independent | legendre5 | known true | 87.5% | 88.5% | 88.5% | 88.5% | 90.6% | 24.87 | 0.97 |
| ordinary_independent | legendre5 | diagonal | 87.5% | 88.5% | 88.5% | 88.5% | 90.6% | 20.42 | 0.97 |
| ordinary_independent | cubic_spline13 | known true | 89.6% | 89.6% | 89.6% | 89.6% | 90.6% | 24.57 | 0.98 |
| ordinary_independent | cubic_spline13 | diagonal | 89.6% | 89.6% | 89.6% | 89.6% | 90.6% | 20.34 | 0.97 |
| ordinary_dependent | legendre5 | known true | 84.4% | 85.4% | 86.5% | 86.5% | 88.5% | 23.56 | 0.98 |
| ordinary_dependent | legendre5 | diagonal | 84.4% | 84.4% | 86.5% | 86.5% | 88.5% | 19.59 | 0.97 |
| ordinary_dependent | cubic_spline13 | known true | 87.5% | 88.5% | 88.5% | 88.5% | 89.6% | 23.33 | 0.98 |
| ordinary_dependent | cubic_spline13 | diagonal | 87.5% | 88.5% | 88.5% | 88.5% | 89.6% | 19.51 | 0.98 |
| extreme_independent | legendre5 | known true | 84.4% | 85.4% | 92.7% | 88.5% | 92.7% | 5.84 | 0.94 |
| extreme_independent | legendre5 | diagonal | 84.4% | 85.4% | 92.7% | 88.5% | 92.7% | 6.08 | 0.93 |
| extreme_independent | cubic_spline13 | known true | 89.6% | 90.6% | 93.8% | 91.7% | 92.7% | 5.91 | 0.95 |
| extreme_independent | cubic_spline13 | diagonal | 89.6% | 90.6% | 93.8% | 91.7% | 92.7% | 6.10 | 0.94 |
| extreme_dependent | legendre5 | known true | 80.2% | 86.5% | 94.8% | 87.5% | 89.6% | 2.62 | 0.97 |
| extreme_dependent | legendre5 | diagonal | 80.2% | 85.4% | 95.8% | 87.5% | 89.6% | 2.92 | 0.95 |
| extreme_dependent | cubic_spline13 | known true | 80.2% | 85.4% | 94.8% | 88.5% | 90.6% | 2.68 | 0.97 |
| extreme_dependent | cubic_spline13 | diagonal | 80.2% | 84.4% | 94.8% | 88.5% | 90.6% | 2.93 | 0.95 |

## n = 96 participants — inclusion from 96 independent blocks per cell

| Source factor | Basis | Target | CR1 | CR2/t(G−1) | CR2/Satt. | CV3J | Oracle | Mean df | Mean CR2/oracle SE |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| ordinary_independent | legendre5 | known true | 80.2% | 80.2% | 80.2% | 80.2% | 86.5% | 51.90 | 0.98 |
| ordinary_independent | legendre5 | diagonal | 80.2% | 80.2% | 80.2% | 80.2% | 86.5% | 42.46 | 0.98 |
| ordinary_independent | cubic_spline13 | known true | 84.4% | 84.4% | 84.4% | 84.4% | 87.5% | 51.25 | 0.99 |
| ordinary_independent | cubic_spline13 | diagonal | 84.4% | 84.4% | 84.4% | 84.4% | 87.5% | 42.29 | 0.98 |
| ordinary_dependent | legendre5 | known true | 84.4% | 84.4% | 84.4% | 84.4% | 84.4% | 49.22 | 0.98 |
| ordinary_dependent | legendre5 | diagonal | 84.4% | 84.4% | 85.4% | 84.4% | 84.4% | 40.68 | 0.98 |
| ordinary_dependent | cubic_spline13 | known true | 84.4% | 86.5% | 86.5% | 86.5% | 86.5% | 48.69 | 0.99 |
| ordinary_dependent | cubic_spline13 | diagonal | 84.4% | 85.4% | 86.5% | 86.5% | 86.5% | 40.51 | 0.98 |
| extreme_independent | legendre5 | known true | 89.6% | 89.6% | 92.7% | 91.7% | 92.7% | 13.36 | 0.97 |
| extreme_independent | legendre5 | diagonal | 89.6% | 89.6% | 92.7% | 91.7% | 92.7% | 13.96 | 0.96 |
| extreme_independent | cubic_spline13 | known true | 88.5% | 88.5% | 93.8% | 90.6% | 92.7% | 13.56 | 0.97 |
| extreme_independent | cubic_spline13 | diagonal | 88.5% | 88.5% | 91.7% | 90.6% | 92.7% | 14.03 | 0.96 |
| extreme_dependent | legendre5 | known true | 84.4% | 86.5% | 91.7% | 86.5% | 89.6% | 4.59 | 0.98 |
| extreme_dependent | legendre5 | diagonal | 84.4% | 86.5% | 91.7% | 86.5% | 89.6% | 5.48 | 0.97 |
| extreme_dependent | cubic_spline13 | known true | 79.2% | 84.4% | 91.7% | 85.4% | 87.5% | 4.74 | 0.98 |
| extreme_dependent | cubic_spline13 | diagonal | 79.2% | 83.3% | 90.6% | 85.4% | 87.5% | 5.50 | 0.97 |

## Paired method contrasts and Monte Carlo uncertainty (selected original cells)

Each cell's 95% Wilson interval estimates Monte Carlo uncertainty for its inclusion rate based on 96 independent generating blocks; paired bootstrap intervals resample whole generating blocks for CR2/Satterthwaite minus CR1, using 2,500 bootstrap resamples. Nonindependent model-target evaluations are never counted as additional Monte Carlo units.

| Cell | CR2/Satt. inclusion | 95% Wilson MC interval | CR2/Satt. − CR1 | 95% paired bootstrap interval |
|---|---:|---:|---:|---:|
| n24/extreme_independent/legendre5/correct | 88.5% | 80.6%–93.5% | 11.5% | 5.2%–17.7% |
| n24/extreme_dependent/legendre5/correct | 96.9% | 91.2%–98.9% | 25.0% | 16.7%–34.4% |
| n24/extreme_dependent/cubic_spline13/correct | 96.9% | 91.2%–98.9% | 27.1% | 18.8%–36.5% |
| n48/extreme_dependent/legendre5/correct | 94.8% | 88.4%–97.8% | 14.6% | 7.3%–21.9% |
| n96/ordinary_independent/legendre5/correct | 80.2% | 71.1%–86.9% | 0.0% | 0.0%–0.0% |
| n96/extreme_dependent/legendre5/correct | 91.7% | 84.4%–95.7% | 7.3% | 2.1%–12.5% |

## Scientific assessment: correction is conditional, not universal

- In high-leverage predictor-dependent designs, conditional Satterthwaite reference df is exceptionally small for n=24 (roughly 1.7–1.9) and n=48 (roughly 2.6–2.9), giving much wider intervals than t(G−1). This markedly improves inclusion relative to CR1; in n=24 extreme-dependent settings it can **overcover** nominal 90%, so neither a universally calibrated estimator nor method winner is established.
- In n=96 ordinary-support designs, **known-covariance oracle** pointwise truth inclusion is sometimes as low as ~84–88%; this is a crucial diagnostic. A correctly computed covariance for the *fitted basis projection* does not guarantee nominal intervals for a different continuous-time generating-function estimand if there is basis-approximation bias. Another explanation is finite Monte Carlo noise. Both possibilities require explicit decomposition against the basis-projected target on the *same original source*, not post-hoc method selection.
- The means across multiple cells should **not** be interpreted as independent block-level replication or used to manufacture narrower uncertainty bounds. The pointwise single-contrast results do not qualify simultaneous functional confidence bands. Correct target covariance is specified from the generator, not estimated; 96 independent blocks still gives meaningful Monte Carlo uncertainty around each probability.

## Required R18 diagnostic gate

Fix the original R17 seed, n, generating observations, bases and fitted coefficients. Independently evaluate the **original midpoint truth** versus the **design-weighted population mean projection** for every cell (R16 `fit()` reports `project`), their displacement in units of known Gaussian standard error and the same oracle interval's inclusion of both targets. Check finite-block variation, empirical standardized errors and theoretical Gaussian error moments. No intervals are retrospectively declared successful, no original 4,608 observations altered or cases discarded. This is a sensitivity/estimand diagnostic, not a substitute for full calibrated inference. Additional independent source replication should be preregistered only after that diagnostic.

Scientific blockers #289 and #296 remain OPEN. `pointwise_coverage_qualified=false`, `simultaneous_bands_qualified=false`, `estimated_working_covariance_qualified=false`, `public_api_authorized=false`, `production_release_ready=false`. No protected-main merge, tag or PyPI release.
