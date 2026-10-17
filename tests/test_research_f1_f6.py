"""Experimental F1-F6 contract smoke tests; not scientific method qualification."""
import json
import numpy as np
import pandas as pd
import pytest

from eyetrajectoriespy import TrajectorySet, IrregularTrajectorySet
from eyetrajectoriespy.research import (
    audit_gaze_measurement_quality, measurement_quality_reporting_frame,
    validate_eyetracking_metadata, from_bids_eyetracking,
    project_simplex, compare_aoi_functional_geometries,
    fit_weighted_mfpca, reconstruct_weighted_mfpca, weighted_component_geometry,
    detect_ordered_functional_changepoint,
    test_sparse_functional_groups as sparse_group_test,
    functional_group_contrast_frame,
)


def dense(n=16, p=2):
    rng = np.random.default_rng(421)
    t = np.linspace(0, 1, 25)
    values = rng.normal(0, .01, (n, len(t), p))
    values[:, :, 0] += .45 + .05 * np.sin(np.pi * t)
    values[:, :, 1] += .52 + .05 * np.cos(np.pi * t)
    return TrajectorySet(time=t, values=values,
                         curve_ids=tuple(f"c{i}" for i in range(n)),
                         dimension_names=("x", "y"),
                         metadata=pd.DataFrame({"participant_id": [f"P{i}" for i in range(n)]}),
                         coordinate_system="normalized", time_unit="s")


def test_quality_missing_is_not_zero_accuracy():
    data = dense()
    record = audit_gaze_measurement_quality(data)
    report = measurement_quality_reporting_frame(record)
    row = report.loc[report.metric == "accuracy_deg"].iloc[0]
    assert row.evidence == "not_available"
    assert np.isnan(row["mean"])
    assert report.iloc[-1]["mean"] == pytest.approx(1.0)
    assert record.provenance["absolute_accuracy_inferred_from_gaze"] is False


def test_quality_measurement_source_required():
    with pytest.raises(ValueError, match="evidence_source"):
        audit_gaze_measurement_quality(
            dense(), validation_records=pd.DataFrame({"participant_id": ["P1"], "accuracy_deg": [0.4]})
        )
    record = audit_gaze_measurement_quality(
        dense(), validation_records=pd.DataFrame({
            "participant_id": ["P1"], "accuracy_deg": [.4],
            "precision_deg": [.2], "evidence_source": ["validation target record"]
        })
    )
    assert measurement_quality_reporting_frame(record).iloc[0]["mean"] == pytest.approx(.4)


def sidecar():
    return {
        "Columns": ["timestamp", "x_coordinate", "y_coordinate"],
        "SamplingFrequency": 100., "StartTime": 0.,
        "PhysioType": "eyetrack", "RecordedEye": "left",
        "SampleCoordinateSystem": "screen-pixel",
        "x_coordinate": {"Units": "px"},
        "y_coordinate": {"Units": "px"},
        "timestamp": {"Units": "s"},
    }


def test_bids_narrow_import_and_missingness(tmp_path):
    path = tmp_path / "sub-01_task-look_recording-eye1_physio.tsv.gz"
    pd.DataFrame([[0, 100, 220], [.01, np.nan, 222], [.02, 101, 221]]).to_csv(
        path, sep="\t", index=False, header=False, compression="gzip", na_rep="n/a"
    )
    meta = sidecar()
    metadata = tmp_path / "sub-01_task-look_recording-eye1_physio.json"
    metadata.write_text(json.dumps(meta))
    item = from_bids_eyetracking(path, sidecar=metadata)
    assert item.values.shape == (1, 3, 2)
    assert np.isnan(item.values[0, 1, 0])
    assert item.provenance["interpolation_performed"] is False
    assert item.coordinate_system == "pixels"


def test_bids_metadata_rejects_unknown_units_and_bad_clock(tmp_path):
    bad = sidecar()
    bad["x_coordinate"]["Units"] = "frames"
    with pytest.raises(ValueError, match="units"):
        validate_eyetracking_metadata(bad)
    path = tmp_path / "sub-01_task-look_recording-eye1_physio.tsv.gz"
    pd.DataFrame([[0, 100, 220], [.01, 120, 240], [.024, 140, 250]]).to_csv(
        path, sep="\t", index=False, header=False, compression="gzip"
    )
    with pytest.raises(ValueError, match="timestamps"):
        from_bids_eyetracking(path, sidecar=sidecar())


