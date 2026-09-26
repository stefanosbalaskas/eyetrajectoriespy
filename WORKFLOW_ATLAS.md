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
    C --> E[Declared participant functional random effects]
    D --> F{Trial functional effect?}
    E --> F
    F -->|No| R{Residual family?}
    F -->|Yes| N[Validate hierarchy + declare trial basis/Psi_T]
    N --> R
    R -->|iid + no trial effect| M[Historical joint Gaussian MixedLM]
    R -->|exponential / AR1 or trial effect| P[Profiled participant-block Gaussian likelihood]
    P --> S{Participant random slope?}
    M --> S
    S -->|Yes| T[Check within-participant variation + covariance complexity]
    S -->|No| G[Retain covariance hierarchy]
    T --> G
    G --> Q[Inspect Psi_P / Psi_T / residual parameter + BLUP diagnostics]
    Q --> X[Raw residual ACF / variogram]
    Q --> Y[0.49 within-trial whitened residual diagnostics]
    Q --> H{Whole-function inference?}
    H -->|Yes| I[Resample whole participants with all trials]
    I --> J[Fixed-covariance GLS or full declared-model refit]
    J --> K[Observed-grid simultaneous bands]
    K --> L{Predeclared covariance alternatives?}
    L -->|Yes| Z[0.50 compare already fitted structures against declared reference]
    Z --> ZA[Coefficient / band / variance / raw+white residual / IC sensitivity]
    ZA --> ZB[Report robustness; no ranking or automatic winner]
```

Whole participants remain the resampling unit. Residual covariance is block
diagonal by trial. Exponential correlation is defined on physical time; AR(1)
uses index steps and requires a regular grid. The fixed-covariance bootstrap
conditions on every fitted covariance term, while the full-refit bootstrap
re-estimates participant covariance, optional trial covariance, residual
variance, and phi/rho without reselecting the covariance family.

Version 0.50 is a separate comparison layer over already fitted, predeclared
structures. It requires identical scientific inputs and likelihood mode,
retains failed declarations, and reports robustness without selecting a model.


## Functional response regression

```mermaid
flowchart LR
    A[Functional response Y_ij(t)] --> B{Response family}
    B -->|Continuous Gaussian| C{Repeated trials?}
    C -->|No independent curves| D[0.35 observed-grid FoSR OLS]
    C -->|Yes participant-level predictors only| E[Participant-average FoSR]
    C -->|Yes trial-varying predictors| F[Gaussian functional mixed effects]
    B -->|Bernoulli 0/1| G[0.51 marginal generalized FoSR: logit]
    B -->|Poisson counts| H[0.51 marginal generalized FoSR: log]
    G --> I[Participant GEE clusters + working independence]
    H --> I
    I --> J[Robust sandwich covariance]
    J --> K[Whole-participant case bootstrap refits]
    K --> L[Observed-grid link-scale simultaneous bands]
```

The 0.51 generalized path is population averaged rather than conditional on
functional random effects. It allows trial-varying predictors, fixes working
independence, and does not select a family, link, basis size, or working
correlation automatically.

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

### Transfer-entropy robustness multiverse

```text
predeclared discrete source/target states
  -> declare target-history grid K
  -> declare source-history grid L
  -> declare source-lag grid D
  -> full Cartesian K x L x D
  -> transfer_entropy_parameter_sensitivity()
      -> one row per declared specification
      -> TE + empirical support diagnostics
      -> optional identical circular-shift null per row
      -> descriptive robustness summary
      -> no automatic winner / hidden averaging
```

### Conditional transfer entropy

```text
explicit discrete source X
explicit discrete target Y
explicit discrete condition Z
        |
        +--> declare k: target history
        +--> declare l: source history
        +--> declare m: condition history
        +--> declare d: source lag
        +--> declare c: condition lag
                    |
                    v
 conditional_transfer_entropy()
        |           |
        |           +--> exact local histories + support diagnostics
        +--> incremental directed predictive information
                    |
                    +--> optional analyst-declared source-only shifts
                    |       target Y fixed
                    |       condition Z fixed
                    v
 conditional_transfer_entropy_circular_shift_test()
                    |
                    v
      no causal-identification claim
```
