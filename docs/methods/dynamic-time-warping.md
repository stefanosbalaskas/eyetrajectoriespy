# Dynamic time warping trajectory cost

Version 0.33 adds unconstrained symmetric three-step dynamic time warping for ordered multivariate trajectories.

## Why the API says cost

The implementation reports the raw cumulative sum of local distances along the optimal warping path.

It is intentionally named dynamic_time_warping_cost() rather than “distance” because standard DTW does not satisfy all metric axioms and published software differs in step patterns, path normalization, and global constraints.

## Recurrence

For ordered point sequences \(P=(p_1,\ldots,p_m)\) and \(Q=(q_1,\ldots,q_n)\), with weighted Euclidean local distance

$$
d_w(p_i,q_j)
=
\left[
\sum_r \omega_r(p_{ir}-q_{jr})^2
\right]^{1/2},
$$

the implemented symmetric recurrence is

$$
C_{i,j}
=
d_w(p_i,q_j)
+
\min
\left(
C_{i-1,j},
C_{i-1,j-1},
C_{i,j-1}
\right),
$$

with cumulative first-row and first-column costs and

$$
\operatorname{DTWcost}(P,Q)=C_{m,n}.
$$

## API

~~~python
cost = dynamic_time_warping_cost(path_a, path_b)
~~~

For an auditable warping path:

~~~python
result = dynamic_time_warping_cost(
    path_a,
    path_b,
    return_path=True,
)
~~~

The returned path is monotone, starts at the first points, ends at the last points, and has local distances whose sum equals the reported raw cost.

Multiple optimal paths can exist. The package returns one deterministic optimum using the tie order diagonal, advance a, advance b.

## No path-length normalization

Version 0.33 does not divide cumulative cost by warping-path length or by either sequence length.

That choice is deliberate because normalized DTW variants define different estimands. If a normalized cost is scientifically required, it should be added under an explicit future contract rather than silently changing the primary result.

## No global warping window

Version 0.33 implements unconstrained symmetric DTW only.

It does not silently impose a Sakoe–Chiba band, Itakura parallelogram, slope constraint, or maximum consecutive horizontal/vertical run.

Those constraints can materially change the alignment and require their own declared contract.

## Time semantics

Despite the name, the implementation does not use observed timestamp values. It uses point order and permits local index stretching/compression.

Therefore DTW should not be interpreted as preserving response latency, dwell time, or physical movement speed.

If latency is part of the scientific question, use a time-preserving analysis alongside or instead of DTW.

## No hidden preprocessing

The implementation does not interpolate, resample, smooth, normalize coordinates, simplify paths, or remove outliers.

Optional dimension_weights define the local weighted Euclidean cost directly and are not normalized.

## DTW versus discrete Fréchet

Both preserve order and permit elastic progression.

Discrete Fréchet minimizes the largest local separation along a coupling.

DTW minimizes the sum of local distances along a warping path.

For three paired unit deviations, discrete Fréchet can equal 1 while raw DTW cost equals 3.

Neither method should be called universally better; they answer different similarity questions.

## Pairwise matrices

~~~python
matrix = pairwise_dynamic_time_warping_costs(
    gaze,
    dimensions=("x", "y"),
)
~~~

With dimensions=None, all stored dimensions are used.

## Reporting

Report the trajectory representation, dimensions and units, sequence lengths, dimension weights, step pattern, normalization rule, global constraint rule, upstream preprocessing, and whether the warping path was inspected.

For version 0.33, report: symmetric three-step recurrence, raw unnormalized cumulative cost, and no global window/slope constraint.

See the worked example, mathematical reference, limitations, and preregistration guidance.