def test_simplex_projection_and_aoi_comparison():
    x = project_simplex(np.array([[-1., 2., 1.], [.4, .6, 0.]]))
    assert (x >= -1e-12).all()
    assert np.allclose(x.sum(axis=1), 1)
    rng = np.random.default_rng(27)
    t = np.linspace(0, 1, 21)
    logits = rng.normal(0, .23, (14, len(t), 3))
    v = np.exp(logits) / np.exp(logits).sum(axis=2, keepdims=True)
    v[0, 0] = [1, 0, 0]
    data = TrajectorySet(time=t, values=v,
                         curve_ids=tuple(f"a{i}" for i in range(14)),
                         dimension_names=("A", "B", "C"))
    result = compare_aoi_functional_geometries(data, n_components=2)
    assert len(result.summary) == 2
    assert np.allclose(result.alr_reconstruction.sum(axis=2), 1)
    assert np.allclose(result.projected_reconstruction.sum(axis=2), 1)
    assert (result.projected_reconstruction >= 0).all()
    assert result.provisional


def test_weighted_geometry_and_fail_closed_input():
    d = dense()
    fit = fit_weighted_mfpca(d, weights=(2., .5), n_components=2)
    assert reconstruct_weighted_mfpca(fit).shape == d.values.shape
    assert weighted_component_geometry(fit).shape[2] == 2
    with pytest.raises(ValueError, match="positive"):
        fit_weighted_mfpca(d, weights=(1., 0.))


def test_ordered_change_point_and_dependence_declared():
    d = dense(n=20)
    values = d.values.copy()
    values[11:, :, 0] += .2
    data = d.with_values(values)
    out = detect_ordered_functional_changepoint(data, dependence="independent",
                                                 n_bootstrap=99, random_state=123)
    assert 5 <= out.split_index <= 15
    assert len(out.null_statistics) == 99
    assert out.evidence["calibration_not_qualified"]
    with pytest.raises(ValueError, match="requires"):
        detect_ordered_functional_changepoint(data, dependence="weak_block", n_bootstrap=99)
    dependent = detect_ordered_functional_changepoint(
        data, dependence="weak_block", block_length=3, n_bootstrap=99
    )
    assert dependent.evidence["block_length"] == 3


def test_sparse_group_prototype_unit_permutation():
    rng = np.random.default_rng(707)
    times, values, ids = [], [], []
    for i in range(16):
        t = np.r_[0., np.sort(rng.uniform(.07, .93, 13)), 1.]
        z = rng.normal()
        v = np.column_stack((.4 + .08*z*np.sin(np.pi*t) + (i>=8)*.07*np.sin(np.pi*t),
                             .5 + .07*z*np.cos(np.pi*t)))
        v += rng.normal(0, .012, v.shape)
        times.append(t); values.append(v); ids.append(f"unit{i}")
    sparse = IrregularTrajectorySet(
        time=tuple(times), values=tuple(values), curve_ids=tuple(ids),
        dimension_names=("x", "y"), coordinate_system="normalized", time_unit="s"
    )
    kwargs = {
        "n_components": 2, "evaluation_grid": np.linspace(0, 1, 21),
        "mean_bandwidth": .3, "covariance_bandwidth": .45,
        "measurement_error": "diagonal",
        "measurement_error_variance": (.0002, .0002),
        "psd_action": "project", "score_failure_action": "retain_nan",
    }
    out = sparse_group_test(sparse, ["A"]*8 + ["B"]*8,
                            fit_kwargs=kwargs, n_permutations=99, random_state=4)
    assert out.n_independent_units == 16
    assert 0 < out.p_value <= 1
    assert len(functional_group_contrast_frame(out)) == 42
    assert out.evidence["not_Koner_Luo_2024_replication"]
    with pytest.raises(ValueError, match="repeated participants|one independent unit"):
        sparse_group_test(sparse, ["A"]*8 + ["B"]*8,
                          fit_kwargs=kwargs, unit_ids=["same"]*16,
                          n_permutations=99)


