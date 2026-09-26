# Method comparison

| Question | Functional trajectory method | What it is not |
|---|---|---|
| Preserve unequal sample times before analysis | native irregular trajectory representation | automatic resampling during import |
| Assess whether FPC shape is reproducible | bootstrap component matching | a significance test |
| Simultaneous mean uncertainty on a common grid | studentized Gaussian multiplier maximum | independent pointwise intervals treated as a global band |
| Flag trajectories for functional review | reconstruction + robust score-space diagnostics | an automatic exclusion rule |
| Assess whether one participant/group drives the basis | leave-one-group-out FPCA influence | proof that the group is invalid |
| Quantify what registration changes | pre/post registration FPC matching | proof that registration is beneficial |
| Model timing deformation itself | phase FPCA on warpings | ordinary spatial FPCA |
| Dominant whole-curve variation | FPCA/MFPCA | time-point significance testing |
| Participant vs trial variation | multilevel FPCA | ordinary PCA treating trials as independent |
| Same shape, different timing | registration / elastic FDA | automatically “better preprocessing” |
| AOI allocation over time | compositional FPCA | independent PCA of bounded proportions |
| Condition-specific smooth mean | often GAMM | FPCA by itself |
| Experimental predictors changing a functional response | function-on-scalar regression | treating every time point as an unrelated regression or treating repeated trials as independent |
| Trial-varying predictors with repeated participant curves | functional mixed-effects regression | participant averaging or independent pointwise mixed models |
| Smooth trial-specific heterogeneity after participant effects | nested trial functional random intercept (0.48) | forcing smooth trial variation into iid or short-range residual error |
| Exact onset of divergence | specialized onset methods | FPCA loading inspection |
| Predict scalar outcome | functional regression / score regression | causal mediation by default |
| Predict an external scalar outcome while tuning retained FPC count | fold-local FPCA regression CV / nested CV | variance-explained or reconstruction selection |

FDA and GAMMs are complementary: FPCA summarizes covariance and dominant modes; GAMMs model conditional mean structure over time.


## Function-on-scalar versus scalar-on-function

| Question | Direction | Primary tool | Boundary |
|---|---|---|---|
| How does a continuous gaze response change with condition, expertise, age, or another scalar predictor? | scalar predictors → functional response | `fit_function_on_scalar_regression()` | 0.35 repeated trials require participant-constant predictors and aggregation |
| How does a repeated binary/count functional response change with scalar predictors? | scalar predictors → non-Gaussian functional response | `fit_generalized_function_on_scalar_regression()` | marginal participant-clustered GEE; Bernoulli/logit or Poisson/log; working independence + robust sandwich in 0.51 |
| How does a functional gaze trajectory predict a scalar outcome? | functional predictor → scalar response | `fit_scalar_on_function_regression()` / FPCR | inference depends on retained FPCA representation |
| Do I need participant-specific random functional effects or within-participant trial predictors? | repeated-measures functional response | `fit_functional_mixed_effects_regression()` | joint Gaussian mixed model; declare bases/covariance assumptions explicitly |
| Do residuals show smooth trial-specific shape beyond participant effects? | participant → trial → time covariance | `fit_functional_mixed_effects_regression(..., trial_random_effect="functional_intercept")` | shared unstructured trial-basis covariance; no automatic covariance selection |

Function-on-scalar regression estimates coefficient functions over time. Scalar-on-function regression instead compresses or integrates information from a functional predictor to explain a scalar response. They answer opposite regression questions and should not be used interchangeably.

## Mixed-effects covariance structures: fit versus sensitivity

| Goal | Tool | Interpretation boundary |
|---|---|---|
| Fit one declared covariance structure | `fit_functional_mixed_effects_regression()` | no automatic covariance-family selection |
| Diagnose residual structure within one fit | `functional_mixed_effects_residual_diagnostics()` | descriptive raw/whitened ACF and variogram |
| Compare predeclared already fitted structures | `functional_mixed_effects_covariance_sensitivity()` | explicit reference; no ranking/winner/LRT |
| Interpret where variability is attributed over time | `functional_mixed_effects_variance_decomposition()` | participant intercept/slope/cross-covariance, trial and residual terms remain separate |

Version 0.50 requires successful comparison fits to use identical observations,
fixed design/basis, participant mapping/basis, time grid, response dimension and
ML/REML mode. Failed predeclared structures remain visible. AIC/BIC are
descriptive and the returned table preserves declaration order instead of
sorting by an information criterion.

## Pointwise versus simultaneous FPC uncertainty

