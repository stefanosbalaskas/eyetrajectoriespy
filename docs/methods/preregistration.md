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

## Sparse functional estimation

If trajectories may be too sparse for defensible common-grid interpolation, pre-specify:

- the rule distinguishing dense-irregular from sparse analysis;
- selected functional dimension(s);
- how missing tracker rows become absent observations;
- minimum observation count or coverage requirements;
- sparse-FPCA backend;
- smoothing configuration and any backend tuning parameters;
- evaluation-grid rule/domain/resolution;
- PACE tolerance;
- component-count strategy;
- planned sensitivity analyses.

If x(t) and y(t) are analyzed separately, pre-register them as separate univariate sparse analyses rather than a joint 2-D MFPCA.

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

## Near-tied eigenvalues and subspace stability

If near-tied components are anticipated, pre-specify:

- whether adjacent eigengaps will be inspected;
- any relative-gap threshold used only for descriptive review;
- the contiguous component block to be evaluated as a subspace;
- curve versus participant bootstrap;
- bootstrap replicate count and random seed;
- principal-angle/projector-distance summaries to report.

Do not choose a near-tie threshold after seeing which threshold produces the preferred component interpretation.

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


## Functional mean inference

If uncertainty for a mean trajectory will be reported, pre-specify:

- the population estimand;
- curve versus participant inference unit;
- participant column for repeated trials;
- whether within-participant trajectories are averaged before inference;
- confidence level;
- multiplier replicate count and random seed;
- the sampled functional dimensions included in the joint maximum;
- how incomplete trajectories will be handled before inference;
- whether the claim is observed-grid simultaneous coverage or a separately justified continuous-domain band.

Do not switch from participant-level to curve-level inference after seeing that trial-level treatment creates narrower bands.


## Predictive FPC-count selection

If FPC count will be tuned for a scalar outcome, pre-specify:

- Gaussian versus binomial family;
- predictive loss (RMSE/MAE or log-loss/Brier);
- candidate FPC counts;
- scaling choice;
- curve versus participant/group fold unit;
- grouping column;
- minimum-loss versus one-standard-error rule;
- covariates and their encoding;
- whether nested outer CV will estimate predictive performance;
- outer/inner fold counts and random seed where applicable.

State that FPCA and regression will be refitted inside training folds. If participant-level outcomes are duplicated over trials, pre-specify aggregation or a grouped-model alternative rather than treating grouped CV as a dependence model.


## Simultaneous FPC-shape uncertainty

If individual FPC uncertainty is confirmatory, pre-specify:

- the number of FPCs for which bands will be constructed;
- curve versus participant bootstrap resampling;
- bootstrap replicate count and random-seed policy;
- confidence level;
- component-wise versus familywise simultaneous scope;
- scaling used by FPCA;
- whether a relative-eigengap screening threshold will be used;
- the action for a screened near tie (error, warning, or descriptive record);
- that calibration is over the observed time-by-dimension grid;
- how eigenspace/subspace results will supersede individual-axis interpretation when identification is weak.

Do not select a near-tie threshold after seeing which FPC labels it permits.


## FPCA spectrum uncertainty

If eigenvalues or variance decomposition will support confirmatory interpretation, pre-specify:

- the number of spectrum components to report;
- curve versus participant bootstrap resampling;
- participant identifier when clustered resampling is used;
- bootstrap replicate count and random-seed policy;
- FPCA/MFPCA scaling;
- confidence level;
- component-wise versus familywise calibration;
- that familywise calibration is separate for each spectrum metric;
- that individual eigenvalues/ratios are shape-matched while cumulative variance remains rank-ordered;
- whether support-exceeding interval limits will be displayed as estimated rather than clipped;
- the separate rule, if any, used for choosing the retained FPC count.

Do not convert the uncertainty result into a post hoc retention threshold after seeing the intervals.


## FPC score basis uncertainty

If score uncertainty will support confirmatory interpretation, pre-specify:

- the FPCA training sample;
- which target trajectories will be projected;
- whether targets are training curves or an external compatible set;
- retained FPC count and scaling;
- curve versus participant basis resampling;
- participant identifier when clustered resampling is used;
- bootstrap replicate count and seed policy;
- percentile level;
- how low component-matching similarity will be handled or reported;
- that targets remain fixed during the bootstrap;
- that the result excludes target measurement error, latent-curve uncertainty, preprocessing uncertainty, future-curve variability, and full downstream-model uncertainty.

Do not relabel a basis-resampling envelope as a complete score confidence interval after seeing its width.


## Gaussian FPCR bootstrap uncertainty

Pre-specify:

- Gaussian scalar-on-function regression as the inferential family;
- the retained FPC count and how it was selected;
- MFPCA scaling;
- curve versus participant paired resampling;
- participant identifier for repeated-trial designs;
- bootstrap replicate count and random-seed policy;
- percentile level;
- whether fixed target trajectories will be evaluated;
- that target intervals refer to the conditional mean rather than future observed outcomes;
- that slope intervals are pointwise rather than simultaneous;
- that rank-deficient bootstrap replicates will terminate the procedure rather than be silently replaced;
- that the component count will remain fixed across bootstrap replicates.

Do not reinterpret the resulting percentile slope envelope as the operator-scaled FPCR significance test from recent theory.


## Simultaneous Gaussian FPCR slope bands

If a simultaneous slope band is confirmatory, pre-specify:

- that the paired Gaussian FPCR bootstrap will be fitted first;
- the bootstrap unit, FPC count, scaling, replicate count, and seed policy inherited from that analysis;
- the simultaneous confidence level;
- global versus dimension-wise calibration scope;
- that the family is defined over observed slope grid coordinates only;
- that no continuous-domain coverage claim will be made;
- that the band is not the Imaizumi-Kato confidence-band procedure or the Yeon operator-scaled significance test;
- how exact zero-variance cells will be reported.

Do not switch from dimension-wise to global scope after inspecting which one changes a substantive conclusion.


## Gaussian FPCR future-outcome prediction

Pre-specify:

- the Gaussian FPCR model and retained FPC count;
- how the FPC count was selected;
- the paired-bootstrap unit and seed policy used by the underlying 0.12 fit;
- the fixed target trajectories to be predicted;
- the future-outcome interval level;
- centered empirical residual resampling as the response-noise model;
- the assumption of a common/exchangeable residual distribution;
- whether residual heterogeneity will be inspected before interpreting prediction intervals;
- that intervals are marginal per target and not simultaneous/joint;
- that target-curve uncertainty and component-selection uncertainty are not included.

Do not switch to the future-outcome interval only after noticing that a conditional-mean interval is too narrow for a preferred conclusion.