def test_bids_rejects_missing_eye_recording_entity(tmp_path):
    path = tmp_path / "sub-01_task-look_physio.tsv.gz"
    pd.DataFrame([[0, 100, 220], [.01, 120, 240]]).to_csv(
        path, sep="\t", index=False, header=False, compression="gzip"
    )
    with pytest.raises(ValueError, match="recording"):
        from_bids_eyetracking(path, sidecar=sidecar())


def test_changepoint_independent_rejects_repeated_participants():
    d = dense(n=16)
    md = d.metadata.reset_index(drop=True).copy()
    md["participant_id"] = [f"P{i // 2}" for i in range(16)]
    shared = TrajectorySet(
        time=d.time, values=d.values, curve_ids=d.curve_ids,
        dimension_names=d.dimension_names, metadata=md,
        coordinate_system=d.coordinate_system, time_unit=d.time_unit,
    )
    with pytest.raises(ValueError, match="repeated participants"):
        detect_ordered_functional_changepoint(
            shared, dependence="independent", n_bootstrap=99,
        )


def test_group_unit_ids_cannot_split_same_participant():
    rng = np.random.default_rng(111)
    times, values, ids = [], [], []
    for i in range(10):
        t = np.r_[0., np.sort(rng.uniform(.1, .9, 6)), 1.]
        times.append(t)
        values.append(np.column_stack((.4 + .03 * np.sin(t), .5 + .04 * np.cos(t))))
        ids.append(f"curve{i}")
    sparse = IrregularTrajectorySet(
        time=tuple(times), values=tuple(values), curve_ids=tuple(ids),
        dimension_names=("x", "y"),
        metadata=pd.DataFrame({"participant_id": [f"P{i // 2}" for i in range(10)]}),
    )
    kwargs = {
        "n_components": 1, "evaluation_grid": np.linspace(0, 1, 11),
        "mean_bandwidth": .3, "covariance_bandwidth": .4,
        "measurement_error": "diagonal",
        "measurement_error_variance": (.0001, .0001),
    }
    with pytest.raises(ValueError, match="one independent unit_id"):
        sparse_group_test(
            sparse, ["A"] * 4 + ["B"] * 6, fit_kwargs=kwargs,
            unit_ids=ids, n_permutations=99,
        )


def test_quality_rejects_out_of_range_calibration():
    with pytest.raises(ValueError, match="fraction"):
        audit_gaze_measurement_quality(
            dense(), validation_records=pd.DataFrame({
                "participant_id": ["P1"], "data_loss_fraction": [1.3],
                "evidence_source": ["calibration-validation-log"],
            })
        )


def test_bids_rejects_undocumented_nonnumeric_tokens_and_wrong_sidecar(tmp_path):
    path = tmp_path / "sub-01_task-look_recording-eye1_physio.tsv.gz"
    pd.DataFrame([[0, 100, 220], [.01, "corrupt", 230], [.02, 102, 240]]).to_csv(
        path, sep="\t", index=False, header=False, compression="gzip"
    )
    with pytest.raises(ValueError, match="invalid nonnumeric"):
        from_bids_eyetracking(path, sidecar=sidecar())
    alternative = tmp_path / "unrelated_physio.json"
    alternative.write_text(json.dumps(sidecar()))
    with pytest.raises(ValueError, match="basename"):
        from_bids_eyetracking(path, sidecar=alternative)


def test_weighted_mfpca_orthogonality_under_declared_geometry():
    data = dense(n=18)
    weights = np.array([1.8, .32])
    result = fit_weighted_mfpca(data, weights=weights, n_components=3)
    basis = weighted_component_geometry(result)
    quad = result.fitted_transformed.weights
    gram = np.einsum("ktd,ltd,t,d->kl", basis, basis, quad, weights)
    np.testing.assert_allclose(gram, np.eye(3), atol=1e-9)
    reconstituted = reconstruct_weighted_mfpca(result)
    assert np.isfinite(reconstituted).all()
    assert reconstituted.shape == data.values.shape


