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

## Base target-wise intervals and 0.18 simultaneous calibration answer different questions

The base `wild_bootstrap_fpca_projection()` result remains target-wise. Supplying several targets to that function alone does not create a familywise statement.

Version 0.18 adds `fpca_wild_bootstrap_projection_simultaneous_interval()`, which post-calibrates one max-|t| critical value across the complete fixed-target family stored in the base result.

That stronger calibration still does not create a joint future-outcome prediction region, cover targets omitted from the declared family, repair repeated-participant dependence, or propagate uncertainty from data-driven component/truncation selection.

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


## Fixed-family maxT tests do not imply universal strong FWER control

Version 0.19 uses the joint bootstrap root matrix to produce target-wise tail probabilities, single-step maxT-adjusted probabilities, and a complete-family global test.

This preserves the empirical dependence among the declared targets, but the package does not impose every intersection null or verify a subset-pivotality condition.

Accordingly, the adjusted values should not be described as a general closed-testing or step-down procedure with guaranteed strong FWER control for every possible subset of null hypotheses.

The resampling distribution is also not regenerated under an explicitly imposed target null. The method is therefore reported as a bootstrap maxT approximation conditional on the same fixed-regressor model used for the 0.16–0.18 inference layers.

Adaptive removal of targets after inspecting marginal results changes the testing family and invalidates the intended confirmatory interpretation.

A small number of bootstrap replicates limits p-value resolution. With the default plus-one correction, the minimum attainable p-value is 1/(B+1).

## Monte Carlo precision is not scientific uncertainty

Version 0.20 quantifies only the simulation variability caused by using finitely many retained bootstrap replicates.

A narrow exact binomial interval does not imply that the FPCA basis, functional regression, target family, truncation choice, preprocessing pipeline, or participant sample is known precisely.

The plug-in Monte Carlo SE can equal zero when every retained replicate is on the same side of the observed statistic. The exact Clopper-Pearson interval should therefore be preferred for boundary-count interpretation.

The diagnostic does not change the configured plus-one/raw p-value rule, does not reverse a reported decision, and does not add strong-FWER or subset-pivotality guarantees.

Version 0.20 also does not implement an always-valid sequential Monte Carlo procedure. Repeatedly increasing B after inspecting significance until a preferred threshold is crossed is outside the package contract and should not be described as a pre-specified fixed-budget analysis.

## Nonlinear-dynamics limitations

### RQA metrics are parameter-dependent

Recurrence rate, determinism, laminarity, entropy, trapping time, and line lengths can change materially with the state representation, recurrence norm, radius, Theiler window, and minimum line lengths. Version 0.23 records these choices and does not present one parameterization as universally correct.

When `target_recurrence_rate` is used, recurrence density is deliberately controlled by the radius-selection rule. RR should not then be interpreted as an independently estimated outcome across those analyses.

### Irregular sampling changes the RQA estimand

Spatial recurrence itself can still be defined for irregularly timed state observations, so `recurrence_matrix()` does not force interpolation. Standard DET, LAM, trapping-time, and diagonal/vertical line statistics, however, treat successive row/column indices as comparable temporal advances. Version 0.24 therefore requires an approximately regular grid before `rqa_metrics()` computes those line-based summaries; cross-RQA also requires matching sampling steps on its two axes.

The package does not silently resample irregular data because interpolation can itself change recurrence line structure. If regularization is scientifically justified, it must occur upstream and remain part of provenance. If an event sequence is the intended object, use an explicit regular event-index representation rather than disguising irregular physical time as equally spaced observations.

### Sliding windows are overlapping descriptive summaries

Windowed RQA can create strongly dependent adjacent estimates when windows overlap. The returned functions are useful as time-varying descriptors and as inputs to a separately justified downstream analysis, but ordinary independent-observation tests should not be applied to overlapping windows without an appropriate dependence model.

The final incomplete tail is not analyzed and its exact number of samples is reported.

### A positive Lyapunov estimate is not proof of chaos

