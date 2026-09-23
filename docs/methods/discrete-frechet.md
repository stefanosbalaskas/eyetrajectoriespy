# Discrete Fréchet trajectory distance

Version 0.32 adds an order-preserving path distance for sampled trajectories.

The public APIs are:

- \`discrete_frechet_distance()\`;
- \`pairwise_discrete_frechet_distances()\`.

The name is intentionally explicit: this is the **discrete Fréchet distance**, not the continuous Fréchet distance between polygonal curves.

## Why this differs from functional L2

The existing functional distance compares two functions at the same observed trial time:

\[
d_{L^2}(A,B)
=
\left[
\int
\|A(t)-B(t)\|^2\,dt
\right]^{1/2}.
\]

That is appropriate when common-time correspondence is part of the scientific question.

Discrete Fréchet instead compares two ordered sampled paths

\[
P=(\mathbf p_1,\ldots,\mathbf p_m),
\qquad
Q=(\mathbf q_1,\ldots,\mathbf q_n)
\]

through a monotone coupling of sample indices.

One path may advance while the other remains at its current sample, but neither path can move backward in its sample order.

The distance is the smallest possible maximum paired-point separation under those monotone couplings.

## Point metric

The package uses a fixed weighted-Euclidean point metric,

\[
d_{\boldsymbol\omega}(\mathbf p_i,\mathbf q_j)
=
\left[
\sum_{d=1}^{D}
\omega_d
(p_{id}-q_{jd})^2
\right]^{1/2}.
\]

All dimension weights must be finite and strictly positive.

The package does not:

- standardize channels;
- scale by sample variance;
- normalize screen coordinates;
- choose weights automatically;
- infer a spatial metric from dimension names.

If dimensions use different or non-commensurate units, choose a scientifically meaningful representation upstream or declare the weights explicitly.

## Dynamic-programming recurrence

For interior cells,

\[
C_{ij}
=
\max
\left\{
d_{\boldsymbol\omega}(\mathbf p_i,\mathbf q_j),
\min(C_{i-1,j},C_{i-1,j-1},C_{i,j-1})
\right\}.
\]

The final discrete Fréchet distance is

\[
\delta_{dF}(P,Q)=C_{mn}.
\]

Boundary cells follow the same monotone traversal logic from the first pair of samples.

## Timestamps are not part of the distance

\`discrete_frechet_distance()\` accepts sampled spatial/state arrays, not timestamps.

\`pairwise_discrete_frechet_distances()\` accepts a \`TrajectorySet\`, but its common time grid is **not included** in the Fréchet point metric.

Therefore:

> a small discrete Fréchet distance does not imply that two trajectories reached the same locations at the same trial times.

Use integrated functional \(L_2\), or another explicitly time-aware analysis, when latency or common-time correspondence is scientifically meaningful.

## Variable-length paths

The low-level API supports different numbers of sampled points:

~~~python
import numpy as np
from eyetrajectoriespy import discrete_frechet_distance

a = np.array([[0.0, 0.0], [1.0, 0.0], [2.0, 0.0]])
b = np.array([[0.0, 0.0], [0.0, 0.0], [1.0, 0.0], [2.0, 0.0]])

distance = discrete_frechet_distance(a, b)
~~~

Here the repeated first point in \`b\` does not force a different geometric path distance.

The pairwise \`TrajectorySet\` API naturally uses the package's common-grid representation, but the monotone coupling remains free to hold one sampled path while advancing the other.

## Dimension selection

~~~python
matrix = pairwise_discrete_frechet_distances(
    gaze,
    dimensions=("x", "y"),
)
~~~

If \`dimensions=None\`, all functional dimensions in the \`TrajectorySet\` are compared.

Use explicit dimension selection when the object contains additional channels that are not part of the intended path geometry.

## Memory and runtime

For paths with \(m\) and \(n\) points, the implementation has:

\[
O(mn)
\]

runtime and uses rolling dynamic-programming rows with

\[
O(\min(m,n))
\]

auxiliary memory.

It deliberately does **not** allocate a dense \(m\times n\) floating-point distance matrix.

This does not make very long pairwise analyses cheap. For \(K\) trajectories of length \(M\), a complete pairwise matrix still requires roughly \(O(K^2M^2)\) point-comparison work.

Downsampling, simplification, or segmentation can materially change the discrete path and therefore must not be introduced silently as a performance shortcut.

## Interpretation

Discrete Fréchet is useful when the scientific object is the **ordered spatial route** and exact common-time correspondence is not the primary estimand.

It is less appropriate when:

- onset/latency differences are scientifically central;
- pauses and dwell timing are part of the effect;
- temporal synchronization itself is the target;
- preprocessing would need to heavily alter the sampled curve merely to make computation feasible.

## Eye-tracking context

The eye-tracking literature already uses Fréchet-style and dynamic-time-warping comparisons for scanpaths. A recent methodological review treats discrete Fréchet as an established order-sensitive scanpath comparison with distinct properties and limitations relative to DTW.

The package does not claim novelty for Fréchet distance itself. The 0.32 contribution is a fail-closed, explicitly weighted, memory-bounded implementation integrated with the package's continuous-trajectory contracts.

## Reporting

Report:

- whether the analysis used discrete rather than continuous Fréchet;
- trajectory dimensions;
- coordinate system and units;
- dimension weights;
- sampling/preprocessing before comparison;
- whether paths had equal or unequal numbers of points;
- that timestamps were not included in the distance;
- any upstream simplification or downsampling;
- the role of Fréchet relative to common-time \(L_2\) or other distances;
- pairwise computational scope if a large distance matrix was formed.

See the [worked example](../examples/discrete-frechet.md), [mathematical reference](mathematical-reference.md#discrete-frechet), [limitations](limitations.md), and [reporting checklist](reporting.md).
