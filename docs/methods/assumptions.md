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

## Basis projection

Basis size controls approximation flexibility. A basis with too few functions can remove meaningful shape; a very flexible basis can retain measurement noise. Basis choice should be justified by the trajectory process rather than by visual smoothness alone.
