# Object contracts

The result objects below preserve the numerical outputs and provenance of the package contracts. Their corresponding equations are collected in the [mathematical reference](../methods/mathematical-reference.md), and representative plotting outputs are shown in the [visual gallery](../methods/visual-gallery.md).


## `MathematicalContract`

Immutable metadata linking one scientific contract to a stable key, title, registered public functions, one or more LaTeX equation bodies, an explicit mathematical-reference anchor, and a short scope boundary.

The registry is documentation metadata only. A contract lookup does not fit a model, select components, alter defaults, or execute an estimator.

## `TrajectoryDistanceSensitivityResult`

Stores all declared distance-specification names, complete native-scale
distance matrices, specification metadata, every unique curve-pair distance
and within-specification rank, pairwise global comparison diagnostics,
per-curve local-neighborhood overlap diagnostics, deterministic neighbor
orders, neighborhood cutoff-tie flags, selected dimensions, dimension
weights, curve IDs, neighbor-k, and provenance.

The object is descriptive. It does not contain a consensus distance, a
preferred metric, or inferential p-values for the dependent upper-triangle
distance entries.

## `DynamicTimeWarpingResult`

Stores the returned DTW distance together with the raw cumulative cost, the N+M-normalized distance when symmetric2 makes that quantity defined, one deterministic optimal monotone alignment path, local distances, per-path step weights, weighted local contributions, path length, mean local distance, input sequence lengths/dimensionality, the optional Sakoe-Chiba sample-index radius, the declared step pattern, normalization denominator, and provenance.

For symmetric1, normalized_distance and normalization_denominator remain undefined rather than being filled with an arbitrary length correction. For symmetric2, weighted_local_costs sum to raw_distance and normalized_distance is raw_distance divided by n_points_a + n_points_b.

The stored path is an audit object, not a claim of unique correspondence: multiple optimal DTW paths can exist. Recorded timestamps are not used by the recurrence, and the object records that distinction explicitly.

## FunctionalMixedEffectsResult

Stores the fixed-effect coefficient functions and pointwise standard errors,
fixed B-spline basis/knots, the participant random basis, fixed basis
coefficients and covariance, residual variance, fitted/residual/observed
functional responses, scalar design/rank diagnostics, participant membership,
optimization state, backend warnings, likelihood, time/dimension semantics,
provenance, and the fitted backend object. Participant-only fits retain the
historical statsmodels result; explicit 0.48 participant→trial fits retain the
profiled nested-backend optimizer state instead.

For every fit it also retains the complete random-effect design matrix, full
random-effect covariance, covariance eigenvalues, covariance condition number,
random-effect dimension, free covariance parameter count, boundary/singularity
diagnostics, and participant BLUP random-intercept coefficients/functions.

When `random_slope_predictor` is supplied, the object additionally retains the
exact predictor name, random-slope basis, participant BLUP slope coefficients
and functions, slope covariance block, and intercept/slope cross-covariance
block. Version 0.45 supports exactly one random functional slope and does not
choose it automatically.

The legacy `random_effect_functions` field remains the participant random-
intercept function. This preserves the historical two-dimensional
participant-by-time contract; random-slope functions are exposed separately
because their contribution to a fitted curve is multiplied by the curve-level
slope-predictor value.

A random-slope fit is refused when the predictor lacks within-participant
variation or when the participant count does not exceed the number of free
unstructured random-effect covariance parameters.

When `trial_random_effect="functional_intercept"` is explicitly requested,
the object additionally retains the trial column, source/composite trial IDs,
trial basis and knots, trial BLUP coefficients/functions, one shared
unstructured trial-basis covariance, its eigenvalues and condition number,
free covariance-parameter count, and boundary/singularity diagnostics. The
nested model requires unique participant/trial pairs and at least two trials
per participant. Participant and trial covariance matrices remain distinct.

Version 0.49 additionally retains the declared residual-correlation family,
jointly estimated `phi` or `rho` when applicable, parameter name/unit and
numerical bounds, within-trial residual correlation matrix, eigenvalues and
condition number, regular-grid diagnostics, explicit numerical-bound and practical exponential-
independence flags, and both raw and whitened conditional residual functions. Exponential
correlation uses physical time; AR(1) uses index steps and is accepted only on
an equally spaced common grid. Residual covariance is block diagonal by source
curve/trial.

