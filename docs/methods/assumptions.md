# Assumptions and diagnostics

## Common-grid FPCA

The core FPCA assumes complete functional observations on a common monotone grid after explicit preprocessing.

Check unresolved missing values, comparability of time domains, influential curves, and stability under defensible preprocessing choices.

## MFPCA scaling

Different dimensions can have different integrated variance. Compare `scaling="none"` and `scaling="dimension_sd"` when the scale choice is scientifically uncertain.

## Registration

Inspect warping functions. Extreme warpings can indicate that curves do not share a meaningful common template.

## Downstream modeling

FPCA scores are estimated features. Standard downstream errors generally do not propagate uncertainty in the estimated functional basis.


## Irregular-to-grid projection

Common-grid FPCA analyzes the **projected curves**, not the raw irregular observations. Inspect how overlap/union choice, target grid, and maximum interpolation gap change the retained data support.

## Bootstrap stability

Bootstrap FPC matching assumes the resampling scheme reflects the sampling design. Repeated trials nested within participants should not generally be resampled as though every trial were an independent participant.

Component similarity can also become ambiguous when eigenvalues are close and the corresponding eigenspace can rotate. In that situation, instability in individual component labels may coexist with stability of the lower-dimensional subspace.

## Sparse PACE FPCA

PACE-style sparse FPCA assumes an underlying smooth stochastic process observed at sparse, irregular times with measurement error. The conditional score estimates depend on the fitted population mean/covariance structure and measurement-error treatment.

The current eyetrajectoriespy adapter assumes that sparsity is represented by **absent samples**. A retained `NaN` at an observed sample time is not silently reinterpreted as an absent observation.

Smoothing choices and the observation-time design therefore form part of the model. Systematic observation patterns related to condition, stimulus, or participant characteristics can violate a simple random sparse-design interpretation and should be diagnosed substantively.

## Held-out reconstruction cross-validation

The fold definition must reflect the sampling unit. If participants contribute repeated trials, participant/group folds prevent the same participant from appearing in both training and testing.

FPCA centering, scaling, and eigenfunctions must be estimated inside each training fold. The resulting RMSE evaluates reconstruction of held-out trajectories under the stated representation; it is not automatically a criterion for external-outcome prediction.

## Matched bootstrap component envelopes

Pointwise envelope interpretation assumes that a bootstrap component can be meaningfully matched to a reference component. When matched similarity is low because eigenvalues are close or the subspace rotates, individual FPC envelopes should not be given strong local labels.

## Near-tied eigenvalues and eigenspaces

Individual eigenfunctions are most interpretable when the corresponding eigenvalues are sufficiently separated. With small eigengaps, sampling variation can rotate or reorder axes within an otherwise stable eigenspace.

Principal-angle diagnostics compare the span of a selected component block and are invariant to rotations inside that block. They still depend on the chosen functional representation, scaling, component boundary, and resampling design.

## Basis projection

Basis size controls approximation flexibility. A basis with too few functions can remove meaningful shape; a very flexible basis can retain measurement noise. Basis choice should be justified by the trajectory process rather than by visual smoothness alone.


## Simultaneous functional mean bands

The Gaussian multiplier procedure treats the chosen inference units as independent draws from the population relevant to the estimand. For repeated-trial studies, participant-level aggregation is therefore the intended route when participants are the independent sampling units.

The implementation requires complete finite values on a common grid. It does not solve informative missingness, asynchronous sparse sampling, or curve registration uncertainty.

Studentization assumes empirical pointwise variability is meaningful. Grid locations with zero empirical variance receive zero-width bands and are excluded from standardized division.

The current simultaneous target is finite: the observed time × functional-dimension grid. Smoothness assumptions needed to extend coverage to the entire continuous domain are not imposed by this API.


## Functional mixed-effects regression

The 0.36 model assumes a common finite observation grid and one Gaussian
functional response dimension. Participant groups are treated as independent,
while repeated curves within participant are linked through one participant
functional random intercept.

Fixed coefficient functions and random participant functions are represented
in analyst-declared clamped B-spline bases. Basis size and degree therefore
define the model space and should be justified or examined in sensitivity
analysis.

