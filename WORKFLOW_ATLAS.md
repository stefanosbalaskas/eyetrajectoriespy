# Workflow atlas

GitHub renders these Mermaid diagrams directly in the repository. The website contains the expanded atlas with links to the function-equation registry, worked examples, and visual gallery.

## Representation

\`\`\`mermaid
flowchart LR
    A[Time-indexed gaze] --> B{Sampling}
    B -->|Common grid| C[TrajectorySet]
    B -->|Irregular| D[IrregularTrajectorySet]
    B -->|Sparse| E[PACE pathway]
    C --> F{Scientific object}
    D --> G[Explicit projection]
    G --> F
    F --> H[FPCA / MFPCA]
    F --> L[Heading / curvature / turning rate]
    F --> I[Multilevel]
    F --> J[Compositional]
    F --> K[Registration / phase]
\`\`\`

## Inference

\`\`\`mermaid
flowchart LR
    A[FPCA representation] --> B{Target}
    B --> C[Mean band]
    B --> D[Paired FPCR bootstrap]
    B --> E[Heteroscedastic wild bootstrap]
    E --> F[Simultaneous fixed targets]
    E --> G[Fixed-family tests]
    G --> H[Monte Carlo precision]
\`\`\`

## Nonlinear dynamics

\`\`\`mermaid
flowchart LR
    A[Continuous trajectory] --> B[Explicit state definition]
    B --> C[Delay embedding diagnostics]
    B --> D[Sparse recurrence / RQA]
    D --> K[Windowed RQA]
    K --> L[RQA functional trajectories]
    L --> M[FPCA / MFPCA / regression]
    C --> E[Local divergence]
    E --> F[Rosenstein LLE]
    F --> G[IAAFT surrogate test]
    B --> H[Declared Poincare section]
    H --> I[Empirical local return map]
    I --> J[Experimental spectral-radius stability]
\`\`\`

Overlapping RQA windows remain within-curve dependent summaries; the source curve/participant remains the downstream sampling unit. Classical Floquet/monodromy and continuation analysis are intentionally excluded from the raw-gaze pathway.

## Documentation contract

\`\`\`mermaid
flowchart LR
    A[Public function] --> B[MathematicalContract registry]
    B --> C[Repository LaTeX index]
    B --> D[Website LaTeX index]
    A --> E[Examples]
    A --> F[Plots]
    F --> G[SVG gallery]
    C --> H[CI validation]
    D --> H
    E --> H
    G --> H
\`\`\`

Website: https://stefanosbalaskas.github.io/eyetrajectoriespy/methods/workflow-atlas/
