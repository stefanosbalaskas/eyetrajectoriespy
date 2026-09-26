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


## Split-conformal FPCA anomaly review

If new-trajectory anomaly review is confirmatory, pre-specify:

- the proper-training, calibration, and target partition rule;
- the scientific inlier reference population;
- retained FPC count and channel scaling;
- reconstruction-RMSE versus score-space Mahalanobis nonconformity;
- empirical versus robust score covariance when Mahalanobis nonconformity is used;
- the review alpha level;
- how calibration size constrains the minimum attainable p-value;
- the curve-level exchangeability assumption;
- how repeated participant trials will be handled before conformal analysis;
- whether more than one nonconformity score will be examined;
- that review flags will not automatically trigger data exclusion;
- that the 0.15 method does not implement calibration-conditional adjustment or FDR control.

Do not choose the proper/calibration split, FPC count, nonconformity score, covariance estimator, or alpha after inspecting which configuration flags the preferred curves.


## Heteroscedastic Gaussian FPCR wild-bootstrap projection inference

Pre-specify:

- Gaussian scalar-on-function FPCR as the model family;
- that the functional regressors and FPCA/MFPCA basis remain fixed during wild resampling;
- the independent sampling unit;
- the metadata column used to verify one row per independent unit, if available;
- residual truncation k;
- bootstrap pseudo-truth truncation g=k;
- inference truncation h with h>=g;
- how k and h were chosen;
- FPCA/MFPCA scaling;
- wild multiplier family;
- bootstrap replicate count and random seed;
- confidence level;
- fixed target trajectories;
- that intervals are target-wise rather than simultaneous;
- that the estimand is the centered projection relative to the training functional mean;
- that future-outcome noise, basis-estimation uncertainty, clustered resampling, and component-selection uncertainty are not included.

Do not select k, h, or multiplier family after inspecting which configuration gives a preferred substantive conclusion.


## Stabilized-volatility wild-bootstrap truncation selection

Pre-specify:

- how residual truncation k will be selected;
- that g=k;
- the consecutive candidate h grid H;
- the wild-bootstrap multiplier family;
- bootstrap replicate count and seed;
- confidence level;
- width threshold rho_w in outcome units;
- center threshold rho_c in outcome units;
- paper run parameter r;
- whether h may vary by target;
- behavior if no stable run is found;
- whether selection is primary or sensitivity analysis.

Do not tune rho_w, rho_c, r, or the candidate grid after inspecting which configuration yields preferred substantive conclusions.


## Simultaneous fixed-target FPCR wild bootstrap

For confirmatory familywise inference across fixed targets, pre-specify:

- the scientific rule defining every target trajectory in the family;
- whether the family contains all planned targets or a named subset;
- the familywise confidence level;
- residual truncation k, pseudo-truth rule g=k, and inference truncation h, or the exact prespecified procedure used to choose them;
- multiplier family and bootstrap replicate count;
- channel scaling;
- the independent sampling unit and any identifier used to verify it;
- that the FPCA basis and functional regressors remain fixed during wild resampling;
- that one maximum absolute studentized root is taken across the complete target family within each bootstrap replicate;
- whether target-wise intervals will also be reported descriptively;
- that future-outcome noise, clustered dependence, preprocessing uncertainty, and component-selection uncertainty are outside this interval unless handled separately.

Do not define or shrink the target family after inspecting which marginal intervals are favorable. Changing the family changes the inferential question.


## Fixed-family FPCR wild-bootstrap hypothesis tests

For confirmatory fixed-target testing, pre-specify:

- the scientific rule defining every target in the testing family;
- the scalar or target-specific null projection values;
- the two-sided alternative used by the current API;
- the significance level;
- the p-value correction, normally the default plus-one rule;
- the planned number of bootstrap replicates and the resulting minimum attainable p-value;
- residual truncation k, pseudo-truth g=k, inference truncation h, and any pre-specified or data-driven rule used to choose them;
- multiplier family and channel scaling;
- the independent sampling unit;
- whether target-wise probabilities, single-step maxT-adjusted probabilities, and the global family test are confirmatory or descriptive;
- that the bootstrap is not regenerated under an explicitly imposed target null;
- that strong FWER for arbitrary subset nulls is not claimed without additional subset-pivotality or closed-testing theory.

Do not drop targets after seeing their unadjusted p-values and retain the original familywise interpretation.

## Finite-bootstrap Monte Carlo precision diagnostics

