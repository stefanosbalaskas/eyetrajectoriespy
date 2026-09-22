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


## Why not just plot pointwise 95% intervals?

Pointwise intervals target each time/dimension location separately. If many locations are inspected together, they do not provide a single simultaneous statement for the whole displayed trajectory. The multiplier band calibrates a maximum statistic over the complete observed grid.

## Should repeated trials count as separate units in a mean band?

Only if curves themselves are genuinely independent sampling units for the population claim. When multiple trials come from the same participant, use `unit="participant"` to average trials within participant and infer on participant-average functions.

## Is the 95% band simultaneous over continuous time?

Not with the current API. It is simultaneous over the observed sampled grid across all included dimensions. Continuous-domain confidence bands require additional theory and assumptions.

## Why reject AOI probability-simplex trajectories?

Ordinary Euclidean lower/upper bands can leave the simplex. The package therefore requires an explicit compositional/log-ratio representation rather than silently applying inappropriate geometry.


## Should I select FPC count by variance, reconstruction, or outcome prediction?

Match the criterion to the question. Variance retention summarizes the predictor, reconstruction CV evaluates unseen functional curves, and predictive FPCA regression CV evaluates an external scalar outcome. They can select different component counts without contradiction.

## Why do I need nested CV after predictive component selection?

If the same cross-validation losses are used both to choose the component count and to report performance, the reported minimum participated in selection. Nested CV repeats component selection inside each outer training set and evaluates the complete procedure on untouched outer test data.

## Does participant-grouped CV solve repeated-measures dependence?

It solves train/test leakage by keeping a participant on one side of each split. It does not by itself turn a curve-level regression into a mixed model or guarantee equal participant weighting. If a participant-level outcome is duplicated across trials, aggregate appropriately or use a specialist grouped model.


## What is the difference between the pointwise FPC envelope and the simultaneous FPC band?

The pointwise envelope summarizes bootstrap quantiles independently at each grid location and is explicitly descriptive. The simultaneous band calibrates the maximum standardized bootstrap deviation over the whole observed grid, so the inferential target is a whole-curve event rather than a collection of isolated pointwise intervals.

## Should I use component-wise or familywise FPC bands?

Use component-wise calibration when each FPC has its own whole-grid uncertainty statement. Use familywise calibration when the statement jointly concerns the entire requested set of FPCs. Familywise calibration is at least as conservative under identical bootstrap draws.

## Can a simultaneous band make a near-tied FPC interpretable?

No. Sign alignment and component matching solve bookkeeping problems, not population identifiability. If eigenvalues are close, inspect eigengaps and subspace stability; the stable scientific object may be the span of several FPCs.


## Why are individual eigenvalues matched but cumulative variance rank-ordered?

They answer different questions. An individual eigenvalue may be discussed alongside a particular reference FPC shape, so matching preserves that identity. Cumulative explained variance asks how much variation is captured by the largest one, two, or k components, so descending rank is the correct ordering.

## Can an eigenvalue uncertainty interval tell me whether to retain an FPC?

Not automatically. Spectrum uncertainty quantifies sampling variability in the variance decomposition. Retention requires a separate explicit criterion such as reconstruction CV, predictive CV, a pre-specified variance threshold, or another justified study rule.

## Why can a variance-ratio interval extend outside [0, 1]?

The current implementation uses symmetric studentized bootstrap calibration around the full-sample estimate. Silently clipping the result would alter the interval. The package preserves the estimated interval and documents the support limitation.

## Does familywise spectrum calibration cover all reported metrics jointly?

No. It controls across the requested components separately within eigenvalues, per-component explained-variance ratios, and cumulative ratios. It is not one joint three-metric family.


## Is the FPC score envelope a confidence interval for the true latent score?

No. It holds the supplied target trajectory fixed and varies the estimated FPCA basis. It therefore measures one decomposition-related source of uncertainty rather than all uncertainty in a latent subject-specific score.

## Why project the same target into every bootstrap basis?

That isolates basis-estimation sensitivity. If the target itself were also resampled or perturbed, basis uncertainty and target/measurement variability would be mixed together and the estimand would change.

## Why are bootstrap components sign-aligned before scores are compared?

FPC sign is arbitrary. Without sign alignment, two identical axes pointing in opposite algebraic directions would produce scores with opposite signs and falsely appear highly uncertain.

## What should I do when component-matching similarity is low?

Treat the named score coordinate cautiously. Inspect eigengaps and principal-angle subspace stability. When eigenvalues are near tied, the stable object may be a multidimensional score subspace rather than FPC1 or FPC2 individually.

## Does this propagate score uncertainty through regression?

No. It exposes the bootstrap score distribution so sensitivity can be inspected, but the current regression APIs do not jointly integrate that distribution with regression coefficient/model uncertainty.


## Why does FPCR regression uncertainty not match FPC labels across bootstrap samples?

The inferential target is the reconstructed full slope or fitted conditional mean, not an individual intermediate FPC coefficient. A sign flip in an FPC is accompanied by a sign flip in its regression coefficient, leaving the reconstructed contribution unchanged. Matching would add an unnecessary axis-specific convention.