The object does not imply that a serial covariance family was selected
automatically, that raw residual ACF should be flat under a correlated-error
model, that whitening removes fitted-parameter uncertainty, or that covariance
components are uniquely identifiable when a smooth trial effect and a
long-range residual process compete. It also does not represent multiple trial
random effects, multiple participant random slopes, or multivariate response
covariance.


## Functional mixed-effects covariance-sensitivity objects

`FunctionalMixedEffectsCovarianceSpecification` is a compact declaration of
one covariance structure: model name, optional participant random-slope
predictor, optional trial functional random intercept, and residual-correlation
family. It is a declaration/audit object; it does not fit a model.

`FunctionalMixedEffectsCovarianceSensitivityResult` stores the ordered
predeclared specifications, explicit reference label, successful fit mapping,
retained failure mapping, model-level comparison table, complete
coefficient-function comparison table, coefficient supremum/L2 summaries,
optional simultaneous-band width comparisons, functional variance
decomposition, raw/whitened residual diagnostic table, declared maximum lag,
and provenance.

Failed specifications remain members of the result even though they have no
fitted object. Their model-summary rows retain the failure reason and NaN
numerical comparison fields.

The result contains no best-model field, ranking, likelihood-ratio p-value,
model weight, or automatic covariance recommendation. Information criteria are
only populated after the strict successful-fit comparability contract passes.
For BIC, the stored convention uses \(n=n_{\mathrm{curves}}n_{\mathrm{time}}\);
the provenance records that this is a calculation convention rather than a
claim about a unique effective sample size for clustered functional data.

Participant intercept variance, participant slope variance when present,
intercept/slope cross-covariance, trial variance, and residual variance remain
separate in the retained functional variance-decomposition table.

## Generalized function-on-scalar result objects

`GeneralizedFunctionOnScalarResult` stores the fitted marginal coefficient
functions on the declared link scale, robust pointwise standard errors, the
B-spline basis coefficients and robust parameter covariance, fitted linear
predictor and marginal mean functions, observed response functions, scalar
design matrix, participant cluster identities, family/link, basis contract,
working-correlation contract, convergence diagnostics and provenance. For an
exposure-adjusted Poisson fit it additionally retains the aligned exposure,
log exposure, exposure units/expansion flag, marginal rate functions, and
separate rate- and count-scale linear predictors. For grouped-binomial fits it
retains the original integer successes, integer denominators, observed success
proportions, denominator-specific fitted expected successes, and whether a
curve-level denominator was explicitly expanded over time.

`GeneralizedFunctionOnScalarBootstrapResult` stores whole-participant
case-bootstrap coefficient-function refits together with the sampled source
participant indices and both source and unique bootstrap participant
identities. Duplicate source-participant draws therefore remain auditable
without being collapsed into one GEE cluster.

`GeneralizedFunctionOnScalarBandResult` stores observed-grid simultaneous
link-scale coefficient bands, bootstrap maximum statistics, critical values,
confidence level, simultaneous scope and the full bootstrap object used for
calibration.

These objects intentionally do not contain conditional random effects,
working-correlation selection results, response-scale coefficient functions, or
an automatically chosen family/link/basis.

### Generalized fixed-profile prediction objects

`GeneralizedFunctionOnScalarPredictionResult` stores the fixed profile IDs,
their exact scalar design rows, marginal linear-predictor and response-mean
functions, robust delta-method standard errors, observed predictor minima/maxima,
and a per-profile extrapolation flag. Exposure-adjusted Poisson predictions
also retain the selected prediction scale, target exposure when supplied,
rate functions, expected-count functions, and separate rate/count linear
predictors. Profile and target-exposure values are fixed targets and are not
resampled.

`GeneralizedFunctionOnScalarPredictionBootstrapResult` projects every retained
whole-participant coefficient-bootstrap draw through every fixed profile. It
therefore preserves the dependence among profile predictions and directly
retains the source coefficient-bootstrap object rather than drawing a second
bootstrap sample.