If Monte Carlo precision will be used to judge whether the planned bootstrap budget is adequate, pre-specify:

- the initial number of bootstrap replicates B;
- the diagnostic confidence level;
- which probabilities will be audited: target-wise, maxT-adjusted, global, or all three;
- the significance level used by the original family test;
- the rule for calling a result Monte-Carlo-sensitive;
- whether a larger fixed bootstrap run will be triggered by a sensitivity flag;
- the maximum follow-up bootstrap budget, if a second fixed run is planned;
- how both the original and follow-up runs will be reported.

Do not repeatedly increase B until a preferred significance outcome appears and then describe the final run as though B had been fixed in advance. Version 0.20 does not implement a sequential always-valid stopping rule.

## Nonlinear trajectory dynamics

Before inspecting nonlinear-dynamics results, predeclare where applicable:

- source trajectory dimensions and their physical/normalized units;
- any interpolation, smoothing, filtering, registration, or coordinate transformation performed upstream;
- whether recurrence uses observed state or a delay reconstruction;
- delay (τ), embedding dimension (m), and the diagnostics used to justify them;
- recurrence metric and exactly one radius policy: fixed (ε) or target recurrence rate;
- Theiler window;
- minimum diagonal and vertical line lengths;
- window size and step for windowed RQA;
- cross-recurrence pairing/reference definition;
- local-divergence maximum horizon;
- LLE fit-start and fit-end interval;
- IAAFT surrogate count, alternative, seed policy, maximum iterations, and convergence tolerance;
- for multivariate IAAFT, selected dimensions, explicit reference dimension, planned acceptable spectrum/cross-spectrum diagnostic thresholds or review policy, and whether reference-dimension sensitivity will be examined;
- Poincare section variable/value, crossing direction, returned state dimensions, reference-state rule, neighborhood policy, and stability tolerance;
- planned sensitivity analyses for all scientifically consequential tuning parameters.

Do not define a positive LLE as “chaos” in the preregistration. If chaos is a scientific hypothesis, state the additional evidence required beyond the local-divergence estimate and specify the surrogate null being tested.


For RQA-derived functional trajectories, additionally predeclare:

- the selected functional RQA metrics;
- fixed-radius versus target-recurrence-rate policy;
- window length and step, including intended overlap;
- whether any edge/tail loss is acceptable for the scientific question;
- `undefined_policy` and the downstream plan if missing functional values remain;
- the independent sampling unit for downstream FDA;
- any downstream metric scaling and FPCA/MFPCA component-selection rule.

Do not switch from fixed radius to target recurrence rate after seeing which setting creates a more favorable RR trajectory. Under target-rate mode, RR itself is controlled by construction and must not be promoted to a confirmatory functional outcome.

Classical Floquet/monodromy and numerical-continuation claims remain outside the 0.25 observational-gaze contract.


## Recurrence networks

If recurrence-network topology is a planned analysis, pre-specify:

- source state representation and selected dimensions;
- coordinate/state scaling;
- recurrence metric;
- fixed-radius versus target-recurrence-rate policy;
- radius or target recurrence rate;
- Theiler window;
- graph outcomes to be interpreted (degree, clustering, transitivity,
  components, isolation);
- whether node-level or global summaries are primary;
- how target-RR density control will affect interpretation.

Do not tune the recurrence threshold after inspecting which value maximizes
clustering, transitivity, connectivity, or group separation.

## Joint recurrence / JRQA

Before inspecting a joint recurrence analysis, pre-specify:

- every subsystem/state representation;
- the time grid and time unit required for synchronization;
- the recurrence metric for every subsystem;
- fixed-radius versus target-recurrence-rate policy for every subsystem;
- all fixed radii or target recurrence rates;
- the shared Theiler window;
- component labels;
- JRQA minimum diagonal and vertical line lengths;
- whether JRR, JDET, JLAM, line lengths, entropy, trapping time, or CORM are
  primary or supporting outcomes.

Do not shift one subsystem in time, change thresholds, or change the subsystem
set after inspecting which choice increases joint recurrence. If lagged
coupling is the scientific question, specify a separate lagged analysis rather
than silently aligning inputs inside the JRP.

## Functional RQA sensitivity and dependence-aware inference

If sliding-window RQA functions are a primary or confirmatory analysis, pre-specify:

- one primary window/step specification, if there is a primary analysis;
- the complete sensitivity grid of alternative window/step pairs;
- which RQA functional metrics are compared across the grid;
- the recurrence radius policy and all recurrence parameters held fixed across the sensitivity grid;
- the rule for interpreting material disagreement across specifications;
- that sensitivity profiles will be compared only at exact shared centers unless a separately justified alignment method is declared;
- that no automatic window/step selector will be applied.

