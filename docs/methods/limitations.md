# Limitations and failure modes

## Not a replacement for event analysis

Whole-trajectory analysis does not make fixations, saccades, dwell, or AOI transitions obsolete.

## Sampling rate still matters

A functional curve cannot recover dynamics that were never sampled.

## Smoothing can invent motion

Over-smoothing can turn abrupt transitions and missing gaps into visually convincing but fictitious movement.

## Registration can erase the effect

If treatment changes inspection latency, registration may align away the effect of interest.

## Layout confounding

FPCA can discover stimulus geometry rather than participant strategy when layouts are pooled without defensible harmonization.

## Components are sample-dependent

FPCs are empirical modes of variation. Replication or stability analysis may be needed before strong substantive labeling.

## Current multilevel implementation

The first release uses a two-level decomposition followed by separate FPCAs, not a full Bayesian or likelihood-based functional mixed model.


## Bootstrap stability is not inferential certainty

A high matched-component similarity shows that a component shape is reproducible under the chosen resampling scheme. It does not establish construct validity, causality, or generalization to another task/stimulus population.

## Irregular projection can change the estimand

Restricting to the common overlap shortens the time window. Using the union preserves the wider window but creates edge missingness. Neither choice is neutral.

## Phase decomposition depends on registration

Phase FPCA describes the estimated warping functions from a specific registration procedure. Different landmarks or elastic penalties can produce different phase representations.

## Basis interoperability is optional

The package preserves provenance around basis projection but delegates the basis mathematics to scikit-fda. Backend-version differences should be recorded in reproducible analyses.


## Sparse PACE is currently univariate in eyetrajectoriespy

The FDApy adapter estimates one named functional dimension at a time with covariance UFPCA and PACE score recovery. Separate x(t) and y(t) fits do not preserve joint planar covariance and must not be interpreted as joint 2-D MFPCA.

## Sparse scores depend on population smoothing

PACE scores are conditional estimates based on the fitted mean/covariance model. With very few observations per curve, individual scores can be strongly informed by population structure rather than by a densely observed individual path.

## Sparse observation design can be informative

A sparse estimator addresses irregular and limited observations; it does not automatically solve informative missingness. If gaze is absent because of blinks, track loss, off-screen viewing, or condition-dependent behavior, the observation mechanism may carry scientific information or bias.

## Sparse evaluation grids do not authorize extrapolation

An explicit FDApy evaluation grid controls where smooth mean/covariance/eigenfunction estimates are represented. eyetrajectoriespy restricts that grid to the pooled observed time support; it does not interpret smoothing outside the observed domain as measured gaze.

## Backend uncertainty is not fully propagated downstream

`SparseFPCAResult` preserves scores, eigenvalues, settings, and backend objects, but downstream score regressions do not automatically propagate uncertainty from sparse mean/covariance estimation and conditional score recovery.

## Reconstruction CV optimizes reconstruction, not scientific truth

Held-out trajectory reconstruction asks how well a training-fold FPCA basis reconstructs unseen curves. A component count that minimizes reconstruction error is not automatically the best dimension for an external prediction task, causal estimand, or substantive interpretation.

For repeated trials, curve-level cross-validation can leak participant-specific structure across train and test folds. Use grouped folds when the scientific sampling unit is the participant or another cluster.

## One-standard-error selection is a heuristic

The one-standard-error rule favors a smaller model within one estimated standard error of the minimum-RMSE candidate. It is a practical parsimony rule, not a hypothesis test or proof that the smaller functional dimension is correct.

## Bootstrap component envelopes are descriptive

Matched, sign-aligned bootstrap envelopes summarize pointwise variability of estimated FPC shapes under a chosen resampling scheme. They do not have simultaneous confidence-band coverage by construction.

When eigenvalues are close, component identity can become unstable even after matching. In that setting, matched similarity and subspace-level sensitivity may be more informative than narrow pointwise interpretation.

## Stable eigenspace does not imply identifiable FPC labels

A low projector distance for an FPC block means the selected functional span is stable under the stated comparison. It does not mean that each axis inside that span has a unique interpretation when eigenvalues are close.

