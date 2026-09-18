# Registration and phase

Registration separates **when** a trajectory traverses a pattern from **what spatial pattern** is traversed.

If one participant inspects a source at 400 ms and another at 1,400 ms, blind registration can erase the experimental effect.

`register_to_landmarks()` therefore returns the registered trajectories, originals, warping functions, observed/reference landmarks, and phase summaries.

```python
registered = register_to_landmarks(
    gaze,
    observed_landmarks=inspection_times,
    reference_landmarks=np.array([1.0]),
)
```

## Recommended pattern

1. Fit the unregistered analysis.
2. Register only when scientifically justified.
3. Plot the warpings.
4. Analyze phase or landmark times when timing matters.
5. Report whether conclusions differ before and after registration.

!!! danger
    Registered curves do not preserve latency. They intentionally alter timing to align selected features.
