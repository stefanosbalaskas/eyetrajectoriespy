"""Experimental D4 design-utility contracts; no new stable namespace promises."""
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from eyetrajectoriespy.types import TrajectorySet
from eyetrajectoriespy.research import (
    compare_repeated_functional_groups,
    fit_functional_reliability,
    functional_reliability_frame,
    repeated_functional_contrast_frame,
    simulate_functional_study_power,
    validate_eyetracking_metadata,
)
from eyetrajectoriespy.research import power_planning


def repeated_fixture(n_subjects: int = 15, trials: int = 3):
    rng = np.random.default_rng(4124)
    time = np.linspace(0, 1, 15)
    values, participants, conditions, ids = [], [], [], []
    for i in range(n_subjects):
        shape = rng.normal(0, .6, 2)
        for condition in ("A", "B"):
            for trial in range(trials):
                curve = np.column_stack((
                    .4 + shape[0] * np.sin(np.pi * time),
                    .35 + shape[1] * np.cos(np.pi * time),
                ))
                if condition == "B":
                    curve[:, 0] += .3 * np.sin(np.pi * time)
                curve += rng.normal(0, .03, curve.shape)
                values.append(curve)
                ids.append(f"s{i}_{condition}_{trial}")
                participants.append(f"s{i}")
                conditions.append(condition)
    return (
        TrajectorySet(
            time=time, values=np.asarray(values), curve_ids=tuple(ids),
            dimension_names=("x", "y"), coordinate_system="normalized",
            time_unit="s",
            metadata=pd.DataFrame(
                {"participant_id": participants, "condition": conditions}
            ),
        ),
        participants, conditions,
    )


def test_paired_contrast_is_unitwise_and_reproducible():
    data, ids, conditions = repeated_fixture()
    res = compare_repeated_functional_groups(
        data, participants=ids, conditions=conditions,
        sign_symmetry_assumed=True, n_permutations=199, random_state=17,
    )
    again = compare_repeated_functional_groups(
        data, participants=ids, conditions=conditions,
        sign_symmetry_assumed=True, n_permutations=199, random_state=17,
    )
    assert res.n_participants == 15
    assert res.mean_paired_difference.shape == (15, 2)
    assert res.statistic == pytest.approx(again.statistic)
    np.testing.assert_array_equal(res.null_statistics, again.null_statistics)
    assert res.p_value_experimental == pytest.approx(again.p_value_experimental)
    assert res.p_value_experimental < .05
    assert len(repeated_functional_contrast_frame(res)) == 30
    assert res.evidence["not_qualified_population_inference"] is True


def test_paired_contrast_rejects_inapplicable_designs():
    data, participants, conditions = repeated_fixture(10, 2)
    kwargs = dict(trajectories=data, participants=participants,
                  conditions=conditions, n_permutations=99)
    with pytest.raises(ValueError, match="sign_symmetry"):
        compare_repeated_functional_groups(
            **kwargs, sign_symmetry_assumed=False
        )
    with pytest.raises(ValueError, match="period/order"):
        compare_repeated_functional_groups(
            **kwargs, sign_symmetry_assumed=True,
            order_or_period=["one"] * data.n_curves,
        )
    wrong = conditions.copy()
    wrong[0] = "B"
    with pytest.raises(ValueError, match="unequal condition"):
        compare_repeated_functional_groups(
            data, participants=participants, conditions=wrong,
            sign_symmetry_assumed=True, n_permutations=99,
        )


def test_functional_reliability_balanced_variance_components():
    data, _, _ = repeated_fixture(18, 4)
    keep = data.metadata["condition"] == "A"
    selected = data.subset(np.flatnonzero(keep))
    result = fit_functional_reliability(selected, condition_column="condition")
    assert result.n_participants == 18
    assert result.trials_per_participant == 4
    assert result.integrated_single_trial_reliability.shape == (2,)
    assert np.all(result.integrated_mean_trial_reliability >=
                  result.integrated_single_trial_reliability)
    assert np.all(result.pointwise_single_trial_reliability[np.isfinite(
        result.pointwise_single_trial_reliability)] >= 0)
    assert len(functional_reliability_frame(result)) == 30
    assert result.evidence["bootstrap_inference_qualified"] is False


def test_functional_reliability_rejects_confounded_and_unbalanced_inputs():
    data, _, _ = repeated_fixture(8, 2)
    with pytest.raises(ValueError, match="multi-condition"):
        fit_functional_reliability(data, condition_column="condition")
    selected = data.subset(np.flatnonzero(data.metadata["condition"] == "A"))
    with pytest.raises(ValueError, match="balanced"):
        fit_functional_reliability(selected.subset(range(15)))


def test_sparse_power_tool_invokes_actual_F1_function_and_retains_failures(monkeypatch):
    called = []
    def fake_test(data, groups, *, unit_ids, fit_kwargs,
                  n_permutations, random_state):
        called.append((data, groups, unit_ids, n_permutations))
        if len(called) == 2:
            raise ValueError("deliberate covariance fit failure")
        return SimpleNamespace(p_value=.03, statistic=1.7)
    monkeypatch.setattr(power_planning, "test_sparse_functional_groups", fake_test)
    result = simulate_functional_study_power(
        units_per_group=4, n_replicates=2, samples_per_trial=9,
        trials_per_participant=2, noise_sd=.015,
        effect_amplitude=.1, n_permutations=99, random_state=25,
    )
    assert len(called) == 4
    assert all(data.n_curves == 16 for data, _, _, _ in called)
    assert result.cases.status.tolist().count("failed") == 1
    assert result.summary.n_fit_failed.sum() == 1
    assert result.recommended_sample_size is None
    assert result.scientifically_qualified is False
    assert result.plan["not_fPASS_theoretical_power"] is True