def test_weighted_mfpca_invariance_to_declared_channel_unit_change():
    data = dense(n=16)
    fit_one = fit_weighted_mfpca(data, weights=(2.0, .5), n_components=2)
    new_values = data.values.copy()
    new_values[:, :, 0] *= 1000
    scaled = data.with_values(new_values)
    fit_two = fit_weighted_mfpca(scaled, weights=(2e-6, .5), n_components=2)
    restored = reconstruct_weighted_mfpca(fit_two)
    restored[:, :, 0] /= 1000
    np.testing.assert_allclose(
        restored, reconstruct_weighted_mfpca(fit_one), atol=1e-8, rtol=1e-8
    )


def test_grouped_holdout_aoi_geometry_and_no_train_test_leakage():
    from eyetrajectoriespy.research import (
        compare_aoi_functional_geometries_holdout,
    )
    rng = np.random.default_rng(914)
    time = np.linspace(0, 1, 21)
    raw = rng.normal(0, .5, (28, len(time), 3))
    compositions = np.exp(raw - raw.max(axis=-1, keepdims=True))
    compositions /= compositions.sum(axis=-1, keepdims=True)
    data = TrajectorySet(
        time=time, values=compositions,
        curve_ids=tuple(f"AOI_{i:03d}" for i in range(28)),
        dimension_names=("headword", "definition", "context"),
        metadata=pd.DataFrame({"participant_id": [f"P{i}" for i in range(28)]}),
        coordinate_system="probability_simplex",
    )
    fit = compare_aoi_functional_geometries_holdout(
        data.subset(range(18)), data.subset(range(18, 28)),
        n_components=2, reference_dimension=2,
    )
    assert fit.leakage_guard_passed and fit.provisional
    assert len(fit.summary) == 2
    assert np.isfinite(fit.summary.holdout_reconstruction_mse).all()
    np.testing.assert_allclose(fit.alr_reconstruction.sum(axis=2), 1, atol=1e-10)
    np.testing.assert_allclose(fit.projected_reconstruction.sum(axis=2), 1, atol=1e-10)
    with pytest.raises(ValueError, match="curve identities"):
        compare_aoi_functional_geometries_holdout(
            data.subset(range(18)), data.subset([17, 20]), n_components=2,
        )


def test_bids_published_millisecond_timestamp_convention(tmp_path):
    """BEP020 publishes device timestamps in ms with StartTime in seconds."""
    path = tmp_path / "sub-01_task-look_recording-eye1_physio.tsv.gz"
    pd.DataFrame([
        [1250, 100, 220], [1260, 101, "n/a"], [1270, 102, 225],
    ]).to_csv(path, sep="\t", index=False, header=False,
              compression="gzip", na_rep="n/a")
    meta = sidecar()
    meta["timestamp"] = {"Units": "ms", "Origin": "System startup"}
    meta["StartTime"] = -2532.0
    audit = validate_eyetracking_metadata(meta)
    assert audit["timestamp_original_unit"] == "ms"
    assert audit["timestamp_seconds_scale"] == pytest.approx(.001)
    gaze = from_bids_eyetracking(path, sidecar=meta)
    np.testing.assert_allclose(gaze.time, [1.25, 1.26, 1.27])
    assert np.isnan(gaze.values[0, 1, 1])
    assert gaze.time_unit == "s"
    assert gaze.provenance["source_timestamp_unit"] == "ms"
    assert gaze.provenance["timestamp_origin"] == "System startup"
    assert gaze.provenance["start_time_seconds"] == -2532.0
    assert gaze.provenance["clock_alignment_performed"] is False


def test_bids_timestamp_units_are_not_inferred():
    meta = sidecar()
    del meta["timestamp"]["Units"]
    with pytest.raises(ValueError, match="timestamp metadata"):
        validate_eyetracking_metadata(meta)
    meta["timestamp"]["Units"] = "frames"
    with pytest.raises(ValueError, match="supported timestamp units"):
        validate_eyetracking_metadata(meta)