Conditional on the declared functional random effects, residual grid errors
are iid Gaussian with one variance. The model can include a participant
functional random intercept, from version 0.45 exactly one explicitly declared
participant random functional slope, and from version 0.48 one explicitly
declared nested trial functional random intercept. It still does not represent
additional serial residual correlation after those smooth random effects.

The participant random-basis coefficient vector is multivariate Gaussian with
an unstructured covariance. The optional trial random-basis coefficient vector
is separately multivariate Gaussian with one shared unstructured covariance
across nested trials. Participant and trial random coefficients are modeled as
independent in 0.48; no participant–trial cross-covariance is estimated.

Enough independent participants are required to estimate the participant
covariance, and enough nested trials are required to estimate the trial
covariance. The participant/trial covariance-complexity guards are minimum
structural safeguards, not adequacy guarantees. Near-boundary covariance
estimates are retained and flagged.

Version 0.47 can diagnose dependence left in the conditional residual
functions through explicitly declared lags. Residual ACF/autocovariance and
empirical semivariance are descriptive checks of the fitted covariance
hierarchy; they do not validate iid errors by themselves and do not identify a
unique replacement covariance structure.

Pointwise fixed-effect standard errors condition on the fitted mixed-model
variance structure. They do not provide simultaneous functional coverage or
full variance-component uncertainty.

## Function-on-scalar regression

The observed-grid function-on-scalar model assumes that the declared scalar design is scientifically meaningful and full rank. Categorical coding, interactions, centering, and scaling must be constructed explicitly before fitting; the package does not infer them from column names or data types.

Curve-level mode assumes that each source trajectory is an independent inferential unit. Participant mode instead averages selected response functions within participant and assumes the declared predictors are constant within participant. This creates an equal-weight participant-level between-subject estimand; it does not identify within-participant trial effects.

The coefficient functions are estimated separately at each observed grid point under one shared design matrix. Version 0.35 imposes no coefficient smoothing or basis regularization, so local roughness in the coefficient curves can reflect both signal and sampling noise.

Pointwise uncertainty uses the HC1 sandwich variance. Simultaneous coefficient bands use a fixed-design wild bootstrap in which one multiplier is applied to the complete residual function for each independent inference unit. The calibrated claim is finite-dimensional over the observed time × selected-dimension grid.

The procedure is not a functional mixed-effects model. Participant-specific random functional effects, within-participant covariance, and trial-varying predictors require a different repeated-measures model.

## Predictive FPCA regression

Outcome-tuned component selection assumes that the chosen fold structure represents the intended prediction setting. FPCA centering, scaling, and eigenfunctions and the scalar regression must be estimated within each training fold.

For grouped repeated trials, group folds prevent participant leakage but do not alter the curve-level regression likelihood. Gaussian regression assumes the stated linear score/outcome relation for the predictive model; binomial regression additionally requires usable class variation and a convergent, non-separated fit in every training fold.

Nested CV is required when the performance of the complete component-selection procedure, rather than only the selected count, is the target of evaluation.


## Simultaneous FPC-shape bands

Bootstrap-calibrated FPC bands assume the selected resampling unit approximates independent sampling units. With repeated trials, participant-level resampling is usually the relevant contract when participants are the independent units.

Component matching and sign alignment handle label/sign indeterminacy across ordinary bootstrap perturbations, but they do not make a near-tied individual eigenfunction identifiable. The optional relative-eigengap screen is therefore descriptive and requires an analyst-supplied threshold.

The current calibration is finite over the observed time × functional-dimension grid. It does not impose smooth-process assumptions sufficient to extend simultaneous coverage continuously between sampled grid points.


## FPCA spectrum uncertainty

Bootstrap spectrum uncertainty assumes that the chosen resampling unit reflects the independent sampling unit. Repeated trials should not be resampled as independent curves when the inferential population is participant-level.

Eigenvalues and explained-variance ratios depend on the covariance geometry used by FPCA. For MFPCA, channel scaling is therefore part of the estimand and must remain fixed across bootstrap refits.

Individual bootstrap eigenvalues/ratios are attached to matched reference-FPC identities. Cumulative explained variance is intentionally different: it remains ordered by descending bootstrap eigenvalue rank because “top k components” is a rank-based estimand.

