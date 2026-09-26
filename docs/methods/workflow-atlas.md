---
title: Workflow atlas
---

# Workflow atlas

These diagrams show **decision order**, not an automatic pipeline. eyetrajectoriespy keeps preprocessing, representation, inference unit, resampling design, and inferential scope explicit.

## Representation first

```mermaid
flowchart LR
    A[Raw time-indexed gaze] --> B{Sampling structure}
    B -->|Common dense grid| C[TrajectorySet]
    B -->|Irregular but projectable| D[IrregularTrajectorySet]
    B -->|Genuinely sparse| E[Sparse PACE path]
    C --> F{Scientific object}
    D --> G[Explicit common-grid projection]
    G --> F
    F -->|Planar x/y| H[MFPCA]
    F -->|Planar geometry| M[Heading / curvature / turning rate]
    F -->|Ordered path similarity| N[Fréchet / DTW]
    F -->|One function| I[FPCA]
    F -->|Repeated trials| J[Multilevel FPCA]
    F -->|AOI probabilities| K[ALR + compositional FPCA]
    F -->|Timing deformation| L[Registration + phase]
```

## Repeated-measures functional regression

```mermaid
flowchart TD
    A[Common-grid functional response Y_ij(t)] --> B[Curve-level scalar design X_ij]
    A --> C[Participant grouping]
    B --> D{Keep repeated trials?}
    D -->|No + participant-level estimand| E[0.35 participant aggregation]
    D -->|Yes| F[Functional mixed-effects regression]
    C --> F
    F --> G[Declare fixed + participant random B-spline bases]
    F --> R{Trial functional intercept?}
    R -->|Yes| T[Validate trial IDs + declare trial basis/Psi_T]
    R -->|No| U[No trial random function]
    T --> V{Residual family?}
    U --> V
    V -->|iid + no trial effect| I[Historical stacked Gaussian MixedLM]
    V -->|iid + trial effect| P[Profiled Gaussian covariance likelihood]
    V -->|exponential| P
    V -->|AR1 on regular grid| P
    P --> S{Participant random slope?}
    I --> S
    S -->|Yes| W[Variation + covariance-complexity guard]
    S -->|No| J[Fixed coefficient functions beta(t)]
    W --> J
    J --> M[Retain Psi_P / Psi_T / serial parameter diagnostics]
    M --> N[Raw residual ACF + variogram]
    M --> X[Whitened residual ACF + variogram for serial fits]
    J --> O{Whole-function inference?}
    O -->|Yes| Q[Resample whole participants]
    Q --> Z[Fixed covariance or full declared-model refit]
    Z --> Y{Predeclared covariance alternatives?}
    Y -->|Yes| ZA[0.50 compare already fitted structures to declared reference]
    ZA --> ZB[Coefficient / band / variance / raw+white residual / IC sensitivity]
    ZB --> ZC[Report robustness; no ranking or winner]
```

Participant-only iid fits preserve `statsmodels.MixedLM`. Nested and/or serial
models use the profiled Gaussian backend. Exponential residual correlation uses
physical elapsed time; signed AR(1) uses index steps and requires an equally
spaced grid. Residual covariance never crosses trial boundaries.

Whole participants remain the bootstrap resampling unit. The fixed-covariance
bootstrap conditions on all declared covariance terms; the full-refit bootstrap
re-estimates them, including phi/rho, while keeping the covariance family fixed.

Version 0.50 compares already fitted, predeclared structures only after strict
comparability checks; failed declarations remain visible and no structure is
ranked or automatically selected.


## Functional response regression

```mermaid
flowchart TD
    A[Common-grid functional response Y_ij(t)] --> B{Response family}
    B -->|Continuous Gaussian| C{Repeated trials?}
    C -->|No independent curves| D[0.35 observed-grid FoSR OLS]
    C -->|Yes participant-level predictors only| E[Participant-average response]
    C -->|Yes trial-varying predictors| F[Gaussian functional mixed effects]
    B -->|Bernoulli 0/1| G[Marginal generalized FoSR: logit]
    B -->|Poisson counts| H[Marginal generalized FoSR: log]
    H --> U{Explicit exposure?}
    U -->|No: expected count| I[Participant is independent GEE cluster]
    U -->|Yes: E > 0| V[0.53 log-rate estimand]
    V --> I
    G --> I
    I --> J[Working independence]
    J --> K[Robust sandwich coefficient covariance]
    K --> L{Whole-function inference?}
    L -->|Yes| M[Resample complete participants]
    M --> N[Refit same family/link/basis GEE]
    N --> O[Observed-grid link-scale simultaneous band]
    O --> P{Fixed marginal profiles declared?}
    P -->|Yes| Q[0.52/0.53 fixed-profile probability, rate, or count]
    Q --> R[Reuse identical participant-bootstrap coefficient draws]
    R --> S[Profile/family simultaneous response bands]
    R --> T[One predeclared probability/rate/count contrast]
```

