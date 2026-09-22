# Object contracts

The result objects below preserve the numerical outputs and provenance of the package contracts. Their corresponding equations are collected in the [mathematical reference](../methods/mathematical-reference.md), and representative plotting outputs are shown in the [visual gallery](../methods/visual-gallery.md).


## `TrajectorySet`

Shape: `n_curves × n_time × n_dimensions`.

Key semantics:
- finite, strictly increasing time;
- unique curve and dimension names;
- one metadata row per curve;
- missing observations represented as `NaN`;
- explicit coordinate and time semantics;
- preserved provenance.

## `FPCAResult`

Stores the mean function, component functions, scores, explained variance, quadrature weights, scale factors, and original coordinate/time semantics.

## `RegistrationResult`

Keeps both original and registered curves. Warping functions are first-class outputs.

## `CompositionalFPCAResult`

Records log-ratio reference and zero-replacement epsilon.

## `MultilevelFPCAResult`

Separates participant-level and within-participant trial-level component fits and score tables.


## IrregularTrajectorySet

Stores one strictly increasing time vector and one value matrix per curve. It preserves curve-specific sampling without implying interpolation or a common grid.

Key semantics:

- every curve has at least two finite time points;
- all curves share the same functional dimension names;
- value matrices may contain missing observations;
- metadata remains one row per curve;
- projection to a common grid is a separate operation.

## FPCAStabilityResult

Stores the full-sample reference FPCA plus matched bootstrap component similarities, signs, assignments, explained-variance ratios, curve counts, resampling unit, random seed, and provenance.

## RegistrationSensitivityResult

Stores paired unregistered/registered FPCA fits, component matching, signed shape similarity, and sign-aligned score correlations.

## BasisProjectionResult

Wraps an optional backend basis object together with the selected functional dimension, basis family, number of basis functions, time domain, and analysis provenance.


## ConformalFunctionalAnomalyResult

Stores the proper-training FPCA/MFPCA reference, calibration and target IDs, calibration and target nonconformity scores, marginal split-conformal p-values, review flags, alpha, nonconformity definition, optional score-covariance choice, component count, scaling, and provenance.

The object makes the finite calibration resolution explicit through <code>minimum_attainable_p = 1 / (n_calibration + 1)</code>.

Review flags are never automatic exclusions.

The result records that this tranche provides **marginal curve-level conformal p-values only**. It does not claim calibration-conditional validity, multiple-testing correction, FDR control, or participant-clustered validity.

## FunctionalOutlierResult

Contains a diagnostic table, method identifier, optional FPCA reference, backend object where relevant, and provenance. Review flags are never interpreted as exclusions by the object.

## FPCAInfluenceResult

Stores the full-sample reference FPCA, group-level influence summary, component-level matched similarities/variance changes, the grouping variable, component count, and provenance.


## FPCACrossValidationResult

Stores fold-level held-out reconstruction error, curve-to-fold assignments,
candidate component counts, cross-validation unit, grouping variable, scaling,
random seed where applicable, and provenance.

The object records diagnostics only. Component selection remains an explicit
separate operation.

## FPCAComponentBandResult

Stores the full-sample reference FPCA, simultaneous lower/upper FPC functions, pointwise bootstrap standard errors, component or familywise critical values, bootstrap maximum statistics, matched similarities, confidence level, resampling semantics, optional eigengap-screen information, random seed, and provenance.

The object records that calibration applies to the observed time-by-dimension grid. It does not assert exact finite-sample coverage, continuous-domain coverage between sampled points, or individual-axis identifiability under near-tied eigenvalues.

## FPCAComponentEnvelopeResult

Stores the full-sample reference FPCA, pointwise lower/median/upper matched
bootstrap component functions, matched component similarities, envelope level,
resampling unit, random seed, and provenance.

The envelope is explicitly descriptive; the object does not assert pointwise or
simultaneous confidence coverage.


## FPCAScoreUncertaintyResult

Stores the full-sample reference FPCA, fixed target curve IDs and reference scores, matched/sign-aligned bootstrap target scores, percentile lower/median/upper summaries, bootstrap score standard deviations, component assignments and similarities, resampling semantics, target source, random seed, and provenance.

The uncertainty target is deliberately narrow: the target curves are fixed while the training sample used to estimate the FPCA basis is resampled. The result quantifies basis-estimation sensitivity only. It is not a complete latent-score confidence interval and does not include target measurement error, future-curve variability, preprocessing uncertainty, or full downstream-model propagation.

## FPCASpectrumUncertaintyResult

Stores the full-sample FPCA, matched bootstrap eigenvalues and per-component explained-variance ratios, rank-ordered bootstrap cumulative variance, bootstrap standard errors, studentized critical values/intervals, component assignments and similarities, calibration scope, resampling semantics, random seed, and provenance.