Studentized calibration is an approximation. The package does not assume that finite-sample bootstrap coverage is exact.


## FPC score basis-resampling uncertainty

The target trajectory is treated as fixed while the FPCA training sample is resampled. The resulting score distribution therefore targets uncertainty induced by re-estimating the functional mean, scaling, and eigenbasis under the selected bootstrap unit.

Curve-level basis resampling assumes curves are independent sampling units. Participant-level resampling should be used when repeated trials are clustered within participants and participants are the independent sampling units.

External targets must already use the same time grid, functional dimensions, coordinate system, and time unit as the training data. The routine does not perform hidden interpolation, coordinate transformation, unit conversion, or feature reordering.

Component matching and sign alignment make score coordinates comparable across ordinary bootstrap perturbations. They do not make a near-tied individual FPC axis population-identifiable.


## Gaussian FPCR paired-bootstrap uncertainty

The resampling unit must match the independent sampling unit. Curve-level resampling assumes independent trajectories. Participant-level resampling preserves repeated trials by resampling whole participant trial bundles together with their scalar outcomes.

The retained component count is treated as fixed during bootstrap inference. Any data-driven component-selection procedure is a separate stage and its uncertainty is not incorporated automatically.

The Gaussian score-regression design must remain full rank in the reference fit and in every bootstrap replicate. Invalid replicates are not silently discarded or redrawn.

For MFPCA with dimension scaling, the functional slope is mapped back to original trajectory units using the same scale parameters estimated inside each replicate.


## Simultaneous Gaussian FPCR slope bands

The 0.13 band assumes that the paired-bootstrap slope distribution from the 0.12 Gaussian FPCR analysis is the resampling distribution to be calibrated. No new independent-unit resampling is introduced at the band stage.

Studentization uses the bootstrap standard deviation of slope **deviations from the full-sample reference slope** at each observed grid cell. This formulation avoids numerical pseudo-variance when a nonzero slope value is exactly invariant across bootstrap refits.

Global scope treats all observed time × dimension cells as one simultaneous family. Dimension scope treats observed time within each functional dimension as a separate family.

The coverage claim is restricted to the observed grid represented by the FPCR fit.


## Gaussian FPCR future-outcome prediction intervals

The future-outcome layer assumes the underlying object comes from the Gaussian paired-bootstrap FPCR pipeline.

The scalar training outcomes supplied to the predictive function must correspond exactly to the training observations used by the reference FPCR fit.

Centered empirical residual resampling assumes one exchangeable/common response-error distribution is appropriate for the future target response.

The target functional trajectory is held fixed. Target measurement error, future predictor uncertainty, latent-curve uncertainty, and preprocessing uncertainty are not included.

Intervals are marginal per target. No joint residual dependence across multiple target outcomes is modeled.


## Split-conformal FPCA anomaly review

The 0.15 conformal routine assumes the proper-training reference, calibration inliers, and inlier targets are exchangeable at the **curve level** relative to the scientific population being monitored.

The FPCA/MFPCA basis and optional score-space covariance are fitted only on proper training. Calibration and target curves must not influence those fitted objects.

Proper-training, calibration, and target trajectories must share the exact time grid, functional dimension names/order, coordinate system, and time unit.

The proper-training and calibration samples are assumed to represent the intended inlier reference population. Contamination can distort both the fitted FPCA basis and the calibration distribution.

The marginal p-value contract uses conservative greater-than-or-equal handling of ties.

Repeated trials from the same participant are not exchangeable independent curves merely because they occupy separate rows. The current API does not provide cluster-conformal validity.


## Heteroscedastic Gaussian FPCR wild-bootstrap projection inference

The 0.16 wild bootstrap treats the functional regressors and fitted FPCA/MFPCA score geometry as fixed.

Curve rows must represent independent sampling units. Supplying <code>independent_unit_column</code> checks this contract by requiring unique, non-missing identifiers. Repeated or clustered IDs are rejected rather than treated as independent.

Residual estimation uses k FPCs, the bootstrap pseudo-truth uses g=k, and the inferential projection uses h FPCs with h>=g. These truncation choices are part of the estimand and are not reselected inside bootstrap replicates.

Wild multipliers are independent of the data and have mean zero and variance one. The supported normal and Mammen distributions are explicit method choices.

