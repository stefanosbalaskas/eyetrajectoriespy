# Analysis decision map

Use the **research question and data structure** to choose the representation.

| Question | Representation / method | Key safeguard |
|---|---|---|
| Where does gaze move over trial time? | joint 2-D MFPCA | harmonize stimulus geometry first |
| Are curves sampled at different times? | native irregular trajectories | do not force a grid during import |
| How does distance from a target evolve? | derived univariate function + FPCA | landmark definition must be meaningful |
| Are stable participant strategies different from trial fluctuations? | multilevel FPCA | preserve participant → trial nesting |
| How does allocation among AOIs evolve? | compositional FPCA | probabilities must remain on the simplex |
| Do people traverse similar paths at different times? | registration + phase FPCA | do not erase meaningful latency |
| Do I need uncertainty for the mean trajectory? | simultaneous multiplier mean band | choose the independent inference unit before calibration |
| How many FPCs should be retained for reconstruction? | held-out reconstruction CV | refit FPCA inside folds; group repeated participants |
| How many FPCs should predict an external scalar outcome? | predictive FPCA regression CV / nested CV | fit FPCA and regression inside folds; keep outer test data out of selection |
| Is component interpretation stable? | bootstrap FPC matching + pointwise envelopes | resample the correct unit; match and sign-align components |
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
