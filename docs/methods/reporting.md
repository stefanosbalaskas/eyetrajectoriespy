# Reporting checklist

Report enough information to reconstruct the functional estimand.

## Representation
- trajectory unit;
- coordinate system and units;
- time origin, units, and window;
- whether curves share stimulus geometry;
- functional dimensions.

## Preprocessing
- common-grid construction;
- interpolation method and maximum bridged gap;
- remaining missingness/exclusion rule;
- smoothing method/parameters, if used;
- coordinate normalization or landmark centering;
- time normalization, if used.

## FPCA/MFPCA
- estimator/backend;
- grid/quadrature treatment;
- channel scaling;
- component-retention rule;
- variance explained;
- component interpretation procedure.

## Registration
- whether registration was performed;
- landmark definition or elastic backend;
- rotation/scale invariance;
- how phase/warpings were retained.

## Multilevel analysis
- nesting structure;
- participant/trial decomposition;
- retained components at each level.

## Compositional analysis
- probability construction;
- log-ratio reference dimension;
- zero replacement epsilon;
- inverse-transform interpretation.


## Irregular sampling

When native irregular trajectories were present, additionally report:

- whether native grids were retained before analysis;
- overlap, union, or custom common time domain;
- target grid size/frequency;
- interpolation method;
- maximum bridged gap;
- residual missingness after projection.

## Sparse irregular / PACE FPCA

If sparse FPCA was used, report:

- selected functional dimension;
- per-curve observation-count distribution or range;
- native observation-time support;
- whether non-finite tracker samples were removed before constructing the sparse object;
- sparse backend and version;
- covariance-operator versus other fitting method;
- mean/covariance smoothing configuration and any backend keyword parameters;
- evaluation grid used for estimated mean/covariance/eigenfunctions, or that backend defaults were retained; if explicit, confirm it remained within pooled observed support;
- PACE score-recovery method and tolerance;
- score-smoothing configuration;
- normalization setting;
- retained component count and eigenvalues;
- sensitivity to smoothing and component-count choices.

State explicitly that no common-grid interpolation preceded the sparse PACE analysis.

Do not describe separate x(t) and y(t) UFPCA fits as joint multivariate FPCA.

## Component stability

If bootstrap stability was evaluated, report:

- bootstrap resampling unit;
- number of replicates;
- random seed;
- participant column for clustered resampling;
- component matching criterion;
- similarity threshold if a descriptive threshold was used;
- median and interval of matched component similarity.

Do not describe the fraction of bootstrap replicates above a threshold as a probability that a component is true.

## Reconstruction diagnostics

Report the component count used for reconstruction and a trajectory-scale error measure when reconstruction adequacy is part of component-retention justification.

## Phase and registration sensitivity

When registration was used, report:

- phase representation;
- phase FPCA retention rule, if used;
- raw/observed landmark timing summaries;
- matched component similarity before versus after registration;
- score correlations before versus after registration.

## Basis representation

When a finite basis was used, report:

- backend;
- basis family;
- basis count;
- spline order where relevant;
- functional dimension projected;
- time domain;
- any sensitivity analysis across basis sizes.


## Component selection

If held-out reconstruction CV was used to choose the retained dimension, report:

- candidate component counts;
- number of folds;
- curve-level versus grouped CV;
- grouping column for repeated measures;
- whether FPCA, centering, and scaling were re-estimated inside each training fold;
- reconstruction error definition;
- minimum-RMSE versus one-standard-error rule;
- selected count and nearby-CV sensitivity.

The one-standard-error rule should be described as a parsimony heuristic, not an inferential test.

## FPC shape uncertainty

If matched-bootstrap component envelopes were inspected, report:

- curve- or participant-level resampling;
- participant/group column where relevant;
- number of bootstrap replicates;
- random seed;
- component matching criterion;
- sign-alignment rule;
- pointwise envelope level;
- matched component similarities.

Describe these outputs as descriptive pointwise bootstrap envelopes unless a separate procedure with demonstrated confidence-band coverage was used.

## Near-tied eigenvalues and eigenspace stability

When adjacent retained eigenvalues are close or individual FPC labels rotate across resamples, report:

- the adjacent eigenvalues and relative eigengap definition;
- any descriptive near-tie threshold, including that it was pre-specified;
- the component block assessed as a subspace;
- curve- versus participant-level resampling;
- number of bootstrap replicates and random seed;
- minimum principal cosine and/or maximum principal angle;
- normalized projector-distance summary;
- whether individual-component stability was lower than block-level subspace stability.

Do not use subspace stability to claim that individual FPC axes inside the block are uniquely identifiable.

## Functional anomaly and influence diagnostics

If trajectory review diagnostics were used, report:

- whether reconstruction error, score-space distance, functional depth, or another method was used;
- number of retained FPCs entering the diagnostic;
- robust versus empirical score covariance;
- review thresholds and whether they were pre-specified;
- number of trajectories flagged for review;
- whether any flagged trajectory was actually excluded, and the independent reason for that exclusion.

For leave-one-group-out influence, additionally report:

- omission unit (participant, trial, stimulus, or other group);
- group column;
- number of refits;
- matched-component similarity measure;
- explained-variance changes;
- whether conclusions changed in sensitivity refits.

Do not write that an algorithm "removed outliers" unless exclusion was a separate, documented decision.


## Simultaneous functional mean bands

If a simultaneous mean band was used, report:

- confidence level;
- Gaussian multiplier replicate count;
- random seed;
- inference unit (curve or participant);
- participant/grouping column for repeated measures;
- effective number of independent units;
- whether participants were first averaged across repeated trajectories;
- the resulting estimand;
- coordinate system and sampled time grid;
- whether all functional dimensions were calibrated jointly;
- number of zero-variance grid points, if any;
- that the current implementation targets the observed time-by-dimension grid rather than continuous-domain coverage between grid points.