| Goal | Preferred tool | Important boundary |
|---|---|---|
| visualize local bootstrap variability of an FPC | matched pointwise envelope | descriptive only; no whole-curve coverage claim |
| whole-grid uncertainty statement for one FPC | component-wise simultaneous FPC band | observed grid only; individual axis must be identifiable |
| joint whole-grid statement across several FPCs | familywise simultaneous FPC band | more conservative; near-tied axes still require subspace interpretation |
| robust interpretation under near-tied eigenvalues | principal-angle subspace analysis | answers an eigenspace question, not individual-axis uncertainty |


## FPCA variance decomposition: estimate versus uncertainty

| Question | Tool | Interpretation boundary |
|---|---|---|
| how much sample variance does each FPC explain? | fitted FPCA spectrum | descriptive sample estimate |
| how variable are individual eigenvalues/ratios? | component-wise spectrum bootstrap | matched reference-FPC identity |
| how variable is the reported spectrum jointly across components? | familywise spectrum bootstrap | separate calibration within each metric |
| how much do the top k components explain? | cumulative spectrum bootstrap | descending eigenvalue rank, not shape matching |
| how many components should I retain? | explicit selection procedure | not answered automatically by spectrum intervals |


## FPC score uncertainty targets

| Question | Tool | What varies? | Important boundary |
|---|---|---|---|
| what are the fitted training scores? | fpca_score_frame() | nothing after fit | point estimates conditional on fitted basis |
| how do fixed-target scores move when the basis changes? | bootstrap_fpca_score_uncertainty() | FPCA training basis | basis-resampling uncertainty only |
| what is the sparse conditional score? | FDApy/PACE interoperability | latent score estimated from sparse observations | different estimator and uncertainty target |
| how uncertain is a downstream regression coefficient? | specialist/full uncertainty procedure | scores + regression/model | not provided by 0.11 score envelopes |


## Gaussian scalar-on-function regression uncertainty

| Question | Tool | What is refit? | Inferential boundary |
|---|---|---|---|
| fit a scalar outcome from FPC scores | fit_scalar_on_function_regression() | one FPCA-conditioned regression | point estimate conditional on fitted basis |
| choose FPC count for prediction | cross_validate_fpca_regression() / nested_cross_validate_fpca_regression() | FPCA + regression inside folds | predictive selection/performance, not coefficient inference |
| inspect basis-only score variability | bootstrap_fpca_score_uncertainty() | FPCA basis | fixed-target score sensitivity only |
| quantify Gaussian FPCR slope/mean uncertainty | bootstrap_fpca_regression_uncertainty() | paired sample + FPCA + Gaussian regression | fixed component count; pointwise slope and conditional-mean intervals |
| test the full slope with operator-scaled asymptotics | specialist recent FPCR method | operator-scaled statistic | not implemented in eyetrajectoriespy 0.12 |


## Gaussian FPCR slope uncertainty: pointwise versus simultaneous

| Question | Tool | Calibration family | Boundary |
|---|---|---|---|
| what is uncertainty at each slope grid cell? | bootstrap_fpca_regression_uncertainty() | each cell separately | pointwise percentile intervals |
| what band covers sampled time within each dimension? | fpca_regression_slope_simultaneous_band(..., simultaneous_scope="dimension") | one maximum over time per dimension | not joint across dimensions |
| what band covers the full sampled multivariate slope grid? | fpca_regression_slope_simultaneous_band(..., simultaneous_scope="global") | one maximum over time × dimensions | observed-grid only |
| what formal operator-scaled FPCR test should be used? | specialist recent method | operator-scaled statistic | not implemented by the 0.13 grid band |


## Gaussian FPCR target uncertainty: mean response versus future outcome

| Question | Tool | Randomness represented | Boundary |
|---|---|---|---|
| what is uncertainty in the fitted conditional mean for a fixed target? | bootstrap_fpca_regression_uncertainty() | paired resampling of predictor/outcome and full FPCR refit | no future response noise |
| what is uncertainty for a future observed scalar response at that fixed target? | fpca_regression_future_prediction_interval() | paired-bootstrap mean distribution + independent centered empirical residual draw | common/exchangeable residual distribution assumed |
| what if response variance is heterogeneous? | specialist wild/bootstrap method | model-specific heteroscedastic error mechanism | not implemented by 0.14 |


## Functional anomaly review: fitted-sample diagnostics versus conformal targets

