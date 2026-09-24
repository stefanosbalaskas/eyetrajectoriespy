# Recurrence networks

Version 0.40 adds a sparse recurrence-network layer on top of the existing
auto-recurrence contract.

A recurrence network treats recurrence states as graph nodes and retained
recurrence pairs as undirected edges. It is therefore a graph representation
of the geometry induced by one already-declared recurrence analysis.

## Construct the recurrence first

~~~python
from eyetrajectoriespy import recurrence_matrix

recurrence = recurrence_matrix(
    embedded,
    curve=0,
    target_recurrence_rate=0.05,
    metric="euclidean",
    theiler_window=10,
)
~~~

All recurrence-network results remain conditional on this upstream state
representation, metric, threshold policy, and Theiler exclusion.

## Build the network

~~~python
from eyetrajectoriespy import recurrence_network

network = recurrence_network(recurrence)
~~~

The adjacency matrix is exactly the sparse symmetric recurrence matrix, with
the already-excluded main diagonal and Theiler band retained.

Version 0.40 does not:

- change the recurrence threshold;
- restore temporally near edges excluded by the Theiler window;
- add edge weights;
- optimize communities;
- estimate a graph embedding;
- infer a fractal or attractor dimension automatically;
- materialize a dense adjacency matrix.

## Node degree

For node (i),

$$
k_i = \sum_j A_{ij}.
$$

Normalized degree is (k_i/(N-1)). Degree describes how many other retained
states fall within the declared recurrence neighborhood of the state at that
time index.

## Local clustering

If (T_i) is the number of triangles incident to node (i),

$$
C_i = \frac{2T_i}{k_i(k_i-1)}.
$$

Nodes with degree below two receive local clustering 0 by explicit graph
convention. This convention is recorded in provenance.

## Global transitivity

$$
\mathcal T = \frac{3N_{\triangle}}{N_{\mathrm{triples}}}.
$$

If the network has no connected triples, transitivity is undefined and is
returned as `NaN`, not silently replaced by zero.

## Graph density is not always recurrence rate

Standard graph density is

$$
\rho_G = \frac{2E}{N(N-1)}.
$$

This denominator uses all unordered node pairs. By contrast, the package
auto-recurrence rate can exclude temporally near pairs through the Theiler
window. Therefore `graph_density` and the source `achieved_recurrence_rate`
can differ even though both are based on the same retained edges.

When target-RR mode is used, recurrence density is partly controlled by
construction. Network density should not then be treated as an unconstrained
scientific outcome.

## Connected components

The result reports:

- number of connected components;
- largest-component fraction;
- isolated-node fraction.

Version 0.40 deliberately avoids all-pairs shortest-path summaries because
those can require dense or quadratic memory and become ambiguous on
disconnected networks without an explicit component policy.

## Node-level table

~~~python
from eyetrajectoriespy import recurrence_network_node_frame

nodes = recurrence_network_node_frame(network)
~~~

The table retains state index, source time, degree, normalized degree, local
clustering, connected-component label, and component size.

## Global summary

~~~python
from eyetrajectoriespy import recurrence_network_summary_frame

summary = recurrence_network_summary_frame(network)
~~~

## Plot

~~~python
from eyetrajectoriespy import plot_recurrence_network_degree

ax = plot_recurrence_network_degree(network)
~~~

The default plot shows normalized degree across the original state index. It
does not invent a force-directed graph layout whose geometry could be
misread as the original phase-space geometry.

## Interpretation

Recurrence networks are commonly interpreted as geometric graphs induced by
recurrence neighborhoods in phase space. Donner et al. (2010) and subsequent
reviews emphasize that graph quantities remain tied to the recurrence
construction and can acquire dynamical interpretations only under additional
conditions.

For behavioral gaze data, an appropriate statement is:

> The declared recurrence relation induced a network with high local
> clustering and a large connected component.

Do not automatically translate this into:

- proof of deterministic chaos;
- proof of a low-dimensional attractor;
- a causal statement;
- a universal subject trait;
- evidence that one recurrence threshold is optimal.

## Evidence basis

Marwan et al. (2009) introduced the complex-network view of recurrence
analysis; Donner et al. (2010) developed recurrence networks as a nonlinear
time-series paradigm and separately discussed ambiguities in their
construction and interpretation. Donner et al. (2011) reviewed
recurrence-based time-series analysis using complex-network methods, and
Marwan and Kraemer (2023) review recurrence networks among modern recurrence
analysis developments.

Version 0.40 does not claim methodological novelty for recurrence networks.
The package contribution is a sparse, provenance-preserving implementation
that refuses hidden threshold tuning and keeps graph density distinct from
Theiler-conditioned recurrence rate.
