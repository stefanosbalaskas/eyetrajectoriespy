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