def test_sparse_power_tool_rejects_unsupported_input():
    with pytest.raises(ValueError, match="four independent"):
        simulate_functional_study_power(units_per_group=3, n_replicates=2)
    with pytest.raises(ValueError, match="replicates"):
        simulate_functional_study_power(units_per_group=4, n_replicates=1)


def test_bids_coordinate_enum_contract():
    meta = {
        "Columns": ["timestamp", "x_coordinate", "y_coordinate"],
        "SamplingFrequency": 100, "StartTime": 0.0,
        "PhysioType": "eyetrack", "RecordedEye": "right",
        "SampleCoordinateSystem": "gaze-on-screen",
        "timestamp": {"Units": "ms"},
        "x_coordinate": {"Units": "pixel"},
        "y_coordinate": {"Units": "pixel"},
    }
    for v in ("eye-in-head", "gaze-in-world", "gaze-on-screen"):
        meta["SampleCoordinateSystem"] = v
        assert validate_eyetracking_metadata(meta)["validated_subset_only"] is True
    meta["SampleCoordinateSystem"] = "screen"
    with pytest.raises(ValueError, match="SampleCoordinateSystem"):
        validate_eyetracking_metadata(meta)
    meta["SampleCoordinateSystem"] = "custom"
    with pytest.raises(ValueError, match="Description"):
        validate_eyetracking_metadata(meta)
    meta["SampleCoordinateSystemDescription"] = "local participant-centred tracker rays"
    assert validate_eyetracking_metadata(meta)["validated_subset_only"] is True


def test_exact_session_and_device_measurement_linkage():
    from eyetrajectoriespy.research import (
        audit_gaze_measurement_quality, link_gaze_validation_sessions,
    )
    data, _, _ = repeated_fixture(8, 2)
    selected = data.subset(range(8))
    metadata = selected.metadata.reset_index(drop=True).copy()
    metadata["session_id"] = "session1"
    metadata["device_id"] = "tracker_A"
    selected = TrajectorySet(
        time=selected.time, values=selected.values,
        curve_ids=selected.curve_ids,
        dimension_names=selected.dimension_names,
        metadata=metadata, coordinate_system="normalized",
        time_unit="s",
    )
    quality = pd.DataFrame({
        "participant_id": metadata.participant_id.unique(),
        "validation_session_id": "session1",
        "device_id": "tracker_A",
        "accuracy_deg": .32,
        "precision_deg": .21,
        "validation_points": 5,
        "evidence_source": "measured_target_check",
    })
    audited = audit_gaze_measurement_quality(
        selected, validation_records=quality,
    )
    matched = link_gaze_validation_sessions(
        selected, audited, require_all=True,
    )
    assert len(matched) == selected.n_curves
    assert (matched.link_status == "exact_identifier_match").all()
    assert not matched.calibration_time_proximity_verified.any()
    assert not matched.calibration_accuracy_from_free_viewing.any()
    corrupted = quality.copy()
    corrupted.loc[0, "device_id"] = "other_tracker"
    audited_wrong = audit_gaze_measurement_quality(
        selected, validation_records=corrupted,
    )
    with pytest.raises(ValueError, match="no exact"):
        link_gaze_validation_sessions(
            selected, audited_wrong, require_all=True,
        )


def test_bids_dataset_audit_checks_eye_labels_and_screen_provenance(tmp_path):
    import json
    from eyetrajectoriespy.research import audit_bids_eyetracking_dataset
    run = tmp_path / "sub-01" / "func"
    run.mkdir(parents=True)
    prefix = "sub-01_task-search"
    event_metadata = {
        "StimulusPresentation": {
            "ScreenDistance": .6, "ScreenOrigin": ["top", "left"],
            "ScreenResolution": [1920, 1080], "ScreenSize": [.51, .29],
        },
    }
    (run / (prefix + "_events.json")).write_text(json.dumps(event_metadata))
    for recording, eye in (("eye1", "left"), ("eye2", "right")):
        file = run / f"{prefix}_recording-{recording}_physio.tsv.gz"
        pd.DataFrame([[0, 100, 200], [10, 101, 201]]).to_csv(
            file, sep="\t", index=False, header=False, compression="gzip"
        )
        metadata = {
            "Columns": ["timestamp", "x_coordinate", "y_coordinate"],
            "SamplingFrequency": 100, "StartTime": 0,
            "PhysioType": "eyetrack", "RecordedEye": eye,
            "SampleCoordinateSystem": "gaze-on-screen",
            "timestamp": {"Units": "ms"},
            "x_coordinate": {"Units": "pixel"},
            "y_coordinate": {"Units": "pixel"},
        }
        file.with_name(file.name.removesuffix(".tsv.gz") + ".json").write_text(
            json.dumps(metadata)
        )
    result = audit_bids_eyetracking_dataset(tmp_path)
    assert len(result.files) == 2
    assert result.group_checks.group_valid.all()
    assert result.provenance["official_bids_validator_executed"] is False
    (run / (prefix + "_events.json")).unlink()
    checked = audit_bids_eyetracking_dataset(tmp_path)
    assert not checked.group_checks.group_valid.any()
    assert checked.files.reason.str.contains("ScreenDistance").all()
