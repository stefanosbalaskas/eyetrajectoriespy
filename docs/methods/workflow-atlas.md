---
title: Workflow atlas
---

# Workflow atlas

These diagrams show **decision order**, not an automatic pipeline. eyetrajectoriespy keeps preprocessing, representation, inference unit, resampling design, and inferential scope explicit.

## Representation first

\`\`\`mermaid
flowchart LR
    A[Raw time-indexed gaze] --> B{Sampling structure}
    B -->|Common dense grid| C[TrajectorySet]
    B -->|Irregular but projectable| D[IrregularTrajectorySet]
    B -->|Genuinely sparse| E[Sparse PACE path]
    C --> F{Scientific object}
    D --> G[Explicit common-grid projection]
    G --> F
    F -->|Planar x/y| H[MFPCA]
    F -->|One function| I[FPCA]
    F -->|Repeated trials| J[Multilevel FPCA]
    F -->|AOI probabilities| K[ALR + compositional FPCA]
    F -->|Timing deformation| L[Registration + phase]
\`\`\`

## FPCA validation before interpretation

\`\`\`mermaid
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
\`\`\`

## Gaussian FPCR inference branches

\`\`\`mermaid
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
\`\`\`

## Function → equation → figure

\`\`\`mermaid
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
\`\`\`

## Use the atlas with the contracts

- [Function → equation index](../reference/function-equation-index.md) gives the concise LaTeX contract for each registered function.
- [Mathematical reference](mathematical-reference.md) expands the equations and boundaries.
- [Visual gallery](visual-gallery.md) shows representative public plotting outputs.
- [Tutorial gallery](../tutorials/index.md) provides runnable scientific workflows.
- [Assumptions](assumptions.md) and [limitations](limitations.md) define where each workflow stops.
