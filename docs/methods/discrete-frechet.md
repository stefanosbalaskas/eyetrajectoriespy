# Discrete Fréchet trajectory distance

Version 0.32 adds an order-preserving elastic trajectory distance without requiring common-time correspondence.

## Functional L2 versus discrete Fréchet

Integrated functional L2 compares functions at the same trial-time grid. Discrete Fréchet compares ordered point sequences and permits one sequence to advance while the other temporarily holds its index.

For point sequences \(P=(p_1,\ldots,p_m)\) and \(Q=(q_1,\ldots,q_n)\), with weighted Euclidean local distance

$$
d_w(p_i,q_j)
=
\left[
\sum_r \omega_r(p_{ir}-q_{jr})^2
\right]^{1/2},
$$

the implemented recurrence is

$$
D_{i,j}
=
\max
\left\{
d_w(p_i,q_j),
\min(D_{i-1,j},D_{i-1,j-1},D_{i,j-1})
\right\},
$$

and

$$
\delta_{dF}(P,Q)=D_{m,n}.
$$

## Core API

~~~python
distance = discrete_frechet_distance(path_a, path_b)
~~~

The paths may contain different numbers of points but must share the same dimensionality.

For an auditable coupling:

~~~python
result = discrete_frechet_distance(
    path_a,
    path_b,
    return_coupling=True,
)
~~~

The returned coupling starts at the first points, ends at the last points, never backtracks, and reaches a maximum coupled local distance equal to the reported Fréchet distance. Multiple optimal couplings can exist; the package returns one deterministic optimum and records the tie order in provenance.

## No elapsed-time correspondence

The recurrence uses sequence order only. Original timestamps, dwell duration, latency, and physical speed are not used. Therefore discrete Fréchet should not replace a time-preserving analysis when latency itself is scientifically meaningful.

## No hidden preprocessing

The implementation does not interpolate, resample, smooth, simplify, normalize, or remove outliers. All supplied points enter the dynamic program.

Optional dimension_weights define the weighted Euclidean local metric directly and are not normalized.

## Pairwise trajectory matrices

~~~python
matrix = pairwise_discrete_frechet_distances(
    gaze,
    dimensions=("x", "y"),
)
~~~

With dimensions=None, all stored dimensions are used in their current order. For a specifically spatial comparison, pass the intended coordinate dimensions explicitly.

## Interpretation

Discrete Fréchet is a bottleneck distance. One large local deviation can dominate the final result.

Recent scanpath-methodology reviews treat discrete Fréchet as an established elastic comparison method. The 0.32 contribution is therefore not novelty of the metric itself, but its explicit coupling, coordinate-weighting, provenance, and no-hidden-preprocessing contract inside the continuous-trajectory package.

Report the coordinate representation, dimensions and units, point counts, any dimension weights, upstream preprocessing, and the fact that order rather than elapsed time defined correspondence.

See the worked example, mathematical reference, limitations, and preregistration guidance.