| Question | Tool | Reference construction | Inferential boundary |
|---|---|---|---|
| which curves in my fitted sample deserve review? | diagnose_fpca_outliers() | same fitted sample | descriptive review diagnostics |
| is a new curve unusually poorly reconstructed? | split_conformal_fpca_anomaly(..., nonconformity="reconstruction_rmse") | proper-training FPCA + disjoint calibration | marginal curve-level conformal p-value |
| is a new curve extreme within the retained score span? | split_conformal_fpca_anomaly(..., nonconformity="score_mahalanobis") | proper-training FPCA/covariance + disjoint calibration | marginal curve-level conformal p-value |
| do I need functional-depth FDR control with CCV adjustments? | specialist Kim–Park/Bates procedure | depth-based conformal framework | not implemented by 0.15 |


## Gaussian FPCR heteroscedastic projection inference

| Question | Tool | Functional basis during bootstrap | Error model / boundary |
|---|---|---|---|
| propagate sampling uncertainty in basis + Gaussian regression | bootstrap_fpca_regression_uncertainty() | refit in each paired sample | curve/participant paired resampling |
| infer a fixed-target centered projection under heterogeneous response errors | wild_bootstrap_fpca_projection() | fixed | multiplier wild bootstrap with bootstrap-level heteroscedastic studentization |
| predict a future observed response under pooled exchangeable errors | fpca_regression_future_prediction_interval() | inherited paired-bootstrap means | centered empirical future residual draw |
| handle repeated/clustered rows with a wild bootstrap | specialist clustered method | method-specific | not implemented by 0.16 |


## Choosing the FPCR truncation for different goals

| Question | Method | Selection target | Important boundary |
|---|---|---|---|
| how many FPCs best predict a scalar outcome? | cross_validate_fpca_regression() | held-out outcome loss | predictive criterion |
| how many FPCs reconstruct trajectories? | cross_validate_fpca_reconstruction() | held-out functional reconstruction | not outcome inference |
| which h should stabilize heteroscedastic WB inference for one target? | scan_wild_bootstrap_fpca_truncations() + select_fpca_wild_bootstrap_truncation() | adjacent interval center + width stability | target-specific heuristic conditional on k=g |
| what h is universally optimal for bootstrap coverage? | not provided | coverage-optimal tuning | unresolved by the current 2026 method |


## Gaussian FPCR fixed-target uncertainty: target-wise versus familywise

| Question | Tool | Calibration | Boundary |
|---|---|---|---|
| what is the heteroscedastic interval for each fixed target separately? | `wild_bootstrap_fpca_projection()` | target-specific quantile of absolute studentized roots | target-wise only |
| what interval family protects all declared fixed targets simultaneously? | `fpca_wild_bootstrap_projection_simultaneous_interval()` | one max-|t| quantile across all targets within each shared bootstrap replicate | fixed declared target family only |
| what is uncertainty in the fitted conditional mean with basis/regression sampling variability? | `bootstrap_fpca_regression_uncertainty()` | paired full-pipeline bootstrap | not heteroscedastic fixed-regressor wild bootstrap |
| what is the interval for a future observed scalar response? | `fpca_regression_future_prediction_interval()` | paired-bootstrap means plus residual draw | pooled/exchangeable future-response error |
| what band covers the reconstructed functional slope over time? | `fpca_regression_slope_simultaneous_band()` | maximum over observed slope grid | different estimand; observed-grid slope band |

The 0.18 familywise helper is a post-calibration of one already generated target-root matrix. It should not be described as a future-response prediction region or as clustered wild-bootstrap inference.


## Fixed-target FPCR evidence: intervals versus tests

| Question | Tool | Calibration | Boundary |
|---|---|---|---|
| what is the heteroscedastic interval for each fixed target separately? | `wild_bootstrap_fpca_projection()` | target-specific absolute studentized roots | marginal / target-wise |
| what interval family covers all declared fixed targets simultaneously? | `fpca_wild_bootstrap_projection_simultaneous_interval()` | one max-|t| critical value across the shared root matrix | fixed declared family |
| what is the bootstrap tail probability for each target null? | `fpca_wild_bootstrap_projection_family_test()` target-wise output | each target's absolute root distribution | no multiplicity adjustment |
| what is the single-step multiplicity-adjusted probability for each target null? | `fpca_wild_bootstrap_projection_family_test()` adjusted output | replicate-wise max absolute root | complete declared family; no universal strong-FWER claim |
| is the complete family of supplied nulls compatible with the joint root approximation? | `fpca_wild_bootstrap_projection_family_test()` global output | maximum observed statistic versus bootstrap maxima | global union-intersection style test |
| what if I need closed/step-down strong FWER under arbitrary subset nulls? | specialist multiple-testing procedure | intersection/subset-aware calibration | not implemented by 0.19 |

## Trajectory similarity and robustness