Heteroscedastic studentization uses the empirical covariance of score × residual contributions and is recomputed inside every wild pseudo-sample.

The target functional trajectory is fixed and interpreted through centered FPCA scores relative to the training functional mean.


## Stabilized-volatility wild-bootstrap truncation selection

The 0.17 selector is conditional on a fixed residual truncation k and g=k.

Candidate h values must be consecutive and at least g.

The interval scan uses identical multiplier draws across candidate h values so neighboring interval changes primarily reflect truncation rather than independent Monte Carlo draws.

Width and center thresholds are absolute quantities in scalar-outcome units and must be scientifically or operationally justified for the study.

The selected h may differ by target trajectory.

The rule is a practical tuning heuristic and does not imply bootstrap-coverage optimality.


## Simultaneous fixed-target FPCR wild-bootstrap inference

The 0.18 simultaneous layer inherits every assumption of the underlying 0.16 wild-bootstrap result. It is not a new resampling model.

The target family is the complete set of fixed trajectories stored in the supplied base result. That family should be scientifically defined before inspecting the target-wise intervals when the familywise statement is confirmatory.

All targets share the same bootstrap replicates. The calibration uses the maximum absolute studentized root across targets within each replicate, preserving their empirical bootstrap dependence.

The common familywise critical value is conditional on the residual truncation k, pseudo-truth g=k, inference truncation h, multiplier family, fixed FPCA basis, and independent-curve sampling contract of the base result.

The familywise statement applies only to the centered fixed-target projections included in that result. It does not imply simultaneous coverage for future scalar responses or for target trajectories introduced after calibration.

If h or the target family is selected adaptively from the same outcomes or intervals, that selection step is outside the stated coverage contract unless separately accounted for.


## Fixed-family FPCR wild-bootstrap hypothesis tests

The 0.19 testing layer inherits every assumption of the underlying heteroscedastic fixed-regressor wild bootstrap.

The complete testing family is exactly the set of fixed target trajectories stored in the supplied base result. Confirmatory families and null projection values should be defined before inspecting target-wise evidence.

The observed statistic for each target is the reference centered projection minus its supplied null value, divided by the stored heteroscedastic reference standard error.

The bootstrap comparison distribution is the absolute studentized root matrix already generated by the base result. The global statistic and single-step adjustment use the maximum absolute root across targets within each bootstrap replicate.

The bootstrap roots are centered estimation-error roots; the package does not regenerate pseudo-responses under an explicitly imposed target null.

The default plus-one correction treats the stored bootstrap replicates as a finite Monte Carlo approximation and prevents zero p-values. The uncorrected empirical exceedance fraction is available only as an explicit alternative.

A zero reference standard error is compatible with a target test only when the null discrepancy is numerically zero. Otherwise the test fails because a finite studentized statistic is undefined.

Single-step maxT adjustment is interpreted for the complete declared family. The package does not assume subset pivotality and does not claim strong family-wise error control for arbitrary subsets of true null hypotheses.

## Finite-bootstrap Monte Carlo precision diagnostics

The 0.20 layer is conditional on the complete 0.19 family-test result. It does not create a new resampling distribution.

Within that fixed analysis, each replicate contributes an exceedance indicator for a target-wise tail, a maxT-adjusted tail, or the global max statistic. The precision calculation treats these independently generated replicate indicators as Bernoulli draws and reports exact binomial intervals for their exceedance probability.

The diagnostic confidence level concerns Monte Carlo precision only. It is not a confidence level for the target projection, regression coefficient, participant population, or family-wise scientific claim.

Decision-stability flags are intentionally subordinate to the original test decision. They indicate whether the exact Monte Carlo interval lies wholly on the same side of alpha as that already reported decision.

The method assumes a fixed completed bootstrap budget. Optional or sequential stopping based on interim p-values is outside the 0.20 validity contract.

## Nonlinear trajectory dynamics

Delay-coordinate and recurrence analyses assume that the chosen state variables, units, preprocessing, and temporal sampling are scientifically interpretable. Version 0.23 never rescales channels, interpolates missing values, smooths trajectories, or chooses the state variables automatically.

