# Dynamic time warping trajectory distance

Version 0.34 hardens the DTW layer by making the local step-weighting rule and normalization contract explicit while preserving the 0.33 default numerically.

## Scientific target

DTW compares complete ordered point sequences by finding a minimum-cost monotone alignment. The local geometry remains weighted Euclidean distance,

$$
d_w(\mathbf p_i,\mathbf q_j)
=
\left[
\sum_r \omega_r(p_{ir}-q_{jr})^2
\right]^{1/2}.
$$

DTW is appropriate when local sample-index progression differences may be nuisance variation. It is not a time-preserving analysis: recorded timestamps are not passed into the recurrence.

## Two explicit step patterns

### symmetric1: backward-compatible raw cumulative cost

The default remains symmetric1 so 0.33 calls keep the same numerical meaning:

$$
C^{(s1)}_{i,j}
=
d_w(\mathbf p_i,\mathbf q_j)
+
\min(C_{i-1,j-1},C_{i-1,j},C_{i,j-1}).
$$

Every visited point contributes one local-distance unit. This formulation is deliberately left unnormalized because there is no path-independent N+M denominator for this step pattern.

~~~python
raw = dynamic_time_warping_distance(
    path_a,
    path_b,
    step_pattern="symmetric1",
)
~~~

### symmetric2: normalizable symmetric weighting

symmetric2 weights diagonal advances by two and horizontal/vertical advances by one,

$$
C^{(s2)}_{i,j}
=
\min\left\{
C_{i-1,j-1}+2d_w,
C_{i-1,j}+d_w,
C_{i,j-1}+d_w
\right\}.
$$

For complete global alignment it is normalizable by the path-independent denominator m+n:

$$
d^{(s2)}_{\mathrm{norm}}(P,Q)
=
\frac{C^{(s2)}_{m,n}}{m+n}.
$$

~~~python
normalized = dynamic_time_warping_distance(
    path_a,
    path_b,
    step_pattern="symmetric2",
    normalize=True,
)
~~~

normalize=True is rejected for symmetric1 rather than silently applying a scientifically different denominator.

## Auditable result

~~~python
audit = dynamic_time_warping_distance(
    path_a,
    path_b,
    step_pattern="symmetric2",
    normalize=True,
    return_path=True,
)
~~~

The result retains:

- the returned distance;
- raw cumulative distance;
- normalized symmetric2 distance when defined;
- deterministic optimal monotone path;
- local distances;
- per-path step weights;
- weighted local contributions;
- path length and mean local distance;
- input dimensions and sequence lengths;
- declared window and full provenance.

The weighted local contributions reproduce the raw dynamic-programming optimum exactly. Multiple optimal paths may exist; deterministic tie handling does not imply unique latent correspondence.

## Optional Sakoe-Chiba sample-index band

~~~python
constrained = dynamic_time_warping_distance(
    path_a,
    path_b,
    step_pattern="symmetric2",
    normalize=True,
    window_radius=12,
)
~~~

Only cells satisfying \(|i-j|\le w\) are admissible. The radius is measured in sample indices, not milliseconds or seconds. A band too narrow to connect unequal-length endpoints raises explicitly.

No window is inferred or optimized from observed outcomes.

## Alignment visualization

~~~python
from eyetrajectoriespy import plot_dynamic_time_warping_alignment

ax = plot_dynamic_time_warping_alignment(audit)
~~~

The plot shows the audited monotone path in sequence-index space against the same-index diagonal. It is a diagnostic of the declared alignment, not proof that the matched samples are psychologically equivalent.

## Pairwise trajectory matrices

~~~python
matrix = pairwise_dynamic_time_warping_distances(
    gaze,
    dimensions=("x", "y"),
    step_pattern="symmetric2",
    normalize=True,
    window_radius=10,
)
~~~

For common-grid TrajectorySet data every curve has the same number of stored samples, but step pattern and normalization still alter the numerical estimand. dimensions=None uses all stored dimensions; pass spatial dimensions explicitly when that is the intended comparison.

## DTW versus L2 versus discrete Fréchet

| Method | Correspondence | Aggregation | Recorded timestamps used? | Main sensitivity |
|---|---|---|---|---|
| Functional L2 | same common-grid time | integrated squared difference | yes, through the common grid | trial-time mismatch |
| Discrete Fréchet | monotone sequence coupling | maximum local distance | no | worst coupled excursion |
| DTW symmetric1 | monotone sequence-index alignment | raw cumulative local cost | no | warping freedom and sequence/path length |
| DTW symmetric2 | monotone sequence-index alignment | weighted cumulative cost; optional N+M normalization | no | warping freedom, window, normalization |

These methods are complementary rather than interchangeable.

## Timing interpretation boundary

DTW can align away latency, dwell, or local progression-rate differences. If those differences are theoretically meaningful, retain a time-preserving analysis and treat DTW as a sensitivity or complementary geometry analysis rather than the sole outcome.

## No hidden analytical decisions

The implementation does not automatically:

- interpolate or delete missing samples;
- resample either trajectory;
- smooth coordinates;
- normalize coordinates or dimension weights;
- simplify paths;
- choose symmetric1 versus symmetric2;
- choose or widen a Sakoe-Chiba band;
- choose whether to normalize;
- rank specifications by the size of a downstream effect.

## Reporting

Use dynamic_time_warping_reporting_text() or report the same information manually: trajectory representation, dimensions/units, sequence lengths, local metric and dimension weights, step pattern, raw/normalized distance, normalization denominator when used, window radius, upstream preprocessing, and the fact that recorded timestamps did not enter the recurrence.

## Evidence basis

Sakoe and Chiba (1978) establish classic dynamic-programming alignment and global/path constraints. Giorgino (2009) distinguishes DTW step patterns and their normalization properties, including the N+M-normalizable symmetric2 pattern. Anderson et al. (2015) emphasize that scanpath comparison metrics capture different aspects of eye-movement behavior. Laborde et al. (2026) review DTW and discrete Fréchet as complementary elastic scanpath-comparison techniques and stress representation- and question-dependent method choice.

Version 0.34 does not claim novelty for these DTW variants. The contribution is an explicit, auditable scientific contract integrated with the package's no-hidden-decisions design.
