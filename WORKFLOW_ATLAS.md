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
