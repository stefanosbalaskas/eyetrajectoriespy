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

## Ordered trajectory similarity

```mermaid
flowchart TD
    A[Complete ordered trajectory points] --> B{What difference matters?}
    B -->|Worst coupled spatial excursion| C[Discrete Fréchet]
    B -->|Cumulative mismatch after elastic index alignment| D[DTW]
    D --> E{Constrain warping?}
    E -->|No| F[Unconstrained monotone DTW]
    E -->|Yes| G[Declare Sakoe-Chiba sample-index radius]
    C --> H[Audit deterministic coupling]
    F --> I[Audit deterministic path]
    G --> I
    H --> J{Is elapsed timing part of the estimand?}
    I --> J
    J -->|Yes| K[Add time-preserving functional comparison]
    J -->|No / nuisance timing| L[Interpret elastic similarity]
```

Fréchet and DTW use sequence order, not the numeric TrajectorySet time grid. Fréchet reports a bottleneck maximum; DTW reports an unnormalized cumulative path cost. Neither contract silently resamples, smooths, normalizes, or chooses a warping rule.

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
    N --> O[IAAFT surrogate test]
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
