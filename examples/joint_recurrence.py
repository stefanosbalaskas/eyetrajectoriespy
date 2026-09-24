"""Synchronized joint recurrence example."""

import matplotlib.pyplot as plt
import numpy as np

from eyetrajectoriespy import (
    TrajectorySet,
    joint_recurrence_component_frame,
    joint_recurrence_matrix,
    joint_recurrence_reporting_text,
    joint_rqa_metrics,
    plot_joint_recurrence,
    recurrence_matrix,
)


time = np.arange(120, dtype=float) * 0.02
phase = 2.0 * np.pi * time / 0.50

gaze = TrajectorySet(
    time=time,
    values=np.column_stack(
        [np.sin(phase), np.cos(phase)]
    )[None, :, :],
    curve_ids=("trial_01",),
    dimension_names=("x", "y"),
    coordinate_system="unknown",
    time_unit="s",
)

pupil = TrajectorySet(
    time=time,
    values=(
        1.0
        + 0.15 * np.sin(phase)
        + 0.05 * np.sin(2.0 * phase)
    )[None, :, None],
    curve_ids=("trial_01",),
    dimension_names=("pupil",),
    coordinate_system="unknown",
    time_unit="s",
)

gaze_rec = recurrence_matrix(
    gaze,
    curve=0,
    dimensions=("x", "y"),
    target_recurrence_rate=0.10,
    metric="euclidean",
    theiler_window=3,
)

pupil_rec = recurrence_matrix(
    pupil,
    curve=0,
    dimensions=("pupil",),
    target_recurrence_rate=0.15,
    metric="cityblock",
    theiler_window=3,
)

joint = joint_recurrence_matrix(
    (gaze_rec, pupil_rec),
    labels=("gaze", "pupil"),
)
jrqa = joint_rqa_metrics(joint)

assert joint.joint_recurrence_rate <= gaze_rec.achieved_recurrence_rate + 1e-12
assert joint.joint_recurrence_rate <= pupil_rec.achieved_recurrence_rate + 1e-12
assert jrqa.recurrence_rate == joint.joint_recurrence_rate

print(joint_recurrence_component_frame(joint).to_string(index=False))
print(joint_recurrence_reporting_text(joint, jrqa))

ax = plot_joint_recurrence(joint)
plt.close(ax.figure)
