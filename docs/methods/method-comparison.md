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
| Exact onset of divergence | specialized onset methods | FPCA loading inspection |
| Predict scalar outcome | functional regression / score regression | causal mediation by default |
| Predict an external scalar outcome while tuning retained FPC count | fold-local FPCA regression CV / nested CV | variance-explained or reconstruction selection |

FDA and GAMMs are complementary: FPCA summarizes covariance and dominant modes; GAMMs model conditional mean structure over time.


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