Finite noisy biological records can show positive local-divergence slopes because of measurement noise, nonstationarity, filtering, stochastic forcing, embedding choices, nearest-neighbor scarcity, or fit-interval choice. The 0.23 result is explicitly a Rosenstein-style estimate conditional on declared settings.

### IAAFT rejection is null-model specific

Version 0.23 implements scalar IAAFT for one explicitly selected signal dimension. Multivariate surrogate generation that preserves cross-spectral structure is not silently approximated.

The surrogate test asks whether the observed statistic is unusually extreme relative to IAAFT surrogates preserving the observed amplitude distribution and approximately the Fourier-amplitude spectrum. Rejection does not prove deterministic chaos, identify a unique nonlinear mechanism, or establish stationarity.

### Return-map stability is experimental

The empirical Poincare workflow assumes meaningful repeated crossings and sufficient local return transitions. Section placement, crossing direction, included state variables, reference state, neighborhood rule, noise, and cycle count can change the fitted Jacobian.

The eigenvalues of that fitted Jacobian are **not Floquet multipliers**. Classical Floquet analysis requires a specified dynamical model and variational equations around a periodic orbit.

### Classical continuation is not implemented

Version 0.23 does not expose `detect_bifurcation(gaze)`, numerical continuation, a monodromy matrix, or `floquet_multipliers(gaze)`. Those would require an identified dynamical system (dot{mathbf x}=f(mathbf x,	heta)) and dedicated model-validation contracts. Raw gaze observations are not silently treated as a known ODE.
## RQA-derived functional trajectories

Sliding-window RQA creates a derived functional process; it does not create new independent experimental units.

- overlapping windows deterministically reuse source samples;
- even non-overlapping windows can remain serially dependent because they come from one continuous source process;
- the functional time support begins at the first full-window center and ends at the last full-window center, so edge support is narrower than the original trajectory;
- trailing samples outside the final complete window remain explicit in provenance rather than becoming a partial window;
- fixed-radius and target-recurrence-rate analyses have different interpretations;
- when target recurrence rate is used, RR is controlled by design and 0.24 refuses to expose RR itself as a downstream functional outcome;
- DET, LAM, line lengths, entropy, and CORM remain conditional on the declared state representation, radius policy, metric, Theiler exclusion, and line thresholds;
- an undefined window-level metric remains undefined; `undefined_policy="keep"` preserves `NaN` but does not make the downstream FDA missing-data-safe automatically;
- a downstream FPCA/MFPCA/regression fit is a separate modeling step whose sampling unit must remain the source curve/participant, not the number of windows.

Version 0.24 therefore provides a provenance-preserving descriptive bridge between nonlinear summaries and FDA. It does not claim a new sampling distribution, simultaneous confidence band, or independent-window theorem for overlapping RQA curves.


### RQA software conventions are estimator choices

RQA libraries disagree on line-of-identity exclusion, Theiler defaults, recurrence-rate denominators, ratio scale, normalization, and border handling. Version 0.24 freezes its own conventions and records them in provenance rather than claiming universal equivalence with another package.

The recurrence threshold is inclusive (`distance <= radius`). Auto RR uses eligible off-diagonal pairs outside the declared Theiler window; cross RR uses the full rectangular all-pairs denominator; RR/DET/LAM are 0-1 ratios.

Finite-matrix diagonal lines are currently counted at their observed length. No border-effect or tangential-motion correction is silently applied. Border truncation can bias diagonal line-length distributions and entropy, so analyses in which entropy or long diagonal lengths are primary outcomes should include window-size/border sensitivity or use a future explicit correction method rather than assuming the base estimator is border invariant.

Target-RR mode can miss the requested rate exactly when many distances are tied. The solved inclusive radius and achieved recurrence rate are therefore the auditable realized quantities.

See [RQA software conventions](rqa-software-conventions.md).

### Multivariate gaze surrogates remain unimplemented

Scalar IAAFT does not become a valid planar-gaze surrogate by running it independently on `x` and `y`. Independent channel randomization can alter the cross-channel structure that defines the trajectory.