`GeneralizedFunctionOnScalarPredictionBandResult` stores simultaneous
linear-predictor bands and their monotone inverse-link transformations to the
marginal response scale. Calibration is over the observed grid with either
profile-specific or complete declared-profile-family scope.

`GeneralizedFunctionOnScalarMeanDifferenceResult` stores one predeclared
response-scale profile difference, its paired bootstrap draws, pointwise
bootstrap standard errors, observed-grid simultaneous band, explicit
`contrast_scale`/`inference_scale`, and physical-bound diagnostic. For
Bernoulli outcomes, intervals that extend beyond the logical [-1, 1] difference
range are flagged and retained rather than silently clipped. Exposure-adjusted
Poisson objects may represent a rate difference, a positive rate ratio
(calibrated on the log-rate-ratio scale), or an expected-count difference.

These objects are mean-function inference objects, not future-response
prediction intervals. They do not select profiles or contrasts automatically
and do not propagate uncertainty in the fixed predictor-profile values.

## Function-on-scalar result objects

`FunctionOnScalarResult` stores the observed-grid coefficient functions, HC1 pointwise sandwich standard errors, fitted and residual functions, the exact functional responses used as inference units, the full scalar design matrix, rank and residual degrees of freedom, coefficient/predictor names, inference-unit IDs, curves-per-unit counts, time/dimension semantics, source curve IDs, and provenance.

`FunctionOnScalarBootstrapResult` stores every wild-bootstrap coefficient replicate and every multiplier draw together with the fixed reference fit. The design matrix is held fixed across bootstrap replicates.

`FunctionOnScalarBandResult` stores simultaneous lower/upper coefficient bands, coefficient-specific or familywise critical values, retained maximum statistics, confidence level, scope, the full bootstrap object, and provenance. The band is simultaneous over the declared observed grid, not between unsampled times.

Participant mode in version 0.35 means equal-weight participant-average functional responses with predictors required to be constant within participant. These objects do not represent a functional mixed-effects model.

## Multivariate surrogate result objects

`MultivariateIAAFTResult` stores the complete surrogate ensemble, original
selected multichannel values, curve/dimension semantics, analyst-declared
reference dimension, channel-pair labels, convergence iterations, per-channel
relative spectrum errors, per-pair relative complex cross-spectrum errors,
algorithm tolerances, random seed, and provenance.

`MultivariateSurrogateNonlinearityResult` stores the observed statistic,
complete surrogate-statistic distribution, plus-one Monte Carlo p-value,
alternative, nested multivariate-surrogate result, and interpretation
provenance.

The exact contract is asymmetric: marginal value distributions are exact after
rank remapping, whereas final spectral/cross-spectral preservation is
approximate and auditable through retained errors.

## `RecurrenceNetworkResult`

Stores the sparse undirected adjacency matrix induced by one auto-recurrence
plot, node degree and normalized degree, local clustering, connected-component
labels/sizes, edge count, all-pairs graph density, transitivity, mean local
clustering, component/isolation summaries, the complete source
`RecurrenceResult`, and provenance.

Graph density uses all unordered node pairs and is kept distinct from the
source recurrence rate when a Theiler window changes the eligible-pair
denominator. No dense graph layout, community partition, shortest-path policy,
or dynamical dimension is selected automatically.

## `JointRecurrenceResult`

Stores the sparse logical intersection of synchronized auto-recurrence
matrices, the exact common time grid, every component recurrence object and
label, joint recurrence rate, unique joint recurrent-pair count, shared
eligible-pair denominator, Theiler window, and provenance.

The nested component objects preserve their own state dimensions, metrics,
radii, target/achieved recurrence rates, and source provenance. The result does
not imply cross-recurrence, lag alignment, threshold harmonization, or causal
coupling.

## Nonlinear-dynamics result objects

`DelayEmbeddingResult` preserves reconstructed state vectors, endpoint times, selected source dimensions, explicit delay in samples/time, and whether a constant physical delay exists.