## Eigengap thresholds are descriptive choices

The package does not provide a universal near-tie cutoff. A relative-gap threshold supplied by the analyst is a transparent review rule, not an inferential test or a guarantee that two population eigenvalues are equal.

## Subspace stability depends on the chosen block

A two-component span can be stable even when the boundary between FPC2 and FPC3 is unstable. Inspect eigengaps around the block boundary and fit enough components to evaluate that boundary.

## Functional outlier methods do not diagnose cause

A flagged curve is unusual under a specified functional representation. The method does not determine whether the cause is tracker error, preprocessing failure, rare but valid behavior, stimulus heterogeneity, or another source.

## In-sample reconstruction can hide influential curves

An atypical curve can shape the FPCA basis and therefore reconstruct surprisingly well. This is why reconstruction error should not be the only review diagnostic.

## Influence is sample-size dependent

Leave-one-participant-out changes can be large in small samples even when every participant is valid. Influence quantifies dependence of the fitted basis on the observed sample; it is not evidence of invalid data.


## Functional mean bands are observed-grid simultaneous bands

The multiplier critical value controls the maximum statistic over the sampled time-by-dimension grid used by the analysis. The implementation does not claim simultaneous coverage at unsampled times between grid points.

## Curve-level inference can be anti-conservative for repeated trials

If several trajectories come from the same participant, treating each curve as an independent inference unit can overstate the effective sample size. Participant-level aggregation changes the estimand and must be chosen explicitly.

## Participant-level aggregation targets participant-average trajectories

When participants contribute different numbers of usable trials, `unit="participant"` gives each participant equal weight after within-participant averaging. This is not the same estimand as a curve-weighted grand mean.

## Euclidean bands are not compositional bands

The API rejects direct bands for `probability_simplex` trajectories because unconstrained lower/upper curves can violate the simplex. An explicitly chosen log-ratio/compositional inferential framework is required instead.

## Multiplier bands remain asymptotic approximations

Finite-sample coverage can depend on the number of independent units, the covariance structure, dimensionality of the grid, and multiplier calibration. Report the design and avoid treating nominal coverage as an exact finite-sample guarantee.


## Predictive component selection is target-specific

The FPC count minimizing scalar-outcome loss need not minimize trajectory reconstruction error or maximize interpretability. It is conditional on the outcome, family, loss, candidate set, covariates, scaling, and fold design.

## Grouped CV is not a mixed-effects model

Keeping repeated participant trials in one fold prevents leakage, but the fitted scalar regression still operates on the supplied curve rows. It does not automatically model within-participant residual correlation or equalize participant weights.

## Binomial folds can fail legitimately

A training fold with only one class, perfect separation, or non-convergence is not silently accepted. Such failures can indicate an unsuitable fold design, insufficient sample size, or an unstable predictive model.

## Inner-CV loss is not unbiased final performance

After tuning FPC count, use an outer held-out loop when predictive performance is reported as a substantive result. The inner minimum loss is selection evidence rather than an untouched performance estimate.


## Simultaneous FPC bands do not solve eigenfunction identifiability

Matched/sign-aligned bootstrap bands quantify resampling variability around a selected individual FPC axis. When adjacent eigenvalues are close, the scientifically stable object may be the eigenspace rather than either axis. Use eigengap and principal-angle subspace diagnostics before giving a near-tied FPC an individual substantive label.

## FPC bands are observed-grid bootstrap approximations

The studentized maximum is calibrated over the sampled time-by-dimension grid. The implementation does not claim exact finite-sample coverage, nor does it claim coverage between observed time points.

## Component-wise and familywise scope answer different questions

Component-wise calibration controls the maximum over one FPC grid at a time. Familywise calibration takes the maximum over all requested FPCs as well as the grid and is therefore more conservative. The scope must be reported.

## Bootstrap unit changes the uncertainty target

Curve resampling treats trajectories as exchangeable independent units. Participant resampling keeps repeated trials clustered within resampled participants. Choosing the wrong unit can produce misleading uncertainty even if the numerical bands look stable.