Individual eigenvalues and explained-variance ratios are attached to matched reference FPC identities. Cumulative explained variance instead preserves descending eigenvalue-rank order so the conventional “top k components” interpretation is not changed by bootstrap component swaps.

Familywise calibration applies across requested components separately for each spectrum metric and is not a joint guarantee across all three metrics. Intervals are not clipped to nonnegative or [0, 1] support.

## FPCASubspaceComparisonResult

Stores a reference and candidate FPCA, the selected contiguous component
indices, principal cosines, principal angles, Frobenius projector distance,
normalized projector distance, and provenance.

The comparison is invariant to sign changes, permutations, and rotations within
the selected subspace.

## FPCASubspaceStabilityResult

Stores the full-sample reference FPCA and bootstrap distributions of principal
cosines, principal angles, Frobenius projector distances, and normalized
projector distances for a selected contiguous FPC block.

The object summarizes descriptive eigenspace stability. It does not assert
identifiability of individual FPC axes or equality of population eigenspaces.


## SparseFPCAResult

Stores PACE score estimates, retained sparse-FPCA eigenvalues, selected
functional dimension, original curve IDs and metadata, coordinate/time
semantics, smoothing settings, PACE tolerance, normalization choice, backend
objects, and provenance.

The result records `fit_method="covariance"` and `score_method="PACE"`.
It does not imply that the original sparse observations were interpolated to a
common grid, and it does not represent joint multivariate x/y PACE.


## FunctionalMeanBandResult

Stores the estimated functional mean, simultaneous lower/upper observed-grid
band, pointwise standard errors, multiplier critical value and maximum
statistics, confidence level, inference-unit definition, effective unit IDs,
time/dimension semantics, and provenance.

For `unit="participant"`, the result targets the equal-weight mean of
participant-average trajectories. The object records that coverage is calibrated
over the observed time-by-dimension grid and does not assert continuous-domain
coverage between sampled points.


## FPCAWildBootstrapTruncationScanResult

Stores one fixed maximum-h FPCA/MFPCA reference, fixed target IDs, the consecutive candidate h grid, k=g, the common pseudo-truth projection, target × h reference projections, heteroscedastic SEs, critical values, lower/upper limits, interval centers and widths, and all candidate × bootstrap × target studentized roots.

Every bootstrap pseudo-response is shared across candidate h values. The object therefore supports direct volatility comparisons without injecting independent bootstrap randomness at each h.

## FPCAWildBootstrapTruncationSelectionResult

Stores a truncation scan together with adjacent width/center changes, width-stability and center-stability masks, their intersection, target-specific selected candidate indices/h values and intervals, analyst-supplied rho_w/rho_c, the paper run parameter r, failure behavior, and provenance.

An unselected target is represented explicitly when warn/ignore behavior is requested. The selector never substitutes the largest candidate silently.

## FPCAWildBootstrapProjectionResult

Stores the fixed FPCA/MFPCA reference, target curve IDs, h-component reference centered projections, g=k pseudo-truth projections, reference heteroscedastic standard errors, bootstrap target projections, bootstrap-level heteroscedastic standard errors, studentized roots, target-wise critical values and interval limits, k-truncation residuals, multiplier/truncation settings, seed, and provenance.

The estimand is the centered functional projection relative to the training functional mean. The object does not add an intercept or future response noise.

The bootstrap keeps the functional regressors and FPCA basis fixed. Residuals and the pseudo-truth use k=g components; inference uses an explicit h>=g truncation.

The result records independent-curve-row semantics. The base object remains target-wise: it is not a clustered wild bootstrap, not a future-outcome prediction interval, and does not include component-selection uncertainty. Version 0.18 can post-calibrate its stored roots across the complete fixed-target family without changing this base object.

## FPCAWildBootstrapSimultaneousResult

Stores an existing `FPCAWildBootstrapProjectionResult`, the same-level target-wise critical values, one familywise max-|t| critical value, bootstrap replicate-wise maximum statistics, simultaneous lower/upper limits, confidence level, and provenance.

The object is a pure post-calibration result. It reuses the exact studentized roots from the base wild bootstrap and does not refit FPCA, refit score regression, recompute residuals, redraw multipliers, or rerun the bootstrap.

The simultaneous family is exactly every fixed target in the base result. A one-target family reduces exactly to the target-wise calibration. The familywise claim does not extend to future outcomes, unlisted targets, clustered/repeated-participant sampling, or component-selection uncertainty.

## FPCAWildBootstrapFamilyTestResult