`EmbeddingDelayDiagnosticResult` and `EmbeddingDimensionDiagnosticResult` retain the diagnostic tables and all AMI/FNN settings without choosing `tau` or `m`.

`RecurrenceResult` stores recurrence as a SciPy CSR sparse matrix together with radius policy, achieved recurrence rate, metric, Theiler exclusion, state dimension, and source provenance. `RQAResult` records line thresholds and recurrence-line counts in addition to summary metrics. `WindowedRQAResult` retains the number of trailing samples outside full windows.

`WindowedRQAFunctionalResult` carries a native RQA-metric `TrajectorySet` plus every per-curve `WindowedRQAResult`. It retains the selected metric list, window and step sizes, overlap samples/fraction, trailing-tail count, undefined-value policy, and the explicit statement that window rows are not independent sampling units. Solved per-window radii remain available in the retained window tables.

`LocalDivergenceResult` retains the full mean log-divergence curve, usable-neighbor counts, zero-distance counts, and neighbor assignments. `LargestLyapunovResult` adds only the analyst-declared linear fit and its slope/R²/SE.

`SurrogateNonlinearityResult` retains every surrogate statistic, IAAFT iteration count, random seed, alternative, plus-one p-value, and test provenance.

`PoincareCrossingResult`, `LocalReturnMapResult`, and `ReturnMapStabilityResult` are explicitly experimental. They retain section definition, interpolated crossings, neighborhood selection, fitted empirical Jacobian, residual diagnostics, design condition number, eigenvalues, spectral radius, and the non-Floquet interpretation boundary.

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

## DiscreteTransferEntropyResult

Stores the empirical transfer-entropy estimate in bits, every local log-ratio
contribution, effective sample indices, complete integer-coded source/target
states, declared target/source history lengths and source lag, state/history
support diagnostics, and provenance. Continuous observations are not silently
discretized and history/lag settings are never selected automatically.

## TransferEntropyCircularShiftTestResult

Stores the observed `DiscreteTransferEntropyResult`, the exact analyst-declared
circular source shifts, every surrogate transfer-entropy estimate, surrogate
mean, surrogate-centered transfer entropy, plus-one upper-tail Monte Carlo
p-value, attainable p-value resolution, and null-model provenance. The object
does not claim causal identification and does not generate or optimize shifts.

## TransferEntropySensitivityResult

Stores the complete transfer-entropy specification table, descriptive variation
summary, declared target/source history and source-lag grids, original
integer-coded source/target states, optional common circular-shift set, and full
provenance. Every Cartesian-product specification is retained unless the
analysis fails closed on an invalid declared combination.

The object does not contain a preferred specification, optimization score,
winner flag, or automatic selection result. When circular shifts are supplied,
the same shift set is applied to every specification; resulting p-values remain
unadjusted across the sensitivity multiverse unless the analyst supplies a
separate multiplicity procedure.

## ConditionalTransferEntropyResult

Stores empirical conditional transfer entropy in bits, every local conditional
TE contribution, effective sample indices, complete integer-coded
source/target/conditioning series, and the exact reconstructed
target/source/conditioning histories used at every effective transition.

The result also retains state counts, target-history count,
conditioning-history count, target+conditioning and source+conditioning support,
complete joint-history support, singleton fraction, minimum/maximum/mean
complete-joint-history cell counts, all five history/lag settings, and full
provenance. No empirical-support threshold is applied automatically.

## ConditionalTransferEntropyCircularShiftTestResult

Stores the observed `ConditionalTransferEntropyResult`, exact analyst-declared
source-only circular shifts, every surrogate conditional-TE estimate, surrogate
mean, surrogate-centered conditional TE, plus-one upper-tail Monte Carlo
p-value, attainable p-value resolution, and null provenance identifying the
source as shifted while target and conditioning processes remain fixed.

Neither object claims causal identification or complete confounder adjustment.

## FunctionalMixedEffectsResidualDiagnosticsResult

Stores the reference converged mixed-effects fit together with three explicit
descriptive residual-diagnostic tables: trial, participant, and overall.