A future multivariate surrogate method must declare and diagnose preservation of the intended auto- and cross-channel linear structure, operate on a common regular grid, expose convergence, and state the exact null hypothesis. Version 0.24 therefore fails by omission rather than silently approximating MIAAFT.


## Functional RQA sensitivity and dependence limits

### Sensitivity diagnostics do not select a window

`windowed_rqa_sensitivity()` evaluates a declared window/step grid and retains every specification. Its RMSE, absolute-difference, correlation, overlap, coverage, and sample-reuse summaries are diagnostics; they are not an optimization criterion and no preferred specification is returned.

Searching many window/step combinations after inspecting the scientific result and then reporting only the most convenient profile is outside the intended confirmatory contract. A primary specification and sensitivity grid should be predeclared when possible.

### A denser RQA profile is not a larger independent sample

Reducing the step produces more window centers and often more deterministic sample reuse. The reported profile-grid spacing describes the sampling grid of the **derived function** only. It is not an estimate of effective independent temporal resolution, degrees of freedom, or effective sample size.

The overlap diagnostics quantify direct source-sample reuse. They do not model all serial dependence. Adjacent non-overlapping windows can remain statistically dependent because they derive from one continuous process.

### Pairwise sensitivity comparisons do not invent a common grid

Profiles from different window specifications are compared only at exact shared window-center times. If there are no exact common centers, pairwise RMSE/correlation remain undefined. Version 0.25 does not interpolate sensitivity profiles merely to manufacture comparable rows.

### Functional RQA mean bands require independent source units

`windowed_rqa_functional_mean_band()` applies the existing studentized Gaussian multiplier band to complete RQA-derived functional curves.

With `unit="participant"`, repeated trial curves are averaged within participant and participants are equally weighted. With `unit="curve"`, source curves are treated as independent units and that assumption must be justified by the design.

The procedure does not resample sliding-window rows. One multiplier acts on the complete residual function for each independent unit, preserving within-function time-by-metric dependence in the bootstrap draw.

### This is not a block bootstrap for one long trajectory

The 0.25 mean band does not solve the inferential problem of one participant contributing one long serially dependent trajectory. A moving/block/stationary bootstrap would require a distinct estimand, block construction, block-length rule, stationarity/mixing assumptions, edge treatment, and validation. Those choices are not silently imported into the current API.

### Window-selection and recurrence-tuning uncertainty remain conditional

The band is conditional on the declared window, step, radius policy, Theiler window, line thresholds, state representation, preprocessing, and selected functional outcomes. It does not propagate uncertainty from choosing those settings after looking at the data.


## Nonlinear parameter-sensitivity limits

### A sensitivity grid is not a sampling distribution

`rqa_parameter_sensitivity()` and `lyapunov_parameter_sensitivity()` summarize the numerical consequences of an analyst-declared set of defensible analysis choices.

The minimum, quartiles, median, range, standard deviation, or positive-LLE fraction across that grid do not have the interpretation of confidence intervals, posterior intervals, p-values, or probabilities. The grid is usually deterministic and chosen by the analyst.

### The grid itself can create a misleading robustness story

A narrow grid can make an unstable method look robust. An implausibly broad grid can make a scientifically well-motivated primary specification look artificially fragile.

Version 0.26 therefore does not define universal ranges for embedding dimension, delay, recurrence radius, target RR, Theiler window, line thresholds, or LLE fit intervals. Those ranges must be justified from the measurement process, diagnostics, scientific question, and relevant literature.

### No specification is selected automatically

The sensitivity layer does not rank specifications by DET, LAM, RR, LLE magnitude, fit R², standard error, or any combined score.

Selecting the most favorable specification after inspecting the grid changes the scientific analysis and introduces selection uncertainty that the sensitivity table does not correct.

### Failed specifications do not disappear

If any declared combination cannot be evaluated, the entire sensitivity call raises an error identifying the failing specification.

This avoids a common robustness failure mode in which difficult parameter combinations are removed and only successful or favorable analyses remain visible. It also means a very broad grid can fail because some corners are not admissible for the available data length.