Time-based delays, Theiler windows, divergence horizons, and LLE fit intervals require an approximately regular common grid. Sample-based delay embedding can be applied on a nonuniform common time grid, but then a single physical delay does not exist; the result records this explicitly.

AMI and false-nearest-neighbor diagnostics require an approximately regular temporal grid even when the requested lag is expressed in samples. Otherwise one sample lag corresponds to different physical delays across the record. If event order rather than physical time is the intended axis, represent that scientific choice explicitly as a regular event-index grid. The diagnostics remain aids rather than universally valid selectors; finite sample size, noise, nonstationarity, periodicity, filtering, and measurement precision can alter both.

A recurrence matrix and its spatial recurrence density can be constructed from irregularly timed state observations, but the standard diagonal/vertical line summaries in `rqa_metrics()` require an approximately regular progression of the source index/time grid. Cross-RQA additionally requires matching regular sampling steps on both axes. The package does not silently interpolate, resample, synchronize, or apply a sampling-rate correction. RQA metrics remain conditional on the chosen state representation, norm, recurrence-radius policy, Theiler window, and minimum line lengths. A target recurrence rate intentionally conditions comparisons on approximately similar recurrence density and therefore changes the interpretation of RR itself.

The recurrence-radius profile treats the observed state vectors and declared metric as the analysis geometry. RR(radius) is the empirical CDF of eligible pairwise state distances after the declared Theiler exclusion. The radius grid must therefore have scientific meaning in the current coordinate/state units; changing channel scaling, state dimensions, embedding, distance metric, or Theiler policy changes the profile. The diagnostic is exact for the observed states but does not model tracker/calibration uncertainty and is not a threshold-selection theorem.

Rosenstein-style local divergence assumes that nearby reconstructed states are meaningful local neighbors and that the declared fit interval captures an approximately linear log-divergence region. Adequate temporally separated neighbors and sufficient forward trajectories are required.

IAAFT testing assumes the surrogate null is scientifically meaningful: a process compatible with the observed marginal distribution and approximately the observed linear autocorrelation/power-spectrum structure. Rejection is relative to that null, not proof of a specific nonlinear generator.

Multivariate IAAFT additionally assumes that the selected dimensions are simultaneously observed on the same regular grid and that preserving their linear cross-spectral structure is part of the intended null. The reference dimension is an explicit finite-sample algorithm choice. Final cross-spectrum preservation is approximate after marginal rank remapping and must be judged using the retained diagnostics rather than assumed from the method name.

Empirical return-map stability additionally assumes that the declared section identifies repeated comparable cycles and that a local affine map is meaningful in the selected neighborhood. The fitted Jacobian is a data-driven local regression object, not a model-derived variational flow.
## Recurrence networks

Recurrence-network topology is conditional on the source auto-recurrence
contract. State representation, coordinate scaling, embedding, distance
metric, radius policy, Theiler exclusion, and sampling design determine which
graph edges exist.

The graph is undirected and unweighted. Nodes are recurrence-state/time
indices, not participants, AOIs, or latent psychological constructs. A Theiler
window removes temporally near graph edges by construction and can therefore
change degree, clustering, transitivity, and connectivity.

When target recurrence rate is used, edge density is partly controlled by the
threshold policy. Graph topology can still vary, but density-related
comparisons must be interpreted conditionally on that control.

## Joint recurrence

Joint recurrence assumes that the component recurrence plots refer to
synchronized observations on the exact same time grid. Each component's
state-space definition, metric, radius policy, and achieved recurrence rate
must already be scientifically defensible on its own.

The component plots must use one shared Theiler exclusion because JRR uses one
shared eligible-pair denominator. Version 0.39 does not reconcile different
Theiler windows automatically.

The JRP is the logical intersection of auto-recurrence events. It therefore
assumes that simultaneous within-system recurrence is the quantity of
interest. It does not assume that subsystem state vectors are directly
comparable across systems.

Line-based JRQA inherits the approximately regular-grid assumption of the base
RQA implementation.

## Functionalized windowed RQA

`windowed_rqa_trajectory_set()` assumes that all source curves share the common grid represented by the input `TrajectorySet` and that the same recurrence contract is scientifically meaningful across those curves.