The trial table is primary. For every source curve and every declared index lag
from zero through `max_lag`, it retains the residual mean/SD/RMS,
autocovariance, autocorrelation, empirical semivariance, pair count, and
mean/minimum/maximum physical time separation. Trials with exactly zero
residual variance are retained and their ACF is undefined rather than replaced
with zero.

Participant and overall tables are pair-count-weighted summaries of the
trial-level quantities and retain the total number of trials and the number
with defined ACF values. Version 0.49 also records `residual_scale`: `"raw"`
uses the native conditional residual functions, while `"whitened"` applies
the fitted within-trial residual-covariance Cholesky factor before computing
the same diagnostics. The object records that no automatic lag selection,
physical-lag binning, AR(1)/exponential selection, trial-level random-effect
selection, or other covariance-structure selection occurred.

Exact physical-lag pair contributions are generated on demand by
`functional_mixed_effects_residual_pair_frame()` rather than materialized
inside the result object.

## FunctionalMixedEffectsBootstrapResult

Stores the reference `FunctionalMixedEffectsResult`, every participant-cluster
bootstrap fixed-basis coefficient estimate, reconstructed coefficient
functions, exact sampled participant-index matrix, bootstrap mean and pointwise
standard deviations, random seed, covariance-conditioning label, and full
provenance.

Whole participant trial bundles are sampled with replacement. Fixed effects are
re-estimated in every replicate, but the reference participant covariance,
optional shared trial covariance, residual variance, fixed/random bases, spline
degree, and preprocessing are held fixed. Rank-deficient or unsolvable
resamples raise; none are silently replaced.

## FunctionalMixedEffectsBandResult

Stores observed-grid simultaneous lower/upper coefficient bands, participant-
bootstrap pointwise standard errors, coefficient-specific or familywise critical
values, retained maximum statistics, confidence level, simultaneous scope, the
complete bootstrap object, and provenance.

The band does not claim simultaneous coverage between unsampled time points and
does not include variance-component, basis-selection, or preprocessing
uncertainty.

## FunctionalMixedEffectsFullRefitBootstrapResult

Stores the reference mixed-effects fit, every bootstrap fixed-basis coefficient
matrix, reconstructed coefficient functions, sampled participant-index matrix,
source participant IDs, distinct bootstrap participant IDs, bootstrap means and
pointwise standard deviations, and the complete refitted variance-component
distributions.

For every bootstrap replicate it retains the full participant random-effect
covariance, intercept covariance, optional slope covariance, optional
intercept/slope cross-covariance, participant covariance eigenvalues and
condition number, boundary and singularity flags, random-slope boundary flag,
residual variance, log likelihood, convergence status, and backend warnings.
For 0.48+ nested fits it additionally retains the full trial covariance
distribution, trial covariance eigenvalues/condition numbers, and
trial-specific boundary/singularity flags. For 0.49 serial fits it also retains
the bootstrap distribution of the residual-correlation parameter together with
its correlation-matrix condition number, numerical-bound flag, and practical
exponential-independence flag in every replicate.

Every occurrence of a sampled participant receives its own bootstrap
participant identity. For a nested trial model, every trial inside that
occurrence also receives a distinct bootstrap trial identity while preserving
the source participant/trial IDs in the audit record. Thus duplicate source
draws cannot be merged into one participant or trial random-effect realization.

The object records `failed_replicate_policy="raise"`. Failed replicates are
not silently discarded or replaced. Basis sizes, spline degree, preprocessing,
predictor specification, random-effect structure, REML/ML choice, and optimizer
remain the declared reference specification and are not automatically
reselected.

## Portable scientific-result snapshots

`PortableScientificResultSnapshot` is a transport/audit container returned by
`load_portable_result()`. It is intentionally **not** a reconstructed fitted
estimator. The snapshot exposes:

- the original result type;
- source and currently loaded package versions;
- decoded scientific payload;
- captured environment metadata when included;
- explicit unit metadata;
- explicit paths of backend/opaque fields that were not portable;
- the original manifest.

The `package_version_match` property reports whether the source package version
matches the package currently loading the snapshot. A mismatch is visible but
does not prevent reading schema-compatible scientific state.

The portable format is documented in
[Portable scientific results](../reproducibility/portable-results.md).

