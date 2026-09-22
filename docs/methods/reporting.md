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