Version 0.51 targets population-averaged marginal coefficient functions.
Trial-varying scalar predictors remain in the generalized design; trials and
time rows are not treated as independent clusters. Working independence is
fixed rather than selected, and bootstrap failures are not silently dropped or
redrawn.

Version 0.52 adds fixed-profile marginal interpretation without a second
resampling scheme. Version 0.53 adds explicit strictly-positive Poisson
exposure: the fitted coefficient predictor is a log rate, exposure travels with
the participant bootstrap bundle, rate prediction is exposure-independent, and
expected-count prediction requires explicit target exposure. Profile values and
target exposures remain fixed; the result is marginal rate/mean-function
inference rather than future-response prediction.

## Ordered trajectory similarity

```mermaid
flowchart TD
    A[Complete ordered trajectory points] --> B{What difference matters?}
    B -->|Worst coupled spatial excursion| C[Discrete Fréchet]
    B -->|Cumulative mismatch after elastic index alignment| D[DTW]
    D --> E{Step pattern}
    E -->|symmetric1| F[Raw cumulative cost]
    E -->|symmetric2| G{Normalize by N+M?}
    F --> H{Constrain warping?}
    G --> H
    H -->|No| I[Unconstrained monotone DTW]
    H -->|Yes| J[Declare Sakoe-Chiba sample-index radius]
    C --> K[Audit deterministic coupling]
    I --> L[Audit deterministic path]
    J --> L
    K --> M{Is elapsed timing part of the estimand?}
    L --> M
    M -->|Yes| N[Add time-preserving functional comparison]
    M -->|No / nuisance timing| O[Interpret elastic similarity]
```

Fréchet and DTW use sequence order, not the numeric TrajectorySet time grid. Fréchet reports a bottleneck maximum. DTW requires an explicit step pattern: symmetric1 preserves the raw cumulative 0.33 contract, while symmetric2 supports the defined N+M normalization. Neither contract silently resamples, smooths, chooses a step pattern, normalizes, or chooses a warping window.

If multiple distance contracts remain defensible, continue to:

```mermaid
flowchart LR
    A[Declared L2 / Fréchet / DTW specifications] --> B[Retain native-scale pairwise matrices]
    B --> C[Compare pair-distance ranks]
    B --> D[Compare top-k neighbor sets]
    C --> E[Spearman agreement + rank differences]
    D --> F[Jaccard + exact-set + nearest-neighbor agreement]
    E --> G[Interpret sensitivity; no automatic winner]
    F --> G
```


## FPCA validation before interpretation

```mermaid
flowchart LR
    A[Choose representation] --> B[Fit FPCA / MFPCA]
    B --> C[Reconstruction]
    B --> D[Explained variance]
    B --> E[Bootstrap stability]
    B --> F[Eigengap / subspace diagnostics]
    C --> G{Retained dimension justified?}
    D --> G
    E --> H{Axes stable enough to interpret?}
    F --> H
    G --> I[Downstream model]
    H --> I
```

## Gaussian FPCR inference branches

```mermaid
flowchart TD
    A[FPCA scores + scalar outcome] --> B{Scientific target}
    B -->|Sampling uncertainty in fitted FPCR| C[Paired full-pipeline bootstrap]
    B -->|Heteroscedastic fixed-target projection| D[Fixed-regressor wild bootstrap]
    C --> E[Conditional mean uncertainty]
    C --> F[Observed-grid slope band]
    C --> G[Future-outcome interval]
    D --> H[Target-wise interval]
    D --> I[Fixed-family max-|t| interval]
    D --> J[Fixed-family tests]
    J --> K[Monte Carlo precision audit]
```

## Recurrence-network topology

```mermaid
flowchart LR
    A[Declared auto-recurrence matrix] --> B[Validate symmetric sparse adjacency]
    B --> C[Degree / normalized degree]
    B --> D[Triangles / local clustering]
    B --> E[Transitivity]
    B --> F[Connected components]
    C --> G[Interpret conditional on recurrence contract]
    D --> G
    E --> G
    F --> G
```

The graph does not retune the recurrence radius, restore Theiler-excluded
edges, optimize communities, or infer dynamical dimension automatically.

## Joint recurrence across synchronized systems

```mermaid
flowchart LR
    A[Synchronized subsystem trajectories] --> B[Define state space A]
    A --> C[Define state space B]
    B --> D[Auto recurrence A]
    C --> E[Auto recurrence B]
    D --> F{Exact same grid and shared Theiler?}
    E --> F
    F -->|No| G[Stop: align upstream explicitly]
    F -->|Yes| H[Logical intersection]
    H --> I[Joint recurrence rate]
    H --> J[JRQA line metrics]
    I --> K[Interpret coincident recurrence]
    J --> K
```