## Are the target intervals prediction intervals?

No. They summarize uncertainty in the estimated conditional mean response for fixed target curves. A future-outcome prediction interval would additionally require the response-noise distribution.

## Does the bootstrap include uncertainty in how many components were selected?

No. The retained component count is fixed. Selection by reconstruction CV or predictive CV must be reported separately.

## Why fail instead of redrawing a rank-deficient bootstrap replicate?

Redrawing conditions the bootstrap distribution on successful samples and silently changes the procedure. A rank-deficient replicate is evidence that the chosen regression dimension is unstable under the declared resampling design.

## Is this the new operator-scaled FPCR bootstrap test?

No. The 0.12 routine is a paired full-pipeline nonparametric bootstrap with percentile summaries. It does not implement the operator-scaled statistic or significance test developed in recent 2026 FPCR theory.


## Does the 0.13 FPCR band cover the continuous slope function everywhere?

No. Its maximum is evaluated on the observed grid used by the fitted trajectories. The package intentionally says “observed-grid simultaneous band.”

## Should I use global or dimension-wise slope calibration?

Use global scope when the inferential family includes all sampled functional dimensions together. Use dimension scope when each dimension is a separately declared family. The choice should be made from the scientific question rather than whichever band is narrower.

## Why does the simultaneous-band function reuse the old bootstrap object?

Reusing the retained 0.12 slope replicates guarantees that pointwise and simultaneous summaries refer to exactly the same paired resamples and FPCR refits. A second bootstrap would add Monte Carlo differences unrelated to the change in calibration target.

## Is this the Imaizumi-Kato PCA confidence band?

No. Imaizumi and Kato derive a distinct theoretically justified confidence-band method for scalar-response functional linear regression. The 0.13 eyetrajectoriespy procedure is a studentized maximum over a finite observed grid from paired-bootstrap reconstructed slopes.

## Is this Yeon's 2026 FPCR test?

No. Yeon's method relies on operator scaling and develops Gaussian/bootstrap approximations for a different formal inferential statistic.


## What is the difference between the 0.12 target interval and the 0.14 target interval?

The 0.12 interval concerns uncertainty in the fitted conditional mean response for a fixed target trajectory. The 0.14 interval adds a sampled response residual and therefore targets a future observed scalar outcome.

## Why pass the training outcome again?

The future-outcome layer needs the original scalar outcomes to reconstruct the full-sample residual distribution transparently. The package does not hide or serialize a residual-noise model inside the 0.12 object.

## Is the future-outcome interval heteroscedasticity-robust?

No. It samples from one centered empirical residual pool. Recent 2026 work develops wild-bootstrap methodology for heterogeneous functional-linear errors; that is a different procedure.

## Are multiple target intervals simultaneous?

No. Each target interval is marginal. The API does not claim familywise coverage or a joint prediction region.

## Does the interval include uncertainty in the future gaze trajectory itself?

No. The supplied target functional trajectory is treated as fixed.


## How is conformal anomaly review different from diagnose_fpca_outliers()?

<code>diagnose_fpca_outliers()</code> reviews curves that helped fit the FPCA model. The 0.15 conformal workflow reserves proper-training and calibration data and evaluates genuinely held-out target curves against that fixed reference.

## Why must proper training and calibration be separate?

Split conformal validity uses calibration scores that were not used to fit the scoring rule. Letting calibration curves influence the FPCA basis would change the inferential construction.

## Why can the smallest p-value be surprisingly large?

With (n) calibration observations, the marginal split-conformal p-value lies on the grid (1/(n+1), 2/(n+1), dots, 1). Small calibration samples therefore limit attainable significance.

## Does p ≤ .05 mean I should delete the trajectory?

No. It means the trajectory is unusually nonconforming relative to the declared reference/calibration population under the selected score. Cause must be investigated separately.

## Does 0.15 control FDR when I test many new curves?

No. It returns marginal p-values. Kim and Park (2026) discuss BH and calibration-conditional adjustments for an FDR-controlled procedure; those broader steps are not implemented in this tranche.

## Can I use repeated participant trials as calibration curves?

Only with great caution. The current guarantee is curve-level exchangeability. Multiple trials from one participant are generally dependent, and the 0.15 API does not supply cluster-conformal validity.

## Which nonconformity score should I use?

Use reconstruction RMSE when deviation from the retained functional span is the target. Use score-space Mahalanobis when unusually extreme retained FPC coordinates are scientifically meaningful. Do not choose after seeing which score flags more desired cases.


## When should I use the wild FPCR bootstrap instead of the paired FPCR bootstrap?

Use the paired bootstrap when the sampling variability of the estimated FPCA basis should be propagated and the independent unit can be resampled directly.

Use the wild bootstrap when the functional regressors are conditioned on as fixed and heteroscedastic response-error inference for fixed target projections is the scientific target.

## Why does the wild-bootstrap API keep the FPCA basis fixed?

That is part of the fixed-regressor wild-bootstrap construction. Refitting FPCA would change the bootstrap procedure into a different estimand/resampling design.

## Why are there both k and h component counts?

