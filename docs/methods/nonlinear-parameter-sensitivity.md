# Nonlinear parameter sensitivity

Version 0.26 adds explicit robustness analysis for the nonlinear estimators that were already present in the package. The purpose is not to search for the parameter combination that produces the most interesting result. It is to make the dependence of RQA and Rosenstein-style local-divergence estimates on defensible analysis choices visible.

The three entry points are:

```python
rqa_parameter_sensitivity(...)
lyapunov_parameter_sensitivity(...)
kantz_parameter_sensitivity(...)
```

All evaluate the full Cartesian product of the declared grid and return every successful specification. They never rank, optimize, or automatically select a preferred setting.

## Why this is a separate scientific layer

A single RQA value is conditional on the reconstructed state and recurrence definition. In shorthand,

$$
\mathrm{DET}
=
\mathrm{DET}
\left(
m,\tau,\varepsilon,w,\ell_{\min},v_{\min}
\right).
$$

Likewise, a Rosenstein slope is conditional on reconstruction, temporal exclusion, and the fitted divergence interval,

$
\widehat\lambda_{\max}^{(R)}
=
\widehat\lambda_{\max}^{(R)}
\left(
m,\tau,w,[t_a,t_b]
\right).
$

For Kantz, the fixed neighborhood radius and minimum-neighbor rule are additional declared analysis dimensions,

$
\widehat\lambda_{\max}^{(K)}
=
\widehat\lambda_{\max}^{(K)}
\left(
m,\tau,\varepsilon,n_{\min},w,[t_a,t_b]
\right).
$

The base APIs already preserve those choices. Version 0.26 adds a structured way to evaluate a predeclared neighborhood of choices without turning the package into a parameter optimizer.

## RQA parameter sensitivity

`rqa_parameter_sensitivity()` operates on a regular-grid `TrajectorySet` and performs delay reconstruction for every declared embedding-dimension/delay pair.

```python
from eyetrajectoriespy import rqa_parameter_sensitivity

sensitivity = rqa_parameter_sensitivity(
    gaze,
    curve=0,
    dimensions=("x", "y"),
    embedding_dimensions=(2, 3, 4),
    delays=(3, 5, 7),
    radii=(0.5, 1.0, 1.5),
    theiler_windows=(3, 6, 9),
    min_diagonal_lengths=(2, 3),
    min_vertical_lengths=(2, 3),
)
```

The function requires **exactly one** threshold family:

- `radii=(...)` for fixed-radius sensitivity; or
- `target_recurrence_rates=(...)` for target-rate sensitivity.

Supplying both or neither is an error.

### What is varied

The table records both requested and resolved quantities:

- embedding dimension;
- requested delay, resolved delay in samples, and physical delay;
- threshold policy;
- requested radius or target recurrence rate;
- resolved radius;
- achieved recurrence rate;
- requested and resolved Theiler window;
- minimum diagonal and vertical line lengths;
- recurrence norm;
- RR, DET, mean/max diagonal length, diagonal entropy, LAM, trapping time, maximum vertical length, and CORM;
- recurrence-point and qualifying-line counts.

This is important when physical-time requests resolve to a discrete sample grid.

### Target recurrence rate

Under target-rate mode, recurrence density is controlled by construction. The achieved rate is retained because distance ties can prevent an exact target, but RR should not then be treated as an independent robustness outcome.

The more informative sensitivity outcomes under target-rate mode are the line-based measures and the solved radius required to produce the declared recurrence-density target.

## Rosenstein-LLE parameter sensitivity

`lyapunov_parameter_sensitivity()` evaluates reconstruction choices, Theiler windows, and fit intervals without automatically selecting a linear region.

```python
from eyetrajectoriespy import lyapunov_parameter_sensitivity

lle_sensitivity = lyapunov_parameter_sensitivity(
    gaze,
    curve=0,
    dimensions=("x", "y"),
    embedding_dimensions=(2, 3, 4),
    delays=(3, 5),
    theiler_windows=(6, 12),
    fit_intervals=((1, 5), (2, 6), (3, 7)),
    max_horizon=10,
)
```

For efficiency, the mean log-divergence curve is computed once for each resolved embedding/Theiler combination and reused across declared fit intervals. This reuse does not change the estimator.

The table records:

- requested and resolved reconstruction settings;
- requested and resolved fit interval;
- maximum divergence horizon;
- estimated exponent and units;
- intercept;
- fit $R^2$;
- slope standard error;
- number of fitted divergence points;
- minimum usable-pair count in the fit interval;
- zero-distance counts in the fit interval.

## Kantz-LLE parameter sensitivity

Version 0.30 adds `kantz_parameter_sensitivity()` for the neighborhood-based estimator.

```python
from eyetrajectoriespy import kantz_parameter_sensitivity

kantz = kantz_parameter_sensitivity(
    gaze,
    curve=0,
    dimensions=("x", "y"),
    embedding_dimensions=(2, 3, 4),
    delays=(3, 5),
    radii=(0.05, 0.08, 0.12),
    min_neighbors=(2, 4),
    theiler_windows=(6, 12),
    fit_intervals=((1, 5), (2, 6)),
    max_horizon=10,
)
```

The complete declared Cartesian product is evaluated. There is no internal search for a radius that maximizes the exponent, fit quality, support, or positivity.

For each resolved embedding/radius/minimum-neighbor/Theiler specification, the Kantz divergence curve is computed once and reused across the declared fit intervals.

