# Recurrence-threshold diagnostics

The recurrence threshold epsilon determines which state pairs are treated as recurrent. Version 0.27 makes this dependence directly inspectable before or alongside RQA.

For eligible auto-recurrence pairs

$$
\mathcal E_w
=
\{(i,j): i<j,\ |j-i|>w\},
$$

where w is the declared Theiler window, define the pairwise state distance

$$
D_{ij}
=
\|\mathbf z_i-\mathbf z_j\|_p.
$$

At radius epsilon,

$$
RR(\varepsilon)
=
\frac{1}{|\mathcal E_w|}
\sum_{(i,j)\in\mathcal E_w}
\mathbb I\{D_{ij}\le\varepsilon\}.
$$

Therefore RR(epsilon) is the empirical cumulative distribution function of eligible pairwise state distances, evaluated at the declared radius.

## API

~~~python
from eyetrajectoriespy import recurrence_radius_profile

profile = recurrence_radius_profile(
    embedded,
    curve=0,
    radii=(0.10, 0.20, 0.30, 0.40, 0.50),
    metric="euclidean",
    theiler_window=6,
)
~~~

For a raw TrajectorySet, dimensions remain explicit:

~~~python
profile = recurrence_radius_profile(
    gaze,
    curve=0,
    radii=(0.02, 0.04, 0.06, 0.08),
    metric="euclidean",
    theiler_window=6,
    dimensions=("x", "y"),
)
~~~

There is deliberately **no default radius grid**.

The analyst supplies a strictly increasing sequence of positive radii. The package does not sort, deduplicate, optimize, or extend the grid.

## What the table contains

For every declared radius the result records:

- the previous radius, when one exists;
- the current radius;
- number of newly included eligible pairs in the current distance shell;
- shell pair fraction;
- cumulative recurrent-pair count;
- cumulative recurrence rate;
- number of Theiler-excluded temporal pairs whose state distance is within the current radius.

The first shell contains distances

$$
D\le\varepsilon_1.
$$

Later shells contain

$$
\varepsilon_{k-1}<D\le\varepsilon_k.
$$

Thus the table simultaneously provides the exact RR(epsilon) curve and a binned empirical pair-distance distribution over the supplied radius range.

## Same recurrence contract as the base estimator

The profile uses the same conventions as recurrence_matrix():

- inclusive distance <= radius threshold;
- same Euclidean/city-block/Chebyshev metric definitions;
- same line-of-identity exclusion;
- same declared Theiler exclusion;
- same eligible-pair recurrence-rate denominator;
- no hidden coordinate normalization or multichannel scaling.

A useful audit check is:

~~~python
fixed = recurrence_matrix(
    gaze,
    curve=0,
    radius=0.06,
    theiler_window=6,
    dimensions=("x", "y"),
)

row = profile.table.loc[profile.table["radius"] == 0.06].iloc[0]

assert row["recurrence_rate"] == fixed.achieved_recurrence_rate
~~~

The test suite verifies this equality across several radii and Theiler settings.

## Sparse/scalable counting

The diagnostic does **not** construct a dense N x N distance matrix.

Cumulative pair counts are obtained from a spatial tree. Temporal pairs excluded by the Theiler window are then corrected exactly from their direct state distances.

This avoids the dense-memory requirement that would otherwise become prohibitive for long sample-level gaze records.

The result stores only the radius-profile table and provenance. It does not retain pairwise distances.

A runnable benchmark is provided in benchmarks/benchmark_recurrence_radius_profile.py. It reports measured wall-clock time for requested sample sizes rather than encoding an unverified performance promise in the documentation.

## Distribution coverage

The largest supplied radius need not contain all eligible pair distances.

The result therefore records maximum_radius_coverage_fraction and full_distance_distribution_captured.

If the largest radius gives RR=0.12, the shell table describes the first 12% of the eligible pair-distance distribution, not its complete support.

This distinction matters when interpreting shell fractions.

## Threshold choice

Kraemer et al. emphasize that threshold selection is a key methodological problem and explicitly analyze the distribution of pairwise state-space distances. Their results show that recurrence characteristics can depend strongly on embedding and threshold strategy.

The profile is therefore a **diagnostic**, not an optimizer.

It can answer questions such as:

- How rapidly does recurrence density grow as radius increases?
- Is the planned radius located in a very steep part of the distance CDF?
- How much pairwise-distance mass lies between two scientifically plausible thresholds?
- Does a threshold sensitivity grid traverse sparse, intermediate, and near-saturated recurrence regimes?
- Does the same numeric radius imply very different recurrence densities after changing the state representation?

It does not answer which radius gives the scientifically best result.

## Relation to target recurrence rate

The base recurrence_matrix(..., target_recurrence_rate=...) contract remains available when recurrence density itself is to be controlled explicitly.

That policy solves for a radius corresponding to a declared target RR. The radius profile serves a different purpose: it displays the mapping

$$
\varepsilon \longmapsto RR(\varepsilon)
$$

over a user-declared range.

If target-RR mode is used in a substantive analysis, report both the requested target and the solved radius. Do not interpret the resulting RR as an unconstrained outcome.

## No universal RR band

The package does not encode a rule such as “use 5–10% recurrence.”

Published applications and domains use different threshold strategies, and overly small or large thresholds can respectively produce sparse/noisy or saturated recurrence structures.

Any reference range belongs in the scientific protocol for the particular state representation and question, not as a package default.

## Plot

~~~python
from eyetrajectoriespy import plot_recurrence_rate_curve

ax = plot_recurrence_rate_curve(profile)
~~~

The plot shows exact recurrence rate against the supplied radius grid. It does not mark an “optimal” radius.

## Reporting

Report the state representation/dimensions, coordinate/state units and any upstream scaling, distance metric, complete declared radius grid, Theiler window and resolved sample count, eligible pair count, recurrence-rate range over the grid, profile coverage at the maximum radius, and the independent scientific rule used to choose any primary radius.

See the worked example, RQA software conventions, nonlinear parameter sensitivity guide, and limitations pages.