### Target-RR sensitivity controls recurrence rate

When `target_recurrence_rates` is the threshold grid, RR is an imposed design target rather than an unconstrained outcome. Distance ties can make the achieved value differ slightly from the requested target, which is why both are retained.

Under this policy, apparent RR stability is not evidence that recurrence density is naturally robust.

### RQA matrices are not retained for every sensitivity specification

The RQA sensitivity result keeps the complete parameter/metric audit table but not one sparse recurrence matrix per specification. This is an explicit memory contract for potentially large Cartesian grids.

If a particular recurrence plot needs inspection, reconstruct that specification through the base embedding and recurrence APIs. This is not silent data loss: the parameter choice and numerical RQA outcomes remain in the sensitivity result.

### Positive LLE frequency is not chaos probability

The fraction of declared Rosenstein specifications with positive slopes only describes sign consistency over the chosen grid.

Noise, nonstationarity, finite data, reconstruction choices, neighbor scarcity, and fit-interval choice remain relevant. Even a positive slope for every declared specification is not sufficient evidence of a deterministic chaotic mechanism.


## Recurrence-threshold diagnostic limits

### The radius profile is descriptive, not a threshold selector

`recurrence_radius_profile()` returns the exact recurrence density over a user-declared radius grid. A steep or flat region is a property of that empirical distance distribution; it is not automatically an optimal operating point.

The package does not maximize DET/LAM separation, search for a plateau, enforce a target RR band, or choose a threshold from the plotted curve.

### The radius grid determines what part of the distance distribution is visible

Shell fractions are binned over the declared radii. If the largest radius reaches RR=0.10, only the first 10% of eligible pairwise-distance mass is represented by the table.

Use `maximum_radius_coverage_fraction` and `full_distance_distribution_captured` before describing the shell table as the complete pair-distance distribution.

### Numeric radius values are representation dependent

A radius has meaning only relative to the state variables, coordinate system, dimensions, embedding, metric, and any upstream scaling.

The same numeric epsilon can imply very different recurrence densities after changing from pixels to normalized coordinates, adding another state dimension, changing embedding dimension, or scaling one channel. Version 0.27 does not normalize state channels to make radii superficially comparable.

### Theiler exclusion changes both the empirical CDF and denominator

The profile removes temporally near pairs under the same Theiler contract as the base recurrence estimator. Changing the Theiler window can therefore alter the observed pair-distance distribution as well as the recurrence denominator.

Do not compare radius profiles with different Theiler policies as though only epsilon changed.

### Exact pair counts do not remove measurement uncertainty

The tree-based calculation is exact for the observed state vectors and declared metric. It does not account for tracker noise, calibration uncertainty, preprocessing uncertainty, interpolation uncertainty, or latent-state error.

A precisely calculated RR(radius) curve can still be scientifically sensitive to those upstream choices.


## RQA population-bootstrap limits

### Population uncertainty is not within-trajectory uncertainty

Version 0.28 resamples independent curves or equal-weight participant averages of curve-level RQA metrics. It therefore quantifies between-unit sampling uncertainty in a population mean.

It does not provide a confidence interval for the RQA of one observed trajectory, and it does not resample recurrence lines, temporal blocks, or raw within-curve samples.

### Participant mode conditions on observed trials

With repeated trials, selected RQA metrics are averaged within participant before participant resampling. This prevents trial pseudo-replication and equalizes participant weight, but the resulting interval conditions on the observed trial set for each participant.

A hierarchical participant-plus-trial bootstrap would be a different inferential contract and is not silently approximated.

### Percentile intervals are marginal and finite-sample dependent

The implemented intervals are metric-wise percentile bootstrap intervals. They are not simultaneous across multiple RQA metrics and are not BCa/studentized intervals.

Percentile intervals are not guaranteed to contain the observed point estimate in every finite sample.

### Parameter-selection uncertainty is excluded

The bootstrap is conditional on the declared state representation, embedding, radius policy, metric, Theiler window, and line thresholds.