## Spectrum uncertainty is not dimension selection

Intervals for eigenvalues or variance-explained ratios do not automatically determine how many FPCs should be retained. Reconstruction CV, predictive CV, variance thresholds, and substantive interpretation answer different questions.

## Spectrum intervals are not support-clipped

Symmetric studentized intervals may extend below zero for eigenvalues or outside [0, 1] for variance ratios. eyetrajectoriespy does not silently truncate them because clipping changes the inferential object without a derived calibration.

## Familywise spectrum calibration is metric-specific

With <code>simultaneous_scope="family"</code>, the maximum is taken across requested components separately for eigenvalues, explained-variance ratios, and cumulative ratios. The result is not one simultaneous guarantee across all three metric families together.

## Cumulative variance is rank-based, not shape-matched

Individual eigenvalues can be associated with matched reference FPC shapes. Cumulative explained variance instead follows descending eigenvalue rank. This distinction is deliberate and prevents near-tied component swaps from changing the meaning of “top k components.”

## Near-tied axes can remain hard to interpret

Eigenvalue inference can remain useful when eigengaps are small, but a near-tied individual eigenfunction direction may still be weakly identified. Spectrum uncertainty should be paired with subspace diagnostics when component shapes are interpreted.


## FPC score uncertainty is basis-resampling uncertainty only

The 0.11 score routine holds target trajectories fixed and resamples the training basis. Its percentile envelopes quantify sensitivity to basis estimation. They do not represent full latent-score confidence intervals.

## Target measurement error is not included

The target curve is not perturbed and no measurement-error model is fitted. Tracker noise, gaze-location error, pupil noise, and other measurement uncertainty are outside this score envelope unless they have already changed the supplied trajectory itself.

## Sparse PACE score uncertainty is different

Conditional-expectation scores for sparse irregular trajectories depend on the estimated mean/covariance model and the subject's sparse measurements. The common-grid basis-resampling routine must not be interpreted as PACE conditional-score uncertainty.

## Downstream regression uncertainty is not propagated

A downstream scalar regression, clustering model, or classifier fitted to one score matrix has additional coefficient/model uncertainty. The package does not currently integrate the full bootstrap score distribution through those models as one inferential procedure.

## Matching quality matters for component-specific scores

If a bootstrap FPC has low similarity to the reference component, the associated matched score coordinate may be unstable even after sign alignment. Near-tied components should be checked with eigengap and subspace diagnostics before component-specific score interpretation.

## Percentile envelopes are descriptive

The lower/upper score summaries are empirical percentile envelopes under the stated basis-resampling design. They are not guaranteed exact finite-sample confidence intervals and are not simultaneous across all targets/components.


## Gaussian FPCR bootstrap is not a universal functional-regression inference engine

The 0.12 implementation targets Gaussian scalar-on-function FPCR. It does not provide binomial/logistic functional-regression inference, generalized functional linear-model inference, or function-on-function regression uncertainty.

## Slope envelopes are pointwise

Percentile slope intervals are evaluated independently at observed grid coordinates. They do not provide simultaneous coverage over the full time × dimension domain and should not be used as a global significance band.

## Fixed-target intervals are conditional-mean intervals

Bootstrap target intervals describe uncertainty in the fitted conditional mean response. They do not add residual outcome noise and therefore are not prediction intervals for future observed outcomes.

## Component-selection uncertainty is excluded

The number of retained FPCs is fixed in every bootstrap replicate. If that number was chosen from the same dataset, the reported intervals are conditional on the selected dimension.

## Rank-deficient bootstrap samples stop the procedure

The implementation does not discard, replace, or redraw rank-deficient bootstrap replicates. Such a failure indicates that the requested regression dimension is not supported reliably by the resampling design.

## The operator-scaled 2026 FPCR test is not implemented

Recent theory establishes formal Gaussian/bootstrap approximations for an operator-scaled FPCR statistic. The paired percentile bootstrap in eyetrajectoriespy is a different procedure and must not be described as that operator-scaled test.