Stores an existing `FPCAWildBootstrapProjectionResult`, supplied scalar or target-specific null values, observed studentized null discrepancies, target-wise bootstrap tail probabilities, single-step maxT-adjusted probabilities, replicate-wise maximum statistics, the complete-family global statistic/p-value, target/global rejection indicators at the declared alpha level, p-value correction, and provenance.

The result is a pure post-processing object. It reuses the exact studentized roots from the base wild bootstrap and does not rerun FPCA, score regression, residual estimation, multiplier generation, or bootstrap sampling.

With `pvalue_correction="plus_one"`, the minimum attainable probability is `1/(B+1)`; the explicit `"none"` option reports the raw empirical exceedance fraction and may return zero.

The package records that the bootstrap distribution is not explicitly generated under the null. Single-step maxT adjustment is reported for the complete declared family, while strong FWER control for arbitrary subsets of nulls is not claimed without additional subset-pivotality conditions.

The tests target fixed centered FPCR projections. They are not future-outcome tests, clustered/repeated-participant wild-bootstrap tests, or automatic corrections for adaptive family/truncation selection.

## FPCAWildBootstrapMonteCarloDiagnosticResult

Stores an existing `FPCAWildBootstrapFamilyTestResult`, target-wise and maxT-adjusted bootstrap exceedance counts, raw exceedance fractions, plug-in binomial Monte Carlo standard errors, Clopper-Pearson exact binomial interval limits, complete-family global precision diagnostics, decision-stability flags, the diagnostic confidence level, and provenance.

The object reuses the exact roots and observed test statistics from the supplied family-test result. It performs no new bootstrap draws and does not change the reported p-values or rejection indicators.

The exact intervals quantify finite Monte Carlo simulation precision conditional on the completed bootstrap design. They are not confidence intervals for target projections, do not quantify participant-sampling uncertainty, and do not add subset-pivotality, strong-FWER, clustered-bootstrap, or component-selection guarantees.

A `False` stability flag means the exact Monte Carlo interval is not wholly on the same side of alpha as the existing reported decision. It is a precision warning, not a reversal of the hypothesis-test result.

## FPCARegressionPredictionIntervalResult

Stores an existing paired-bootstrap Gaussian FPCR uncertainty object together with the centered full-sample residual pool, independently sampled residual draws, future-outcome predictive draws, marginal percentile limits, predictive standard deviations, confidence level, seed, and provenance.

Every predictive draw is exactly:

    paired-bootstrap conditional mean + independently sampled centered residual

The object therefore keeps estimation uncertainty and future response noise visible as separate ingredients.

The predictive intervals are marginal per fixed target trajectory. They assume a common/exchangeable response-error distribution and do not claim heteroscedasticity robustness, simultaneous target coverage, or a joint multivariate prediction region.

## FPCARegressionSlopeBandResult

Stores an existing paired-bootstrap Gaussian FPCR uncertainty object together with studentized simultaneous slope-band limits, pointwise bootstrap SEs, dimension-level critical values, bootstrap maximum statistics, calibration confidence level, scope, and provenance.

With global scope one maximum is taken over all observed time × dimension slope cells. With dimension scope one maximum is taken over time separately for each functional dimension.

The band reuses the exact slope bootstrap replicates already stored in the regression-uncertainty object; it does not initiate a new resampling scheme.

Coverage language is restricted to the observed grid. The object does not claim coverage between sampled time points and is not the operator-scaled FPCR significance procedure from recent theory.

## FPCARegressionUncertaintyResult

Stores the full-sample FPCA and Gaussian score-regression fits, the reconstructed functional slope in original trajectory units, bootstrap slope replicates and pointwise percentile summaries, reference/bootstrapped intercepts, fixed-target conditional-mean predictions and percentile summaries, resampling semantics, component count, scaling, seed, and provenance.

The functional slope is reconstructed from each complete FPCR refit, including the inverse-square channel-scale adjustment needed to map the score-regression coefficients back to the original functional predictor units.

Target intervals are confidence-style bootstrap summaries for the fitted conditional mean response of fixed target curves. They are not prediction intervals for future observed outcomes.

The component count is held fixed across bootstrap replicates. The object does not include model-selection uncertainty.

## FPCARegressionCVResult

Stores fold-level predictive losses, test-fold assignments, held-out predictions for every candidate FPC count, family/loss settings, grouping semantics, scaling, random-state information, and provenance. The object records selection evidence only; it does not silently choose a component count.

## FPCANestedRegressionCVResult

Stores outer-fold predictive losses, every inner candidate-loss summary, outer held-out predictions, selected component count for each outer fit, fold design, family/loss, and provenance. Outer test outcomes are not used during inner FPC-count selection.