If those settings were selected after inspecting the same data, the interval does not correct for that selection. Use the separate sensitivity APIs to expose robustness, and report post-hoc choice transparently.

### Undefined metrics fail rather than disappear

If a requested RQA metric is undefined for any source curve, the analysis terminates. Deleting that curve, replacing the metric with zero, or silently changing recurrence settings would alter the population estimand.

### Target-RR mode changes the estimand

When target recurrence rate controls recurrence density, RR is not an independent outcome. Version 0.28 therefore refuses to bootstrap recurrence rate under target-RR mode.


## Kantz LLE limits

### Radius choice remains consequential

Kantz divergence replaces one nearest neighbor with a fixed-radius neighborhood; it does not remove neighborhood-choice sensitivity. A radius that is too small can leave too few supported reference states, while a large radius can average over states that are no longer locally comparable.

Version 0.29 deliberately does not implement adaptive radius growth, automatic scale selection, or a universal radius default.

### Minimum-neighbor support can decay with horizon

Forward evolution near the end of the reconstructed record removes some neighborhood pairs. The package retains reference and pair counts at each horizon, but it does not convert those counts into a reliability correction or automatic stopping rule.

### Rosenstein and Kantz estimates need not agree

The methods use different neighborhood definitions and can produce different divergence curves and fitted slopes. Agreement is not guaranteed and disagreement is not automatically a software error.

### Positive slope is not proof of chaos

Measurement noise, filtering, nonstationarity, finite records, task changes, reconstruction choices, and the declared radius/fit interval can affect the slope. The estimator is therefore reported as a conditional local-divergence estimate rather than a chaos classifier.

### The surrogate test remains Rosenstein-specific

The current IAAFT test continues to use the package's named Rosenstein LLE statistic. Kantz surrogate testing requires a separately declared statistic contract and is not silently substituted in 0.29.


### Sensitivity grids do not solve radius selection

Version 0.30 makes radius/minimum-neighbor dependence visible but does not create a universally valid selection rule. A narrow exponent range over one declared grid does not prove robustness outside that grid, and a wide range does not identify which setting is correct.

The package does not rank settings by exponent magnitude, fit (R^2), slope standard error, supported-reference fraction, or sign.

### Grid fractions are not inferential probabilities

The fraction of declared specifications with a positive exponent is a descriptive property of the analyst-defined multiverse. It is not a posterior probability of chaos, a p-value, or a confidence level. Likewise, supported-reference fractions describe neighborhood support and are not sampling uncertainty.


## Continuous trajectory geometry limits

### Numerical derivatives amplify noise

Heading, curvature, and turning rate inherit the noise sensitivity of first and second numerical derivatives. Version 0.31 deliberately does not smooth before differentiation. A scientifically justified smoother must be applied explicitly upstream and reported.

### Near-zero velocity is intrinsically problematic

Curvature divides by speed cubed and turning rate by speed squared. Values near stationary periods can therefore become unstable even when they are mathematically finite. The package exposes `min_speed` rather than choosing a universal threshold.

### Coordinate scaling changes the geometry

Curvature and tortuosity are not invariant to anisotropic scaling of \(x\) and \(y\). Separately normalized screen axes can therefore change the estimand. Convert to a meaningful isotropic spatial metric upstream if geometric interpretation requires it.

### Signed curvature depends on axis orientation

The formula is evaluated in the recorded coordinates. If screen \(y\) increases downward, visual sign interpretation is reversed relative to a standard \(y\)-up Cartesian plot. No silent axis flip is performed.

### Wrapped heading is not ordinary Euclidean data

The discontinuity between \(+\pi\) and \(-\pi\) is representational, not physical. Standard linear summaries or FPCA on wrapped heading can be misleading without an explicit circular-data strategy.

### Tortuosity is undefined for zero endpoint displacement

The implemented ratio uses path length divided by endpoint displacement. Closed and sufficiently near-closed paths are undefined under the declared `min_displacement`; the package returns NaN or raises according to the explicit policy rather than adding a denominator epsilon.
