# R32 — observed-only REML plug-in covariance versus known-target CR2: original 90%-nominal pointwise feasibility

**Research-only exploratory numerical/inferential falsification study; no calibrated interval claim.** [Draft PR #334](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/334) and [original-source science run #38797789648](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/38797789648), source head `0ed91639b13419b82090e5aed26637f8a2a5eb42`. Independent known-covariance/original R17 Gaussian numerical contract and complete original source run BOTH PASSED. Distinct master source seed `202610153232`, **16 genuinely independent generating blocks**, nested n24/n96, ordinary predictor-independent and dependent Gaussian covariance, original native complete or observed-time MAR (~20% point loss), Legendre-5 fixed mean basis: **128/128 paired source cases recorded**, zero missing source cases, zero REML nuisance failures, **zero scaled-Cholesky CR2 numerical refusals** in either known-target or plug-in-target arm. Each source case is paired across Gaussian covariance assumptions and observation regime: these are NOT 128 independent generating studies.

The [original complete 128-case science artifact #12002587603](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/38797789648/artifacts/12002587603) retains case ledger, source checkout SHA, summary and SHA256SUMS. The three original source files passed independent SHA256 verification on archive download.

## Independent known-target check and estimand

The simulation-known Gaussian covariance target was built independently using the true four generating variance-component coefficients and **observed native** WLS weights, times, trial and participant labels. On unchanged complete source, the independent oracle matrix blocks exactly matched the prior R17 original-source covariance reference; dedicated CI tests passed. The second target comes from an entirely independent **observed-only Gaussian REML nuisance fit** using the same prespecified covariance family. Generator true parameters/random effects/innovations are never passed to REML.

To separate fixed mean approximation from covariance uncertainty, the prespecified pointwise inclusion truth is `c' beta_projected`, the generating mean projected onto the exact observed Legendre-5 WLS design, rather than silently equating it to the original functional slope at the focal time. Both values and their difference were recorded in every case. The median absolute basis-projection discrepancy was only around **1e−8 to 1.6e−7** across cells, but this favorable small discrepancy is specific to this one generating mean/basis combination and cannot be assumed for empirical gaze functions.

The nominal 90% two-sided criteria used `|c' beta_hat−c' beta_projected| ≤ t_0.95,df × SE_CR2`, once with coefficient-specific **conditional Satterthwaite df** and once with `G−1` df. Plug-in Satterthwaite df **does not account for fitting REML covariance on the same observed outcomes**, and neither target qualified this inference procedure for general eye tracking.

## Complete eight experimental source cells

Every denominator is **16 independently generated original source blocks per cell**, intentionally paired with other cells. 'Inclusion' is truth inclusion **conditional on a numerically accepted computation**. Here all computations were accepted, so the joint numerical-success-and-inclusion fractions happen to coincide; this is not guaranteed under other seeds or covariance configurations.

| Participants | Covariance source | Observations | Point deletion | Oracle accepted | Plug-in accepted | Oracle conditional Sat inclusion | REML plug-in conditional Sat inclusion | Oracle median Sat df | Plug-in median Sat df |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| 24 | independent | complete | 0.000 | 16/16 | 16/16 | 15/16 | 15/16 | 11.624 | 11.617 |
| 24 | independent | time_mar_20 | 0.203 | 16/16 | 16/16 | 15/16 | 15/16 | 11.210 | 11.227 |
| 24 | dependent | complete | 0.000 | 16/16 | 16/16 | 15/16 | 15/16 | 10.985 | 10.223 |
| 24 | dependent | time_mar_20 | 0.201 | 16/16 | 16/16 | 15/16 | 15/16 | 10.741 | 9.211 |
| 96 | independent | complete | 0.000 | 16/16 | 16/16 | 15/16 | 15/16 | 52.292 | 52.284 |
| 96 | independent | time_mar_20 | 0.203 | 16/16 | 16/16 | 15/16 | 15/16 | 49.876 | 49.871 |
| 96 | dependent | complete | 0.000 | 16/16 | 16/16 | 16/16 | 16/16 | 49.680 | 48.891 |
| 96 | dependent | time_mar_20 | 0.198 | 16/16 | 16/16 | 16/16 | 16/16 | 47.410 | 46.257 |

## Statistical interpretation and limitations

In this favorable, correctly specified Gaussian covariance source, *both* target methods accepted all 128 paired computations. Their recorded 90%-nominal **conditional Satterthwaite truth-inclusion indicators agreed in every original source cell**: 15/16 (93.75%) for n24 independent/dependent, complete/time-MAR and n96 independent complete/time-MAR, and 16/16 (100%) for n96 dependent complete/time-MAR. The conventional t(G−1) decisions were also identical in this source. These are very coarse empirical proportions based on **16 independent source blocks only**; for 15/16, the unadjusted Wilson 95% interval for each cell's independent generating-block inclusion probability is approximately **0.717–0.989**, and for 16/16 approximately **0.806–1**. Both include nominal 0.90. Reusing the same latent generating block across multiple conditions makes the eight cells highly dependent and prevents pooling their 128 records as independent coverage replicates.

The observed near-equality of two targets' final interval decisions is **NOT proof that estimating covariance is irrelevant**: plug-in and oracle Satterthwaite df can differ, and the computational decisions might diverge under high-leverage, covariance-boundary, non-Gaussian, misspecified, or informative-dropout cases. Model-relative component variance uncertainty, estimated REML nuisance score uncertainty, fitted covariance sensitivity and the R22 explicit refusal gate must be examined in larger **genuinely independent** simulation blocks. This first pilot can identify gross failures but lacks precision to establish satisfactory calibration, equivalence, or a release-ready procedure.

This source did not test MNAR, participant-level dropout, sensor-floor model boundaries, large high-leverage covariates, incorrectly selected working covariance, or simultaneous functional bands. **No source-specific nuisance covariance estimation correction was built into the Satterthwaite df**, and no multiple-comparison-adjusted or function-wide inference was calculated.

`oracle_covariance_reference_contract_verified=true`; `r32_original_pilot_source_complete=true`; `plug_in_covariance_inclusion_same_as_oracle_in_this_small_source=true`; `nuisance_estimation_inference_qualified=false`; `90pct_pointwise_interval_qualified=false`; `simultaneous_functional_bands_qualified=false`; `release_authorized=false`. Maintain [#289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289) and [#296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296) OPEN. Original R20 41/256 failures and R22 32 numerically refused R20 cases unchanged; protected main, supported package API, 1.2 release tags and PyPI unmodified.
