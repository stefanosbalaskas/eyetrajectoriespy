# R25 — Gaussian REML versus original NNLS component estimator: paired numerical pilot results

**Original scientific evidence:** [R25 draft PR #327](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/327), [science run #38702360917](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/38702360917), source research head `065ede92b6a692b4b49af9ee18d4aaf2102423f4`. Numerical analytic-score contract and original-source scientific jobs both passed. **All 64 prespecified cases recorded, zero source/estimator failures or REML nonconvergence, zero missing.** They arise from **FOUR independent source generating blocks** (seed `202610153525`), nested n24/n48, four source conditions, one Legendre-5 mean basis and two fitted covariance nuisance families. No original R20–R24 cases or findings were changed.

The [complete R25 scientific artifact](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/38702360917/artifacts/11956714701) contains both method estimates for every source case, named failure/boundary indicators, source commit and SHA256SUMS. **All three files in the original downloaded archive passed independent SHA256 verification.**

## Observed numerical outcomes

| Method | Fits | Exact zeros: intercept | Slope | Trial | Sensor | Near-boundary definition |
|---|---:|---:|---:|---:|---:|---|
| Original leverage-adjusted NNLS | 64/64 | 13/64 | 18/64 | 36/64 | 0/64 | Exactly 0; sensor separately has disclosed floor |
| Independent Gaussian REML | 64/64 | 2/64 | 14/64 | 0/64 | 0/64 | Positive estimate below `1e-4 ×` observed response residual-variance reference; bounded log variance limits |

**Boundary frequencies are not directly interchangeable:** REML's positive log-scale parameterization rules out exact zero; a low fitted variance may instead be recorded as near-boundary. As a result, trial boundary counts alone are NOT a valid proof of REML superiority. Component *error against generating values*, evaluated only for matched nuisance structure, is more relevant.

## Matched working-family component recovery

Exactly **32 matched-family paired model cases** share only four independent generating blocks; the remaining 32 deliberately misspecified-family cases are not scored against incompatible generating component values. The following are *descriptive pooled medians over paired cases*, not independent-replication confidence intervals.

| Component | Original NNLS median absolute relative error | REML median absolute relative error | Matched-family boundaries: NNLS versus REML |
|---|---:|---:|---|
| Participant intercept | 0.385 | 0.412 | 8 versus 0 |
| Participant slope | 1.416 | 1.634 | 6 versus 5 |
| Trial variance | **1.000** | **0.221** | 18 versus 0 |
| Sensor variance | **0.113** | **0.020** | 0 versus 0 |

In the current four original blocks, REML improves trial-variance error considerably, although participant-intercept and slope recovery are **not uniformly improved**, and REML depends on Gaussian likelihood assumptions. For trial error, the descriptive median NNLS versus REML was **1.000 vs 0.370 at n24** and **1.000 vs 0.131 at n48**. This is evidence for pursuing independent reliability replication, not an estimator selection decision.

## All 16 prespecified source condition × working-family cells

All denominators per method are **four paired generating blocks**. 'Matched' means the fitted working covariance family uses the same functional form as the Gaussian generator; generator truth was appended only **after** method estimation. Columns provide successful estimates, trial and slope boundary counts, and median trial-variance *relative errors* when matched.

| n | Source factor | Working family | Matched | NNLS successes | REML successes | NNLS trial zero/4 | REML trial near-zero/4 | NNLS slope zero/4 | REML slope near-zero/4 | Median trial error NNLS | Median trial error REML |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 24 | ordinary_independent | shared_slope | Yes | 4/4 | 4/4 | 1 | 0 | 1 | 0 | 1.04 | 0.37 |
| 24 | ordinary_independent | predictor_scaled_slope | No | 4/4 | 4/4 | 1 | 0 | 3 | 2 | — | — |
| 24 | ordinary_dependent | shared_slope | No | 4/4 | 4/4 | 1 | 0 | 0 | 0 | — | — |
| 24 | ordinary_dependent | predictor_scaled_slope | Yes | 4/4 | 4/4 | 1 | 0 | 2 | 2 | 0.72 | 0.37 |
| 24 | extreme_independent | shared_slope | Yes | 4/4 | 4/4 | 2 | 0 | 0 | 1 | 1.47 | 0.37 |
| 24 | extreme_independent | predictor_scaled_slope | No | 4/4 | 4/4 | 2 | 0 | 1 | 1 | — | — |
| 24 | extreme_dependent | shared_slope | No | 4/4 | 4/4 | 1 | 0 | 1 | 0 | — | — |
| 24 | extreme_dependent | predictor_scaled_slope | Yes | 4/4 | 4/4 | 2 | 0 | 0 | 0 | 0.69 | 0.37 |
| 48 | ordinary_independent | shared_slope | Yes | 4/4 | 4/4 | 3 | 0 | 1 | 1 | 1.00 | 0.13 |
| 48 | ordinary_independent | predictor_scaled_slope | No | 4/4 | 4/4 | 3 | 0 | 2 | 2 | — | — |
| 48 | ordinary_dependent | shared_slope | No | 4/4 | 4/4 | 3 | 0 | 1 | 2 | — | — |
| 48 | ordinary_dependent | predictor_scaled_slope | Yes | 4/4 | 4/4 | 3 | 0 | 1 | 0 | 1.00 | 0.14 |
| 48 | extreme_independent | shared_slope | Yes | 4/4 | 4/4 | 3 | 0 | 1 | 1 | 1.00 | 0.13 |
| 48 | extreme_independent | predictor_scaled_slope | No | 4/4 | 4/4 | 4 | 0 | 2 | 1 | — | — |
| 48 | extreme_dependent | shared_slope | No | 4/4 | 4/4 | 3 | 0 | 2 | 1 | — | — |
| 48 | extreme_dependent | predictor_scaled_slope | Yes | 4/4 | 4/4 | 3 | 0 | 0 | 0 | 1.00 | 0.14 |

## Scientific and engineering interpretation

R25 independently checked the **analytic REML gradient** against finite differences on the observed covariance kernels and the restricted likelihood's invariance to arbitrary fixed-effect mean shifts. Both estimates use the *same observed native source rows*, with true generating covariance parameters excluded during fitting. REML parameter estimation includes the fixed-effect profiling term `log|Zᵀ V⁻¹ Z|`, which distinguishes it fundamentally from the original noisy residual-outer-product NNLS method.

This small source pilot shows that a likelihood-based alternative can substantially reduce *trial and sensor* recovery error in the matched Gaussian source. It is not yet evidence that REML has better participant random-effect recovery, better robustness to misspecified covariance models, fewer scientific refusals under more realistic gaze errors, or valid finite-sample CR2 inference. Near-boundary thresholds and initializations differ between estimators and have been disclosed. Four independent generating blocks are insufficient for credible relative recovery uncertainty or a method winner.

**Next gate:** a genuinely new, larger independent source study should quantify method-specific convergence, component recovery, near-boundary sensitivity under common *variance-to-truth* tolerances, and robustness to deviations from conditional Gaussian covariance, while reporting original-source independent-block Monte Carlo uncertainty. Only after this would it be appropriate to investigate feasible CR2 inference with nuisance-estimation-aware uncertainty. Neither a Gaussian REML likelihood nor successful component estimation fixes the currently conditional Satterthwaite degrees of freedom.

`estimated_covariance_nuisance_qualified=false`, `pointwise_inference_qualified=false`, `simultaneous_bands_qualified=false`, `production_release_ready=false`. Scientific issues #289 and #296 remain open. All research drafts isolated; no supported public API, protected-main merge, 1.2 release tag or PyPI publication.
