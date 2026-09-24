# Joint recurrence of gaze and pupil dynamics

This example combines two synchronized subsystem recurrence plots without
forcing the systems into one common state vector.

## Create synchronized systems

~~~python
import numpy as np

from eyetrajectoriespy import TrajectorySet

time = np.arange(120) * 0.02
phase = 2.0 * np.pi * time / 0.50

gaze = TrajectorySet(
    time=time,
    values=np.column_stack([
        np.sin(phase),
        np.cos(phase),
    ])[None, :, :],
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
~~~

## Build separate recurrence contracts

~~~python
from eyetrajectoriespy import recurrence_matrix

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
~~~

The two systems use different dimensions, metrics, and target recurrence
rates, while preserving the same time grid and Theiler exclusion.

## Intersect the recurrence events

~~~python
from eyetrajectoriespy import joint_recurrence_matrix

joint = joint_recurrence_matrix(
    (gaze_rec, pupil_rec),
    labels=("gaze", "pupil"),
)

print(joint.joint_recurrence_rate)
~~~

## Audit the component definitions

~~~python
from eyetrajectoriespy import joint_recurrence_component_frame

print(joint_recurrence_component_frame(joint))
~~~

## Compute JRQA

~~~python
from eyetrajectoriespy import joint_rqa_metrics

jrqa = joint_rqa_metrics(joint)
print(jrqa.determinism)
print(jrqa.laminarity)
~~~

## Visualize

~~~python
from eyetrajectoriespy import plot_joint_recurrence

ax = plot_joint_recurrence(joint)
~~~

## Reporting helper

~~~python
from eyetrajectoriespy import joint_recurrence_reporting_text

print(joint_recurrence_reporting_text(joint, jrqa))
~~~

The result means that the two declared systems recur simultaneously at those
time pairs. It does not mean that their state vectors are close to each other,
nor does it identify direction or causal coupling.

The executable counterpart is `examples/joint_recurrence.py`.
