# Worked example: repeated-trial multilevel FPCA

```python
from eyetrajectoriespy import fit_multilevel_fpca, simulate_planar_trajectories

gaze = simulate_planar_trajectories(
    n_participants=25,
    trials_per_participant=8,
    random_state=11,
)

fit = fit_multilevel_fpca(
    gaze,
    participant_column="participant_id",
    participant_components=0.90,
    trial_components=0.90,
    scaling="dimension_sd",
)
```

Use `participant_scores` for stable participant-level trajectory modes and `trial_scores` for within-participant deviations.

!!! note
    Trial-level scores remain repeated observations. Do not treat them as independent participant-level cases downstream.
