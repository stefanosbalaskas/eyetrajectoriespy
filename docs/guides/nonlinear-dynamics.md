# Nonlinear trajectory dynamics

Version 0.23 adds nonlinear-dynamics tools for continuous gaze trajectories while preserving the package rule that **diagnostics do not silently become analysis choices**.

The implementation is divided into three scientific layers:

1. **established reconstruction / recurrence analysis** — delay embedding, AMI/ACF diagnostics, false-nearest-neighbor diagnostics, sparse RQA, windowed RQA, and cross-RQA;
2. **advanced nonlinear diagnostics** — Rosenstein local divergence / largest-Lyapunov estimation and IAAFT surrogate testing;
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

This is useful for participant-participant, participant-reference, repeated-session, or expert-novice comparisons. The two state spaces must use the same named variables in the same order, coordinate system, time unit, and—when embedded—the same embedding dimension and delay semantics. Cross-recurrence currently does not report CORM because the auto-recurrence normalization is not transferred silently to the rectangular cross-recurrence setting.

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
