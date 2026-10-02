# Analysis decision map

Use the **research question and data structure** to choose the representation before choosing a function name.

## Representation first

| Question / data structure | Representation / method | Key safeguard |
|---|---|---|
| Joint x/y trajectories already represented on a defensible common grid | `fit_mfpca()` | harmonize stimulus geometry first |
| Sparse/irregular **paired x/y** samples with the same retained timestamps per curve | `fit_sparse_mfpca()` | verify paired timestamps; retain native samples; declare smoothing/noise/PSD policy |
| Sparse/irregular single functional coordinate | `fit_sparse_fpca()` | retain native samples; do not manufacture dense trajectories |
| Dense curves sampled at somewhat different times | native irregular trajectories → explicit projection if defensible | do not force a grid during import |
| Distance from a target evolves over time | derived univariate function + FPCA | landmark definition must be meaningful |
| Planar path bends or turns over time | heading / signed curvature / turning rate | use commensurate x/y units; declare low-speed handling and axis orientation |
| Stable participant strategies differ from trial fluctuations | multilevel FPCA | preserve participant → trial nesting |
| Allocation among AOIs evolves | compositional FPCA | probabilities must remain on the simplex |
| Similar paths occur at different times | registration + phase FPCA | do not erase meaningful latency |

## If sample times are irregular

**Are x and y jointly observed at the same retained timestamps?**

- **Yes, and joint planar covariance is the target:** use `fit_sparse_mfpca()`.
- **No:** do not silently align unmatched channels into the joint estimator.
- **Only one coordinate is the target:** use `fit_sparse_fpca()`.
- **The curves are densely observed and projection is scientifically defensible:** retain native data first, then explicitly choose common support/grid/gap rules.

Start ingestion with `from_irregular_long_dataframe_native()` when the raw observation process is irregular. File import should not decide the analysis grid.

## Functional variation, uncertainty and selection

| Scientific question | Use | Key caution |
|---|---|---|
| Dominant modes of common-grid variation | FPCA / MFPCA | declare channel scaling and retained components |
| How many FPCs are needed for reconstruction? | held-out reconstruction CV | refit FPCA inside folds; group repeated participants |
| How many FPCs predict an external outcome? | predictive FPCA regression CV / nested CV | keep outer test data out of selection |
| Is component interpretation stable? | bootstrap FPC matching / bands | resample the correct unit; inspect eigengaps |
| Are adjacent FPCs weakly identified? | eigengap + principal-angle subspace stability | interpret the span when axes rotate/swap |
| Eigenvalue / variance-explained uncertainty | spectrum bootstrap | declare resampling unit and calibration scope |
| Fixed-target score sensitivity to basis re-estimation | score uncertainty bootstrap | not full latent-score uncertainty |
| One curve/participant unusually influential? | outlier/influence review | review flag is not automatic exclusion |
| New trajectory anomalous relative to calibration data? | split-conformal FPCA anomaly review | finite calibration limits attainable p-values |
| Mean trajectory uncertainty | simultaneous multiplier mean band | choose independent inference unit first |

## Functional regression and repeated measures

| Scientific question | Use | Key caution |
|---|---|---|
| Scalar predictor changes a continuous functional response | function-on-scalar regression | declare design coding and inference unit |
| Trial-varying predictor with repeated curves per participant | functional mixed-effects regression | preserve participant → trial → time hierarchy |
| Whole-function mixed-effects coefficient statement | participant-cluster simultaneous band | resample whole participants; observed-grid claim |
| Participant-specific time-varying effect of one predictor | guarded random functional slope | require within-participant predictor variation |
| Trial-level functional random effect | trial functional random effect | declare trial IDs and complexity guard |
| Residual serial dependence | explicit residual covariance + whitening | diagnose on the appropriate residual scale |
| Conclusions depend on defensible covariance structures? | covariance-structure sensitivity | no automatic ranking or model winner |
| Repeated binary/count functional response | marginal generalized FoSR GEE | participant cluster; declare family/link/denominator/exposure |
| Fixed-profile marginal probability/rate/count function | generalized FoSR prediction | fixed declared profiles; not future-response prediction |

