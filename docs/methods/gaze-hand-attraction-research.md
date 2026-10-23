# Experimental gaze and hand attraction trajectories (unreleased)

**Status:** private research implementation; no stable/root export, no automatic promotion to 1.2, no scientific qualification of attention or causal attraction.

The September 2026 VR continuous-trajectory briefing motivates preserving the time course of gaze and hand movements rather than reducing all evidence to reaction-time endpoints.

```python
from eyetrajectoriespy._gaze_hand_attraction_research import describe_gaze_hand_attraction

# One synchronized, common-unit, common-coordinate-frame table per participant/trial.
proximity = describe_gaze_hand_attraction(
    frame, shared_clock_certified=True,
)
```

For 3D gaze/hand positions `q(t)`, target `T(t)` and distractor `D(t)`, the returned signed relative target proximity is

```text
P_q(t) = (||q(t)-D(t)|| - ||q(t)-T(t)||) /
         (||q(t)-D(t)|| + ||q(t)-T(t)||)
```

The score is between −1 and +1; +1 is at the target, −1 at the distractor, and 0 is equidistant. It provides separate gaze and hand trajectories, leaving functional smoothing, regression, participant-cluster inference, and time-locking to explicitly selected later models.

It does **not** align cameras, calibrate 3D space, reconstruct occluded coordinates, infer attention, or claim clinical/motor validity. A caller assertion of shared clock is not itself external synchronization evidence. Qualification should use known-truth 3D trajectories, clock perturbations, and task data with objective target/distractor definitions.

See [continuous trajectory representations](../guides/derived-functions.md) and [functional simulation](../guides/functional-simulation.md).
