# 1.1 integration audit

This audit records the supported post-1.0 surface on the `1.1.0.dev0` line after completion of the sparse/irregular programme tracked in issue #158. The audit base is protected `main` commit `97c2036bc30ecad099fc4d71e2ca6c8aed94ddf3`.

The purpose is integration governance, not another estimator tranche. Frozen `1.0.0` evidence and `ONE_DOT_ZERO_API_STABILITY.json` remain unchanged.

## Decision summary

The post-1.0 capabilities remain **supported module-scoped 1.1 APIs**. They are not mechanically promoted into `eyetrajectoriespy.__init__`.

This is deliberate:

- the frozen 1.0 root namespace remains a clear compatibility baseline;
- module names communicate the scientific contract (`sparse_multilevel`, `sparse_multivariate_async`, `sparse_partial_prediction`, and so on);
- root promotion would add many specialized result objects and helpers without simplifying the scientific workflow;
- a module-scoped API is still public and supported when its import path is explicitly documented and tested.

The formal 1.1 module API is listed in [1.1 module API](one-dot-one-module-api.md).

## Audited surface

| Tranche | Module | Supported 1.1 surface | Tabular/reporting contract | Root decision | Audit disposition |
|---|---|---|---|---|---|
| A1 conditional PACE uncertainty | `sparse_score_uncertainty` + `sparse_score_uncertainty_reporting` | `SparseFPCAScoreUncertaintyResult`, `sparse_fpca_score_uncertainty()` | `sparse_fpca_score_uncertainty_frame()`; reporting helper remains in the companion reporting module | module-scoped | Keep. The reporting split predates later co-located helpers; moving it now would create churn without changing the scientific contract. |
| A2 audited univariate bandwidth selection | `sparse_bandwidth_selection` | `SparseFPCABandwidthSelectionResult`, `select_sparse_fpca_bandwidths()` | result retains assignments, fold results, curve losses, candidate summaries and candidates; `sparse_fpca_bandwidth_selection_reporting_text()` | module-scoped | Keep. A single generic frame would collapse distinct audit tables and is not warranted. |
| A3 observation-process diagnostics | `observation_process` | `ObservationProcessData`, `ObservationProcessDiagnosticResult`, `observation_process_data()`, `diagnose_observation_process()` | `observation_process_frame()` selects retained diagnostic tables; `observation_process_reporting_text()` | module-scoped | Keep. Diagnostic/descriptive status remains explicit; no correction estimator is implied. |
| A4 conditional joint-PACE uncertainty | `sparse_multivariate_score_uncertainty` | `SparseMFPCAScoreUncertaintyResult`, `sparse_mfpca_score_uncertainty()` | `sparse_mfpca_score_uncertainty_frame()`, `sparse_mfpca_score_uncertainty_reporting_text()` | module-scoped | Keep. Mirrors A1 scientific semantics for the joint score system. |
| A5 audited planar bandwidth selection | `sparse_multivariate_bandwidth_selection` | `SparseMFPCABandwidthSelectionResult`, `select_sparse_mfpca_bandwidths()` | result retains multiple audit tables; `sparse_mfpca_bandwidth_selection_reporting_text()` | module-scoped | Keep. No generic frame for the same reason as A2. |
| B1 sparse participant/trial multilevel FPCA | `sparse_multilevel` | `SparseMultilevelFPCAResult`, `fit_sparse_multilevel_fpca()` | participant scores, trial scores and score diagnostics are explicit result tables; `sparse_multilevel_fpca_reporting_text()` | module-scoped | Keep. Separate level-specific tables are scientifically meaningful and should not be flattened into one ambiguous frame. |
| B2 asynchronous sparse planar MFPCA | `sparse_multivariate_async` | `SparseAsyncMFPCAResult`, `fit_sparse_mfpca_async()` | `sparse_mfpca_async_score_frame()`, `sparse_mfpca_async_reporting_text()` | module-scoped | Keep. The separate import path makes the asynchronous observation contract visible and avoids implying changed `fit_sparse_mfpca()` semantics. |
| C1 partial/future sparse prediction | `sparse_partial_prediction` | `SparseFPCAPartialPredictionResult`, `sparse_fpca_partial_trajectory_prediction()` | `sparse_fpca_partial_prediction_frame()`, `sparse_fpca_partial_prediction_reporting_text()` | module-scoped | Keep. Conditional prediction uncertainty is explicitly distinct from population-estimation uncertainty. |
| C1 participant-aware conformal band | `sparse_partial_conformal` | `SparseFPCAPartialConformalCalibrationResult`, `SparseFPCAPartialConformalBandResult`, `calibrate_sparse_fpca_partial_prediction_conformal()`, `sparse_fpca_conformal_prediction_band()` | calibration retains curve/unit scores directly; band uses `sparse_fpca_conformal_band_frame()` and `sparse_fpca_conformal_band_reporting_text()` | module-scoped | Keep. Coverage remains finite-grid future-observation coverage, not continuous latent-function coverage. |