For a functional RQA mean band, additionally pre-specify:

- curve versus participant inference unit;
- the participant column and repeated-trial aggregation rule;
- confidence level;
- multiplier replicate count and seed;
- the observed functional time-by-metric domain entering the simultaneous maximum;
- that complete derived functions, not sliding-window rows, are the resampling objects;
- that the procedure is not a moving/block bootstrap for a single long trajectory;
- that window/step selection uncertainty is not included unless a separate procedure is specified.

Do not reduce the step merely to create more apparent observations for inference. A denser derived RQA grid increases temporal sampling of the functional summary and often source-sample reuse; it does not create additional independent participants or curves.


## Nonlinear parameter-sensitivity multiverse

If reconstructed-state RQA robustness will be evaluated, pre-specify:

- the source trajectory dimensions;
- the complete embedding-dimension grid;
- the complete delay grid and units;
- exactly one threshold family: fixed radii or target recurrence rates;
- the complete threshold grid;
- the Theiler-window grid and units;
- the minimum diagonal-line grid;
- the minimum vertical-line grid;
- the recurrence distance metric;
- the RQA outcomes whose variation will be interpreted;
- whether a primary specification exists independently of the sensitivity grid.

If Rosenstein-LLE robustness will be evaluated, pre-specify:

- source dimensions;
- embedding-dimension and delay grids;
- Theiler-window grid;
- maximum divergence horizon;
- every fit interval and its units;
- which diagnostics (slope, R², SE, usable-pair support) will be reported;
- whether sign consistency is descriptive or tied to a separately stated hypothesis.

Do not choose the sensitivity grid after inspecting which values preserve a preferred conclusion. Do not define the specification with the largest positive exponent, largest DET/LAM, highest R², or smallest standard error as the primary analysis unless that selection rule itself was independently justified and its selection uncertainty is handled separately.

The package will not convert the fraction of positive LLE specifications into a probability of deterministic chaos.


## Recurrence-threshold diagnostics

If a radius profile will be used to justify or audit recurrence thresholds, pre-specify:

- source trajectory/state representation;
- dimensions and coordinate/state units;
- any upstream channel scaling or normalization;
- observed-state versus delay-embedded analysis;
- recurrence distance metric;
- complete strictly increasing radius grid;
- Theiler window and units;
- whether the profile is exploratory, a sensitivity diagnostic, or part of a threshold-selection protocol;
- the independent rule used to define any primary radius;
- whether a target-recurrence-rate analysis will be compared against the fixed-radius profile.

Do not choose the displayed radius range after inspecting where the recurrence-rate curve produces the preferred RQA result. Do not convert a visually flat or steep section into an “optimal epsilon” rule unless that selection rule was separately specified and validated.

If the maximum radius does not capture the complete eligible pair-distance distribution, pre-specify how partial coverage will be reported.


## Population bootstrap for RQA summaries

If population uncertainty for RQA metrics will be reported, pre-specify:

- source trajectory dimensions and any delay embedding;
- fixed radius versus target-recurrence-rate policy;
- recurrence distance metric;
- Theiler window and units;
- minimum diagonal and vertical line lengths;
- the exact RQA metrics to receive intervals;
- curve versus participant resampling unit;
- participant identifier for repeated-trial designs;
- that participant mode averages curve-level RQA metrics within participant before resampling;
- confidence level;
- bootstrap replicate count;
- random-seed policy;
- percentile interval as the interval method;
- how undefined source-curve metrics will be handled;
- any separate parameter-sensitivity analysis.

Do not switch from participant- to curve-level resampling after seeing narrower intervals. Do not select recurrence parameters after inspecting which settings produce the preferred confidence interval.

If target-RR mode is used, do not pre-register RR itself as an independent bootstrap outcome.


## Kantz largest-Lyapunov estimation

If Kantz LLE will be used, pre-specify:

- source dimensions and preprocessing;
- embedding dimension and delay;
- coordinate/state scaling;
- fixed neighborhood radius;
- minimum neighbors per reference;
- Theiler window and units;
- maximum divergence horizon and units;
- linear fit interval and units;
- whether Rosenstein will also be reported as a robustness comparison;
- how insufficient neighborhood support will be interpreted;
- any separate radius-sensitivity grid.

