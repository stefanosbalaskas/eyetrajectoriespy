# Nonlinear trajectory dynamics

Version 0.23 adds nonlinear-dynamics tools for continuous gaze trajectories while preserving the package rule that **diagnostics do not silently become analysis choices**.

The implementation is divided into three scientific layers:

1. **established reconstruction / recurrence analysis** — delay embedding, AMI/ACF diagnostics, false-nearest-neighbor diagnostics, sparse RQA, windowed RQA, cross-RQA, and functionalized RQA trajectories;
2. **advanced nonlinear diagnostics** — named Rosenstein and Kantz local-divergence / largest-Lyapunov estimation plus IAAFT surrogate testing. LLE has direct eye-movement signal-analysis precedent, but remains uncommon as a continuous behavioral-scanpath descriptor;
3. **experimental behavioral stability** — empirical Poincare sections and local return-map contraction/expansion.

Classical Floquet multipliers, monodromy matrices, and numerical bifurcation continuation are **not** raw-gaze statistics and are not exposed as such.

## When to use these methods

Use them when the scientific question concerns temporal organization that ordinary averages or static FPCA scores do not directly describe, for example:

- repeated returns to nearby gaze states;
- persistence of sequential scanning patterns;
- changes in recurrence structure during a trial;
- cross-participant or participant-reference recurrence;
- local divergence of reconstructed trajectories;
- evidence against a declared linear-stochastic surrogate null;
- repeated approximate cycles for which cycle-to-cycle contraction/expansion is scientifically meaningful.

Do **not** use them merely because a gaze trace looks visually complex.

## 1. Delay-coordinate reconstruction

For a multivariate gaze trajectory,

$$
\mathbf z_t=
[
\mathbf G(t),
\mathbf G(t-\tau),
\ldots,
\mathbf G(t-(m-1)\tau)
].
$$

Example:

