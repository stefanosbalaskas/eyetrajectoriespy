# R31 — native gaze sample loss and trial dropout: Gaussian covariance component recovery

**Research-only original source evidence:** [draft PR #333](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/333), [scientific run #38796470096](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/38796470096), original source head `d3a5b8398f87e1213f2d40f2fa93bcf261e3153f`. Both native-observation integrity tests and full original source study **passed**. Fresh seed `202610153131`, **12 independent generating blocks**, n24/n96, ordinary predictor-independent/dependent Gaussian covariance, Legendre-5 functional mean, four prespecified within-block observed regimes. **192/192 paired case evaluations recorded, zero source failures, zero NNLS or REML estimator/optimizer failures, zero missing cases.** There are only TWELVE independently generated source blocks; 192 paired model regimes are not independent source studies.

The [complete original 192-case source artifact](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/38796470096/artifacts/12002985367) contains the case ledger, study summary, source checkout SHA and SHA256SUMS. All **three** named original files passed independent SHA256 verification after downloading the original artifact.

## Source integrity and actual missingness

The observation-only input is an original `IrregularTrajectorySet` of native jittered timestamps and their **exact original outcome values**; incomplete cases remove only original selected sample indices or original trial series. No imputation, interpolation, smoothing, outcome regeneration or replacement occurred. Source/metadata tests verified exact time/value subarrays, participant and trial labels, monotonic retained native time, original unmodified source and nested n24/n96 participant-specific loss masks.

The four prior registered regimes were (i) original complete native observations, (ii) MCAR outcome-independent point deletion probability 0.20, (iii) observed-time MAR point deletion probability 0.05 at the first native time to 0.35 at the last, and (iv) predictor-dependent MAR drop of at most one later participant trial at probability 0.35 for x≤0 and 0.60 for x>0, preserving every participant. MCAR and time-MAR each removed about **19.6%–20.3% of original points** across the relevant cells. Trial MAR removed about **14.6%–16.2% of original trials**, with an equal or comparable proportion of native points due to fixed original trial length. These labels reflect *known simulated deletion mechanisms*, not an empirical determination of missingness from data. No MNAR scenario was tested.

Both existing covariance-component methods saw precisely the same retained observed rows and matching prespecified Gaussian working covariance family (independent source: shared slope; dependent: predictor-scaled slope). Both methods use observed-only rebalanced WLS weights over retained trials and times; such rebalancing is not itself a proof of ignorability. True positive source variances were consulted **only after fitting** for absolute-relative recovery and a common estimated-variance-below-5%-of-truth threshold.

## Complete descriptive results: 16 source × observation regimes

Each row represents 12 independent generating blocks paired across observation regimes. Error values are *median absolute relative error* compared with positive generating source variance. Near-zero counts are **out of 12**; the same simulation-only threshold is applied to NNLS and REML. Every method fitted 12/12 rows per cell.

| Participants | Source covariance | Observation regime | Point loss | Trial loss | NNLS slope median error | REML slope median error | NNLS trial median error | REML trial median error | NNLS slope near-zero | REML slope near-zero |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 24 | independent | complete | 0.000 | 0.000 | 1.228 | 1.000 | 1.000 | 0.252 | 4/12 | 5/12 |
| 24 | independent | mcar_20 | 0.200 | 0.000 | 2.281 | 2.043 | 1.000 | 0.277 | 2/12 | 2/12 |
| 24 | independent | time_mar_20 | 0.203 | 0.000 | 1.000 | 1.067 | 1.000 | 0.257 | 5/12 | 4/12 |
| 24 | independent | predictor_mar_trial_dropout | 0.155 | 0.155 | 1.000 | 1.503 | 1.594 | 0.176 | 6/12 | 5/12 |
| 24 | dependent | complete | 0.000 | 0.000 | 1.000 | 1.000 | 1.000 | 0.252 | 7/12 | 6/12 |
| 24 | dependent | mcar_20 | 0.196 | 0.000 | 1.000 | 1.000 | 1.000 | 0.213 | 6/12 | 7/12 |
| 24 | dependent | time_mar_20 | 0.199 | 0.000 | 1.000 | 1.000 | 1.000 | 0.257 | 7/12 | 6/12 |
| 24 | dependent | predictor_mar_trial_dropout | 0.146 | 0.146 | 1.000 | 1.000 | 1.000 | 0.238 | 7/12 | 6/12 |
| 96 | independent | complete | 0.000 | 0.000 | 1.000 | 0.967 | 1.000 | 0.166 | 3/12 | 2/12 |
| 96 | independent | mcar_20 | 0.202 | 0.000 | 1.000 | 0.939 | 1.000 | 0.143 | 6/12 | 1/12 |
| 96 | independent | time_mar_20 | 0.202 | 0.000 | 1.000 | 0.967 | 1.000 | 0.166 | 6/12 | 2/12 |
| 96 | independent | predictor_mar_trial_dropout | 0.162 | 0.162 | 1.000 | 1.000 | 1.347 | 0.113 | 5/12 | 2/12 |
| 96 | dependent | complete | 0.000 | 0.000 | 0.907 | 1.000 | 1.000 | 0.175 | 2/12 | 4/12 |
| 96 | dependent | mcar_20 | 0.200 | 0.000 | 0.967 | 1.000 | 1.000 | 0.169 | 2/12 | 3/12 |
| 96 | dependent | time_mar_20 | 0.198 | 0.000 | 0.911 | 1.000 | 1.000 | 0.151 | 2/12 | 4/12 |
| 96 | dependent | predictor_mar_trial_dropout | 0.154 | 0.154 | 1.000 | 0.973 | 1.000 | 0.162 | 3/12 | 2/12 |

## Predeclared paired recovery change: incomplete minus complete source

For every generating block, take each incomplete regime's absolute-relative *random-slope variance* error minus the error on that block's own complete original source. A positive change indicates worse variance component recovery with observation loss. The interval is a **2,000-draw bootstrap resampling entire independent generating blocks**, not raw gaze samples or within-block paired regimes. These intervals are descriptive and not adjusted for 24 comparisons.

| n | Covariance source | Observation process | Estimator | Mean paired slope recovery-error change | 95% whole-block bootstrap interval |
|---|---|---|---|---:|---|
| 24 | independent | mcar_20 | Original NNLS | 0.426 | 0.142 to 0.742 |
| 24 | independent | mcar_20 | Gaussian REML | 0.399 | -0.055 to 0.886 |
| 24 | independent | time_mar_20 | Original NNLS | -0.314 | -1.277 to 0.522 |
| 24 | independent | time_mar_20 | Gaussian REML | 0.266 | 0.018 to 0.583 |
| 24 | independent | predictor_mar_trial_dropout | Original NNLS | -0.435 | -1.071 to 0.026 |
| 24 | independent | predictor_mar_trial_dropout | Gaussian REML | 0.479 | -0.030 to 1.086 |
| 24 | dependent | mcar_20 | Original NNLS | -0.000 | -0.086 to 0.092 |
| 24 | dependent | mcar_20 | Gaussian REML | -0.032 | -0.082 to 0.009 |
| 24 | dependent | time_mar_20 | Original NNLS | 0.009 | -0.016 to 0.036 |
| 24 | dependent | time_mar_20 | Gaussian REML | 0.014 | -0.123 to 0.188 |
| 24 | dependent | predictor_mar_trial_dropout | Original NNLS | -0.080 | -0.655 to 0.313 |
| 24 | dependent | predictor_mar_trial_dropout | Gaussian REML | 0.100 | -0.059 to 0.268 |
| 96 | independent | mcar_20 | Original NNLS | -0.145 | -0.605 to 0.298 |
| 96 | independent | mcar_20 | Gaussian REML | -0.060 | -0.547 to 0.323 |
| 96 | independent | time_mar_20 | Original NNLS | 0.025 | -0.489 to 0.469 |
| 96 | independent | time_mar_20 | Gaussian REML | 0.005 | -0.379 to 0.437 |
| 96 | independent | predictor_mar_trial_dropout | Original NNLS | -0.496 | -1.208 to 0.081 |
| 96 | independent | predictor_mar_trial_dropout | Gaussian REML | 0.044 | -0.155 to 0.250 |
| 96 | dependent | mcar_20 | Original NNLS | -0.009 | -0.063 to 0.039 |
| 96 | dependent | mcar_20 | Gaussian REML | 0.046 | -0.068 to 0.202 |
| 96 | dependent | time_mar_20 | Original NNLS | 0.004 | -0.052 to 0.065 |
| 96 | dependent | time_mar_20 | Gaussian REML | -0.073 | -0.175 to 0.032 |
| 96 | dependent | predictor_mar_trial_dropout | Original NNLS | -0.059 | -0.265 to 0.137 |
| 96 | dependent | predictor_mar_trial_dropout | Gaussian REML | 0.066 | -0.139 to 0.301 |

## Interpretation: numerical reliability versus covariance component recovery

All 192 sources and both methods were numerically accepted, **but random-slope component recovery was frequently poor even in the original complete cases**. The observed-deletion results are heterogeneous and source-dependent. For example, at n24 under predictor-independent covariance, MCAR worsened mean NNLS slope error by **0.426 [0.142, 0.742]** and time-MAR worsened mean REML slope error by **0.266 [0.018, 0.583]** versus their own complete-data baseline. These are exploratory cellwise comparisons from only 12 independently generated blocks. Most loss/estimator source contrasts have intervals crossing zero. We must not generalize two apparent differences into an overall MCAR/MAR effect, infer selection bias without a model, or describe nominal coverage rates because no coefficient CI was computed.

The trial variance remains better recovered by REML than NNLS for the tested Gaussian source and covariance family, yet this does **not** establish empirical REML superiority: the original Gaussian likelihood assumptions, conditional observation process, variance-component boundary and covariance estimation uncertainty are all material. Under the predictor-dependent MAR dropout, participants remain observed but later trial selection depends on x; that can alter information and the effective weighting structure. The extent to which missingness is ignorable for a correctly specified likelihood requires separate analysis.

This stage is a finite-source reliability **diagnostic**, not validation of MNAR, physiological measurement processes, heterogeneous gaze calibration, or data collected with eye-tracking devices. The sample loss mechanisms are predeclared and simulated and do not establish missingness properties of an empirical dataset.

## Qualification gates unchanged

**No estimated-target CR2 SE or Satterthwaite degrees of freedom were calibrated, no nuisance covariance estimation uncertainty was incorporated into functional-effect CI construction, and no nominal 90% pointwise or simultaneous function-wide interval coverage was computed.** Strong numerical completion does not imply confidence interval validity. A future scientifically justified stage would have to specify nuisance-estimation-aware interval procedures, independently seed sufficiently many source blocks, include unconditional computational completion/refusal and conditional-on-success coverage, and separately validate function-wide bands.

`native_source_integrity_verified=true`; `mcarmar_component_recovery_study_completed=true`; `numerical_fits_all_successful_in_this_seed=true`; `estimated_covariance_inference_qualified=false`; `simultaneous_bands_qualified=false`; `release_authorized=false`. Scientific blockers [#289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289) and [#296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296) remain open; original R20 41/256 numerical failures and R22 32 refusals unchanged; all research branches draft, protected main and supported API untouched; no version 1.2 tag or PyPI upload.