Do not select the Kantz radius or fit interval by searching for the strongest positive exponent or best (R^2). Do not switch between Rosenstein and Kantz after outcome inspection without reporting that estimator selection.


### Kantz sensitivity analysis

If a robustness multiverse is planned, pre-specify the full sets of embedding dimensions, delays, radii, minimum-neighbor requirements, Theiler windows, fit intervals, and maximum horizon. State whether one primary specification exists independently of the sensitivity analysis.

Pre-specify the failure rule. The 0.30 API fails the complete analysis if any declared specification is invalid rather than removing inconvenient settings.

Do not define the sensitivity grid after inspecting which radii produce positive exponents, high (R^2), small standard errors, or high neighborhood support.


## Continuous trajectory geometry

If heading, curvature, turning rate, or tortuosity will be analyzed, pre-specify:

- the two planar dimensions;
- coordinate system and any calibration to pixels, physical units, or degrees of visual angle;
- whether horizontal and vertical scales are commensurate;
- recorded \(y\)-axis orientation if signed geometry will be interpreted;
- upstream filtering/smoothing, if any;
- `min_speed` and `undefined_policy`;
- whether wrapped heading will be analyzed directly or transformed using a declared circular/unwrapping method;
- `min_displacement` and undefined handling for tortuosity;
- whether geometry is a primary outcome or exploratory derived function.

Do not choose a low-speed threshold, coordinate rescaling, or heading unwrapping strategy after inspecting which version produces the preferred condition difference.


## Discrete Fréchet trajectory comparison

If discrete Fréchet will be used, pre-specify the trajectory representation, included dimensions, coordinate units/scaling, optional dimension weights, any upstream resampling or simplification, and whether the distance is primary or sensitivity analysis.

Do not choose coordinate scaling, dimensions, or preprocessing after inspecting which version produces the preferred group separation. State whether elapsed timing is intentionally ignored by the comparison.


## Functional mixed-effects regression

If repeated functional responses will be modeled with the 0.36 mixed-effects
model, pre-specify:

- the selected functional response dimension and common-grid time domain;
- participant identifier and expected repeated-trial structure;
- scalar predictors and exact numeric coding, including interactions;
- fixed B-spline basis size and degree;
- participant random B-spline basis size and degree;
- ML versus REML estimation;
- optimizer and maximum iterations;
- the conditionally iid Gaussian residual assumption;
- how a near-boundary random-effect covariance will be reported;
- any planned basis-size sensitivity analysis;
- whether pointwise Wald uncertainty is descriptive/supporting rather than a
  simultaneous whole-function inferential claim.

Do not choose the basis size, response dimension, predictor coding, optimizer,
or time window after inspecting which specification yields the preferred
functional effect.

If residual-dependence diagnostics are planned, also pre-specify the maximum
index lag, the primary diagnostic level (trial, participant summary, or
overall summary), and any planned before/after mixed-model comparison. Do not
expand the lag window or choose a residual covariance structure only because a
post hoc diagnostic pattern gives the preferred inferential result.

If a nested trial functional random effect is planned, also pre-specify:

- the trial identifier;
- `trial_random_effect="functional_intercept"`;
- the trial B-spline basis size;
- the requirement for unique participant/trial pairs and at least two trials
  per participant;
- the minimum trial-count/covariance-parameter guard;
- how trial covariance eigenvalues, condition number, boundary/singularity
  diagnostics, and trial BLUP functions will be inspected;
- whether residual diagnostics will be repeated after adding the trial effect.

Do not add the trial functional effect, change its basis size, or remove it at a
boundary estimate only because doing so yields a preferred fixed-effect result.

## Function-on-scalar regression

If a functional response will be modeled using scalar predictors, pre-specify:

- the functional response representation and selected dimensions;
- the analysis time domain and common-grid construction;
- the scalar predictors and exact numeric coding;
- the intercept convention;
- all planned interaction terms;
- whether predictors are centered/scaled and how;
- the independent inference unit: curve or participant;
- for participant mode, the participant identifier and the requirement that predictors are constant within participant;
- whether repeated trials are averaged within participant;
- the wild-bootstrap multiplier distribution;
- bootstrap replicate count and random seed;
- coefficient-wise versus declared-family simultaneous scope;
- the confidence level;
- whether interpretation is limited to the observed grid;
- any separately predeclared rule for interpreting zero-exclusion regions.

Do not choose predictor coding, interactions, inference unit, time window, simultaneous scope, or response transformation after inspecting which specification produces the preferred coefficient curve. Do not analyze trial-varying within-participant predictors with curve-level independence merely because participant aggregation would reject them.

