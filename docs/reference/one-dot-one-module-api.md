# 1.1 module-scoped API

The `1.1.0.dev0` line adds specialized sparse/irregular capabilities as **supported module-scoped APIs**. These names are intentionally not inserted into the frozen 1.0 root namespace.

Use the import paths shown below. The frozen 1.0 root API remains documented in [Public API](api.md); the rationale and integration decisions are recorded in the [1.1 integration audit](one-dot-one-integration-audit.md).

## Conditional sparse PACE score uncertainty

::: eyetrajectoriespy.sparse_score_uncertainty.SparseFPCAScoreUncertaintyResult
::: eyetrajectoriespy.sparse_score_uncertainty.sparse_fpca_score_uncertainty
::: eyetrajectoriespy.sparse_score_uncertainty.sparse_fpca_score_uncertainty_frame
::: eyetrajectoriespy.sparse_score_uncertainty_reporting.sparse_fpca_score_uncertainty_reporting_text

## Audited sparse-FPCA bandwidth selection

::: eyetrajectoriespy.sparse_bandwidth_selection.SparseFPCABandwidthSelectionResult
::: eyetrajectoriespy.sparse_bandwidth_selection.select_sparse_fpca_bandwidths
::: eyetrajectoriespy.sparse_bandwidth_selection.sparse_fpca_bandwidth_selection_reporting_text

The result intentionally retains several audit tables rather than exposing one catch-all frame.

## Observation-process diagnostics

::: eyetrajectoriespy.observation_process.ObservationProcessData
::: eyetrajectoriespy.observation_process.ObservationProcessDiagnosticResult
::: eyetrajectoriespy.observation_process.observation_process_data
::: eyetrajectoriespy.observation_process.diagnose_observation_process
::: eyetrajectoriespy.observation_process.observation_process_frame
::: eyetrajectoriespy.observation_process.observation_process_reporting_text

These APIs are descriptive diagnostics. They do not identify MAR/MNAR mechanisms or apply inverse-intensity correction.

## Conditional sparse joint-PACE score uncertainty

::: eyetrajectoriespy.sparse_multivariate_score_uncertainty.SparseMFPCAScoreUncertaintyResult
::: eyetrajectoriespy.sparse_multivariate_score_uncertainty.sparse_mfpca_score_uncertainty
::: eyetrajectoriespy.sparse_multivariate_score_uncertainty.sparse_mfpca_score_uncertainty_frame
::: eyetrajectoriespy.sparse_multivariate_score_uncertainty.sparse_mfpca_score_uncertainty_reporting_text

## Audited sparse-MFPCA bandwidth selection

::: eyetrajectoriespy.sparse_multivariate_bandwidth_selection.SparseMFPCABandwidthSelectionResult
::: eyetrajectoriespy.sparse_multivariate_bandwidth_selection.select_sparse_mfpca_bandwidths
::: eyetrajectoriespy.sparse_multivariate_bandwidth_selection.sparse_mfpca_bandwidth_selection_reporting_text

The measurement-error covariance is declared separately and is not silently tuned by this selector.

## Native sparse participant/trial multilevel FPCA

::: eyetrajectoriespy.sparse_multilevel.SparseMultilevelFPCAResult
::: eyetrajectoriespy.sparse_multilevel.fit_sparse_multilevel_fpca
::: eyetrajectoriespy.sparse_multilevel.sparse_multilevel_fpca_reporting_text

Participant scores, trial scores, and score diagnostics remain separate result tables because they have different observational units.

## Asynchronous coordinate-specific sparse planar MFPCA

::: eyetrajectoriespy.sparse_multivariate_async.SparseAsyncMFPCAResult
::: eyetrajectoriespy.sparse_multivariate_async.fit_sparse_mfpca_async
::: eyetrajectoriespy.sparse_multivariate_async.sparse_mfpca_async_score_frame
::: eyetrajectoriespy.sparse_multivariate_async.sparse_mfpca_async_reporting_text

This path operates on exact coordinate-specific native observation times represented by a union timestamp container. It does not interpolate or nearest-neighbour synchronize raw x/y measurements.

## Sparse partial/future trajectory prediction

::: eyetrajectoriespy.sparse_partial_prediction.SparseFPCAPartialPredictionResult
::: eyetrajectoriespy.sparse_partial_prediction.sparse_fpca_partial_trajectory_prediction
::: eyetrajectoriespy.sparse_partial_prediction.sparse_fpca_partial_prediction_frame
::: eyetrajectoriespy.sparse_partial_prediction.sparse_fpca_partial_prediction_reporting_text

The conditional moments use the full fitted sparse-FPCA covariance and are conditional on the fitted population objects.

## Participant-aware split-conformal future-trajectory bands

::: eyetrajectoriespy.sparse_partial_conformal.SparseFPCAPartialConformalCalibrationResult
::: eyetrajectoriespy.sparse_partial_conformal.SparseFPCAPartialConformalBandResult
::: eyetrajectoriespy.sparse_partial_conformal.calibrate_sparse_fpca_partial_prediction_conformal
::: eyetrajectoriespy.sparse_partial_conformal.sparse_fpca_conformal_prediction_band
::: eyetrajectoriespy.sparse_partial_conformal.sparse_fpca_conformal_band_frame
::: eyetrajectoriespy.sparse_partial_conformal.sparse_fpca_conformal_band_reporting_text

The conformal claim is simultaneous finite-grid coverage for future **observed measurements** under the declared exchangeability/grouping contract. It is not continuous-domain latent-function coverage.

## Compatibility note

These supported 1.1 module paths are additive. They do not alter the signatures, result schemas, or scientific meanings frozen in `ONE_DOT_ZERO_API_STABILITY.json`. A later decision to expose selected names at package root would itself be an additive API decision and would require a separate explicit review; this page does not imply such promotion.
