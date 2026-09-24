# Recurrence-network topology from a gaze-state recurrence plot

This example converts one already-declared auto-recurrence matrix into a
sparse undirected network.

## Simulate a trajectory

~~~python
from eyetrajectoriespy import simulate_planar_trajectories

gaze = simulate_planar_trajectories(
    n_participants=2,
    trials_per_participant=1,
    n_time=120,
    random_state=41,
)
~~~

## Build the recurrence matrix

~~~python
from eyetrajectoriespy import recurrence_matrix

rec = recurrence_matrix(
    gaze,
    curve=0,
    dimensions=("x", "y"),
    target_recurrence_rate=0.08,
    theiler_window=5,
)
~~~

## Convert to a network

~~~python
from eyetrajectoriespy import recurrence_network

net = recurrence_network(rec)
print(net.graph_density)
print(net.transitivity)
print(net.largest_component_fraction)
~~~

## Inspect node-level topology

~~~python
from eyetrajectoriespy import recurrence_network_node_frame

node_table = recurrence_network_node_frame(net)
print(node_table.head())
~~~

## Inspect global topology

~~~python
from eyetrajectoriespy import recurrence_network_summary_frame

print(recurrence_network_summary_frame(net))
~~~

## Plot degree over the original state sequence

~~~python
from eyetrajectoriespy import plot_recurrence_network_degree

ax = plot_recurrence_network_degree(net)
~~~

## Reporting helper

~~~python
from eyetrajectoriespy import recurrence_network_reporting_text

print(recurrence_network_reporting_text(net))
~~~

Because a target recurrence rate was used, network topology is conditional on
that density-control rule. The graph is a representation of the declared
recurrence geometry, not an automatically discovered causal network.

The executable counterpart is `examples/recurrence_networks.py`.
