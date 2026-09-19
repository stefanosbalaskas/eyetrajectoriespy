# Research FAQ and decision clinic

## Do I need to smooth raw gaze before FPCA?

No automatic smoothing is recommended. Abrupt gaze changes can be genuine. Smooth only when the scientific representation requires it, report the method, and compare against an unsmoothed analysis when shape or timing could change.

## Should I interpolate every blink or tracker-loss interval?

No. Use an explicit maximum gap. Long unobserved intervals should remain missing unless the study has a defensible reason to reconstruct them.

## My trials have different sample times. Should I immediately resample them?

Not anymore. Preserve them first with <code>IrregularTrajectorySet</code>, inspect sampling support, then choose an overlap, union, or custom common grid.

## Should I normalize every trial to 0–1 time?

Only if the estimand is **trial progress** rather than elapsed time. Normalization removes absolute-duration information.

## Should I register curves before FPCA?

Only when phase variability is a nuisance for the scientific question. If verification latency, hesitation, or inspection timing matters, analyze the unregistered trajectories and preserve the warping/phase functions.

## How many FPCs should I retain?

Use a pre-specified rule and inspect more than variance explained. Reconstruction error and component stability can show whether the chosen low-dimensional representation is adequate and reproducible.

## Minimum RMSE or one-standard-error rule?

Use the rule that matches a pre-specified goal. The minimum-RMSE rule chooses the candidate with the lowest average held-out reconstruction error. The one-standard-error rule deliberately favors a smaller representation when its error is within one estimated standard error of the minimum. The latter is a parsimony heuristic, not a statistical significance test.

## Are the bootstrap FPC envelopes confidence bands?

No. `bootstrap_fpca_component_envelopes()` returns matched, sign-aligned pointwise descriptive envelopes. It exposes where estimated component shapes vary under the chosen resampling scheme but does not assert calibrated pointwise or simultaneous coverage.

## Why did an FPC change sign?

FPC sign is arbitrary. A component and its negative describe the same eigendirection. Interpret the contrast between the two ends of the component, not the sign label itself.

## Why do FPC1 and FPC2 swap in bootstrap samples?

When eigenvalues are close, component order can change and the corresponding eigenspace can rotate. The package therefore matches bootstrap components by absolute functional similarity instead of assuming labels remain fixed.

## What if FPC1 and FPC2 keep swapping or rotating?

First inspect their adjacent eigengap. If the eigenvalues are close, the individual axes can be weakly identified even when their joint span is reproducible. Use `compare_fpca_subspaces()` or `bootstrap_fpca_subspace_stability()` to evaluate the block with principal angles instead of forcing one-to-one labels.

A stable two-dimensional eigenspace does not justify assigning fixed psychological meanings to FPC1 and FPC2 separately.

## Is there a universal cutoff for a near-tied eigengap?

No. `fpca_eigenvalue_gap_table()` reports the gap without flagging anything by default. If a study uses a relative-gap review threshold, supply it explicitly, pre-specify it where possible, and report it as a descriptive rule rather than a significance test.

## Should I bootstrap trials or participants?

If multiple trials belong to the same participant and the goal is population-level component stability, participant-level resampling is usually the defensible default. Trial-level resampling treats repeated trials as independent units.

## Can I pool different stimulus layouts?

Only after a scientifically defensible spatial harmonization. Normalizing screen pixels to 0–1 does not make semantically different layouts equivalent.

## Do functional trajectories replace AOI or fixation analysis?

No. FDA preserves whole-trajectory variation. AOI, fixation, latency, and sequence models answer different questions and can be complementary.

## When should I use a B-spline or Fourier basis?

Use basis projection when a lower-dimensional smooth representation is scientifically useful. B-splines are flexible for non-periodic trajectories. Fourier bases are most natural for periodic structure. Basis family and size should not be selected only because the resulting curve looks smoother.

## Can I use FPC scores in prediction?

Yes, but the entire preprocessing and FPCA estimation should be fit inside the training fold. Estimating FPCs on the full dataset before cross-validation leaks information into the test data.

## Is a stable FPC automatically psychologically meaningful?

No. Bootstrap stability supports reproducibility of the functional shape under the chosen resampling scheme. Construct interpretation still requires the experimental design and preferably external behavioral evidence.


## Should I delete every trajectory flagged as a functional outlier?

No. A functional outlier can be a genuine rare strategy, a stimulus-layout mismatch, a preprocessing artifact, or a quality failure. The diagnostic tells you what to inspect; the exclusion decision requires an independent, documented rule.

## Why combine reconstruction error and score-space distance?

An atypical trajectory can be represented poorly by the retained basis, giving high reconstruction error. But the opposite can also happen: a strong atypical trajectory can influence the FPCA basis and therefore reconstruct well while occupying an extreme location in FPC score space. The two diagnostics are complementary.

## Should influence be calculated per trial or participant?

For repeated trials, participant-level omission is generally the scientifically meaningful sensitivity unit because trials from one participant are dependent. Curve-level omission remains available for designs where curves truly are the independent units.

## Is a Mahalanobis cutoff a hypothesis test?

No. In this package it is a review threshold used for functional diagnostics. It should not be reported as a confirmatory p-value or used as an automatic deletion rule.


## When should I use sparse PACE instead of interpolation?

Use sparse FDA when the observed points are too few or too irregular for interpolation to be a minor representation step. If common-grid interpolation would create much of the analyzed trajectory, the sparse model is usually the more honest representation.

## Does PACE fill in my missing gaze samples?

Not in the sense of silently replacing missing tracker rows. The sparse estimator models a latent smooth process from observed irregular points and obtains conditional FPC scores. eyetrajectoriespy requires the selected sparse dimension to contain finite observed values; absent measurements should be absent from the native curve-specific grid.

## Can I run PACE on x(t) and y(t) separately and call it MFPCA?

No. Two univariate sparse analyses do not estimate the joint covariance of the planar gaze process. The current public FDApy adapter is intentionally univariate.

## Why expose both fit smoothing and score smoothing?

FDApy distinguishes smoothing used while fitting sparse functional structure from smoothing used during score transformation. eyetrajectoriespy makes both settings explicit so backend defaults do not become hidden analytical decisions.