k controls residual estimation and also defines the g=k bootstrap pseudo-truth. h controls the target projection used for inference. The methodology requires h to be at least g under the implemented contract.

## Why recompute the heteroscedastic scale in every bootstrap sample?

Bootstrap-level studentization is part of the 2026 method. Reusing only the original standard error can make finite-sample coverage more sensitive to the multiplier distribution.

## Can I use repeated participant trials?

Not as independent rows in the current API. If a participant identifier is supplied and duplicates are present, the function stops. Clustered wild-bootstrap validity is a separate methodological problem.

## Are the wild-bootstrap intervals future-response prediction intervals?

No. They concern the centered FPCR projection for a fixed functional target. They do not add future scalar response noise.

## Which multiplier should I use?

The API supports standard normal and Mammen two-point multipliers. The multiplier should be declared before inspecting results; a sensitivity comparison can be reported when scientifically justified.


## What is the stabilized-volatility method?

It is a practical rule for choosing the wild-bootstrap inference truncation h by finding where adjacent interval widths and centers both stop changing materially.

## Why must h candidates be consecutive?

The published rule compares h directly with h+1. A non-consecutive grid changes the meaning of the stability criterion.

## Why reuse the same bootstrap multipliers across h?

If every h used independent bootstrap random numbers, changes in interval width or center would mix truncation sensitivity with avoidable Monte Carlo variability.

## Why is there no default 0.01 threshold?

The paper used 0.01 in a numerical study, but width and center are measured in scalar-outcome units. The same number can mean very different things for differently scaled outcomes.

## What does r mean?

r is the paper's run parameter. The selected h must begin r+1 consecutive stable transitions. Thus r=0 means one stable transition and r=1 means two.

## What happens if nothing stabilizes?

The default is an error. Optional warn/ignore modes preserve an unselected target for diagnostics. The package never silently substitutes the largest h.


## When should I use simultaneous fixed-target wild-bootstrap calibration?

Use it when the scientific claim concerns a predeclared **family** of fixed target projections and you want one familywise calibration rather than separate marginal statements.

If each target is an unrelated descriptive analysis and no familywise claim is intended, the base target-wise intervals may be the appropriate object.

## Does simultaneous calibration rerun FPCA or the wild bootstrap?

No. The 0.18 helper reuses the exact studentized-root matrix stored in an existing `FPCAWildBootstrapProjectionResult`.

It performs no new random-number generation and does not refit the FPCA basis, score regressions, or residual model.

## Can I add or remove targets after seeing the marginal intervals?

You can define a different scientific family, but that is a different calibration problem. Construct a new base result containing the intended target family and calibrate that complete family.

For confirmatory inference, do not choose the family after inspecting which target-wise intervals are favorable and then report the result as if the family had been predeclared.

## Does familywise calibration solve repeated-participant dependence?

No. It controls multiplicity across the fixed targets under the base wild-bootstrap sampling contract. It does not change the requirement that curve rows represent independent sampling units.


## What does the 0.19 family test add beyond simultaneous intervals?

The 0.18 interval layer gives one familywise max-|t| confidence calibration.

The 0.19 layer exposes the same joint root geometry as explicit two-sided hypothesis-test evidence: target-wise bootstrap probabilities, single-step maxT-adjusted probabilities, and a complete-family global maximum-statistic p-value.

## Why is the plus-one correction the default?

With a finite number B of bootstrap replicates, a raw exceedance proportion can be zero simply because no simulated root was more extreme.

The default `(r+1)/(B+1)` correction prevents zero Monte Carlo p-values and makes the finite resampling resolution visible. The minimum attainable value is `1/(B+1)`.

## Does an adjusted p-value guarantee strong FWER for every subset of hypotheses?

Not from the package contract alone.

The implementation uses a single-step maximum over the complete declared family and preserves the empirical joint bootstrap dependence. Strong FWER for arbitrary subsets generally requires additional conditions such as subset pivotality or a dedicated closed/step-down construction. Version 0.19 records that those conditions are not assumed automatically.

## Is the bootstrap regenerated under the null?

No. The test reuses the centered studentized roots stored by the base fixed-regressor wild bootstrap.

That makes the method computationally transparent and consistent with the 0.18 post-calibration philosophy, but it is not described as a null-imposed bootstrap test.

## Can different targets have different null projection values?

Yes. Supply one finite null value per target. A scalar null is broadcast to the entire family.

Null values are in centered scalar-response projection units, not in gaze-coordinate units.


## What does the 0.20 Monte Carlo precision layer add?

It quantifies how much finite-B simulation uncertainty remains in the target-wise, maxT-adjusted, and global resampling tail probabilities. It reports exceedance counts, raw r/B estimates, MCSEs, exact binomial intervals, and whether those intervals lie below, above, or overlap alpha.

## Does an interval overlapping alpha change the original test decision?

No. The 0.19 p-values and rejection indicators are unchanged. The overlap label is a numerical precision diagnostic, not a replacement test or stopping rule.

## Is the exact binomial interval an effect-size confidence interval?

No. It is an interval for the resampling exceedance probability induced by finite bootstrap Monte Carlo sampling. It says nothing directly about uncertainty in the scientific effect size.