| Question | Primary method | What it is not |
|---|---|---|
| Same-time integrated functional separation | functional L2 | elastic sequence alignment |
| Worst separation along an order-preserving coupling | discrete Fréchet | cumulative alignment cost |
| Cumulative mismatch after elastic sequence-index alignment | DTW | direct elapsed-time correspondence |
| Does the similarity conclusion depend on the declared distance contract? | `trajectory_distance_sensitivity()` | an automatic selector of the "best" metric |

The 0.38 sensitivity layer compares rankings and local neighbors while retaining
each distance matrix on its native scale. It is descriptive and does not attach
ordinary correlation p-values to dependent pair distances.

## RQA versus recurrence networks

| Question | Use | Main dependency |
|---|---|---|
| What line structures occur in the recurrence plot? | RQA | radius policy, Theiler window, minimum line lengths |
| What graph topology is induced by recurrence neighborhoods? | recurrence network | radius policy, Theiler window, graph convention |
| How many recurrent neighbors does each state have? | recurrence-network degree | threshold and state-space geometry |
| Are recurrent neighborhoods locally interconnected? | clustering / transitivity | threshold, state-space geometry, temporal exclusions |

RQA and recurrence networks reuse the same recurrence relation but summarize
different structures. Neither should be selected post hoc because it produces a
more favorable result.

## Cross-recurrence versus joint recurrence

| Question | Method | Interpretation |
|---|---|---|
| Is a state in system A close to a state in system B? | cross-recurrence | cross-system state similarity |
| Do separately defined systems recur within their own state spaces at the same time pair? | joint recurrence | coincident within-system recurrence |
| Is there directional information transfer? | neither by itself | requires a separate directional model such as transfer entropy or another justified coupling model |

Joint recurrence permits different subsystem dimensions, variables, metrics,
and thresholds, but version 0.39 requires an exact common time grid, common
time unit, and shared Theiler exclusion. It does not search over lags or choose
thresholds to maximize apparent coupling.

## Nonlinear trajectory dynamics

| Scientific question | Preferred 0.23 tool | What it does not establish |
|---|---|---|
| Does gaze return to nearby spatial/state configurations? | `recurrence_matrix()` + `rqa_metrics()` | a unique latent cognitive state or deterministic attractor |
| Does recurrent structure change during the trial? | `windowed_rqa()` | independent observations across overlapping windows |
| Do between-curve differences in time-varying recurrence shape matter? | `windowed_rqa_trajectory_set()` → FPCA/MFPCA/regression | independent window rows or a new overlapping-window inferential theorem |
| Do two trajectories share recurrent state structure? | `cross_recurrence_matrix()` + `cross_rqa_metrics()` | causal coupling or synchronization mechanism |
| How quickly do nearby reconstructed states separate? | `local_divergence_curve()` + Rosenstein LLE | proof of deterministic chaos |
| Is the nonlinear statistic unusual under a linear-stochastic surrogate null? | `surrogate_nonlinearity_test()` | a unique nonlinear mechanism |
| Do repeated observed cycles contract or expand locally? | empirical Poincare return map | a monodromy matrix, Floquet multipliers, or model-based orbital stability |
| How does a modeled attractor change with a control parameter? | not implemented in 0.23 | requires explicit system identification / continuation model |

RQA and FPCA are complementary rather than substitutes. FPCA summarizes dominant between-curve functional variation; RQA summarizes within-trajectory recurrent temporal organization. Version 0.24 makes that bridge explicit with `windowed_rqa_trajectory_set()`, while preserving overlap, edge/tail, radius-policy, and source-unit provenance. The FDA step remains separately justified and does not turn overlapping windows into independent observations.

## Directed dependence versus recurrence coupling

| Method | Question | Time contract | Directionality |
|---|---|---|---|
| Cross recurrence | When are two declared state spaces close across all index pairs? | rectangular all-pairs; no implicit alignment | no |
| Joint recurrence | When do synchronized subsystems recur simultaneously within themselves? | exact common grid | no |
| Transfer entropy | Does declared source history add predictive information about the current target beyond declared target history? | explicit sample-index histories and source lag | yes, predictive direction only |

Transfer entropy is not a replacement for cross/JRQA, and none of these methods
is automatically a causal estimator. The representation and scientific
question determine which estimand is appropriate.

## Fixed TE versus TE specification sensitivity

| Method | Primary purpose | Output | Selection behavior |
|---|---|---|---|
| Fixed discrete TE | Estimate directed predictive information under one declared history/lag contract | one TE estimate plus support diagnostics | none |
| Fixed TE + circular-shift test | Compare one declared TE estimate with one declared circular-shift null | observed TE, surrogate distribution, plus-one p-value | none |
| TE specification sensitivity | Describe robustness across a declared history/lag Cartesian grid | complete specification table + descriptive summaries | never selects a winner |

