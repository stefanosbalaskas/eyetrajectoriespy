# Pre-registration checklist for functional gaze analysis

Functional analysis contains enough researcher degrees of freedom that the main choices should be specified before inspecting condition effects.

## Functional object

- raw horizontal/vertical coordinates;
- landmark-relative coordinates;
- derived distance/speed/path function;
- AOI probability composition;
- registered spatial trajectory;
- phase/warping function.

## Time domain

- trial time origin;
- analysis start/end;
- absolute time versus normalized trial progress;
- common-grid construction;
- overlap versus union domain for irregular data.

## Missingness and interpolation

- what counts as missing;
- maximum gap eligible for interpolation;
- interpolation method;
- trial/curve review rule after projection.

## Smoothing or basis projection

- whether smoothing is used;
- smoothing parameters;
- basis family and basis count if using basis representation;
- sensitivity analysis for smoothing/basis choices when substantively important.

## FPCA

- univariate or multivariate;
- channel scaling;
- component-retention rule;
- component interpretation procedure;
- whether bootstrap stability will be assessed;
- resampling unit for stability.

## Component-count selection

If component count will be selected by reconstruction CV, specify:

- candidate component counts;
- number of folds;
- curve versus participant/group fold unit;
- grouping column;
- scaling choice;
- minimum-RMSE versus one-standard-error rule.

FPCA must be re-estimated inside each training fold. Do not pre-fit the basis on the full dataset and then call the resulting error cross-validated.

## FPC uncertainty

If component-shape resampling will be used, specify:

- curve versus participant bootstrap;
- number of replicates;
- random seed;
- number of components to align;
- pointwise envelope level;
- how low matched similarity will be interpreted.

Pre-register descriptive bootstrap envelopes separately from any formal confidence-band procedure.

## Registration

- whether registration is planned;
- landmark definition or elastic method;
- whether rotation/scale invariance is permitted;
- how phase information will be retained;
- planned registered-versus-unregistered comparison.

## Repeated measures

- participant/trial hierarchy;
- whether multilevel FPCA is required;
- unit used for resampling or downstream inference.

## Downstream modeling

- whether FPC scores are predictors or outcomes;
- cross-validation unit;
- whether FPCA is re-fit inside training folds for predictive analyses.

The goal is not to force one workflow. It is to make the chosen workflow auditable.


## Functional anomaly / influence review

If functional diagnostics will be used, specify before condition-effect inspection:

- which diagnostic family is planned;
- FPC count used for reconstruction/score-space screening;
- robust or empirical covariance;
- review thresholds;
- independent criteria that could justify exclusion;
- omission unit for influence analysis;
- whether sensitivity refits after justified exclusions will be reported.

Pre-registering a **review rule** is different from pre-registering an **exclusion rule**.
