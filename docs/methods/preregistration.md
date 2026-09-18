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