The sensitivity layer answers whether the substantive TE result depends on
defensible analysis choices. It does not replace a primary specification,
cross-validation procedure, multiplicity plan, or causal-identification design.

## Pairwise versus conditional transfer entropy

| Method | Question | Conditioning | Interpretation boundary |
|---|---|---|---|
| Pairwise discrete TE | Does source history predict the next target beyond target history? | target history | directed predictive information |
| Conditional discrete TE | Does source history add predictive information beyond target history and one declared process? | target history + explicit conditioning history | conditional directed predictive information, not causal proof |
| Conditional TE + source-shift test | Is observed conditional TE large relative to declared source-only circular shifts? | same fixed conditioning process | surrogate evidence under the declared shift null |

Use conditional TE when a scientifically specified process is part of the
question. Do not add conditioning variables merely to search for a preferred
result.

## Pointwise versus simultaneous mixed-effects coefficient inference

| Output | Independent resampling unit | Scope | Key limitation |
|---|---|---|---|
| MixedLM pointwise Wald interval | none; model covariance only | one coefficient value at one observed time | no whole-function multiplicity calibration |
| 0.44 coefficient-scope band | participant | one fixed coefficient over the complete observed time grid | covariance parameters and bases held fixed |
| 0.44 family-scope band | participant | all declared fixed coefficients × observed time grid | more conservative; same fixed-covariance limitation |

Use the base pointwise interval for explicitly pointwise questions. Use the
0.44 participant-cluster band when the scientific claim concerns the complete
observed coefficient trajectory or a predeclared family of coefficient
trajectories. Neither band mode provides continuous-domain coverage between
unsampled time points or propagates variance-component/basis-selection
uncertainty.

## Random functional intercept versus one random functional slope

| Model | Random-effect dimension | Free unstructured covariance parameters | Identification safeguard |
|---|---:|---:|---|
| Functional random intercept | $q$ | $q(q+1)/2$ | participant count at least max(4, q+1) |
| Intercept + one random functional slope | $2q$ | $(2q)(2q+1)/2$ | named predictor varies within every participant and participant count exceeds covariance-parameter count |
| Nested trial functional intercept | $q_u$ per trial | $q_u(q_u+1)/2$ shared across trials | unique participant/trial pairs, at least two trials per participant, total nested trials exceed covariance-parameter count |

The 0.45 slope model is appropriate when the scientific question concerns
participant heterogeneity in the time-varying effect of one predeclared
predictor. It is not an automatic improvement over the simpler random-
intercept model and the package does not compare or select the structures on
the analyst's behalf.

## Fixed-covariance versus full-refit participant bootstrap

| Bootstrap | Participant resampling | Fixed effects refit | Random-effect covariance refit | Residual variance refit | Model specification reselected |
|---|---|---|---|---|---|
| Fixed-covariance (0.44) | yes | yes, GLS | no | no | no |
| Full-refit (0.46+) | yes | yes, declared backend | yes; participant and, when present, trial covariance | yes | no |

Both methods resample whole participants. The full-refit version additionally
propagates variance-component re-estimation through the fixed-effect bootstrap
distribution.

Use `compare_functional_mixed_effects_bootstraps()` to inspect how much this
changes simultaneous-band width over the observed time grid. The width ratio is
a descriptive sensitivity measure, not a criterion for choosing a preferred
model.

## Mixed-effects covariance hierarchy

| Declared structure | Participant functional effect | Trial functional effect | Residual process | Diagnostic emphasis |
|---|---|---|---|---|
| participant + iid | yes | no | iid | raw residual ACF/variogram |
| participant + trial + iid | yes | shared-Ψ trial intercept | iid | whether broad smooth residual structure remains |
| participant + exponential | yes | no | physical-time exponential | whitened residual ACF/variogram |
| participant + trial + exponential | yes | shared-Ψ trial intercept | physical-time exponential | whitening plus covariance-decomposition stability |
| participant + AR(1) | yes | optional | signed index-step AR(1), regular grid only | whitened residual ACF/variogram |

Version 0.49 fits only the analyst-declared row; it does not rank these
structures or choose a winner. A long-range exponential process can compete
with a smooth trial functional random effect, so trial-covariance conditioning,
serial-parameter boundaries, bootstrap stability, and fixed-effect sensitivity
must be interpreted together. Version 0.50 makes that structural sensitivity
explicit without turning it into automatic model selection.

