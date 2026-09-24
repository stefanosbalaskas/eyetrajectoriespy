# Dynamic time warping trajectory distance

Version 0.33 adds a transparent dynamic time warping (DTW) contract for comparing complete ordered gaze trajectories when local sample-index timing differences may be treated as nuisance variation.

## What DTW estimates

For ordered point sequences \(P=(p_1,\ldots,p_m)\) and \(Q=(q_1,\ldots,q_n)\), eyetrajectoriespy uses the same optional weighted Euclidean local distance as the discrete Fréchet layer,

$$
d_w(\mathbf p_i,\mathbf q_j)
=
\left[
\sum_r \omega_r(p_{ir}-q_{jr})^2
\right]^{1/2}.
$$

The cumulative recurrence is

$$
C_{i,j}
=
d_w(\mathbf p_i,\mathbf q_j)
+
\min
\left(
C_{i-1,j-1},
C_{i-1,j},
C_{i,j-1}
\right),
$$

with ordinary first-row and first-column cumulative boundary conditions. The reported distance is

$$
d_{\mathrm{DTW}}(P,Q)=C_{m,n}.
$$

This is the **unnormalized sum of local costs along the minimum-cost monotone path**. The package does not silently divide by path length or sequence length.

## Core API

~~~python
from eyetrajectoriespy import dynamic_time_warping_distance

distance = dynamic_time_warping_distance(path_a, path_b)
~~~

For an auditable alignment path:

~~~python
audit = dynamic_time_warping_distance(
    path_a,
    path_b,
    return_path=True,
)

print(audit.distance)
print(audit.path)
print(audit.local_distances)
print(audit.mean_local_distance)
~~~

The returned path starts at the first pair, ends at the last pair, preserves order, and advances by diagonal, vertical, or horizontal unit steps. More than one optimal path can exist. The implementation returns one deterministic optimum using tie order diagonal, then advance sequence A, then advance sequence B.

## Optional Sakoe-Chiba sample-index band

An explicit window can limit index displacement:

~~~python
constrained = dynamic_time_warping_distance(
    path_a,
    path_b,
    window_radius=12,
)
~~~

The admissible cells satisfy \(|i-j|\le w\), where \(w\) is window_radius. This is a **sample-index constraint**, not a physical-time constraint. If unequal sequence lengths make the endpoint unreachable under the declared radius, the function raises rather than widening the band silently.

No default band is inferred from the data. Unconstrained DTW and a constrained DTW answer different analysis questions and should not be mixed after inspecting outcomes.

## Pairwise trajectory matrices

~~~python
from eyetrajectoriespy import pairwise_dynamic_time_warping_distances

matrix = pairwise_dynamic_time_warping_distances(
    gaze,
    dimensions=("x", "y"),
    window_radius=10,
)
~~~

dimensions=None uses every stored functional dimension in its current order. For spatial scanpaths, pass the intended coordinate dimensions explicitly rather than accidentally including unrelated derived channels.

## DTW versus functional L2 versus discrete Fréchet

| Method | Correspondence | Aggregation | Recorded timestamps used? | Main sensitivity |
|---|---|---|---|---|
| Functional L2 | same common-grid time | integrated squared difference | yes, through the supplied common grid | trial-time mismatch |
| Discrete Fréchet | monotone sequence coupling | maximum local distance | no | worst coupled excursion |
| DTW | monotone sequence-index alignment | sum of local distances | no | cumulative alignment cost and warping freedom |

DTW and discrete Fréchet are therefore not interchangeable. They can even prefer different pairs of trajectories because Fréchet is a bottleneck metric while DTW accumulates local mismatch.

## Timing interpretation boundary

The function name follows standard DTW terminology, but this API does **not** consume the TrajectorySet time grid or arbitrary timestamp vectors. It aligns ordered sample indices. If two trajectories have different physical sampling rates, irregular timing, or scientifically meaningful latency, index warping can erase differences that should remain part of the estimand.

Use a time-preserving functional comparison, or make upstream time regularization explicit and defend it scientifically, when elapsed trial time is part of the question.

## No hidden preprocessing

The implementation does not automatically:

- interpolate missing samples;
- resample either trajectory;
- smooth coordinates;
- normalize coordinates or weights;
- simplify paths;
- remove outliers;
- choose a warping window;
- normalize cumulative cost by path length.

All supplied values must be finite.

## Interpretation and reporting

Report at minimum the trajectory representation, coordinate dimensions and units, sequence lengths, local metric, dimension weights, whether the path was unconstrained or windowed, the window radius in sample indices, the raw cumulative DTW cost, and all upstream preprocessing.

When latency is scientifically meaningful, report the complementary time-preserving analysis rather than describing DTW as preserving timing.

## Evidence basis

Sakoe and Chiba (1978) provide the classic dynamic-programming time-normalization framework and global path constraints. Anderson et al. (2015) emphasize that scanpath comparison measures quantify different aspects of eye-movement behavior and require method-specific interpretation. Laborde et al. (2026) review DTW and discrete Fréchet as established elastic scanpath-comparison methods and explicitly describe DTW as dynamic-programming alignment that tolerates local acceleration/deceleration.

Version 0.33 therefore does not claim novelty for DTW itself. The package contribution is the explicit scientific contract: deterministic path audit, dimension weighting, optional declared index band, provenance, and no hidden preprocessing or timing claims.

See the worked example, mathematical reference, assumptions, limitations, preregistration guidance, and reporting checklist.
