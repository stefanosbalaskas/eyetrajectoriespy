# Workflow atlas

GitHub renders these Mermaid diagrams directly in the repository. The website contains the expanded atlas with links to the function-equation registry, worked examples, and visual gallery.

## Representation

```mermaid
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
    F --> M[Ordered trajectory similarity]
    M --> N[Discrete Fréchet bottleneck]
    M --> O[DTW cumulative alignment]
    F --> I[Multilevel]
    F --> J[Compositional]
    F --> K[Registration / phase]
```

## Repeated-measures functional regression

```mermaid
flowchart LR
    A[Repeated Y_ij(t)] --> B[Trial-level scalar design]
    A --> C[Participant groups]
    B --> D[Declared B-spline fixed effects]
    C --> E[Declared participant functional random intercept]
    D --> F[One joint Gaussian MixedLM]
    E --> F
    F --> G[beta(t) + participant random functions]
```

## Functional response regression

```mermaid
flowchart LR
    A[Functional response Y(t)] --> B{Inference unit}
    B -->|Independent curves| C[Curve-level design]
    B -->|Repeated trials + participant-level predictors| D[Participant-average response]
    D --> E{Predictors constant within participant?}
    E -->|No| F[Defer to functional mixed effects]
    E -->|Yes| G[Participant-level design]
    C --> H[Observed-grid function-on-scalar OLS]
    G --> H
    H --> I[HC1 pointwise SE]
    H --> J[Whole-function wild bootstrap]
    J --> K[Coefficient/family simultaneous bands]
```

## Trajectory-distance robustness

```mermaid
flowchart LR
    A[Same complete trajectories] --> B[Declared L2]
    A --> C[Declared Fréchet]
    A --> D[Declared DTW specification]
    B --> E[Native-scale distance matrices]
    C --> E
    D --> E
    E --> F[Pair-rank agreement]
    E --> G[Top-k neighbor agreement]
    F --> H[Robustness interpretation]
    G --> H
```

No consensus metric, p-value, or preferred distance is constructed automatically.

## Ordered trajectory comparison

```mermaid
flowchart LR
    A[Ordered trajectory points] --> B{Scientific target}
    B -->|Worst coupled separation| C[Discrete Fréchet]
    B -->|Cumulative elastic mismatch| D[DTW]
    D --> E{Step pattern}
    E -->|symmetric1| F[Raw cumulative cost]
    E -->|symmetric2| G[N+M normalization available]
    F --> H{Warp constraint}
    G --> H
    H -->|Unconstrained| I[Full monotone path]
    H -->|Declared index radius| J[Sakoe-Chiba band]
    C --> K[No elapsed-time correspondence]
    I --> K
    J --> K
    K --> L{Latency scientifically meaningful?}
    L -->|Yes| M[Add time-preserving analysis]
    L -->|No / nuisance timing| N[Interpret elastic similarity]
```

## Inference

```mermaid
flowchart LR
    A[FPCA representation] --> B{Target}
    B --> C[Mean band]
    B --> D[Paired FPCR bootstrap]
    B --> E[Heteroscedastic wild bootstrap]
    E --> F[Simultaneous fixed targets]
    E --> G[Fixed-family tests]
    G --> H[Monte Carlo precision]
```

## Recurrence network

```mermaid
flowchart LR
    A[Auto recurrence] --> B[Sparse undirected adjacency]
    B --> C[Degree]
    B --> D[Clustering / transitivity]
    B --> E[Connected components]
    C --> F[Topology under declared recurrence contract]
    D --> F
    E --> F
```

Graph topology remains threshold- and Theiler-dependent; no automatic
dimension or chaos interpretation is made.

## Joint recurrence

```mermaid
flowchart LR
    A[Subsystem A auto recurrence] --> C[Exact synchronized grid + shared Theiler]
    B[Subsystem B auto recurrence] --> C
    C --> D[Logical AND]
    D --> E[JRR]
    D --> F[JRQA]
    E --> G[Coincident recurrence interpretation]
    F --> G
```

No cross-state distance, lag optimization, or causal direction is implied.

## Nonlinear dynamics

```mermaid
flowchart LR
    A[Continuous trajectory] --> B[Explicit state definition]
    B --> C[Delay embedding diagnostics]
    B --> D[Sparse recurrence / RQA]
    D --> K[Windowed RQA]
    K --> L[RQA functional trajectories]
    L --> M[FPCA / MFPCA / regression]
    C --> E[Local divergence]
    E --> F[Rosenstein LLE]
    F --> G{Surrogate null}
    G -->|Scalar| H[IAAFT]
    G -->|Joint channels| I[Multivariate IAAFT + retained cross-spectrum diagnostics]
    B --> H[Declared Poincare section]
    H --> I[Empirical local return map]
    I --> J[Experimental spectral-radius stability]
```

Overlapping RQA windows remain within-curve dependent summaries; the source curve/participant remains the downstream sampling unit. Classical Floquet/monodromy and continuation analysis are intentionally excluded from the raw-gaze pathway.

## Documentation contract

```mermaid
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
```

Website: https://stefanosbalaskas.github.io/eyetrajectoriespy/methods/workflow-atlas/

### Directed discrete-state dependence

```text
predeclared discrete source/target states
  -> explicit target history k + source history l + source lag d
  -> discrete_transfer_entropy()
  -> local history/support diagnostics
  -> optional analyst-declared circular shifts
  -> transfer_entropy_circular_shift_test()
  -> reporting with no automatic causal claim
```

See `docs/methods/transfer-entropy.md` and the
`discrete-transfer-entropy` mathematical contract.
