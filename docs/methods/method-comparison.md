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