## FPCA regression inference

| Scientific question | Use | Key caution |
|---|---|---|
| Gaussian scalar-on-function slope uncertainty after FPCA re-estimation | paired full-pipeline FPCR bootstrap | resample predictor/outcome pairs by independent unit |
| Simultaneous slope band over sampled grid | studentized max calibration | declare global vs per-dimension scope |
| Future observed scalar outcome interval | target means + centered empirical residual draw | Gaussian FPCR only |
| Heteroscedastic fixed-target projection inference | fixed-regressor wild bootstrap | explicit g/h truncations; not future prediction |
| Sensitivity to inference truncation h | stabilized-volatility scan | descriptive declared scan, not hidden tuning |

## Trajectory comparison and geometry

| Scientific question | Use | Key caution |
|---|---|---|
| Integrated time-aligned functional separation | functional L2 distance | common support/units required |
| Ordered path separation without elapsed-time matching | discrete Fréchet | one local excursion can dominate |
| Elastic matching of ordered path samples | DTW | can align away meaningful latency; declare step pattern/window/normalization |
| Robustness across defensible distance contracts | trajectory-distance sensitivity | descriptive robustness only; no automatic winner |
| Registration sensitivity | registered vs unregistered comparison | preserve phase information and interpretation |

## Recurrence, nonlinear dynamics and information flow

Use nonlinear methods when recurrence, state-space divergence, repeated-cycle stability, or directed predictive information is the scientific target rather than dominant between-curve variance.

```text
continuous trajectory
    |
    +-- nearby state returns? --------> recurrence / RQA
    +-- changing recurrence in time? -> windowed RQA
    +-- compare two trajectories? ---> cross recurrence
    +-- synchronized recurrence? ----> joint recurrence
    +-- local state divergence? -----> explicit delay embedding
    |                                 -> Rosenstein / Kantz LLE
    |                                 -> surrogate nonlinearity tests
    +-- repeated approximate cycles? -> Poincare section / local return map
```

| Scientific question | Use | Key caution |
|---|---|---|
| Recurrence graph topology | recurrence network | threshold/Theiler policy defines edges |
| Population RQA mean uncertainty | participant/curve bootstrap | preserve inference unit |
| RQA parameter robustness | RQA sensitivity | do not choose parameters by best-looking result |
| Rosenstein/Kantz LLE robustness | Lyapunov sensitivity | descriptive multiverse; no chaos-probability claim |
| Nonlinearity against matched surrogates | IAAFT surrogate tests | surrogate null and statistic must be declared |
| Directed predictive information in discrete states | transfer entropy | state construction/histories/lags must be scientifically defined |
| TE robustness | transfer-entropy sensitivity | do not search for minimum p-value |
| Source information beyond a declared conditioning process | conditional TE | not automatic causal identification |

Do not route raw gaze directly to classical Floquet or bifurcation-continuation claims without a separately identified dynamical model.

## If timing is part of the theory

Fit the unregistered/time-preserving representation first. Registration can then be used as sensitivity or phase decomposition, not automatic cleaning.

## If FPCs will receive substantive labels

At minimum add:

1. reconstruction diagnostics;
2. bootstrap component stability; and
3. eigengap/subspace diagnostics when adjacent components are near-tied.

A visually appealing FPC is not automatically a reproducible viewing strategy.

## Before fitting anything

1. Verify coordinate geometry is comparable.
2. Decide whether absolute latency is part of the construct.
3. Preserve irregular sampling until the common-grid or sparse-estimator rule is explicit.
4. Resolve missingness and maximum interpolation gap where projection is used.
5. Decide whether smoothing or basis projection is defensible.
6. Decide whether channels retain native scales or are equalized.
7. For sparse planar analysis, verify paired x/y retained timestamps and declare measurement-error structure.
8. Pre-specify component retention and interpretation.
9. Pre-specify the resampling unit for uncertainty/stability.
10. Pre-specify anomaly/influence review rules separately from any exclusion criterion.
11. If registration is used, pre-specify how phase information will be retained.

Use the [pre-registration checklist](../methods/preregistration.md) for a manuscript-ready version.
