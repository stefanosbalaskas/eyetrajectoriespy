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


## Finite-B Monte Carlo precision diagnostics

The 0.20 layer treats each retained bootstrap exceedance indicator as a Bernoulli draw conditional on the observed data and bootstrap construction. The exact binomial interval quantifies uncertainty in the underlying resampling exceedance probability caused by finite B.

The plug-in MCSE can equal zero when r is 0 or B; the exact interval remains the primary boundary-aware precision summary.

These diagnostics inherit every scientific assumption of the underlying 0.19 test and do not establish model validity, subset pivotality, strong FWER, clustered dependence handling, or component-selection robustness.
