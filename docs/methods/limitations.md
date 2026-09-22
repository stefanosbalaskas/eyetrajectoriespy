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


## Simultaneous FPCR slope bands are observed-grid approximations

The 0.13 maximum is evaluated only at the sampled time × dimension slope coordinates. The band does not establish simultaneous coverage between sampled times or over an abstract continuous domain.

## Dimension scope is not global scope

With <code>simultaneous_scope="dimension"</code>, x(t) and y(t) are calibrated separately. Statements simultaneous across both dimensions require <code>simultaneous_scope="global"</code>.

## The band is not the Imaizumi-Kato confidence-band construction

Imaizumi and Kato (2019) develop a theoretically justified PCA-based confidence-band procedure aimed at covering most of the slope function under their assumptions. The eyetrajectoriespy 0.13 method instead calibrates a finite observed-grid maximum from paired-bootstrap FPCR slope refits.

## The band is not the Yeon operator-scaled FPCR test

The 2026 operator-scaled Gaussian/bootstrap theory addresses a different statistic and inferential construction. eyetrajectoriespy does not equate its studentized grid maximum with that formal operator-scaled significance test.

## Zero-variance slope cells are handled structurally

If every bootstrap slope equals the reference at a cell, zero width is retained. If bootstrap SE is effectively zero but the bootstrap distribution is displaced from the reference, calibration fails explicitly instead of adding an epsilon denominator.


## Future-outcome FPCR intervals assume pooled residual exchangeability

The 0.14 predictive layer samples from one centered empirical residual pool. If residual spread changes with the fitted mean, functional predictor, condition, participant, or another variable, coverage may be distorted.

The implementation does not claim heteroscedasticity robustness.

## Future-outcome intervals are marginal per target

Supplying several fixed target trajectories does not produce a simultaneous familywise prediction guarantee or a joint multivariate prediction region.

## The target functional trajectory is treated as fixed

Uncertainty in the target gaze curve itself is not simulated. Measurement error, latent-trajectory uncertainty, preprocessing choices, and future-functional-predictor variability remain outside the interval.

## Component-selection uncertainty is inherited as excluded

The prediction layer reuses the 0.12 paired-bootstrap object, whose retained FPC count is fixed. Data-driven component-selection uncertainty is therefore not added automatically.

## Residual resampling is not the 2026 wild bootstrap

Recent functional-linear work develops a wild bootstrap for mean-response inference under heterogeneous errors. The 0.14 future-outcome procedure uses centered empirical residual draws and must not be described as that heteroscedasticity-robust method.


## Split-conformal anomaly p-values have finite calibration resolution

With (n_{calib}) calibration trajectories, the smallest attainable marginal p-value is (1/(n_{calib}+1)).

If this exceeds the chosen alpha threshold, no target can be flagged regardless of how extreme its score is.

The package reports this resolution rather than interpolating smaller p-values.

## Split randomness is not removed by the 0.15 API

Marginal split-conformal p-values can depend on how observations are assigned to proper training versus calibration.

The 0.15 implementation requires the analyst to provide the split explicitly and does not average over multiple random partitions.

## Calibration-conditional validity is not implemented

Kim and Park (2026), following Bates et al. (2023), discuss calibration-conditional p-value adjustments that reduce split sensitivity.

The 0.15 API returns ordinary marginal split-conformal p-values and does not claim calibration-conditional validity.

## No multiple-testing or FDR guarantee is applied

Supplying many target curves yields many marginal p-values.

The package does not automatically apply Benjamini-Hochberg or another multiplicity procedure in this tranche and does not claim FDR control.

## FPCA nonconformity is not functional depth

Kim and Park (2026) use multivariate functional depth-based nonconformity.

eyetrajectoriespy 0.15 instead uses reconstruction RMSE or score-space Mahalanobis distance around a proper-training FPCA/MFPCA reference.

The inferential wrapper is split conformal, but the nonconformity score is package-specific.

## Reconstruction and score-space anomalies are different

A target can be extreme in retained FPC scores while reconstructing well, or reconstruct poorly while having moderate retained scores.

Version 0.15 does not silently combine the two scores into one statistic.

## Repeated participant trials can invalidate curve-level exchangeability

The current conformal p-values are calibrated at the curve level.

Within-participant dependence is not corrected by participant metadata, and no participant-clustered conformal guarantee is provided.


## The 0.16 wild bootstrap keeps the FPCA basis fixed

This is a fixed-regressor functional-linear wild bootstrap. It does not propagate sampling uncertainty from re-estimating the functional mean, channel scaling, eigenfunctions, or FPC scores.

Use the paired FPCR bootstrap when basis-estimation uncertainty is part of the scientific target.

## Clustered/repeated trials are not supported by the wild-bootstrap API

Independent curve rows are required.

A participant contributing several trial rows violates that contract unless those trials have first been aggregated into a scientifically justified independent-unit trajectory.

Supplying duplicated values through <code>independent_unit_column</code> causes an explicit failure.

## Target intervals are not future-outcome prediction intervals

The estimand is the centered FPCR projection for a fixed target trajectory. Future scalar response noise is not added.

The 0.14 predictive layer answers a different question and currently relies on pooled residual exchangeability.

## Target-wise intervals are not simultaneous

Each target receives its own studentized critical value. Supplying several targets does not create a familywise or joint coverage statement.

## Truncation-selection uncertainty is excluded

The k=g and h truncations are fixed before the bootstrap. If chosen from the same data, their model-selection uncertainty is not propagated automatically.

## Multiplier choice remains a sensitivity decision

Normal and Mammen multipliers both satisfy the required first two moment conditions, but finite-sample behavior can differ.

The package records the multiplier family and does not silently choose or average across them.

## The implementation is a score-space analogue, not a numerical port of BTSinFLRM

The 0.16 method reproduces the fixed-regressor, k/g/h, multiplier, and bootstrap-level studentization structure inside eyetrajectoriespy's common-grid FPCR score geometry.

It is not claimed to be numerically identical to the companion R package for every tuning configuration or statistic.


## Stabilized-volatility selection has no universal threshold

The 0.01 width/center thresholds illustrated in the 2026 simulation study are not unit-free.

Transplanting them unchanged to outcomes on different scales can make the rule arbitrarily strict or permissive.

Version 0.17 therefore has no package default for rho_w or rho_c.

## Stabilization does not prove optimal coverage

The stabilized-volatility method chooses a region where interval center and width stop changing materially.

It does not provide a theorem that the selected h minimizes coverage error for a finite sample.

## The candidate grid matters

If the stable region lies beyond the largest candidate h, selection can fail.

The package does not silently extend the grid or return the largest available candidate.

## Target-specific h complicates cross-target comparisons

Different targets can select different inference truncations.

When target contrasts are compared directly, report this fact and consider whether a common pre-specified h is more appropriate for the scientific question.
