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
