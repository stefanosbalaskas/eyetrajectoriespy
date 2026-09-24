# Trajectory-distance sensitivity

Version 0.38 adds a robustness layer across the trajectory-distance methods
already present in eyetrajectoriespy. It does **not** add another distance
metric.

The purpose is to ask a more useful question:

> Does the substantive similarity structure remain similar when the analyst
> changes the defensible trajectory-distance contract?

The initial public layer compares integrated functional L2, discrete Fréchet,
and explicit DTW specifications.

## Why this matters

These distances answer different questions.

- **Functional L2** compares functions at the same trial times and integrates
  pointwise squared displacement over the common grid.
- **Discrete Fréchet** compares ordered geometric paths through a monotone
  coupling and is driven by the worst coupled local separation.
- **DTW** uses a monotone dynamic-programming alignment and accumulates local
  distances under an explicitly selected step pattern, optional sample-index
  band, and normalization rule.

A finding that depends strongly on which of these contracts is used should not
be presented as if "trajectory similarity" were one uniquely defined object.

## Declare a sensitivity set

~~~python
from eyetrajectoriespy import trajectory_distance_sensitivity

robustness = trajectory_distance_sensitivity(
    gaze,
    specifications=(
        {
            "name": "l2",
            "method": "functional_l2",
        },
        {
            "name": "frechet",
            "method": "discrete_frechet",
        },
        {
            "name": "dtw_s2_norm",
            "method": "dtw",
            "step_pattern": "symmetric2",
            "normalize": True,
            "window_radius": None,
        },
    ),
    dimensions=("x", "y"),
    dimension_weights=(1.0, 1.0),
    neighbor_k=3,
)
~~~

Every specification needs a unique name.

For DTW, the supported specification fields are:

- `step_pattern`: `"symmetric1"` or `"symmetric2"`;
- `normalize`: explicit Boolean;
- `window_radius`: explicit Sakoe-Chiba radius in sample-index units or
  `None`.

Unknown options fail instead of being ignored.

## What is retained

The result keeps:

- every raw distance matrix;
- the complete specification table;
- every unordered curve-pair distance and within-specification rank;
- every pairwise comparison between specifications;
- per-curve top-\(k\) neighbor sets;
- per-curve top-\(k\) Jaccard overlap;
- nearest-neighbor identity agreement;
- deterministic neighbor selections;
- cutoff-tie flags;
- dimensions, weights, curve IDs, and provenance.

## Global pair-order agreement

For specification \(s\), let the upper triangle of the distance matrix be
\(\mathbf v^{(s)}\). Version 0.38 compares pair ordering using Spearman
correlation:

$$
\rho_S(s,r)
=
\operatorname{corr}
\left(
\operatorname{rank}\mathbf v^{(s)},
\operatorname{rank}\mathbf v^{(r)}
\right).
$$

The output also keeps mean, median, and maximum absolute rank differences.

Raw-scale Pearson correlation is retained as a secondary descriptive
diagnostic. It should be interpreted cautiously when distance definitions have
different native scales.

## Local neighborhood agreement

For each curve, top-\(k\) neighbor sets are compared using Jaccard overlap,

$$
J_k
=
\frac{|A\cap B|}{|A\cup B|}.
$$

The result additionally records:

- exact top-\(k\) set agreement;
- nearest-neighbor identity agreement;
- whether a tie occurs at the \(k\)/\(k+1\) cutoff.

That last point is important: when the cutoff is tied, one deterministic
neighbor set is still returned for reproducibility, but it is not presented as
uniquely identified.

## No hidden common scale

The package does not standardize or rescale distance matrices before the
robustness analysis.

That is intentional. L2, Fréchet, raw DTW, and normalized DTW have different
numerical meanings. A hidden z-score or range normalization would add another
analytical decision.

Cross-contract comparison therefore focuses on ordering and neighborhood
structure.

## No p-values from dependent pair distances

The \(n(n-1)/2\) pairwise distances are not independent observations because
each trajectory appears in many pairs.

Version 0.38 therefore reports descriptive rank and neighborhood agreement only.
It does not attach ordinary correlation p-values to the condensed distance
vectors.

If a study needs inferential comparison of distance matrices, the resampling
unit and null hypothesis must be specified separately.

## No best-metric selector

The API deliberately does not return:

- a winner;
- a consensus distance;
- an averaged distance matrix;
- a robustness score threshold;
- an automatic DTW window;
- an automatic DTW step pattern;
- an automatic coordinate scaling rule.

The scientific question determines which contracts are defensible. The
sensitivity analysis then shows how much the resulting similarity structure
changes across those contracts.

## Reporting

~~~python
from eyetrajectoriespy import (
    trajectory_distance_comparison_frame,
    trajectory_distance_neighbor_frame,
    trajectory_distance_sensitivity_reporting_text,
)

comparison = trajectory_distance_comparison_frame(robustness)
local = trajectory_distance_neighbor_frame(robustness)
print(trajectory_distance_sensitivity_reporting_text(robustness))
~~~

Report the full specification set, selected dimensions, dimension weights,
neighbor \(k\), global rank agreement, local neighbor agreement, cutoff ties,
and the fact that the analysis is descriptive rather than a statistical test
of which distance is correct.

## Plot

~~~python
from eyetrajectoriespy import (
    plot_trajectory_distance_rank_correlations,
)

ax = plot_trajectory_distance_rank_correlations(robustness)
~~~

The heatmap displays descriptive Spearman agreement among declared distance
specifications.

## Interpretation example

A result such as:

> Pair-distance rankings were highly similar between normalized symmetric2 DTW
> and discrete Fréchet, whereas L2 produced lower rank agreement and changed
> several nearest-neighbor identities.

is appropriate.

A statement such as:

> DTW was statistically proven to be the best trajectory distance.

is not supported by this analysis.

## Evidence basis

The distance definitions remain those documented for integrated functional L2,
Eiter-Mannila discrete Fréchet, and Sakoe-Chiba/Giorgino DTW. The sensitivity
layer follows a conservative methodological principle already used elsewhere
in eyetrajectoriespy: when multiple defensible analysis contracts exist,
retain their outputs and quantify whether conclusions depend on the choice
rather than silently selecting one after inspecting results.

The 0.38 layer does not claim that rank correlation or nearest-neighbor overlap
is a novel trajectory-comparison method.
