# Analysis decision map

Use the **research question and data structure** to choose the representation.

| Question | Representation / method | Key safeguard |
|---|---|---|
| Where does gaze move over trial time? | joint 2-D MFPCA | harmonize stimulus geometry first |
| Are curves sampled at different times? | native irregular trajectories | do not force a grid during import |
| How does distance from a target evolve? | derived univariate function + FPCA | landmark definition must be meaningful |
| How does a planar path bend or turn over time? | heading / signed curvature / turning rate | use commensurate x/y units; declare low-speed handling and axis orientation |
| Are stable participant strategies different from trial fluctuations? | multilevel FPCA | preserve participant → trial nesting |
| How does allocation among AOIs evolve? | compositional FPCA | probabilities must remain on the simplex |
| Do people traverse similar paths at different times? | registration + phase FPCA | do not erase meaningful latency |
| Do I need a bottleneck measure of ordered path separation without elapsed-time matching? | discrete Fréchet | declare dimensions/units; one local excursion can dominate |
| Do I need cumulative elastic matching of ordered path samples? | dynamic time warping | pre-specify symmetric1 vs symmetric2, normalization, and sample-index window; DTW can align away meaningful latency |
| Are multiple trajectory-distance contracts scientifically defensible and I need to know whether conclusions depend on the choice? | trajectory-distance sensitivity | predeclare the specification set and neighbor k; descriptive robustness only, no automatic winner |
| Do I need uncertainty for the mean trajectory? | simultaneous multiplier mean band | choose the independent inference unit before calibration |
| How does an experimental condition or scalar predictor change a continuous gaze metric over time? | function-on-scalar regression | declare design coding and inference unit; repeated trials are participant-aggregated only when predictors are constant within participant |
| How does a trial-varying predictor change a functional response when curves repeat within participant? | functional mixed-effects regression | fit all curve-by-time observations jointly; declare spline bases and residual covariance boundary |
| Do fixed-effect conclusions depend on several defensible repeated-measures covariance structures? | mixed-effects covariance sensitivity | predeclare and fit each structure independently, choose an explicit reference, require strict comparability, and do not rank or auto-select a winner |
| Do participants differ in the time-varying effect of one within-participant predictor? | one guarded participant random functional slope | predeclare the predictor; require within-participant variation; audit covariance dimension, eigenvalues, condition number and BLUP slopes |
| Do I need a whole-function confidence statement for a repeated-trial mixed-effects coefficient? | participant-cluster simultaneous mixed-effects band | resample whole participants; predeclare coefficient/family scope; covariance parameters and bases remain fixed; observed-grid claim only |
| How many FPCs should be retained for reconstruction? | held-out reconstruction CV | refit FPCA inside folds; group repeated participants |
| How many FPCs should predict an external scalar outcome? | predictive FPCA regression CV / nested CV | fit FPCA and regression inside folds; keep outer test data out of selection |
| Is component interpretation stable? | bootstrap FPC matching + pointwise envelopes | resample the correct unit; match and sign-align components |
| How uncertain are the eigenvalues/variance-explained summaries? | matched bootstrap spectrum uncertainty | report scaling, bootstrap unit, calibration scope, and cumulative-rank semantics |
| How sensitive are fixed-curve FPC scores to re-estimating the basis? | matched/sign-aligned basis bootstrap | keep targets fixed; do not call this full latent-score uncertainty |
| How uncertain is a Gaussian scalar-on-function slope after FPCA is re-estimated? | paired full-pipeline FPCR bootstrap | resample predictor/outcome pairs at the independent-unit level; keep component count fixed |
| Do I need one band across the sampled Gaussian FPCR slope grid? | studentized max calibration of paired-bootstrap slopes | choose global versus per-dimension scope explicitly; observed-grid claim only |
| Do I need an interval for a future observed scalar response, not only its conditional mean? | paired-bootstrap target means + centered empirical residual draw | Gaussian FPCR only; common/exchangeable residual distribution assumed |
| May Gaussian FPCR response variance be heteroscedastic and I need target projection inference? | fixed-regressor studentized wild bootstrap | independent curve rows; explicit k=g and h>=g truncations; not future-outcome prediction |
| How should I choose h for fixed-regressor wild-bootstrap target inference? | stabilized-volatility scan of interval width + center | consecutive h grid, shared multiplier draws, explicit outcome-scale thresholds and r |
| Do I need a whole-curve uncertainty statement for an individual FPC? | matched bootstrap simultaneous FPC band | choose component-wise vs familywise scope; inspect eigengaps/subspaces |
| Do adjacent FPCs rotate or swap? | eigengap + principal-angle subspace stability | interpret the span when axes are weakly identified |
| Is one curve/participant unusually influential? | FPCA review + leave-one-group-out influence | flag for review, never auto-exclude |
| Does a finite basis help? | B-spline/Fourier projection | basis family and size constrain shape |
| Does a trajectory predict a scalar response? | score-based functional regression | refit FPCA inside training folds for prediction |