## Trajectory-distance sensitivity

If similarity robustness is planned, pre-specify:

- the complete set of distance specifications to compare;
- selected trajectory dimensions and dimension weights;
- every DTW step pattern, normalization rule, and window radius;
- neighbor k for local agreement;
- which pair-rank, rank-difference, neighbor-Jaccard, exact-set, and
  nearest-neighbor identity diagnostics are primary or supporting;
- how cutoff ties will be interpreted;
- the scientific criterion that made each compared distance contract
  defensible before results were inspected.

Do not add or remove a distance specification after seeing which one produces
the preferred trajectory grouping or nearest-neighbor pattern.

## Dynamic time warping trajectory comparison

If DTW will be used, pre-specify:

- the trajectory representation and included dimensions;
- coordinate units/scaling and any dimension weights;
- whether sequence lengths/sampling densities are expected to differ;
- the step pattern: symmetric1 or symmetric2;
- whether the reported scalar is raw cumulative cost or, for symmetric2 only, N+M-normalized distance;
- whether alignment is unconstrained or uses a Sakoe-Chiba sample-index radius;
- the exact `window_radius` when constrained;
- all upstream interpolation, resampling, smoothing, normalization, or path simplification;
- whether the optimal path will be inspected descriptively;
- whether a time-preserving comparison is primary or a planned sensitivity analysis when latency may matter.

Do not tune the step pattern, normalization choice, warping radius, coordinate scaling, dimensions, or preprocessing after inspecting which specification maximizes a preferred condition difference. Do not reinterpret the sample-index band as a physical-time tolerance unless the upstream sampling design makes that equivalence explicit.

## Discrete transfer entropy

Pre-register the source and target state definitions, sampling/index unit,
direction(s), target-history length, source-history length, source lag, and the
scientific reason for those choices. If continuous signals are converted to
states upstream, pre-register the complete discretization rule.

For circular-shift inference, declare the shift-generation rule or complete
shift set before analysis, the number of shifts, the tail, and why wrap-around
is defensible. If several directions, lags, histories, channels, or windows
will be examined, pre-register how multiplicity and specification sensitivity
will be handled. Do not select the specification producing the largest TE and
then report it as if it had been fixed in advance.

## Transfer-entropy specification sensitivity

Pre-register the complete target-history, source-history, and source-lag grids
or clearly label the multiverse exploratory. State why every grid value is
scientifically defensible and whether one fixed specification remains the
primary analysis.

If circular-shift inference is included, pre-register one common shift rule or
shift set for all specifications. State how formal multiplicity will be handled
if individual multiverse p-values are used inferentially. Do not define the
primary specification after inspecting which combination maximizes TE,
surrogate-centered TE, or statistical significance.

## Conditional transfer entropy

Pre-register the scientific role of the conditioning process and all five
history/lag settings: target history (k), source history (l), conditioning
history (m), source lag (d), and conditioning lag (c). State the discrete
state definitions and any analyst-defined empirical-support adequacy rule.

If circular-shift inference is planned, pre-register the source-only shift rule
or exact shift set and justify the wrap-around/stationarity assumption. State
that target and conditioning series remain fixed under the null.

Do not add or remove the conditioning process after inspecting which choice
produces the most favorable CTE or p-value.

## Functional mixed-effects simultaneous bands

If whole-function inference is planned, pre-register:

- the coefficient or fixed-effect family to receive simultaneous coverage;
- confidence level;
- participant as the bootstrap resampling unit;
- bootstrap replicate count and random seed;
- coefficient-wise versus full-family simultaneous scope;
- the fixed/random basis sizes and spline degree;
- whether covariance parameters are treated as fixed at the reference fit;
- the observed-grid coverage interpretation.

Do not switch from coefficient scope to family scope, change the coefficient
family, or alter basis sizes after seeing which choice yields a preferred band.

A rank-deficient participant resample should be treated as a bootstrap-design
failure requiring review, not silently replaced with another draw.

## One participant random functional slope

Pre-register:

- the exact random-slope predictor;
- why within-participant heterogeneity in that predictor is scientifically
  expected;
- fixed and random basis sizes and spline degree;
- ML versus REML and optimizer;
- the participant-count/covariance-complexity requirement;
- how covariance eigenvalues, condition number, boundary/singularity
  diagnostics, and participant BLUP slope functions will be inspected;
