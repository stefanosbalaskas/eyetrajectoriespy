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
