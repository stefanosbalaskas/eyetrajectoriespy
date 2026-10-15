# R24 — population covariance moments versus finite-sample NNLS boundaries

**Scientific source:** [draft PR #326](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/326), [independent numerical-contract and original-source run #38700467812](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/38700467812), original research head `080b851225a071c1051b5166cae37bc6c1720f0e`. **8/8 frozen source-design cases and 1,024 conditional innovation draws** completed with no source or analytical contract failures. The source designs reuse **only two independent original R23 generating blocks** (indices 0 and 7), native time/participant/trial rows and mean basis Legendre-5. No new independent source-design experiments have been generated and none of the earlier R23 results were amended.

## Population moment algebra and finite-sample noise

For all eight designs, the independently assembled Gaussian residual covariance expectations agreed with the original observable residual-moment design operator to a **maximum relative discrepancy 2.020e-16**. The constrained NNLS moments at these exact *population expectations* recovered all four simulation-known nonnegative variance components to **maximum relative error 1.071e-15**. Thus the frozen population moment mapping is algebraically correct and full-rank with positive generating parameters in the tested designs; this does not imply low finite-sample uncertainty.

A finite participant cluster contributes only one noisy residual outer product `e_i e_iᵀ` to the method-of-moments objective. Under conditional Gaussian residuals `e_i~N(0,D_i)`, the expected squared Frobenius deviation is

`E||e_i e_iᵀ-D_i||²_F=(tr D_i)²+tr(D_i²)`.

For these eight frozen designs, the analytic root-mean-square outer-product noise was **1.56–1.60 times the norm of the expected covariance moment signal**. Therefore a large raw moment residual and NNLS boundary solutions can arise without population covariance-family misspecification.

## All eight prespecified frozen designs

Every zero count is over **128 newly generated conditional Gaussian innovation draws at the same fixed design**, not over independent generating blocks. The original observed source component zero list is retained separately. 'Relative recovery' is the median absolute relative error of the estimated component compared with its positive generating value, using only matching model-family configurations.

| Original R23 block | n | Source covariance | Operator condition | Analytic noise/signal | Slope zero/128 | Trial zero/128 | Intercept zero/128 | Sensor zero/128 | Median slope recovery error | Median trial recovery error |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 24 | independent | 145.76 | 1.57 | 69 | 56 | 32 | 2 | 1.00 | 1.00 |
| 0 | 24 | dependent | 4.01 | 1.60 | 56 | 57 | 4 | 1 | 1.00 | 1.00 |
| 0 | 96 | independent | 145.06 | 1.56 | 57 | 49 | 14 | 0 | 1.00 | 1.00 |
| 0 | 96 | dependent | 3.75 | 1.59 | 40 | 45 | 0 | 0 | 1.00 | 1.00 |
| 7 | 24 | independent | 143.73 | 1.57 | 69 | 52 | 22 | 6 | 1.00 | 1.00 |
| 7 | 24 | dependent | 3.68 | 1.60 | 53 | 45 | 2 | 0 | 1.00 | 1.00 |
| 7 | 96 | independent | 145.52 | 1.56 | 56 | 46 | 10 | 0 | 1.00 | 1.00 |
| 7 | 96 | dependent | 3.57 | 1.59 | 41 | 48 | 0 | 0 | 1.00 | 1.00 |

## Interpretation and strict boundaries

Across fixed n=24 designs, the random-slope variance was estimated at zero in **53–69/128** Gaussian repetitions and the trial variance in **45–57/128**. At fixed n=96, random slope was at zero in **40–57/128** and trial variance in **45–49/128**. Sensor variance was seldom zero. These repeated conditional experiments strongly support a *finite-sample noise plus nonnegative-boundary mechanism* for the particular source and moments, rather than a failure of the population expected-moment algebra. They do **not** establish that all R23 boundary results have this explanation, or that numerical conditioning and structural covariance misspecification never matter.

There are only **two independent frozen generating blocks** here; the 1,024 conditional Gaussian innovations represent nested repeated-sampling noise tests at eight fixed configurations and must not be pooled into nominal independent-source confidence bounds. These same-source conditional observations preserve the original R23 baseline; no selection, correction or reclassification of its 576-case ledger occurred. The unrestricted signal-to-noise ratio and component sensitivity remain poor in some cases, despite full rank, so component estimators may need more efficient, theoretically justified methods (e.g., moment weighting accounting for correlated noise, independent nuisance likelihood estimation) before estimated-target CR2 intervals are considered.

**No confidence-interval inclusion or 90% coverage analysis was performed.** The coefficient-specific Satterthwaite reference currently conditions on the working covariance target, which is estimated from the same data, and its nuisance-estimation uncertainty remains unaccounted for. Even a numerically reliable CR2 adjustment cannot validate inference when covariance components are weakly estimated. Further alternatives should be declared and validated on independent data, retaining all original failure/refusal rates and Monte Carlo uncertainty.

`population_moment_operator_verified=true`; `fixed_design_noise_boundary_diagnostic_complete=true`; `estimated_covariance_inference_qualified=false`; `simultaneous_functional_bands_qualified=false`; `release_authorized=false`. Scientific blockers #289/#296 remain open. No public API promotion, protected-main merge, release tag or PyPI upload.