\`\`\`python
from eyetrajectoriespy import delay_embed_trajectory

embedded = delay_embed_trajectory(
    gaze,
    embedding_dimension=3,
    delay=0.050,
    delay_units="seconds",
    dimensions=("x", "y"),
)
\`\`\`

The package requires a common grid. Time-based delays require an approximately regular grid and must map to an integer number of observed samples. Missing values are not dropped or interpolated.

### Delay diagnostics

\`embedding_delay_diagnostics()\` reports:

- lag in samples and time units;
- autocorrelation;
- average mutual information;
- a marker for the first interior AMI local minimum, if one exists.

The marker is a diagnostic only.

\`\`\`python
delay_diag = embedding_delay_diagnostics(
    gaze,
    curve=0,
    dimension="x",
    max_lag=0.30,
    max_lag_units="seconds",
    bins=16,
)
\`\`\`

### Embedding-dimension diagnostics

\`embedding_dimension_diagnostics()\` implements Kennel-style false-nearest-neighbor fractions across requested dimensions.

\`\`\`python
dimension_diag = embedding_dimension_diagnostics(
    gaze,
    curve=0,
    dimension="x",
    delay=0.050,
    delay_units="seconds",
    max_dimension=8,
    theiler_window=0.100,
    theiler_window_units="seconds",
    rtol=10.0,
    atol=2.0,
)
\`\`\`

No dimension is selected automatically.

Both AMI and false-nearest-neighbor diagnostics require an approximately regular temporal grid. Expressing a lag in samples does not remove that requirement: on an irregular physical-time grid, the same sample offset corresponds to different elapsed times. If event order is the intended axis, encode that choice explicitly as a regular event-index grid.

## 2. Sparse recurrence analysis

For states \(\mathbf z_i\),

$$
R_{ij}
=
\mathbb I
[
\|\mathbf z_i-\mathbf z_j\|_p\le\varepsilon
].
$$

\`recurrence_matrix()\` stores the matrix as SciPy CSR rather than creating an \(N\times N\) dense Boolean array.

You must declare exactly one radius policy:

=== "Fixed radius"

    \`\`\`python
    recurrence = recurrence_matrix(
        embedded,
        curve=0,
        radius=1.25,
        metric="euclidean",
        theiler_window=0.100,
        theiler_window_units="seconds",
    )
    \`\`\`

=== "Target recurrence rate"

    \`\`\`python
    recurrence = recurrence_matrix(
        embedded,
        curve=0,
        target_recurrence_rate=0.05,
        metric="euclidean",
        theiler_window=0.100,
        theiler_window_units="seconds",
    )
    \`\`\`

Target-rate mode solves for a radius; the achieved rate and solved radius remain visible.

### Radius / pair-distance diagnostics

Before interpreting a fixed recurrence radius, inspect the mapping from radius to recurrence density over a scientifically declared grid:

```python
profile = recurrence_radius_profile(
    gaze,
    curve=0,
    dimensions=("x", "y"),
    radii=(0.02, 0.04, 0.06, 0.08, 0.12),
    metric="euclidean",
    theiler_window=0.05,
    theiler_window_units="seconds",
)
```

The returned recurrence-rate column is the empirical CDF of eligible pairwise state-space distances at the supplied thresholds. Shell counts/fractions record how much pair-distance mass enters between successive radii.

The diagnostic uses the same inclusive threshold and eligible-pair denominator as `recurrence_matrix()`, applies the Theiler exclusion exactly, and does not construct a dense distance matrix.

No radius is selected. The supplied grid is never sorted, deduplicated, extended, or optimized by the package. If the maximum declared radius does not capture all eligible pair distances, the result records that the distance profile is partial.

See [recurrence-threshold diagnostics](../methods/recurrence-threshold-diagnostics.md).

### RQA metrics

\`\`\`python
from eyetrajectoriespy import rqa_metrics

metrics = rqa_metrics(
    recurrence,
    min_diagonal_length=2,
    min_vertical_length=2,
)
\`\`\`

The result contains:

- recurrence rate;
- determinism;
- mean and maximum diagonal length;
- diagonal-line entropy;
- laminarity;
- trapping time;
- maximum vertical length;
- auto-recurrence CORM;
- recurrence-point and qualifying-line counts.

The line-length thresholds are part of the result provenance.

The base estimator also freezes several software conventions that differ across RQA libraries: recurrence uses an inclusive `distance <= radius` rule; auto-recurrence excludes the line of identity and declared Theiler window from both the recurrence set and eligible-pair RR denominator; cross-recurrence uses the full rectangular all-pairs denominator; RR/DET/LAM are reported on the 0-1 scale; diagonal-line entropy is normalized over qualifying lines; and finite-matrix border lines are counted at their observed length without a hidden border correction. See [RQA software conventions](../methods/rqa-software-conventions.md).


The recurrence matrix itself can represent spatial returns among irregularly timed observations, but the standard line-based RQA summaries above require an approximately regular source grid. For cross-RQA, both source grids must be regular with matching sampling steps. No interpolation or sampling-rate correction is performed internally; the raw recurrence result remains available even when line-based RQA is not admissible.

### Windowed RQA

\`\`\`python
dynamic = windowed_rqa(
    gaze,
    curve=0,
    window=2.0,
    step=0.25,
    window_units="seconds",
    step_units="seconds",
    radius=1.25,
    theiler_window=0.100,
    theiler_window_units="seconds",
    dimensions=("x", "y"),
)
\`\`\`

The returned table contains \(RR(t)\), \(DET(t)\), \(LAM(t)\), trapping time, entropy, CORM, and the radius used in each window.

Only complete windows are analyzed. Any trailing samples not included in a full window are reported as \`dropped_tail_samples\`; they are never silently forgotten.

### RQA metrics as functional trajectories

Version 0.24 can lift the same sliding-window contract across every source curve:

```python
functional_rqa = windowed_rqa_trajectory_set(
    gaze,
    metrics=("recurrence_rate", "determinism", "laminarity"),
    window=2.0,
    step=0.5,
    window_units="seconds",
    step_units="seconds",
    radius=1.25,
    theiler_window=0.100,
    theiler_window_units="seconds",
    dimensions=("x", "y"),
)
```

The window centers become a common functional time grid and the selected RQA measures become functional dimensions. The result retains the complete per-curve window tables, including solved radii, so functionalization does not discard the underlying RQA audit trail.

Overlapping windows are explicitly recorded. They reuse source samples and are **not independent observations**. Downstream FDA may model the resulting within-curve temporal shape, but inferential resampling must still respect the source curve/participant sampling unit.

When target recurrence rate is used, recurrence density is controlled by construction. Version 0.24 therefore refuses to use `recurrence_rate` itself as a downstream functional outcome under target-rate mode.

Undefined RQA metrics fail closed by default. `undefined_policy="keep"` retains those cells as `NaN`; no zero-filling or interpolation is introduced.

See the [worked functional RQA example](../examples/rqa-functional-trajectories.md).

### Window/step sensitivity and independent-unit inference

Version 0.25 adds an explicit sensitivity layer rather than a default window size:

```python
sensitivity = windowed_rqa_sensitivity(
    gaze,
    metrics=("recurrence_rate", "determinism", "laminarity"),
    window_step_pairs=((40, 20), (40, 10), (60, 20)),
    radius=0.35,
    theiler_window=2,
    dimensions=("x", "y"),
)
```

Every declared window/step pair is retained. The design table separates window span, derived-profile grid spacing, overlap fraction, analyzed-source coverage, reused-sample fraction, and mean/maximum window membership. None of those quantities is re-labeled as an effective independent sample size.

Pairwise profile diagnostics use only exact shared window centers. No interpolation is introduced merely to compare two sensitivity specifications, and the function never selects a preferred window/step setting automatically.

For population mean inference on the derived functions, use a scientifically justified independent unit:

```python
mean_band = windowed_rqa_functional_mean_band(
    gaze,
    metrics=("determinism", "laminarity"),
    window=40,
    step=20,
    unit="participant",
    participant_column="participant_id",
    radius=0.35,
    theiler_window=2,
    dimensions=("x", "y"),
    n_multiplier=2000,
    random_state=42,
)
```

The participant/curve residual function is multiplied as a whole across the complete window-center-by-metric grid. Overlapping window rows are never bootstrapped as independent observations. This preserves within-function dependence in the existing multiplier-band calibration while keeping the independent sampling unit explicit.

This procedure is **not** a moving/block bootstrap within one long trajectory and does not propagate post-hoc window-selection uncertainty. See [functional RQA sensitivity and dependence](../methods/rqa-functional-dependence.md) and the [worked 0.25 example](../examples/rqa-functional-sensitivity.md).
### Cross recurrence

\`\`\`python
cross = cross_recurrence_matrix(
    gaze_a,
    gaze_b,
    curve_a=0,
    curve_b=0,
    radius=1.25,
    metric="euclidean",
    dimensions_a=("x", "y"),
    dimensions_b=("x", "y"),
)

cross_metrics = cross_rqa_metrics(cross)
\`\`\`

This is useful for participant-participant, participant-reference, repeated-session, or expert-novice comparisons. The two state spaces must use the same named variables in the same order, coordinate system, time unit, and—when embedded—the same embedding dimension and delay semantics.

A cross-recurrence matrix does **not** align, synchronize, resample, or warp the two trajectories. Its row and column axes retain the two source time/index domains. If the scientific question requires clock synchronization, a declared lag restriction, or another alignment operation, perform and document that step explicitly before cross-recurrence analysis rather than treating the recurrence calculation itself as an alignment algorithm.

Cross-recurrence currently does not report CORM because the auto-recurrence normalization is not transferred silently to the rectangular cross-recurrence setting.

## 3. Local divergence and Rosenstein LLE

Start from an explicit delay embedding:

\`\`\`python
divergence = local_divergence_curve(
    embedded,
    curve=0,
    theiler_window=0.100,
    theiler_window_units="seconds",
    max_horizon=0.300,
    max_horizon_units="seconds",
)
\`\`\`

For each state \(i\), the nearest positive-distance neighbor outside the Theiler window is followed forward:

$$
d_i(k)=
\|
\mathbf z_{i+k}-\mathbf z_{j(i)+k}
\|_2.
$$

The result retains the mean log-distance, usable-pair count, and zero-distance count at every horizon.

Then declare the fit interval yourself:

\`\`\`python
lle = estimate_largest_lyapunov_rosenstein(
    divergence,
    fit_start=0.03,
    fit_end=0.12,
    fit_units="seconds",
)
\`\`\`

No automated “linear region” selector is used.

!!! warning "Interpretation"
    A positive estimated \(\lambda_{\max}\) does **not** by itself prove deterministic chaos in gaze behavior. Noise, filtering, nonstationarity, short records, embedding choices, and fit-interval choice can all create or alter apparent divergence.

### Kantz fixed-radius neighborhood divergence

Version 0.29 adds the second named maximal-Lyapunov path rather than treating all local-divergence estimators as interchangeable.

`local_divergence_curve()` follows one nearest temporally separated neighbor per reference state (Rosenstein-style). `kantz_divergence_curve()` instead uses every eligible neighbor inside one analyst-declared radius, averages their forward distances within each reference neighborhood, takes the log of that mean distance, and then averages across reference states.

```python
from eyetrajectoriespy import (
    kantz_divergence_curve,
    estimate_largest_lyapunov_kantz,
)