Joint recurrence does not perform lag search, resampling, synchronization
repair, or threshold harmonization.

## Nonlinear trajectory dynamics

```mermaid
flowchart TD
    A[Scientifically interpretable common-grid trajectory] --> B{Question}
    B -->|Reconstructed state geometry| C[Declare dimensions m and tau]
    C --> D[Delay embedding]
    B -->|Recurrent structure| E[Declare observed/reconstructed state]
    E --> F[Radius policy + metric + Theiler window]
    F --> G[Sparse recurrence]
    G --> H[RQA]
    G --> I[Windowed or cross-RQA]
    I --> V{Between-curve functional question?}
    V -->|Yes| W[Promote selected windowed RQA metrics]
    W --> X[Record overlap, edge support, tail, radius policy]
    X --> Y[TrajectorySet of RQA functions]
    Y --> Z[FPCA / MFPCA / regression with source-unit inference]
    B -->|Local divergence| J[Delay embedding]
    J --> K[Nearest neighbors outside Theiler window]
    K --> L[Local divergence curve]
    L --> M[Declare fit interval]
    M --> N[Rosenstein LLE]
    N --> O{Surrogate null}
    O -->|One signal dimension| P[Scalar IAAFT]
    O -->|Joint planar or multichannel structure| Q[Declare MIAAFT reference dimension]
    Q --> R[Multivariate IAAFT + cross-spectrum diagnostics]
    B -->|Repeated approximate cycle| P[Declare Poincare section]
    P --> Q[Interpolated crossings]
    Q --> R[Declare reference + neighborhood]
    R --> S[Empirical local return map]
    S --> T[Spectral radius]
    T --> U[Experimental contraction / expansion]
```

!!! warning
    The return-map branch is empirical. It does not produce a classical monodromy matrix or Floquet multipliers. Numerical continuation likewise requires a separately identified dynamical model.

## Function → equation → figure

```mermaid
flowchart LR
    A[Public function] --> B[MathematicalContract registry]
    B --> C[FUNCTION_EQUATION_INDEX.md]
    B --> D[Website function-equation index]
    B --> E[Expanded mathematical reference]
    A --> F[Executable synthetic example]
    A --> G[Plot helper]
    G --> H[Deterministic SVG gallery]
    C --> I[CI drift check]
    D --> I
    E --> I
    H --> I
```

## Use the atlas with the contracts

- [Function → equation index](../reference/function-equation-index.md) gives the concise LaTeX contract for each registered function.
- [Mathematical reference](mathematical-reference.md) expands the equations and boundaries.
- [Visual gallery](visual-gallery.md) shows representative public plotting outputs.
- [Tutorial gallery](../tutorials/index.md) provides runnable scientific workflows.
- [Assumptions](assumptions.md) and [limitations](limitations.md) define where each workflow stops.

## Directed discrete-state dependence

```text
explicit discrete source/target states
        |
        +--> declare k, l, source lag d
        |       |
        |       +--> discrete_transfer_entropy()
        |               |
        |               +--> mean TE in bits
        |               +--> local TE/history frame
        |               +--> empirical support diagnostics
        |
        +--> declare defensible circular source shifts
                |
                +--> transfer_entropy_circular_shift_test()
                        |
                        +--> surrogate distribution / centered TE
                        +--> plus-one upper-tail p-value
```

No branch in this workflow automatically bins continuous measurements, chooses
history/lag settings, generates shifts, or promotes directed prediction to
causal identification.

## Transfer-entropy robustness multiverse

```text
explicit discrete state series
        |
        +--> declare K: target histories
        +--> declare L: source histories
        +--> declare D: source lags
                    |
                    v
        full Cartesian K × L × D
                    |
                    v
 transfer_entropy_parameter_sensitivity()
        |           |             |
        |           |             +--> support diagnostics
        |           +--> optional common circular-shift null
        +--> complete TE table
                    |
                    v
         explicit one-parameter slices
         no hidden averaging / no winner
```

## Conditional transfer entropy

```text
X: explicit discrete source
Y: explicit discrete target
Z: explicit discrete conditioning process
        |
        +--> k, l, m histories
        +--> d, c lags
                    |
                    v
 conditional_transfer_entropy()
        |           |
        |           +--> local contributions
        |           +--> effective indices
        |           +--> exact histories
        |           +--> empirical support diagnostics
        |
        +--> optional source-only circular shifts
                    |
                    v
 conditional_transfer_entropy_circular_shift_test()
        target and condition remain fixed
                    |
                    v
 incremental predictive information
 not proof of causal influence
```