The derived functional grid consists of complete-window centers. Overlapping windows reuse source samples; non-overlapping windows can still be serially dependent. The package therefore assumes **no window-level independence**. Any downstream inferential procedure must define its sampling/resampling unit from the original study design.

With a fixed radius, the radius must have a common interpretation in the supplied state-space units. With target-recurrence-rate mode, recurrence density is controlled by construction and RR is not a permissible downstream functional outcome.


## Population bootstrap for RQA summaries

`bootstrap_rqa_metric_means()` assumes that the declared resampling unit reflects the independent sampling design. Curve-level resampling is appropriate only when source curves are the independent units. Repeated trials from the same participant should generally use participant-level inference.

Participant mode treats the estimand as the equal-weight mean of participant-average curve-level RQA metrics. It conditions on the observed set of trials for each participant and does not model within-participant trial-sampling uncertainty.

The recurrence/RQA specification is fixed before resampling. Radius policy, embedding, distance metric, Theiler exclusion, and line thresholds are not re-selected inside bootstrap replicates.

Percentile intervals assume that resampling the observed independent units is a defensible approximation to population sampling variation. They do not model tracker noise, calibration error, preprocessing uncertainty, or the temporal-data-generating process within one trajectory.


## Kantz neighborhood divergence

`kantz_divergence_curve()` assumes that Euclidean neighborhoods in the declared reconstructed state space are scientifically meaningful local neighborhoods. Channel scaling, embedding, delay, coordinate units, and preprocessing therefore directly affect which states fall within the declared radius.

The radius is fixed for the analysis. It is not an adaptive bandwidth and is not enlarged until a desired neighbor count is achieved.

The minimum-neighbor rule controls which reference states contribute. Loss of reference support at later horizons is retained explicitly through reference and pair counts.

As with Rosenstein LLE, the temporal grid must be approximately regular so forward sample horizons correspond to a stable elapsed-time increment. The fitted linear interval must be scientifically declared and interpreted conditionally on the reconstruction and neighborhood contract.


### Kantz sensitivity grids

`kantz_parameter_sensitivity()` assumes every value in the declared grid was scientifically defensible independently of the observed preferred result. The Cartesian grid is an analyst-defined robustness set, not a data-driven tuning space.

Radius and minimum-neighbor values must therefore be interpreted jointly with coordinate scaling and state-space construction. A radius is not comparable across analyses that silently change channel units or normalization.

The supported-reference fraction is descriptive support under one declared neighborhood rule. It is not an inverse-variance weight, effective sample size, or automatic criterion for preferring that radius.


## Continuous trajectory geometry

The heading, curvature, turning-rate, and tortuosity APIs assume that the two declared planar dimensions form a scientifically meaningful Euclidean coordinate system.

Horizontal and vertical axes should therefore be commensurate. Coordinates normalized independently to display width and height can distort angle, curvature, path length, and tortuosity when the physical/visual scales differ.

The sign of curvature and turning rate follows the **recorded coordinate orientation**. In common screen coordinates where \(y\) increases downward, visual clockwise/counterclockwise interpretation is reversed relative to a conventional Cartesian \(y\)-up plot.

Differential geometry assumes the observed trajectory is complete and has at least three time points. Derivatives are computed on the supplied strictly increasing grid without hidden smoothing or interpolation.

The `min_speed` threshold is part of the estimand. The default zero threshold masks only exactly stationary numerical derivatives; any positive near-zero threshold must be scientifically declared.

Wrapped heading is circular data. Ordinary Euclidean FDA of heading requires an explicit representation decision because the \(-\pi/+ \pi\) branch cut is not a true directional discontinuity.


## Discrete Fréchet trajectory distance

Discrete Fréchet assumes that the ordered point sequence itself is the relevant trajectory representation. The local geometry depends directly on coordinate units and any explicit dimension weights.

The coupling preserves order but not elapsed-time correspondence. It is therefore suitable for order-preserving geometric comparison, not for analyses where latency or physical traversal speed is itself the estimand.

All points must be finite. The package does not silently delete missing samples or repair incomplete paths before comparison.


## Trajectory-distance sensitivity

The sensitivity layer assumes that every declared distance specification is
scientifically defensible for the same selected trajectories and dimensions.
It does not make conceptually different estimands interchangeable merely by
placing their matrices in one result.

