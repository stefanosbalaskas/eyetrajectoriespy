# W3 R22 — scaled-Cholesky CR2 numerical results and refusal boundaries

**Research draft:** [PR #324](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/324), stacked on [R21 cleanup PR #323](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/323). This stage does **not** replace or reclassify the original R20 scientific negative outcome (215 successes, 41 failures out of 256 original case/model evaluations). All evaluations remain source-paired within the original eight independent generating blocks.

## Independent numerical evidence

- **Mathematical adjustment:** the unique symmetric SPD solution `A_i D_i A_iᵀ=Φ_i` was constructed by independent scaled-Cholesky factorization `L_i^{-T}(L_iᵀ Φ_i L_i)^{1/2}L_i^{-1}`, with separate normalization of working and residual covariance. No eigenvalue was artificially clipped or shifted.
- **75-digit independent linear algebra:** [dedicated high-precision test workflow](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/38697954639) passed. Tests independently constructed the matrix root using mpmath at 75 decimal digits, checked scaling invariance and explicit rejection of untrustworthy conditions, and compared final CR2 SE/Satterthwaite df against the existing numerical reference on nontrivial well-conditioned Gaussian source designs.
- **External R comparator:** [dedicated R-equipped workflow](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/38697954766) passed against `clubSandwich::vcovCR` and `linear_contrast(test="Satterthwaite")` on four predeclared working-target designs (unequal cluster sizes, covariance correlation, extreme leverage) and two contrasts each. Required final SE, coefficient-specific df, critical value and point-estimate agreement, not merely matrix positivity. This comparison is on **specified**, appropriately conditioned covariance targets; it does not establish cross-language recovery in the 32 severe sensor-floor cases.

## Full replay of the original R20 256-case feasibility experiment

The [original 256-case R22 numerical replay](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/38697954512) passed its original-status preservation and accepted-case agreement checks. Its [archived artifact](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/38697954512/artifacts/11954693508) stores old and new case ledgers, summary, source checkout SHA, and SHA256SUMS; all **four** manifest entries have been independently verified against downloaded archive content.

| Case classification | Number | R22 disposition |
|---|---:|---|
| Original R20 successes | **215** | All 215 accepted; no final CR2 SE/df mismatch beyond predeclared relative preflight tolerance 5×10⁻⁵ |
| Original R20 failures from absolute product eigenvalue cutoff | **9** | Accepted by independent normalized scaled-Cholesky computation |
| Original R20 severe sensor-floor/conditioning failures | **32** | **Refused** under the predeclared normalized product condition cap 10¹¹ |
| Original source cases and historical failed-case identities | **256; 41 failed** | Exactly preserved, failure-key SHA256 `a75ffbf14fb632ffa7ce18ad0203e25141c3ff9d83bbb676ecf6ac55dbc0010e` |

The new standalone numerical method produced **224/256** accepted computations (87.5%) and **32/256 refusals** (12.5%). These figures represent *numerical completion*, not empirical 90% coverage. The original R20 41/256 failure count remains the historical scientific result.

Across the R22 accepted cases, the maximum reported **relative** adjustment identity error was approximately 9.6×10⁻¹². The 32 refused source cases had normalized product condition numbers approximately **1.2×10¹⁵ to 9.7×10¹⁵**, vastly exceeding the fixed, predeclared **10¹¹** cap. In these cases successful double-precision Cholesky factorization of the separate covariances would not, by itself, establish trustworthy CR2 contrasts or degrees of freedom.

## What is and is not qualified

The controlled numerical implementation has stronger **reference evidence** than the original absolute-eigenvalue method, especially for the nine artificial subthreshold rejections. It retains a defensible refusal policy for extremely poorly conditioned estimated targets. This does **not** establish that the four variance components are well identified, that the sensor-floor solution is scientifically appropriate, that a given pupil/gaze recording meets the structural covariance assumptions, or that fitted-target Satterthwaite degrees of freedom account for nuisance-estimation uncertainty.

The original pilot has only **eight independently generated source blocks**, and all 256 cases are highly paired. Therefore neither the new 224/256 numerical completion count nor selected coverage among its accepted cases can qualify pointwise 90% inference. R23 must prespecify larger independent blocks, identifiability diagnostics, nuisance-estimation accounting, unconditional success/refusal and conditional-on-success coverage **before** inspecting new outcomes; failed computations cannot disappear.

`original_R20_failures_reclassified=false`; `R22_explicit_refusal_policy=true`; `specified_covariance_numerical_preflight_passed=true`; `estimated_working_covariance_inference_qualified=false`; `simultaneous_band_qualified=false`; `production_release_ready=false`. Scientific issues #289/#296 stay open. No public API promotion, protected-main merge, version 1.2 release tag or PyPI upload.