## Result-object contract

All analysis result containers introduced by A1-C1 are frozen dataclasses. They retain scientific state and provenance rather than returning loosely structured tuples. Where a fitted population object is required for interpretation, the result keeps an explicit `reference` or equivalent fitted-object link; where that would be redundant (for example a full multilevel fit result), the fitted scientific objects are stored directly.

The audit does **not** require every result to have one `*_frame()` helper. A frame helper is appropriate when one natural tidy representation exists. It is not appropriate when the result intentionally contains multiple tables with different observational units, such as bandwidth-selection ledgers or participant/trial multilevel scores.

## Failure semantics

The post-1.0 sparse methods consistently fail closed for scientific-contract violations. Native sparse numerical/support failures use the established `SparseNativeError` family where a machine-readable status code is scientifically useful; ordinary Python `TypeError`, `ValueError`, or `KeyError` remain appropriate for malformed argument types/names.

The audit found no justification for inventing a second exception hierarchy for 1.1. In particular:

- bandwidth selectors retain candidate/fold failures when the declared `failure_action` requests retention;
- score-uncertainty and prediction systems expose conditioning/PSD failures rather than silently regularizing beyond the declared ridge/policy;
- observation-process diagnostics do not infer missing candidate rows from timestamp gaps;
- asynchronous MFPCA does not silently synchronize coordinates;
- conformal calibration does not interpolate missing future responses.

## Terminology and uncertainty scope

The combined surface uses the following distinctions consistently:

- **curve**: one functional trajectory/trial row in `IrregularTrajectorySet`;
- **participant/group**: clustering/resampling unit declared through metadata when repeated curves are dependent;
- **sample/observation**: one retained native measurement, never a synonym for participant;
- **conditional score/prediction uncertainty**: conditions on fitted mean/covariance/eigensystem/noise objects;
- **population-estimation uncertainty**: not included unless a separate full-refit procedure explicitly states otherwise;
- **conformal coverage** in C1: simultaneous coverage of future observed measurements on the declared finite target grid under the stated exchangeability/grouping contract, not continuous-domain latent-function coverage.

No integration edit should weaken these distinctions for shorter wording.

## Naming audit

The new names follow the established forward conventions closely:

- fitters use `fit_*` (`fit_sparse_multilevel_fpca`, `fit_sparse_mfpca_async`);
- selectors use explicit `select_*_bandwidths` rather than hiding selection inside a fitter;
- result objects end in `Result`;
- natural tidy views use `*_frame`;
- manuscript wording uses `*_reporting_text`;
- participant/group resampling requires an explicit metadata column rather than treating repeated trials as independent.

Two intentional structural exceptions are retained:

1. A1's reporting helper remains in `sparse_score_uncertainty_reporting` rather than being moved into the numerical module.
2. A2/A5/B1 expose multiple scientifically distinct DataFrames directly rather than manufacturing one catch-all frame.

Neither exception changes the estimand, creates duplicate analysis routes, or prevents a stable documented import path.

## Duplicate-route audit

No post-1.0 method is merely a duplicate spelling of an existing stable analysis:

- `select_sparse_fpca_bandwidths()` and `select_sparse_mfpca_bandwidths()` are opt-in selectors and do not replace fitter defaults;
- `fit_sparse_multilevel_fpca()` estimates a sparse hierarchical covariance decomposition, unlike dense common-grid `fit_multilevel_fpca()`;
- `fit_sparse_mfpca_async()` generalizes the raw observation contract to coordinate-specific grids and leaves synchronous `fit_sparse_mfpca()` unchanged;
- sparse partial prediction forecasts a future functional segment from native history and is distinct from scalar-outcome FPCR future prediction;
- participant-aware partial conformal bands target future observed trajectory measurements, not anomaly p-values from `split_conformal_fpca_anomaly()`.

## Concrete integration finding

The scientific modules and guides were qualified individually, but the central `docs/reference/api.md` remained centered on the frozen/root 1.0 namespace and therefore omitted the supported module-scoped A1-C1 APIs. This is a documentation integration defect.

R1 resolves it by:

1. declaring the supported module-scoped surface in [1.1 module API](one-dot-one-module-api.md);
2. adding an executable import/immutability/root-boundary contract test;
3. linking the module-scoped catalogue from the API-stability documentation;
4. leaving the frozen 1.0 manifest and root namespace untouched.

## Deferred to later readiness tranches

This audit does not decide release-candidate readiness. R2-R4 under issue #183 still need to reconcile the release narrative, run end-to-end product analyses, and consolidate exact-main validation/performance evidence. Those steps may identify ergonomic gaps that warrant small additive integration fixes before any `1.1.0rc1` decision.
