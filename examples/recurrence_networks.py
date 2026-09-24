"""Sparse recurrence-network example."""

import matplotlib.pyplot as plt

from eyetrajectoriespy import (
    plot_recurrence_network_degree,
    recurrence_matrix,
    recurrence_network,
    recurrence_network_node_frame,
    recurrence_network_reporting_text,
    recurrence_network_summary_frame,
    simulate_planar_trajectories,
)


gaze = simulate_planar_trajectories(
    n_participants=1,
    trials_per_participant=1,
    n_time=120,
    random_state=41,
)

rec = recurrence_matrix(
    gaze,
    curve=0,
    dimensions=("x", "y"),
    target_recurrence_rate=0.08,
    theiler_window=5,
)

net = recurrence_network(rec)
nodes = recurrence_network_node_frame(net)
summary = recurrence_network_summary_frame(net)

assert net.n_nodes == gaze.n_time
assert net.edge_count > 0
assert nodes.shape[0] == gaze.n_time
assert summary.shape[0] == 1

print(summary.to_string(index=False))
print(recurrence_network_reporting_text(net))

ax = plot_recurrence_network_degree(net)
plt.close(ax.figure)