The table retains:

- requested and resolved reconstruction settings;
- fixed radius;
- minimum-neighbor requirement;
- requested and resolved Theiler window;
- requested and resolved fit interval;
- maximum divergence horizon;
- exponent, units, intercept, $R^2$, and slope standard error;
- number of fitted divergence points;
- fraction of reconstructed reference states that satisfy the minimum-neighbor rule at horizon zero;
- minimum contributing-reference count in the fitted interval;
- minimum contributing-pair count in the fitted interval;
- zero-mean neighborhood counts in the fitted interval.

The supported-reference fraction is a **support diagnostic**, not an inferential weight. A high value does not make a radius scientifically preferable; it only describes how much of the reconstructed state set is supported under that declared neighborhood rule.

If any declared radius/minimum-neighbor combination yields no supported reference state, the entire sensitivity analysis fails and identifies that specification. The package does not silently remove the sparse-neighborhood row or expand the radius.

### Plot one explicit Kantz slice

```python
from eyetrajectoriespy import plot_kantz_sensitivity

ax = plot_kantz_sensitivity(
    kantz,
    parameter="requested_radius",
    response="exponent",
    filters={
        "embedding_dimension": 2,
        "requested_delay": 3.0,
        "min_neighbors": 4,
        "requested_theiler_window": 6.0,
        "requested_fit_start": 1.0,
        "requested_fit_end": 5.0,
    },
)
```

As with the other sensitivity plots, the helper refuses to average over unspecified parameter dimensions.

## Descriptive stability summaries

Both result objects include `summary_table`.

For each output it reports:

- number of declared specifications;
- number and fraction with finite values;
- minimum;
- first quartile;
- median;
- third quartile;
- maximum;
- absolute range;
- standard deviation across the declared grid.

These are **descriptive summaries of analyst-declared specifications**. They are not bootstrap uncertainty, posterior uncertainty, sampling distributions, or multiplicity-adjusted inference.

For LLE, the exponent row additionally reports how many declared specifications produce positive, negative, or exactly zero slopes and the corresponding fractions.

A positive-specification fraction such as 0.85 means only:

> 85% of the declared analysis specifications produced a positive fitted slope.

It does **not** mean an 85% probability of deterministic chaos.

## Failure policy

A sensitivity analysis is not allowed to look robust merely because difficult specifications disappeared.

If any declared specification cannot be evaluated—for example because the embedding leaves too few states or a fit interval contains too few finite divergence points—the entire sensitivity call raises an error identifying the offending combination.

The package does not:

- drop failed specifications;
- redraw a replacement grid;
- change the fit interval;
- reduce an embedding dimension;
- alter the Theiler window;
- change the recurrence threshold.

## Memory contract

RQA grids can become large. Retaining one sparse recurrence matrix for every combination would make sensitivity analysis unnecessarily memory-intensive.

Version 0.26 therefore retains the full tidy metric/provenance table but **does not store every recurrence matrix**. A particular recurrence matrix can always be reconstructed with the base `delay_embed_trajectory()` and `recurrence_matrix()` APIs using the stored specification.

This differs from silent result dropping: all parameter choices and all reported numerical outcomes remain in the sensitivity table.

## Plotting without hidden aggregation

`plot_rqa_sensitivity()`, `plot_lyapunov_sensitivity()`, and `plot_kantz_sensitivity()` deliberately plot only one explicit one-parameter slice.

```python
ax = plot_rqa_sensitivity(
    sensitivity,
    parameter="requested_radius",
    metric="determinism",
    filters={
        "embedding_dimension": 3,
        "requested_delay": 5.0,
        "requested_theiler_window": 6.0,
        "min_diagonal_length": 2,
        "min_vertical_length": 2,
    },
)
```

If the remaining table contains multiple rows for one x-axis value, plotting fails and asks for additional filters. The plotting helper never averages over unspecified embedding dimensions, delays, fit intervals, or other sensitivity dimensions.

## How to define the grid

The package does not supply universal ranges such as "2-4 dimensions", "5-10% RR", or a fixed LLE fit fraction.

A defensible grid should come from:

1. measurement resolution and sampling rate;
2. preprocessing and state representation;
3. AMI/ACF and false-nearest-neighbor diagnostics where relevant;
4. substantive temporal scales;
5. published conventions for the specific analysis;
6. values that would have been scientifically defensible before inspecting the desired outcome.

Kraemer et al. show that recurrence characteristics can depend strongly on threshold and embedding dimension, motivating explicit threshold sensitivity rather than a universal epsilon. Rosenstein et al. describe robustness of their estimator across reconstruction choices, but that does not eliminate the need to inspect those choices in a new finite biological data set. Kantz's neighborhood method makes the local scale explicit through $\varepsilon$; a robust analysis should therefore expose plausible radius/minimum-neighbor dependence rather than hide it inside a tuned setting.

## Reporting

For confirmatory work, report the complete declared grid, the primary specification if one existed independently of the sensitivity analysis, the range/quantiles of the main sensitivity outcomes, failed-specification behavior, and whether any substantive conclusion changed across the grid.

Do not select the specification with the largest DET, strongest positive LLE, highest $R^2$, or smallest slope standard error and then present it as though it had been selected a priori.

See the [worked example](../examples/nonlinear-parameter-sensitivity.md), [nonlinear guide](../guides/nonlinear-dynamics.md), [limitations](limitations.md), [pre-registration checklist](preregistration.md), and [references](references.md).
