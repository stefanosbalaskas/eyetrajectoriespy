# Quick start

## 1. Build a canonical trajectory set

```python
from eyetrajectoriespy import from_long_dataframe

gaze = from_long_dataframe(
    samples,
    curve_columns=["participant_id", "trial_id"],
    time_column="time_s",
    value_columns=["x", "y"],
    metadata_columns=["condition", "stimulus_id"],
    coordinate_system="normalized",
    time_unit="s",
)
```

The constructor does **not** smooth, interpolate, normalize time, or average duplicate timestamps.

## 2. Inspect the representation

```python
from eyetrajectoriespy import summarise_trajectory_set
print(summarise_trajectory_set(gaze))
```

## 3. Fit joint x/y MFPCA

```python
from eyetrajectoriespy import fit_mfpca, summarise_fpca

fit = fit_mfpca(gaze, n_components=0.95, scaling="dimension_sd")
print(summarise_fpca(fit))
```

## 4. Interpret functions, not only scores

```python
from eyetrajectoriespy import plot_fpca_component
plot_fpca_component(fit, component=0, dimension="x")
plot_fpca_component(fit, component=0, dimension="y")
```

!!! warning
    Do not call an FPC “attention,” “verification,” or another psychological construct solely because its geometry looks plausible. Interpret against the experimental design and, when possible, validate against external behavior.


## 5. Validate before labeling components

For repeated trials, use participant-level bootstrap:

    stability = bootstrap_fpca_stability(
        gaze,
        n_bootstrap=200,
        n_components=3,
        scaling="dimension_sd",
        resample_unit="participant",
        participant_column="participant_id",
        random_state=2026,
    )

    print(summarise_fpca_stability(stability))

Use the stability result to qualify component interpretation rather than to create a new significance test.

## If your trials are irregularly sampled

Do not force them through <code>from_long_dataframe()</code>. Start with <code>from_irregular_long_dataframe_native()</code>, inspect the native sampling, and only then choose the common-grid projection.