- whether fixed-effect simultaneous bands will use the existing
  fixed-covariance participant bootstrap.

Do not inspect several candidate predictors and retain only the random slope
that produces the most interesting heterogeneity. Version 0.45 intentionally
provides no automatic random-slope selection.

## Full-refit participant bootstrap

Pre-register:

- participant as the bootstrap unit;
- bootstrap replicate count and random seed;
- fixed-covariance versus full-refit bootstrap as distinct planned analyses;
- the fixed/participant-random/trial-random basis sizes and spline degree;
- predictor set, any single participant random-slope predictor, and whether a
  trial functional random intercept is declared;
- REML versus ML;
- optimizer and iteration limit;
- coefficient-wise versus familywise simultaneous scope;
- `failed_replicate_policy="raise"`.

State that duplicate source-participant draws receive distinct bootstrap
participant identities. For a nested trial model, state that each trial inside
each sampled participant occurrence receives a distinct bootstrap trial
identity. Model/basis/preprocessing choices remain fixed across replicates.

If both bootstrap methods are planned, specify whether the full-refit/fixed-
covariance band-width ratio is a descriptive sensitivity diagnostic rather than
a model-selection rule.

## Explicit mixed-effects residual covariance

Before examining outcome-driven residual patterns, pre-specify when feasible:

- whether the primary residual model is iid, physical-time exponential, or
  regular-grid AR(1);
- the scientific reason that the chosen family matches the sampling grid and
  expected dependence;
- whether a trial functional random effect is also included;
- the declared basis sizes for participant/trial random functions;
- the primary residual diagnostic scale after fitting (`raw`,
  `whitened`, or both), and the maximum diagnostic lag;
- the bootstrap path (fixed covariance versus full refit);
- how numerical boundary, singularity, or covariance-decomposition warnings
  will be reported.

Do not choose exponential versus AR(1), add/remove the trial functional effect,
or expand the lag window solely because one specification produces a preferred
fixed-effect conclusion. Version 0.50 is intended for transparent sensitivity
across predeclared covariance structures rather than outcome-favorable
selection.

## Covariance-structure sensitivity

If covariance robustness is planned, pre-register the finite set of covariance
specifications before inspecting comparative results. For each structure,
declare the participant random-slope predictor or its absence, trial functional
random effect or its absence, residual-correlation family, basis dimensions,
likelihood mode, optimizer contract, and convergence policy.

Also pre-register:

- the reference specification used for coefficient/band/IC differences;
- the maximum residual-diagnostic lag;
- whether simultaneous-band sensitivity will be reported and the common
  confidence/scope/bootstrap design;
- the fixed successful-fit comparability criteria;
- how failed declared structures will be retained and reported;
- the information-criterion convention, including the BIC observation count;
- which coefficient-function changes and variance-decomposition quantities are
  substantively important.

Do not choose the reference, remove failed models, expand the specification set,
or redefine a residual diagnostic after seeing which covariance structure gives
the preferred substantive conclusion.

## Generalized function-on-scalar regression

For a 0.51 generalized functional response model, pre-register:

- response family (`binomial` or `poisson`) and the scientific meaning of the response at each observed time;
- response coding rule, including whether observations are exact Bernoulli 0/1 or non-negative integer counts;
- participant column defining independent clusters;
- scalar predictors and any analyst-created interactions;
- response dimension, coefficient B-spline basis size and spline degree;
- the fixed working-independence GEE contract;
- robust sandwich covariance as the inferential covariance;
- whether whole-participant bootstrap simultaneous bands will be reported;
- bootstrap replicate count, seed, confidence level and simultaneous scope.

Do not switch family/link, change basis size, reinterpret proportions as Bernoulli outcomes, or introduce a different working correlation after seeing which specification gives a preferred coefficient trajectory.

## Generalized fixed-profile prediction

If 0.52 marginal prediction is planned, pre-register the fixed scalar predictor
profiles before examining response-scale curves. Record every predictor value,
profile identifier, and which profiles will be compared.

Also pre-register:

- the coefficient-bootstrap size and seed;
- profile-specific versus complete-profile-family simultaneous scope;
- the exact ordered profile pair for any response-scale mean difference;
- the observed-grid interpretation of simultaneous coverage;
- how extrapolation flags will be reported;
- whether an extrapolative profile is scientifically intended;
- that profile values are treated as fixed without measurement/estimation
  uncertainty.

Do not choose a profile pair after inspecting which response-scale difference
looks largest or which simultaneous band excludes zero.