Global Spearman agreement is descriptive agreement of pair-distance orderings.
The condensed upper-triangle distances are dependent because each trajectory
appears in multiple pairs; ordinary correlation-test p-values are therefore
not attached.

Top-k neighbor agreement assumes that local neighborhood structure is a useful
scientific diagnostic. When the kth and (k+1)th distances tie, the selected
neighbor set is not uniquely identified; the result flags that cutoff tie.

## Dynamic time warping trajectory distance

DTW assumes that monotone sample-index warping is scientifically admissible. It is appropriate when local progression-rate differences may be nuisance variation, but it can align away latency or dwell-pattern differences that are substantive effects.

The 0.33 symmetric1 recurrence remains the default for backward compatibility. Its public distance is a raw cumulative cost and has no path-independent N+M normalization. The symmetric2 option changes the weighting of diagonal versus horizontal/vertical advances and, for global alignment, admits explicit N+M normalization. These are different estimands and should not be switched after outcome inspection.

The optional `window_radius` is measured in sample indices, not milliseconds or seconds. Comparability of a fixed radius therefore depends on the sampling representation supplied to the function.

Coordinate units and explicit dimension weights define the local geometry. All points must be finite; the package does not silently delete missing samples or repair incomplete paths. Recorded timestamps do not enter either DTW recurrence.

## Discrete transfer entropy assumptions

- Source and target are already scientifically meaningful discrete state sequences; the package does not discretize continuous measurements.
- `target_history`, `source_history`, and `source_lag` are part of the estimand and must be declared rather than tuned to maximize TE.
- Empirical count support must be adequate for the joint histories actually used. The result exposes singleton-history and minimum/maximum support diagnostics instead of applying a hidden cutoff.
- The circular-shift test assumes the declared wrap-around shifts provide a defensible no-alignment null for the scientific series. Strong trial boundaries or nonstationarity can invalidate that null.
- Pairwise TE can remain nonzero under common drivers or omitted history. It is a directed predictive-information diagnostic, not automatic causal identification.

## Transfer-entropy sensitivity assumptions

- Every value in the target-history, source-history, and source-lag grids is scientifically defensible before outcome inspection; the multiverse is not a search over arbitrary values.
- The same discrete source/target state representation is used for every specification.
- Increasing history depth can make empirical probability support sparse. The table therefore retains effective counts and joint-history support diagnostics instead of imposing a hidden adequacy threshold.
- If circular-shift inference is requested, the identical declared shift set is used for every specification and the wrap-around/stationarity assumptions of that null apply to all rows.
- Descriptive variation across specifications is not a sampling distribution, posterior distribution, or causal probability.

## Conditional transfer entropy assumptions

- Source, target, and conditioning series use analyst-declared discrete state
  definitions that are meaningful for the scientific question.
- Target, source, and conditioning history lengths and both lags are fixed by
  the analysis specification rather than optimized against the observed CTE.
- The supplied conditioning process is the process the analyst intends to
  adjust for; unmeasured common drivers are not assumed away.
- Empirical support is adequate enough for the analyst's intended
  interpretation. The package exposes support diagnostics but does not encode a
  universal cell-count threshold.
- If circular-shift inference is requested, source wrap-around shifts are
  scientifically defensible while target and conditioning series remain fixed.

## Functional mixed-effects simultaneous-band assumptions

- Participants, not individual trials or time points, are the independent
  resampling units.
- Every participant bootstrap draw retains that participant's complete trial
  bundle and observed time grid.
- The fitted random-effect covariance and residual variance provide an adequate
  conditional weighting model for the fixed-effect GLS refits.
- The fixed/random bases, spline degree, scalar design coding, preprocessing,
  and response representation are treated as fixed analysis decisions.
- The participant-resampled fixed-effect information matrix remains full rank.
  A rank-deficient replicate is an analysis failure, not a row to discard.
- Simultaneous coverage refers to the observed time grid. Continuous-domain
  coverage between sampled points requires additional theory not claimed here.

## Random functional slope assumptions

- The random-slope predictor is explicitly named and is also included among the
  declared fixed predictors.
- The predictor varies within **every** participant under the guarded 0.45
  contract.