def test_target_based_calibration_accuracy_precision_and_data_loss():
    from eyetrajectoriespy.research import summarize_gaze_validation_targets
    # Known target offsets 0.3/0.7 deg imply 0.5-degree mean
    # positional error and 0.2-degree within-target radial RMS.
    data = pd.DataFrame({
        "participant_id": ["P1"] * 5,
        "validation_session_id": ["S1"] * 5,
        "target_id": ["A", "A", "B", "B", "B"],
        "target_x_deg": [0., 0., 3., 3., 3.],
        "target_y_deg": [0., 0., 2., 2., 2.],
        "gaze_x_deg": [.3, .7, 3.3, 3.7, np.nan],
        "gaze_y_deg": [0., 0., 2., 2., np.nan],
    })
    measured = summarize_gaze_validation_targets(
        data, evidence_source="known_targets_validation_S1"
    )
    assert len(measured) == 1
    row = measured.iloc[0]
    assert row.accuracy_deg == pytest.approx(.5)
    assert row.precision_deg == pytest.approx(.2)
    assert row.validation_points == 2
    assert row.data_loss_fraction == pytest.approx(.2)
    assert row.validation_samples_valid == 4
    audit = audit_gaze_measurement_quality(
        dense(), validation_records=measured,
        source_description="independent target validation fixture",
    )
    assert measurement_quality_reporting_frame(audit).iloc[0]["mean"] == pytest.approx(.5)
    assert audit.provenance["absolute_accuracy_inferred_from_gaze"] is False


def test_target_based_calibration_rejects_undocumented_and_inconsistent_targets():
    from eyetrajectoriespy.research import summarize_gaze_validation_targets
    frame = pd.DataFrame({
        "participant_id": ["P0", "P0"],
        "validation_session_id": ["S1", "S1"],
        "target_id": ["A", "A"],
        "target_x_deg": [0., 1.],
        "target_y_deg": [0., 0.],
        "gaze_x_deg": [.2, .3],
        "gaze_y_deg": [.1, .2],
    })
    with pytest.raises(ValueError, match="inconsistent target"):
        summarize_gaze_validation_targets(frame, evidence_source="reference")
    with pytest.raises(ValueError, match="evidence_source"):
        summarize_gaze_validation_targets(frame, evidence_source="")


def test_bids_subset_is_pinned_to_stable_specification():
    audit = validate_eyetracking_metadata(sidecar())
    assert audit["specification_basis"] == (
        "BIDS_1.11.2_EyeTracking_subset_not_full_conformance"
    )
    assert audit["validated_subset_only"] is True
    assert audit["clock_alignment_performed"] is False


def test_bids_specification_example_supports_four_columns_and_device_ms(tmp_path):
    """Fixture sampled from BIDS 1.11.2 example with optional pupil_size."""
    path = tmp_path / "sub-01_task-visualSearch_recording-eye1_physio.tsv.gz"
    data = [
        [7186799, 416.29, 267.39, 4612],
        [7186800, 416.29, 268.10, 4623],
        [7186801, 416.20, 269.00, 4623],
    ]
    pd.DataFrame(data).to_csv(
        path, sep="\t", index=False, header=False, compression="gzip"
    )
    meta = {
        "Columns": ["timestamp", "x_coordinate", "y_coordinate", "pupil_size"],
        "SamplingFrequency": 1000,
        "StartTime": -2532,
        "PhysioType": "eyetrack",
        "RecordedEye": "right",
        "SampleCoordinateSystem": "gaze-on-screen",
        "timestamp": {"Units": "ms", "Origin": "System startup"},
        "x_coordinate": {"Units": "pixel"},
        "y_coordinate": {"Units": "pixel"},
        "pupil_size": {"Units": "arbitrary"},
    }
    sample = from_bids_eyetracking(path, sidecar=meta)
    np.testing.assert_allclose(sample.time, [7186.799, 7186.800, 7186.801])
    assert sample.values.shape == (1, 3, 2)
    assert sample.coordinate_system == "pixels"
    assert sample.provenance["import_contract"] == (
        "BIDS_1.11.2_EyeTracking_subset"
    )
    assert sample.provenance["full_bids_conformance_tested"] is False


def test_weighted_geometry_freezes_analyst_declared_weights():
    original = np.array([2.0, .5])
    fitted = fit_weighted_mfpca(dense(), weights=original, n_components=2)
    reconstruction = reconstruct_weighted_mfpca(fitted).copy()
    original[0] = 5000
    np.testing.assert_allclose(reconstruct_weighted_mfpca(fitted), reconstruction)
    assert fitted.weights.tolist() == [2.0, .5]
    with pytest.raises(ValueError):
        fitted.weights[0] = 1.0
