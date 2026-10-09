# Three research case studies — synthetic, non-inferential

All demonstrations use deterministic synthetic or explicitly prepared recordings. They are executable starting points on **research 1.2 development source**, not stable 1.1.0, and do **not** establish calibrated p-values.

## 1. Sparse independent groups

```python
from eyetrajectoriespy.research import simulate_functional_study_power

pilot = simulate_functional_study_power(
    units_per_group=8,
    n_replicates=10,
    samples_per_trial=19,
    trials_per_participant=1,
    effect_amplitude=.08,
    n_permutations=199,
    random_state=2026,
)
print(pilot.summary)
assert not pilot.scientifically_qualified
assert pilot.recommended_sample_size is None
```

The native test is refitted for both null and effect scenarios; a failed covariance fit is retained, not deleted from the simulation record. Ten replicates do not suffice for precision.

## 2. Participant repeatability and paired conditions

Use a common-grid **TrajectorySet** with a metadata row per trial (participant_id and condition). First stratify to one homogeneous condition; compute balanced trial reliability; only then consider a within-participant contrast on the complete paired design.

```python
from eyetrajectoriespy.research import (
    fit_functional_reliability, compare_repeated_functional_groups,
)
# reliability = fit_functional_reliability(one_condition, condition_column="condition")
# paired = compare_repeated_functional_groups(
#     all_conditions,
#     participants=all_conditions.metadata.participant_id,
#     conditions=all_conditions.metadata.condition,
#     sign_symmetry_assumed=True, n_permutations=999, random_state=17,
# )
```

No period/carryover inference is provided; participant, not individual trial, is the resampling unit.

## 3. BIDS ingestion and quality linkage

```python
from eyetrajectoriespy.research import (
    audit_bids_eyetracking_dataset,
    from_bids_eyetracking,
    summarize_gaze_validation_targets,
    audit_gaze_measurement_quality,
    link_gaze_validation_sessions,
)
# audit = audit_bids_eyetracking_dataset("study_bids/")
# gaze = from_bids_eyetracking("stream_physio.tsv.gz", sidecar="stream_physio.json")
# measured = summarize_gaze_validation_targets(reference_pairs, evidence_source="log")
# quality = audit_gaze_measurement_quality(gaze, validation_records=measured)
# matched = link_gaze_validation_sessions(gaze, quality, require_all=True)
```

The link requires genuinely matching session and device IDs in metadata. No time proximity, drift correction, eye-clock reconciliation, or official BIDS certification is inferred.

[Scientific figure gallery](f1-f6-gallery.md) · [Evidence ledger](research-evidence-matrix.md)
