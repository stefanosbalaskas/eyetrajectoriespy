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