kantz = kantz_divergence_curve(
    embedded,
    curve=0,
    radius=0.08,
    min_neighbors=4,
    theiler_window=0.100,
    theiler_window_units="seconds",
    max_horizon=0.300,
    max_horizon_units="seconds",
)

kantz_lle = estimate_largest_lyapunov_kantz(
    kantz,
    fit_start=0.03,
    fit_end=0.12,
    fit_units="seconds",
)
```

The radius is never expanded automatically. A reference state with too few eligible neighbors simply does not contribute at that horizon; if no reference state is usable at horizon zero, the function fails and asks for an explicit scientific change to radius or `min_neighbors`.

The result retains:

- the declared radius and minimum-neighbor requirement;
- every reference state's initial neighbor count;
- contributing-reference count at each horizon;
- contributing pair count at each horizon;
- neighborhoods whose forward mean distance is exactly zero;
- the declared Theiler and divergence horizon.

Rosenstein and Kantz may produce different divergence curves because their neighborhood definitions differ. That difference is methodological sensitivity, not evidence that one implementation is defective.

Use a comparison only after holding the embedding, Theiler window, divergence horizon, time units, and fit interval fixed. Do not search over the Kantz radius and then report only the most convenient exponent.

See [Kantz LLE guidance](../methods/kantz-lle.md) and the [worked estimator comparison](../examples/kantz-lle.md).

### Sensitivity across reconstruction and fit choices

Version 0.26 adds a separate robustness layer for the parameter dependence of both RQA and Rosenstein LLE.

For reconstructed-state RQA:

```python
rqa_sensitivity = rqa_parameter_sensitivity(
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

For Rosenstein local divergence:

```python
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

These APIs evaluate the complete declared Cartesian grid. They do not optimize a radius, choose an embedding, choose a Theiler window, or select an LLE fit interval.

The returned quartiles/ranges describe variation **across analysis specifications**. They are not confidence intervals. Likewise, the fraction of declared LLE specifications with positive slopes is not a probability that gaze is chaotic.

If any declared specification is invalid, the sensitivity call fails and identifies it; the failed row is not silently removed. See [nonlinear parameter sensitivity](../methods/nonlinear-parameter-sensitivity.md).

## 4. IAAFT surrogate testing

The package therefore pairs the LLE estimator with an explicit surrogate-data test:

\`\`\`python
test = surrogate_nonlinearity_test(
    gaze,
    curve=0,
    dimension="x",
    statistic="largest_lyapunov",
    embedding_dimension=3,
    delay=0.050,
    delay_units="seconds",
    theiler_window=0.100,
    theiler_window_units="seconds",
    max_horizon=0.300,
    max_horizon_units="seconds",
    fit_start=0.03,
    fit_end=0.12,
    fit_units="seconds",
    method="iaaft",
    n_surrogates=199,
    alternative="greater",
    random_state=42,
)
\`\`\`

Every IAAFT surrogate preserves the source amplitude distribution exactly and iteratively approximates its Fourier-amplitude spectrum. Each surrogate is processed with the same embedding and LLE settings.

The Monte Carlo p-value uses the plus-one form

$$
p=
\frac{r+1}{B+1}.
$$

A failed surrogate raises an error; no replacement replicate is silently drawn.

Rejecting the surrogate null means the observed statistic is inconsistent with the declared linear-stochastic surrogate model at the chosen test level. It does not identify a unique nonlinear mechanism.

### Multivariate gaze surrogates are deferred

The current IAAFT implementation is **scalar**. It does not independently surrogate `x` and `y` and then call the result a multivariate gaze surrogate.

A future MIAAFT/multivariate-Fourier surrogate path must preserve the declared cross-channel linear structure as well as per-channel marginal/spectral constraints, expose convergence diagnostics, state the multivariate null explicitly, and validate against a primary/reference implementation. Until that contract is met, multivariate surrogate testing remains intentionally unavailable. See [RQA software conventions](../methods/rqa-software-conventions.md#multivariate-surrogate-contract-deferred-not-approximated).


## 5. Experimental Poincare return-map stability

For genuinely repeated gaze cycles, a section can be defined by one state variable:

\`\`\`python
crossings = poincare_crossings(
    gaze,
    curve=0,
    section_dimension="x",
    section_value=0.0,
    direction="positive",
    state_dimensions=("y",),
)
\`\`\`

Crossings are linearly interpolated between observed samples.

Fit a local return map only after declaring both a reference and neighborhood:

\`\`\`python
local_map = fit_local_return_map(
    crossings,
    reference="median",
    n_neighbors=12,
)

stability = return_map_stability(local_map)
\`\`\`

The local affine approximation is

$$
\mathbf z_{n+1}
=
\mathbf a+
\mathbf J(\mathbf z_n-\mathbf z_0)+
\boldsymbol\varepsilon_n.
$$

The fit also retains its design condition number and per-state fit \(R^2\), with no package-imposed condition-number cutoff. The spectral radius

$$
\rho(\mathbf J)=\max_j|\lambda_j(\mathbf J)|
$$

is labeled contracting, expanding, or near-neutral relative to an explicit tolerance.

!!! danger "Experimental—not classical Floquet theory"
    The fitted \(\mathbf J\) is estimated from noisy observed cycle-to-cycle data. It is not obtained by integrating a known ODE's variational equations. Do not call it a monodromy matrix and do not report its eigenvalues as Floquet multipliers.

## Computational scaling

A dense recurrence plot requires \(O(N^2)\) storage. Version 0.23 therefore stores recurrence matrices sparsely and uses spatial-tree neighbor search.

Target-recurrence-rate mode repeatedly counts neighbors while solving for \(\varepsilon\); it avoids a full dense pairwise-distance matrix but can still be computationally demanding for very long or high-dimensional embeddings.

Windowed RQA repeats recurrence construction in each declared window. Keep exploratory grids modest and report every parameter.

The repository includes `benchmarks/benchmark_recurrence.py` for retained wall-clock and CSR-memory measurements. Documentation should not state a runtime threshold unless it is tied to a recorded benchmark environment and parameterization.


## What the package deliberately does not choose for you

No silent choice is made for:

- interpolation or smoothing;
- dimensions included in state space;
- delay \(\tau\);
- embedding dimension \(m\);
- recurrence radius \(\varepsilon\);
- fixed-radius versus target-RR policy;
- distance metric;
- Theiler window;
- minimum diagonal/vertical line length;
- window length or step;
- LLE divergence horizon;
- LLE fit interval;
- surrogate count or test alternative;
- Poincare section;
- crossing direction;
- local-map reference state;
- local-map neighborhood.

## Reporting checklist

At minimum report:

1. sampling rate/grid and analyzed dimensions;
2. whether recurrence used observed or reconstructed state;
3. \(m\), \(\tau\), scaling/preprocessing, metric, \(\varepsilon\) policy, and Theiler window;
4. line-length thresholds for RQA;
5. window/step and explicit trailing-tail count for windowed RQA;
6. LLE fit interval, exponent units, \(R^2\), and number of fit points;
7. IAAFT surrogate count, seed, alternative, plus-one p-value, and convergence settings;
8. section, crossing direction, state dimensions, reference, neighborhood, and spectral radius for return maps;
9. the interpretation boundaries above.

See the [worked nonlinear-dynamics example](../examples/nonlinear-dynamics.md), [return-map example](../examples/return-map-stability.md), [mathematical reference](../methods/mathematical-reference.md#delay-embedding), and [limitations](../methods/limitations.md).