## If the sample times are irregular

Start with <code>from_irregular_long_dataframe_native()</code>. Audit the native sampling, then decide whether the common domain should be the overlap or union of observed time support.

Do not let file import silently decide the analysis grid.

## If timing is part of the theory

Fit the unregistered representation first. Registration can then be used as a sensitivity/phase decomposition, not as an automatic cleaning operation.

## If the FPCs will receive substantive labels

Add both:

1. reconstruction diagnostics; and
2. bootstrap component stability.

A visually appealing FPC is not automatically a reproducible viewing strategy.

## Before fitting anything

1. Verify coordinate geometry is comparable.
2. Decide whether absolute latency is part of the construct.
3. Preserve irregular sampling until the common-grid rule is explicit.
4. Resolve missingness and maximum interpolation gap.
5. Decide whether smoothing or basis projection is defensible.
6. Decide whether channels retain native scales or are equalized.
7. Pre-specify component retention and interpretation.
8. Pre-specify the bootstrap resampling unit if stability will be assessed.
9. If functional anomaly/influence review is planned, pre-specify review thresholds and the independent rule that could justify exclusion.
10. If registration is used, pre-specify how phase information will be retained.

Use the [pre-registration checklist](../methods/preregistration.md) for a manuscript-ready version.

## If recurrence itself should become a graph

| Question | Use | Key caution |
|---|---|---|
| Which recurrent states have many recurrence neighbors? | recurrence-network degree | threshold and Theiler policy define the edges |
| How locally interconnected are recurrence neighborhoods? | clustering / transitivity | do not infer chaos/dimension automatically |
| Is the recurrence graph fragmented? | component summaries | graph density and connectivity are threshold-dependent |

## If you have multiple synchronized dynamical systems

| Question | Use | Key caution |
|---|---|---|
| Are states from two systems similar to each other? | cross-recurrence | requires compatible state variables/dimensions and cross-system distance semantics |
| Do multiple systems recur within their own state spaces at the same time pairs? | joint recurrence | exact common grid/time unit and shared Theiler; does not imply direction or causality |

## When the question is dynamical rather than variance-based

Use the 0.23 nonlinear path when the scientific target is recurrence, state-space divergence, or repeated-cycle stability rather than dominant between-curve variation.

```text
continuous trajectory
    |
    +-- nearby state returns? --------> recurrence / RQA
    |
    +-- changing recurrence in time? -> windowed RQA
    |
    +-- compare two trajectories? ----> cross recurrence
    |
    +-- local state divergence? ------> explicit delay embedding
    |                                  -> Rosenstein divergence / LLE
    |                                  -> IAAFT surrogate test
    |                                  -> multivariate IAAFT when joint channels matter
    |
    +-- repeated approximate cycles? -> explicit Poincare section
                                       -> empirical local return map
                                       -> experimental contraction / expansion
```

Do not route raw gaze directly to classical Floquet or bifurcation-continuation claims. Those require a separately identified dynamical model.

## Do you need directed predictive information between two discrete state series?

Use `discrete_transfer_entropy()` only after the source and target states,
target/source history lengths, and source lag are scientifically defined.
Use `transfer_entropy_circular_shift_test()` only when the declared circular
source shifts are a defensible null. If your inputs are continuous gaze
coordinates or pupil signals and the state construction is not already
specified, stop there rather than letting the package invent bins.

If the question is synchronized recurrence rather than predictive direction,
use joint recurrence; if it is all-pairs cross-system state similarity, use
cross recurrence. These estimands are not interchangeable.

## Do you need robustness across several defensible TE histories or lags?

Use `transfer_entropy_parameter_sensitivity()` when more than one target
history, source history, or source lag is scientifically defensible. Supply the
complete grid and inspect every row together with finite-support diagnostics.

Do not use the sensitivity function merely to search for the largest TE or the
smallest p-value. If one specification is primary, keep it primary and use the
multiverse to describe robustness around that decision.

## Do you have a scientifically specified process that may explain pairwise TE?

Use `conditional_transfer_entropy()` when the scientific question is whether
source history contributes predictive information about the target beyond both
the target's own past and one explicitly supplied conditioning process.

Do not add conditioning processes post hoc merely because they reduce or
increase TE. Conditioning is not automatic causal identification and does not
guarantee that unmeasured common drivers have been controlled.