- The participant random intercept and the one random slope share the same
  declared B-spline basis size.
- Their stacked random-basis coefficient vector follows one multivariate
  Gaussian distribution with a full unstructured covariance.
- The participant count must exceed the number of free covariance parameters,
  ((2q)(2q+1)/2), before fitting is attempted.
- A converged optimizer does not by itself establish a stable covariance;
  inspect eigenvalues, condition number, boundary/singularity flags, and the
  recovered participant BLUP functions.
- Grid-level residual errors remain conditionally iid Gaussian after fixed and
  participant random effects are conditioned upon.

## Full-refit mixed-effects bootstrap assumptions

- Participants are the independent bootstrap units.
- All repeated trials/time points from a sampled participant are copied
  together.
- Each occurrence of a duplicated source participant is assigned a distinct
  bootstrap mixed-model group identity.
- The declared model specification remains fixed across bootstrap samples:
  response dimension, predictors, random-slope structure, basis sizes, spline
  degree, REML/ML choice, optimizer, and preprocessing are not reselected.
- The bootstrap sample must produce a valid converged fit under that same model.
  Failed fits terminate the bootstrap rather than being replaced.
- The resulting coefficient-function distribution includes variance-component
  re-estimation but does not represent uncertainty over alternative model
  specifications.

## Explicit residual covariance (0.49)

For `residual_correlation="exponential"`, the residual process is stationary
within each source curve/trial under the declared physical-time kernel
(R_\phi(t,s)=\exp\{-|t-s|/\phi\}). The common grid may be unequally spaced,
but timestamps must retain their scientific physical-time meaning.

For `residual_correlation="ar1"`, the common grid must be equally spaced.
AR(1) lag is a sample-index step, not arbitrary elapsed time; negative
correlation is allowed.

Residual covariance is block diagonal across trials. The model assumes no
residual-process correlation between different source curves/trials after the
declared participant/trial random effects.

The fitted serial parameter is an estimated covariance parameter, not a tuning
constant. A fitted value near its numerical optimizer bound, a large exponential
range, a large condition number, or material movement in the trial covariance
after adding serial correlation should be treated as a covariance-decomposition
diagnostic.

When a serial residual model is fitted, raw conditional residuals are expected
to retain the modeled dependence. Residual adequacy should therefore be
inspected on the whitened scale as well as the raw scale.

## Covariance-structure sensitivity assumptions

Version 0.50 assumes that successful models differ only in the predeclared
covariance structures under study. Observations, source-curve order, fixed
design and coefficient basis, participant mapping and participant random basis,
response dimension, time grid/unit, spline degree, and ML/REML mode must match.
When two models both contain trial functional random effects, their source trial
identities and trial basis must also match.

Likelihood/AIC/BIC differences therefore condition on this comparability
contract. Under ML, the information-criterion parameter count includes fixed and
covariance parameters. Under REML, the package uses the restricted likelihood
with covariance-parameter count only and requires the same fixed design/basis.

The BIC sample size is explicitly defined as the number of curve-by-time
observations, \(n_{\mathrm{curves}}n_{\mathrm{time}}\). This is a transparent
calculation convention, not an assumption that clustered functional data have a
uniquely defined effective sample size equal to that quantity.

Raw and whitened residual summaries are descriptive. Whitened residual
structure diagnoses what remains after the fitted residual covariance; it is
not a formal test that the covariance structure is correct.

## Marginal generalized functional-response assumptions

Version 0.51 targets the marginal mean

\[
g\{E[Y_{ij}(t)\mid x_{ij}]\}=x_{ij}^{\top}\beta(t).
\]

Participants are assumed independent across clusters. Dependence among trials and time points within participant may be misspecified by the working independence structure; the robust sandwich covariance is used for coefficient uncertainty.

Bernoulli responses must be genuine 0/1 observations under the declared sampling interpretation. Poisson responses must be non-negative integer counts under the current no-offset contract. The package does not infer binomial denominators or exposure time.

The coefficient basis is fixed before fitting. The participant-count > expanded-parameter-count rule is a structural guard only. Robust sandwich quality still depends on having enough independent, heterogeneous participant clusters.

The marginal coefficient interpretation is different from a non-Gaussian mixed model conditioned on latent participant effects.