Do not report the participant-level band as if it were based on the raw number of trials. The effective inferential sample size is the number of participant-average functions.


## Predictive FPCA regression selection

Report:

- outcome and family;
- held-out loss;
- candidate FPC counts;
- FPCA scaling;
- fold count and curve/group unit;
- grouping variable for repeated measures;
- covariates;
- confirmation that FPCA and regression were refitted inside every training fold;
- minimum-loss or one-standard-error selection rule;
- selected FPC count;
- whether predictive performance was estimated with an outer nested-CV loop.

For nested CV, report outer and inner fold counts, distribution of selected FPC counts across outer folds, and mean/SD of outer held-out loss. Do not present the inner minimum selection loss as untouched predictive performance.


## Simultaneous FPC-shape bands

Report:

- the FPCs receiving bands and the fitted scaling;
- the bootstrap resampling unit and participant column when applicable;
- the number of bootstrap replicates and confidence level;
- whether calibration was component-wise or familywise;
- that bootstrap FPCs were matched and sign-aligned to the reference;
- the median matched similarities;
- any pre-specified relative-eigengap threshold and its action;
- whether near-tied components were identified;
- that the band is simultaneous over the observed time-by-dimension grid, not the continuous domain between sampled points.

Example:

> FPC-shape uncertainty was evaluated with 1,000 participant-level bootstrap resamples. Bootstrap components were matched and sign-aligned to the full-sample FPCA, and 95% studentized maximum-deviation bands were calibrated separately for each FPC over the observed time × x/y grid. The pre-specified relative-eigengap review threshold was 0.05; components meeting that threshold were not interpreted individually and were instead evaluated at the eigenspace level.


## FPCA spectrum uncertainty

Report:

- the number of FPCs whose spectrum was evaluated;
- scaling used by FPCA/MFPCA;
- bootstrap resampling unit and participant column when applicable;
- bootstrap replicate count and random-seed policy;
- confidence level;
- component-wise versus familywise calibration;
- that bootstrap FPCs were shape-matched before assigning individual eigenvalues/ratios;
- that cumulative explained variance remained descending-rank ordered;
- that familywise calibration applied separately within each metric;
- that intervals were not silently clipped to parameter support;
- the distinct procedure used to select component count, if component selection was performed.

Example:

> Uncertainty in the FPCA variance decomposition was quantified with 1,000 participant-level bootstrap refits under dimension-SD scaling. Bootstrap FPCs were matched to the full-sample reference before individual eigenvalues and explained-variance ratios were assigned, while cumulative variance retained descending eigenvalue-rank order. Ninety-five-percent familywise studentized intervals were calibrated across the three reported components separately for each spectrum metric. Bounds were reported without support clipping. Component retention was determined independently using grouped held-out reconstruction CV.


## FPC score basis-resampling uncertainty

Report:

- the training sample used to estimate the FPCA basis;
- whether targets were training curves or an external compatible set;
- number of fixed target trajectories;
- retained FPC count and scaling;
- curve versus participant bootstrap unit and participant column;
- bootstrap replicate count, seed policy, and percentile level;
- that bootstrap FPCs were matched and sign-aligned before target projection;
- component-matching similarity summaries;
- that targets were fixed rather than resampled/perturbed;
- the excluded uncertainty sources.

Example:

> Sensitivity of individual FPC scores to estimation of the functional basis was assessed with 1,000 participant-level bootstrap refits. Six target trajectories were held fixed while participants were resampled to re-estimate a two-component, dimension-SD-scaled MFPCA basis. Bootstrap FPCs were matched and sign-aligned to the full-sample reference before each target was re-projected. Ninety-five-percent percentile envelopes summarize basis-resampling variability only and do not include target measurement error, latent-curve uncertainty, preprocessing uncertainty, future-curve variability, or downstream regression uncertainty.


## Gaussian FPCR paired-bootstrap uncertainty

Report:

- Gaussian scalar-on-function FPCR as the model family;
- retained FPC count and the separate procedure used to choose it;
- scaling used by FPCA/MFPCA;
- paired bootstrap unit and participant column when applicable;
- bootstrap replicate count, seed policy, and percentile level;
- that FPCA/MFPCA and regression were refitted together in every replicate;
- that the functional slope was reconstructed in original trajectory units;
- that slope intervals are pointwise;
- whether target trajectories were training or external fixed curves;
- that target intervals are for the fitted conditional mean response, not future noisy outcomes;
- that component count was fixed during bootstrap inference;
- that rank-deficient replicates were not discarded/redrawn.

Example:

> Gaussian scalar-on-function FPCR uncertainty was quantified with 1,000 participant-level paired bootstrap refits. MFPCA and the Gaussian score regression were refitted jointly in every replicate using two prespecified components and dimension-SD scaling. The slope was back-transformed to the original x/y coordinate units and summarized with 95% pointwise percentile intervals. For six fixed target trajectories, bootstrap intervals describe uncertainty in the fitted conditional mean response rather than future-outcome prediction intervals. The component count was held fixed across bootstrap replicates.


## Simultaneous Gaussian FPCR slope bands

Report:

- the underlying paired-bootstrap FPCR specification;
- bootstrap replicate count and resampling unit;
- simultaneous confidence level;
- global versus dimension scope;
- the observed-grid family used in the maximum;
- dimension-specific critical values;
- that pointwise SEs were estimated from bootstrap deviations from the reference slope;
- that the band was derived from the existing paired-bootstrap slopes rather than a second bootstrap;
- that coverage is claimed only over the sampled grid;
- that the procedure is distinct from the Imaizumi-Kato functional-linear confidence-band construction and Yeon's operator-scaled FPCR test.

Example:

> A 95% studentized simultaneous Gaussian FPCR slope band was calibrated from the 1,000 participant-level paired-bootstrap slope refits. One maximum was taken over the full observed time-by-dimension slope grid. Cellwise standard errors were estimated from bootstrap deviations from the full-sample slope. The resulting band is simultaneous over the sampled grid only and does not imply continuous-domain coverage between time samples. This finite-grid calibration is distinct from the confidence-band method of Imaizumi and Kato (2019) and the operator-scaled FPCR significance test of Yeon (2026).


## Gaussian FPCR future-outcome prediction intervals

Report:

- the underlying Gaussian paired-bootstrap FPCR specification;
- retained FPC count and its selection procedure;
- paired resampling unit and bootstrap count;
- target-source semantics;
- prediction confidence level;
- centered empirical residual resampling;
- residual sample size and residual standard deviation;
- that residual draws were independent of the stored paired-bootstrap conditional-mean draws;
- that the residual distribution was assumed common/exchangeable across targets;
- that the method is not heteroscedasticity-robust;
- that intervals are marginal per target and not simultaneous or joint;
- that target functional-predictor uncertainty is not included.

Example:

> Future scalar outcomes for six fixed target gaze trajectories were summarized with 95% marginal Gaussian FPCR prediction intervals. The predictive distribution reused 1,000 participant-level paired-bootstrap conditional-mean predictions and added independent draws from the centered empirical residual distribution of the full-sample FPCR fit. The residual-resampling step assumes a common exchangeable response-error distribution. Intervals were not interpreted as heteroscedasticity-robust, simultaneous across targets, or a joint prediction region.


## Split-conformal FPCA anomaly review

Report:

- the sizes and construction of proper-training, calibration, and target sets;
- confirmation that the partitions were disjoint;
- FPCA/MFPCA component count and scaling;
- nonconformity definition;
- score-covariance estimator and random seed when relevant;
- the exact marginal conformal p-value formula;
- conservative tie handling;
- calibration size and minimum attainable p-value;
- review alpha;
- number of targets flagged for review;
- curve-level exchangeability assumptions;
- any repeated-trial dependence;
- that flags were not automatic exclusions;
- that no calibration-conditional or multiple-testing/FDR adjustment was applied unless a separately justified procedure was actually used.

Example:

> A three-component MFPCA reference was estimated from 40 proper-training gaze trajectories. Twenty disjoint calibration curves defined reconstruction-RMSE nonconformity. For each of six new target curves, the marginal split-conformal p-value was calculated as ((1+#{s_i^{calib}ge s^*})/(20+1)) with conservative greater-than-or-equal tie handling, giving a minimum attainable p-value of .0476. Curves with p ≤ .05 were flagged for review only. No calibration-conditional adjustment, multiplicity correction, or FDR guarantee was applied.


## Heteroscedastic Gaussian FPCR wild-bootstrap projection inference

Report:

- Gaussian FPCR as the model family;
- that the functional regressors and FPCA/MFPCA basis were fixed during wild resampling;
- the independent sampling unit and any identifier column used to verify independence;
- residual truncation k, pseudo-truth truncation g=k, and inference truncation h;
- how k and h were chosen;
- FPCA/MFPCA scaling;
- multiplier family;
- bootstrap replicate count and seed;
- heteroscedastic score-covariance studentization;
- that the heteroscedastic scale was recomputed inside every pseudo-fit;
- confidence level;
- whether targets were training or external compatible trajectories;
- that intervals are symmetrized and target-wise;
- that the estimand is the centered projection relative to the training functional mean;
- exclusions: future response noise, basis refitting, clustered wild bootstrap, simultaneous target coverage, and component-selection uncertainty.

Example:

> Heteroscedastic uncertainty in centered Gaussian FPCR projections was evaluated with 1,000 fixed-regressor wild-bootstrap replicates using standard-normal multipliers. Residual estimation and the bootstrap pseudo-truth used k=g=2 FPCs, while inference used h=3 FPCs. In each pseudo-sample the target projection root was studentized using a heteroscedastic score-covariance scale recomputed from the pseudo-fit residuals. Ninety-five-percent symmetrized intervals were reported separately for four fixed target trajectories. Curve rows represented independent participants. The analysis did not claim FPCA-basis resampling, clustered wild-bootstrap validity, future-outcome prediction coverage, or simultaneous coverage across targets.


## Stabilized-volatility wild-bootstrap truncation selection

Report:

- residual truncation k and how it was chosen;
- g=k;
- complete consecutive h candidate grid;
- fixed FPCA/MFPCA scaling;
- multiplier family;
- bootstrap replicate count and seed;
- that multiplier draws were shared across h candidates;
- confidence level;
- width and center thresholds with scalar outcome units;
- run parameter r and its interpretation as r+1 required stable transitions;
- target-specific selected h values;
- targets for which no stable run was found;
- the configured failure behavior;
- that the rule is a practical tuning heuristic rather than a coverage-optimality guarantee.

Example:

> With residual truncation k=2 and g=k, 95% heteroscedastic wild-bootstrap projection intervals were scanned over h=2,...,6 using the same standard-normal multiplier draws across h. A transition was stable when absolute changes in interval width and center were at most 0.15 and 0.10 outcome units, respectively. Using r=1, the earliest h beginning two consecutive stable transitions was selected separately for each target. No package-default threshold or largest-h fallback was used.


## Simultaneous fixed-target FPCR wild bootstrap

Report at minimum:

- the number of fixed targets and the scientific rule defining the family;
- the familywise confidence level;
- k, g=k, and h;
- multiplier family and number of wild-bootstrap replicates;
- the independent sampling unit;
- whether a participant/unit identifier was checked for uniqueness;
- the fixed-regressor/fixed-FPCA-basis construction;
- bootstrap-level heteroscedastic studentization;
- the familywise max-|t| critical value;
- whether the same-level target-wise intervals were shown for comparison;
- that the simultaneous calibration reused the stored bootstrap roots rather than initiating a second bootstrap;
- any data-driven truncation selection that occurred before calibration;
- the boundary that coverage concerns only the declared fixed centered projections, not future observed responses, unlisted targets, or clustered/repeated-participant outcomes.

A concise description can state that the maximum absolute studentized root was formed across all declared targets within each bootstrap replicate and its requested empirical quantile was used as a common critical value.


## Fixed-family FPCR wild-bootstrap hypothesis tests

Report at minimum:

- the number and scientific definition of fixed targets in the family;
- every null projection value, including whether a common zero null was used;
- the two-sided alternative and alpha;
- k, g=k, h, scaling, multiplier family, and bootstrap replicate count;
- the independent sampling unit;
- that observed statistics used the stored heteroscedastic reference standard errors;
- target-wise bootstrap tail probabilities;
- single-step maxT-adjusted probabilities;
- the complete-family global maximum statistic and bootstrap p-value;
- whether the plus-one or raw empirical p-value rule was used;
- the minimum attainable p-value implied by B when plus-one correction is used;
- that the exact stored root matrix was reused without a second bootstrap;
- that the bootstrap was not explicitly regenerated under the target null;
- that strong FWER for arbitrary subset nulls is not claimed without additional conditions;
- any adaptive family definition or truncation selection, if such exploration occurred.

Do not report a zero Monte Carlo p-value when the default plus-one correction was used; its lower bound is 1/(B+1).

## Finite-bootstrap Monte Carlo precision diagnostics

When version 0.20 diagnostics are used, report:

- the original fixed-family testing procedure and its p-value correction;
- the planned bootstrap replicate count B;
- the diagnostic confidence level;
- target-wise, adjusted, and global exceedance counts where relevant;
- that raw r/B values are diagnostic exceedance fractions rather than replacements for the configured test p-values;
- the Monte Carlo SE definition;
- that Clopper-Pearson exact binomial intervals quantify finite-simulation precision;
- the number of maxT-adjusted decisions flagged as Monte-Carlo-sensitive at the declared alpha;
- that the diagnostic reused the existing roots and generated no new multipliers or model fits;
- whether additional bootstrap replicates were generated after seeing the diagnostic;
- that these intervals do not quantify participant-sampling uncertainty or strengthen the multiplicity claim.

Example:

> The fixed-family wild-bootstrap test used 1,999 replicates and the plus-one p-value rule. Finite-bootstrap precision was evaluated post hoc from the retained roots using raw exceedance counts, plug-in binomial Monte Carlo SEs, and 95% Clopper-Pearson intervals. Adjusted decisions were flagged as Monte-Carlo-sensitive when the exact interval was not wholly on the same side of alpha=.05 as the reported decision. No additional resampling was performed for the diagnostic.

## Nonlinear trajectory dynamics

For delay reconstruction and RQA, report the source sampling grid/rate, analyzed dimensions, preprocessing, (m), (τ), recurrence metric, radius policy and resulting radius, Theiler window, line thresholds, and whether the state was observed or reconstructed. If a target recurrence rate was used, report both the target and achieved rate.

For windowed RQA, also report the window and step, whether windows overlap, number of windows, and `dropped_tail_samples`.

For local divergence/LLE, report the reconstructed state, Theiler window, maximum divergence horizon, analyst-declared fit interval, fitted (lambda_{max}) with units, (R^2), standard error, and number of fit points. Use language such as “Rosenstein-style local-divergence estimate” rather than “proof of chaos.”

For IAAFT testing, report the exact statistic, surrogate algorithm, number of surrogates, seed/reproducibility policy, iteration/tolerance settings, final spectrum-mismatch diagnostics, alternative, Monte Carlo p-value rule, and interpretation of the surrogate null.

For multivariate IAAFT, additionally report the selected channel set, analyst-declared reference dimension, exact marginal-rank constraint, maximum/summary per-channel spectrum mismatch, maximum/summary pairwise complex cross-spectrum mismatch, and that final spectral preservation is approximate after rank remapping. State explicitly that channels were not surrogate-generated independently.

For empirical return maps, report the section, crossing direction, interpolated crossing count, returned state variables, reference state, neighborhood policy/value, selected transition count, local-fit (R^2), Jacobian eigenvalues, spectral radius, and stability tolerance. Label the method experimental and state explicitly that the eigenvalues are not classical Floquet multipliers.
## Recurrence networks

Report:

- source state representation, dimensions, coordinate/state units, and
  preprocessing;
- recurrence metric and threshold policy;
- fixed radius or requested/achieved target recurrence rate;
- Theiler window;
- node definition and number of nodes;
- edge count and graph density;
- whether graph density differs from the source recurrence-rate denominator;
- mean/local clustering and transitivity conventions;
- component count, largest-component fraction, and isolated-node fraction when
  used;
- that the graph is undirected/unweighted;
- that no threshold tuning, community optimization, dense shortest-path
  analysis, or automatic dimension interpretation was performed.

## Joint recurrence / JRQA

When reporting joint recurrence, state:

- every subsystem/state definition and selected dimensions;
- each subsystem's distance metric and radius policy;
- requested and achieved recurrence rates when target-RR mode is used;
- the exact shared time grid, time unit, and sampling interval;
- the shared Theiler window;
- the number of eligible unordered time pairs;
- JRR and the number of joint recurrent pairs;
- JRQA minimum line lengths and any reported JDET/JLAM/line/entropy/trapping
  statistics;
- that the JRP was the logical intersection of the component auto-recurrence
  matrices;
- that no interpolation, resampling, lag shifting, synchronization repair, or
  threshold harmonization was performed;
- that joint recurrence is distinct from cross-recurrence and does not by
  itself establish direction or causal coupling.

## RQA-derived functional trajectories

When reporting windowed RQA as functional data, report:

- the source trajectory dimensions and their units/coordinate system;
- window and step in both the supplied units and resolved sample counts;
- the resulting overlap in samples or percentage;
- the original source-time support and the narrower window-center functional support;
- any trailing samples outside complete windows;
- recurrence metric, radius policy, Theiler window, and minimum line lengths;
- the exact RQA metrics promoted to functional dimensions and their units;
- whether undefined metrics caused failure or were retained as missing values;
- whether a fixed radius or a target recurrence rate was used;
- if target recurrence rate was used, that RR was controlled by design and was not analyzed as a functional outcome;
- the number and definition of independent source curves/participants separately from the number of windows;
- downstream FDA scaling, component count/selection rule, and inferential sampling unit.

Do not report the number of overlapping windows as the inferential sample size.


## Functional RQA window/step sensitivity and mean inference

When `windowed_rqa_sensitivity()` is used, report:

- every predeclared window/step specification, not only the preferred-looking profile;
- requested values and resolved sample counts;
- window span and derived-profile grid spacing;
- overlap samples/fraction;
- analyzed-source coverage;
- fraction of analyzed source samples reused in multiple windows;
- mean and maximum window memberships;
- functional support and explicit trailing-tail count;
- selected RQA metrics and recurrence contract;
- whether pairwise sensitivity comparisons had exact shared centers;
- the number of exact shared centers used by each pairwise comparison;
- RMSE/absolute-difference/correlation diagnostics where defined;
- that no interpolation or automatic window/step selection was used.

Do not describe profile-grid spacing, number of windows, or overlap-adjusted counts as an effective independent sample size.

When `windowed_rqa_functional_mean_band()` is used, additionally report:

- the single window/step specification receiving inference and how it was chosen;
- curve versus participant inference unit;
- participant identifier for repeated-trial designs;
- number of independent curve/participant functions;
- whether repeated trials were averaged within participant;
- confidence level, multiplier count, and random seed;
- simultaneous calibration over the observed window-center-by-metric grid;
- that whole residual functions, not window rows, received multipliers;
- that within-function temporal dependence was retained in each multiplier draw;
- that the method is not a within-trajectory moving/block bootstrap;
- that the band is conditional on the declared window/step and recurrence specification.

If the primary specification was selected after examining the sensitivity results, state that explicitly and do not present the band as if window-selection uncertainty had been included.


## Reconstructed-state nonlinear parameter sensitivity

When `rqa_parameter_sensitivity()` is used, report:

- the complete embedding-dimension grid;
- delay grid, supplied units, and resolved sample delays;
- fixed-radius versus target-RR policy;
- complete threshold grid;
- solved radius and achieved RR where target-rate mode is used;
- Theiler-window grid and resolved sample windows;
- minimum diagonal- and vertical-line grids;
- recurrence distance metric;
- total number of Cartesian-product specifications;
- finite-result fraction for each primary RQA outcome;
- minimum, quartiles, median, maximum, and range for the primary robustness outcomes;
- any specification that made the analysis fail and how the preregistered grid was subsequently handled;
- that no preferred specification was selected automatically;
- that the sensitivity summary is descriptive across analysis choices rather than sampling uncertainty.

Under target-rate sensitivity, state explicitly that RR was controlled by design.

When `lyapunov_parameter_sensitivity()` is used, report:

- embedding-dimension and delay grids;
- Theiler-window grid;
- maximum divergence horizon;
- every declared fit interval and units;
- total number of evaluated specifications;
- exponent range and quartiles;
- fit R² and slope-SE variation;
- usable-pair support and any zero-distance issues;
- counts/fractions of positive and negative fitted slopes if reported;
- that positive-specification frequency is descriptive across the declared grid and not a probability of deterministic chaos;
- that no fit interval or reconstruction setting was selected automatically.

If one specification is highlighted as primary, state the independent scientific reason for that choice rather than selecting it from the robustness table after inspection.


## Recurrence-threshold profile

When `recurrence_radius_profile()` is used, report:

- source state representation and selected dimensions;
- coordinate/state units and any upstream scaling;
- observed-state versus delay-embedded representation;
- distance metric;
- complete declared radius grid;
- inclusive threshold convention;
- Theiler window in supplied units and resolved samples;
- number of eligible off-diagonal pairs;
- recurrence rate at each reported radius or the complete profile table;
- shell pair counts/fractions when they are interpreted;
- recurrence-rate coverage at the maximum supplied radius;
- whether the full eligible pair-distance distribution was captured;
- that no dense distance matrix was required by the implementation;
- that the package did not select a radius automatically;
- the separate scientific or design rule used for any primary radius.

If target recurrence rate is used subsequently, report the requested target, solved radius, and achieved RR, and state that recurrence density was controlled by design.

Do not call the largest, flattest, steepest, or visually most convenient radius “optimal” unless a separate validated optimization criterion was genuinely part of the method.


## Population bootstrap for RQA summaries

When `bootstrap_rqa_metric_means()` is used, report:

- source state representation and selected dimensions;
- embedding dimension/delay if used;
- fixed radius or target recurrence rate;
- distance metric;
- Theiler window and resolved sample count;
- minimum diagonal/vertical line thresholds;
- selected RQA metrics;
- curve versus participant inference unit;
- participant identifier and number of curves per participant when relevant;
- number of independent bootstrap units;
- bootstrap replicate count and random seed;
- confidence level and percentile interval method;
- observed population mean, bootstrap SE, bias, and interval for each metric;
- that undefined selected source-curve metrics caused failure rather than deletion/imputation;
- that the interval is conditional on the fixed RQA specification;
- that within-single-trajectory recurrence uncertainty, trial-level hierarchical resampling, and parameter-selection uncertainty were not included.

Under target-RR mode, state that recurrence density was controlled by design and RR was not treated as an inferential outcome.

Do not report the number of trials or recurrence points as the independent bootstrap sample size when participants are the sampling unit.


## Kantz largest-Lyapunov estimation

When `kantz_divergence_curve()` and `estimate_largest_lyapunov_kantz()` are used, report:

- source dimensions, coordinate units, and preprocessing;
- embedding dimension and delay;
- fixed neighborhood radius;
- minimum-neighbor requirement;
- Theiler window;
- maximum divergence horizon;
- contributing reference and pair counts across the fitted interval;
- fit interval;
- exponent and units;
- (R^2) and slope standard error;
- whether Rosenstein was evaluated under the same reconstruction for sensitivity;
- that the radius and fit interval were not selected automatically;
- that a positive slope was not interpreted as standalone evidence of deterministic chaos.

If Rosenstein and Kantz disagree, report the difference as estimator sensitivity rather than retaining only the preferred result.


### Kantz sensitivity analysis

For `kantz_parameter_sensitivity()`, report the complete declared grid and the number of Cartesian-product specifications; the range/quantiles of exponent and fit diagnostics; the range of supported-reference fractions; minimum reference/pair support where relevant; and whether sign or substantive interpretation changed across the grid.

If a primary Kantz specification existed, distinguish it from the sensitivity grid. Do not report the most convenient radius or fit interval as though it were primary.

State explicitly that the positive-specification fraction is descriptive across declared analysis choices and not a probability of deterministic chaos.


## Continuous trajectory geometry

When continuous geometry is reported, state:

- selected planar dimensions and coordinate system;
- whether the two axes use the same spatial scale;
- screen \(y\)-axis orientation if curvature/turning sign is interpreted visually;
- preprocessing and any explicit smoothing performed upstream;
- derivative method and observed time unit;
- `min_speed` and `undefined_policy`;
- number/fraction of undefined samples by curve or analysis set;
- whether heading remained wrapped;
- curvature units and turning-rate units;
- tortuosity definition, `min_displacement`, and treatment of closed/near-closed paths.

Do not describe continuous signed curvature as interchangeable with event-level saccade maximum-deviation, area-curvature, or polynomial-fit metrics.


## Discrete Fréchet trajectory comparison

Report the trajectory representation, coordinate dimensions and units, sequence lengths, any dimension weights, upstream interpolation/smoothing/resampling/path simplification, and whether the coupling was inspected.

State explicitly that the method preserved point order but did not use elapsed-time correspondence. If latency is scientifically meaningful, report the complementary time-preserving analysis rather than implying Fréchet captured timing.


## Functional mixed-effects regression

Report:

- response dimension, coordinate units, common time grid, and number of grid
  points;
- number of source curves, participants, and trials per participant;
- scalar predictors, exact coding, and any interactions;
- fixed B-spline basis size and degree;
- participant random B-spline basis size and degree;
- that the participant random-basis covariance was unstructured;
- ML or REML estimation, optimizer, iteration limit, and convergence;
- boundary-fit status and retained backend warnings;
- residual variance and the conditionally iid grid-residual assumption;
- that the model was fitted jointly across all curve-by-time observations,
  rather than with separate pointwise mixed models;
- whether predictors varied within participant;
- that 95% coefficient intervals are pointwise Wald intervals unless another
  explicitly calibrated inferential procedure was used.

Do not describe the 0.36 model as a fully general functional additive mixed
model. State the omitted covariance/random-effect structures that matter for
the study design.

If a 0.48 nested trial functional random intercept is used, additionally
report:

- the exact `trial_column` and confirmation that participant/trial pairs were
  unique;
- the number of nested trials and trials per participant;
- `trial_random_effect="functional_intercept"`;
- the declared trial B-spline basis size;
- that one shared unstructured trial-basis covariance was estimated separately
  from the participant covariance;
- trial covariance eigenvalues/condition number and boundary/singularity
  status;
- that participant and trial random coefficients were modeled without a
  cross-covariance;
- that the profiled Gaussian nested backend was used, while participant-only
  fits retain the historical MixedLM backend;
- that grid residuals remain conditionally iid after the participant/trial
  smooth random effects.

If version 0.47 residual diagnostics are used, additionally report:

- that the diagnostics use conditional residual functions from the fitted
  mixed-effects model;
- the explicitly declared maximum index lag;
- the time unit and whether index lags corresponded to one exact physical lag
  or a range on a non-equally-spaced common grid;
- trial-level ACF/autocovariance and empirical-semivariance definitions;
- participant/overall aggregation level and the number of trials with defined
  ACF values;
- any before/after comparison of declared mixed-effects specifications;
- that no AR(1), trial-level functional random effect, or other covariance
  structure was selected automatically from the diagnostic output.

## Function-on-scalar regression

Report:

- the functional response representation, dimensions, coordinate units, and time grid;
- the scalar predictors and exact coding, including all interactions;
- whether any centering/scaling was performed upstream;
- the number of source curves and the number of independent inference units;
- curve-level versus participant-level inference;
- for participant mode, the participant identifier, curves-per-participant summary, and confirmation that declared predictors were participant-constant;
- the observed-grid OLS estimator and full-rank design requirement;
- HC1 pointwise sandwich standard errors;
- wild-bootstrap multiplier distribution, number of replicates, and random seed;
- coefficient-wise versus familywise simultaneous scope;
- confidence level and observed-grid coverage boundary;
- whether coefficient functions were smoothed or basis-regularized; in version 0.35 they are not;
- all upstream construction choices for derived responses such as speed, curvature, or windowed RQA.

State explicitly when repeated trials were averaged within participant and that the 0.35 model is not a functional mixed-effects model. If a simultaneous band excludes zero over a grid region, report the region descriptively unless a separate onset/excursion-set procedure was predeclared and calibrated.

## Trajectory-distance sensitivity

Report:

- all compared distance specifications by name and exact method;
- selected dimensions and dimension weights;
- DTW step pattern, normalization, and window radius for every DTW
  specification;
- number of curves and unique curve pairs;
- neighbor k;
- pairwise Spearman rank agreement and absolute rank-difference summaries;
- top-k neighbor Jaccard agreement, exact-set agreement, and nearest-neighbor
  identity agreement;
- any cutoff ties;
- that distance matrices remained on native scales;
- that no consensus distance or preferred metric was selected automatically;
- that correlation quantities are descriptive and no ordinary p-values were
  computed from dependent pair distances.

## Dynamic time warping trajectory comparison

Report:

- trajectory representation, coordinate dimensions, and units;
- sequence lengths and relevant sampling representation;
- weighted-Euclidean local metric and any dimension weights;
- the exact step pattern: symmetric1 or symmetric2;
- raw cumulative DTW cost;
- for symmetric2, the N+M-normalized distance and normalization denominator when normalization is reported;
- whether alignment was unconstrained or windowed;
- the Sakoe-Chiba radius in sample indices when used;
- path length and mean local distance when used as audit summaries;
- all upstream interpolation, resampling, smoothing, coordinate normalization, or simplification;
- whether an alignment path was inspected and that multiple optimal paths may exist;
- explicitly that recorded timestamps were not used by the recurrence.

If latency or physical traversal timing is scientifically meaningful, report the complementary time-preserving analysis rather than implying that DTW preserves trial-time correspondence. Do not describe mean local distance as the DTW distance, and do not describe symmetric2 normalization as a post hoc normalization of the symmetric1 estimand.

## Discrete transfer entropy

Report the discrete source/target state definitions, sampling unit, direction,
target history \(k\), source history \(l\), source lag \(d\), effective
transition count, TE in bits, and empirical history-support diagnostics. State
explicitly how any continuous signal was converted to states upstream.

For `transfer_entropy_circular_shift_test()`, report the declared shifts or
their pre-specified construction rule, number of surrogates, observed TE,
surrogate mean, surrogate-centered TE, plus-one upper-tail p-value, and minimum
attainable p-value resolution. Describe the result as directed predictive
information under the declared model/null rather than as proof of causality.

## Transfer-entropy specification sensitivity

Report the complete history/lag grids, total Cartesian-product specification
count, whether the multiverse was preregistered or exploratory, and the TE
range and median. Report support deterioration across the grid, including
effective-transition counts and singleton/minimum joint-history diagnostics.

For plotted sensitivity slices, report the exact fixed values of every
non-plotted parameter. When a common circular-shift null is used, report the
shift set/rule, number of shifts, surrogate-centered TE range, unadjusted
plus-one p-value range, and any separate multiplicity correction. Do not report
a multiverse maximum as though it were a prespecified single-analysis estimate.

## Conditional transfer entropy

Report the source, target, and conditioning state definitions; target/source/
conditioning history lengths; source and conditioning lags; effective
transition count; CTE in bits; and complete joint-history support diagnostics
including singleton fraction and minimum/mean/maximum cell counts.

Explain why the conditioning process was scientifically relevant. Describe the
result as incremental directed predictive information after conditioning on
that declared process, not as proof of causal influence or complete confounder
control.

For source-shift surrogate testing, report the exact shift rule/set, number of
shifts, surrogate mean, surrogate-centered CTE, plus-one upper-tail p-value,
attainable p-value resolution, and that target and conditioning processes were
held fixed.

### Simultaneous functional mixed-effects coefficient bands

In addition to the base mixed-model specification, report the participant
bootstrap replicate count, random seed, coefficient-wise or familywise scope,
confidence level, and observed-grid interpretation.

State that whole participant trial bundles were sampled with replacement and
that fixed B-spline coefficients were re-estimated by GLS for every resample.
Also state explicitly that the fitted participant random-effect covariance,
optional shared trial random-effect covariance, residual variance, and declared
bases were held fixed.

Report the simultaneous critical value and participant-bootstrap pointwise
standard errors for the coefficient(s) of interest. Do not describe the band as
including variance-component, basis-selection, preprocessing, or between-grid
uncertainty.

### Participant random functional slope

Report the exact `random_slope_predictor`, participant count, trials per
participant, fixed/random basis sizes, random-effect dimension, and number of
free unstructured covariance parameters.

Report that the random-slope predictor varied within every participant and that
the participant count exceeded the package's covariance-parameter guard.

Provide the full covariance-block interpretation: intercept covariance, slope
covariance, and intercept/slope cross-covariance. Also report covariance
eigenvalues or an appropriate summary, condition number, boundary/singularity
status, optimizer/convergence state, and any retained backend warnings.

Participant BLUP slope plots may be used descriptively to show how the
predictor-response relationship varies over trial time. State that these are
shrunken model-based random effects.

If 0.44 simultaneous fixed-effect bands are reported from a random-slope fit,
state explicitly that the fitted intercept/slope covariance and residual
variance were held fixed during bootstrap refits.

### Full-refit participant bootstrap

Report the participant count, bootstrap replicate count, random seed, REML/ML
choice, optimizer, fixed/random basis sizes, random-effect structure, and
simultaneous-band scope.

State explicitly that whole participants were sampled with replacement and that
duplicate participant draws received distinct bootstrap participant identities.
For a 0.48 nested model, also state that every nested trial in each sampled
occurrence received a distinct bootstrap trial identity while source
participant/trial IDs were retained.

Report that each replicate re-estimated fixed coefficients, the complete
declared participant covariance, the shared trial covariance when present, and
residual variance, while preprocessing, basis sizes, predictor specification,
random-effect structure, and optimizer choice remained fixed.

Summarize the stability of residual variance, covariance eigenvalues/condition
numbers, boundary/singularity frequency, and optimizer warnings where relevant.
Do not describe the retained variance-component bootstrap distributions as
automatically calibrated confidence intervals.

If comparing to the fixed-covariance bootstrap, report the time-varying
full-refit/fixed-covariance band-width ratio as a sensitivity diagnostic rather
than a hypothesis test.

## Explicit mixed-effects residual covariance

When reporting a 0.49 serial mixed-effects fit, state:

- the declared residual family (`iid`, `exponential`, or `ar1`);
- for exponential correlation, (widehat\phi) and its physical time unit;
- for AR(1), (widehat\rho), the verified regular grid interval, and that lag
  is index-step based;
- the recorded numerical parameter bounds and any
  `residual_correlation_boundary_fit` flag;
- that residual covariance is block diagonal by trial;
- the residual-correlation matrix condition number or other relevant
  conditioning diagnostics;
- whether raw and/or whitened residual ACF/variogram diagnostics were examined;
- any evidence that the serial process and trial functional covariance compete,
  including large range, trial-covariance conditioning/boundary changes, or
  bootstrap instability;
- whether inference used the fixed-covariance participant bootstrap or the
  full-refit participant bootstrap that re-estimates the serial parameter;
- that the covariance family was declared rather than automatically selected.

## Covariance-structure sensitivity reporting

For a 0.50 mixed-effects covariance sensitivity analysis, report:

- every predeclared covariance specification and the declared reference;
- whether each specification converged or failed, retaining failure reasons;
- the successful-fit comparability contract: same observations, fixed design and
  fixed basis, participant mapping/basis, time grid/unit, response dimension,
  and ML/REML mode;
- fixed coefficient-function differences from the reference, including
  observed-grid supremum and functional-L2 differences;
- simultaneous-band width ratios only when bands use the same
  confidence/scope/bootstrap contract and identical participant bootstrap draws;
- participant-intercept variance, participant-slope variance and
  intercept/slope cross-covariance when present, trial variance, and residual
  variance as separate functional components;
- raw and whitened residual ACF/variogram diagnostics, residual RMS and pair
  support through the declared maximum lag;
- participant/trial covariance condition and boundary diagnostics, residual
  serial parameter and units, and residual-correlation boundary/independence
  diagnostics;
- log likelihood, total free parameters, the exact information-criterion
  parameter count, AIC/BIC, and the BIC convention
  \(n=n_{\mathrm{curves}}n_{\mathrm{time}}\);
- that information criteria and residual diagnostics were descriptive and no
  covariance structure was automatically selected;
- that no naive likelihood-ratio p-values were computed.

Do not report a package-selected best covariance model, AIC rank, model weight,
or residual-diagnostic winner. When a long-range serial process and smooth trial
effect compete, report the covariance shifts themselves rather than converting
them into an automatic component-deletion rule.

## Generalized function-on-scalar reporting

For the generalized FoSR fit report:

- the functional response dimension and whether the family was Bernoulli/logit
  or Poisson/log;
- exact binary/count response coding and any exclusions performed upstream;
- for grouped-binomial models, the integer-success definition, denominator definition, denominator range/shape, any curve-level expansion, and confirmation that denominators were not inferred from proportions;
- for Poisson models, whether exposure was supplied; if so, its scientific
  meaning, units, shape/expansion rule, range, and why proportional scaling of
  expected count with exposure is defensible;
- the participant column defining independent clusters;
- every scalar predictor and whether predictors vary across trials;
- B-spline basis size, degree and observed time domain;
- that working independence was fixed rather than selected;
- that coefficient uncertainty used the robust cluster sandwich covariance;
- the participant count and expanded coefficient-parameter count, making clear
  that the count guard is not an adequacy theorem;
- coefficient functions on the link scale and their marginal
  population-averaged interpretation;
- bootstrap resampling at the whole-participant level when simultaneous bands
  are used;
- number of bootstrap replicates, seed, confidence level and coefficient/family
  simultaneous scope;
- that duplicate sampled participants received distinct bootstrap GEE group
  identities;
- for exposure-adjusted bootstrap inference, that exposure travelled with the
  source-participant response/design bundle and was treated as observed/fixed;
- for grouped-binomial bootstrap inference, that denominators travelled with the
  source-participant success/design bundle and were treated as observed/fixed;
- any backend warnings or bootstrap fit failures.

Do not describe these coefficients as subject-specific/conditional random-effect
coefficients. Do not describe aggregated proportions as Bernoulli observations
unless an explicit denominator-aware model has actually been fitted. For a
grouped-binomial model, report coefficients as marginal log-odds effects on the
success probability and state that denominator weights determine the grouped
observation information. For Poisson models without exposure, report log
expected-count effects rather than rates. With exposure, report log-rate effects and exponentiated coefficients as
rate ratios holding exposure fixed.

## Generalized fixed-profile prediction reporting

For fixed-profile marginal prediction, including the 0.53 exposure extension,
report:

- the fitted family/link, coefficient basis size and participant-cluster
  definition;
- every fixed prediction profile and its exact scalar predictor values;
- the observed scalar predictor minima/maxima used for the support audit;
- which profiles, if any, were flagged as extrapolative;
- that target profile values were treated as fixed and were not resampled;
- the inherited whole-participant coefficient-bootstrap size and seed;
- the requested prediction scale;
- for an exposure-adjusted Poisson fit, distinguish rate from expected count
  and report every target exposure used for expected-count prediction;
- whether simultaneous calibration was profile-specific or across the complete
  declared profile family;
- that calibration occurred on the linear-predictor scale and endpoints were
  transformed through the monotone inverse link;
- that the simultaneous claim applies only to the observed functional grid;
- for a contrast band, the exact predeclared ordered profile pair and
  `contrast_scale`;
- for a rate ratio, that calibration occurred on the log-rate-ratio scale before
  exponentiation;
- for a Bernoulli difference, whether the interval exceeded the logical
  \([-1,1]\) range;
- that no profile or contrast was selected automatically and no
  multiple-contrast family adjustment is implied.

Do not describe these response-scale bands as future-response prediction
intervals. They quantify uncertainty in fixed-profile marginal probability,
rate, or expected-count functions.

