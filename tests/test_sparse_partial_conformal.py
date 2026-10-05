import numpy as np
import pandas as pd
import pytest

from eyetrajectoriespy._sparse_native import SparseNativeError
from eyetrajectoriespy.sparse_partial_conformal import (
    SparseFPCAPartialConformalBandResult,
    SparseFPCAPartialConformalCalibrationResult,
    _split_conformal_critical_value,
    calibrate_sparse_fpca_partial_prediction_conformal,
    sparse_fpca_conformal_band_frame,
    sparse_fpca_conformal_band_reporting_text,
    sparse_fpca_conformal_prediction_band,
)
from eyetrajectoriespy.types import IrregularTrajectorySet, SparseFPCAResult


_GRID = np.asarray([0.0, 0.25, 0.75, 1.0])
_FUTURE_GRID = np.asarray([0.75, 1.0])


def _fit(*, participant_ids=("train-p1", "train-p2", "train-p3")):
    covariance = 2.0 * np.ones((_GRID.size, _GRID.size), dtype=float)
    return SparseFPCAResult(
        scores=np.zeros((3, 1), dtype=float),
        eigenvalues=np.asarray([0.25]),
        dimension="x",
        curve_ids=("train1", "train2", "train3"),
        metadata=pd.DataFrame({"participant_id": list(participant_ids)}),
        coordinate_system="normalized",
        time_unit="s",
        n_components=1,
        fit_method="native_covariance",
        fit_smoothing="local_linear_epanechnikov",
        score_method="PACE",
        score_smoothing=None,
        tolerance=1e-10,
        normalize=False,
        provenance={
            "sparse_fpca": {
                "backend": "native",
                "score_ridge": 0.0,
                "score_condition_limit": 1e12,
                "min_score_samples": 2,
            }
        },
        evaluation_grid=_GRID.copy(),
        mean=np.zeros(_GRID.size),
        covariance=covariance,
        eigenfunctions=np.ones((1, _GRID.size)),
        noise_variance=1.0,
        quadrature_weights=np.ones(_GRID.size),
        score_diagnostics=pd.DataFrame(),
        covariance_diagnostics={},
        mean_support_counts=np.ones(_GRID.size, dtype=int),
        covariance_support_counts=np.ones((_GRID.size, _GRID.size), dtype=int),
    )


def _calibration_from_scores(scores, *, participants=None, curve_ids=None):
    scores = np.asarray(scores, dtype=float)
    if curve_ids is None:
        curve_ids = tuple(f"cal{i + 1}" for i in range(scores.size))
    scale = np.sqrt(1.4)
    values = []
    times = []
    for score in scores:
        times.append(_GRID.copy())
        values.append(
            np.asarray([0.0, 0.0, float(score * scale), 0.0])[:, None]
        )
    metadata = pd.DataFrame()
    if participants is not None:
        metadata = pd.DataFrame({"participant_id": list(participants)})
    return IrregularTrajectorySet(
        time=tuple(times),
        values=tuple(values),
        curve_ids=tuple(curve_ids),
        dimension_names=("x",),
        metadata=metadata,
        coordinate_system="normalized",
        time_unit="s",
    )


def _target(*, curve_id="target", participant_id="target-p", future_value=0.0):
    return IrregularTrajectorySet(
        time=(_GRID.copy(),),
        values=(np.asarray([0.0, 0.0, future_value, future_value])[:, None],),
        curve_ids=(curve_id,),
        dimension_names=("x",),
        metadata=pd.DataFrame({"participant_id": [participant_id]}),
        coordinate_system="normalized",
        time_unit="s",
    )


def test_finite_sample_order_statistic_matches_hand_calculation():
    critical, rank = _split_conformal_critical_value(
        np.asarray([1.0, 2.0, 3.0, 4.0]),
        alpha=0.4,
    )
    assert rank == 3
    assert critical == pytest.approx(3.0)


def test_curve_level_calibration_and_band_match_exact_arithmetic():
    fit = _fit()
    calibration = _calibration_from_scores([1.0, 2.0, 3.0, 4.0])
    calibrated = calibrate_sparse_fpca_partial_prediction_conformal(
        fit,
        calibration,
        history_cutoff=0.25,
        prediction_grid=_FUTURE_GRID,
        alpha=0.4,
    )

    assert isinstance(calibrated, SparseFPCAPartialConformalCalibrationResult)
    assert calibrated.n_calibration_units == 4
    assert calibrated.critical_value == pytest.approx(3.0)
    assert calibrated.unit_scores == pytest.approx([1.0, 2.0, 3.0, 4.0])
    assert calibrated.provenance["calibration_unit"] == "curve"
    assert calibrated.provenance["continuous_domain_coverage_claimed"] is False

    band = sparse_fpca_conformal_prediction_band(calibrated, _target())
    assert isinstance(band, SparseFPCAPartialConformalBandResult)
    scale = np.sqrt(1.4)
    assert band.prediction.conditional_mean == pytest.approx([0.0, 0.0])
    assert band.lower == pytest.approx([-3.0 * scale, -3.0 * scale])
    assert band.upper == pytest.approx([3.0 * scale, 3.0 * scale])
    assert band.provenance["continuous_domain_coverage_claimed"] is False

    frame = sparse_fpca_conformal_band_frame(band)
    assert frame.shape[0] == 2
    assert frame["critical_value"].to_numpy() == pytest.approx([3.0, 3.0])
    text = sparse_fpca_conformal_band_reporting_text(band)
    assert "future observed measurements" in text
    assert "No continuous-domain" in text
    assert "no interpolation" in text


def test_group_calibration_uses_maximum_trial_score_per_participant():
    fit = _fit()
    calibration = _calibration_from_scores(
        [1.0, 3.0, 2.0, 4.0],
        participants=("p1", "p1", "p2", "p2"),
    )
    calibrated = calibrate_sparse_fpca_partial_prediction_conformal(
        fit,
        calibration,
        history_cutoff=0.25,
        prediction_grid=_FUTURE_GRID,
        alpha=0.5,
        group_column="participant_id",
    )

    assert calibrated.calibration_unit_ids == ("p1", "p2")
    assert calibrated.unit_scores == pytest.approx([3.0, 4.0])
    assert calibrated.critical_value == pytest.approx(4.0)
    assert calibrated.provenance["calibration_unit"] == "group"
    assert (
        calibrated.provenance["group_aggregation"]
        == "maximum_curve_nonconformity_within_group"
    )


def test_calibration_requires_actual_future_grid_observations_without_interpolation():
    fit = _fit()
    calibration = IrregularTrajectorySet(
        time=(np.asarray([0.0, 0.25, 0.8, 1.0]),),
        values=(np.zeros((4, 1)),),
        curve_ids=("cal1",),
        dimension_names=("x",),
        coordinate_system="normalized",
        time_unit="s",
    )
    with pytest.raises(SparseNativeError) as exc:
        calibrate_sparse_fpca_partial_prediction_conformal(
            fit,
            calibration,
            history_cutoff=0.25,
            prediction_grid=_FUTURE_GRID,
            alpha=0.5,
        )
    assert exc.value.code == "calibration_future_grid_observation_missing"
    assert exc.value.details["raw_interpolation_performed"] is False


def test_alpha_below_finite_sample_resolution_fails():
    fit = _fit()
    calibration = _calibration_from_scores([1.0, 2.0, 3.0, 4.0])
    with pytest.raises(SparseNativeError) as exc:
        calibrate_sparse_fpca_partial_prediction_conformal(
            fit,
            calibration,
            history_cutoff=0.25,
            prediction_grid=_FUTURE_GRID,
            alpha=0.1,
        )
    assert exc.value.code == "insufficient_calibration_units_for_alpha"
    assert exc.value.details["n_calibration_units"] == 4


def test_curve_id_overlap_between_training_and_calibration_fails():
    fit = _fit()
    calibration = _calibration_from_scores(
        [1.0, 2.0],
        curve_ids=("train1", "cal2"),
    )
    with pytest.raises(ValueError, match="curve IDs must be disjoint"):
        calibrate_sparse_fpca_partial_prediction_conformal(
            fit,
            calibration,
            history_cutoff=0.25,
            prediction_grid=_FUTURE_GRID,
            alpha=0.5,
        )


def test_group_overlap_between_training_and_calibration_fails():
    fit = _fit(participant_ids=("p1", "train-p2", "train-p3"))
    calibration = _calibration_from_scores(
        [1.0, 2.0],
        participants=("p1", "p2"),
    )
    with pytest.raises(ValueError, match="participant/group units must be disjoint"):
        calibrate_sparse_fpca_partial_prediction_conformal(
            fit,
            calibration,
            history_cutoff=0.25,
            prediction_grid=_FUTURE_GRID,
            alpha=0.5,
            group_column="participant_id",
        )


def test_target_curve_and_group_must_be_disjoint_from_training_and_calibration():
    fit = _fit()
    calibration = _calibration_from_scores(
        [1.0, 2.0, 3.0, 4.0],
        participants=("p1", "p2", "p3", "p4"),
    )
    calibrated = calibrate_sparse_fpca_partial_prediction_conformal(
        fit,
        calibration,
        history_cutoff=0.25,
        prediction_grid=_FUTURE_GRID,
        alpha=0.4,
        group_column="participant_id",
    )

    with pytest.raises(ValueError, match="target curve ID"):
        sparse_fpca_conformal_prediction_band(
            calibrated,
            _target(curve_id="cal1", participant_id="target-p"),
        )
    with pytest.raises(ValueError, match="target participant/group"):
        sparse_fpca_conformal_prediction_band(
            calibrated,
            _target(curve_id="new", participant_id="p2"),
        )
    with pytest.raises(ValueError, match="proper-training units"):
        sparse_fpca_conformal_prediction_band(
            calibrated,
            _target(curve_id="new", participant_id="train-p1"),
        )


def test_nonfinite_future_calibration_response_fails():
    fit = _fit()
    calibration = _calibration_from_scores([1.0, 2.0, 3.0])
    values = list(calibration.values)
    values[0] = values[0].copy()
    values[0][2, 0] = np.nan
    bad = IrregularTrajectorySet(
        time=calibration.time,
        values=tuple(values),
        curve_ids=calibration.curve_ids,
        dimension_names=calibration.dimension_names,
        metadata=calibration.metadata.reset_index(drop=True),
        coordinate_system=calibration.coordinate_system,
        time_unit=calibration.time_unit,
    )
    with pytest.raises(SparseNativeError) as exc:
        calibrate_sparse_fpca_partial_prediction_conformal(
            fit,
            bad,
            history_cutoff=0.25,
            prediction_grid=_FUTURE_GRID,
            alpha=0.5,
        )
    assert exc.value.code == "calibration_future_grid_observation_nonfinite"


def test_invalid_group_and_helper_types_fail_cleanly():
    fit = _fit()
    calibration = _calibration_from_scores([1.0, 2.0, 3.0])
    with pytest.raises(ValueError, match="group_column"):
        calibrate_sparse_fpca_partial_prediction_conformal(
            fit,
            calibration,
            history_cutoff=0.25,
            prediction_grid=_FUTURE_GRID,
            alpha=0.5,
            group_column="participant_id",
        )
    with pytest.raises(TypeError):
        sparse_fpca_conformal_prediction_band(object(), _target())
    with pytest.raises(TypeError):
        sparse_fpca_conformal_band_frame(object())
    with pytest.raises(TypeError):
        sparse_fpca_conformal_band_reporting_text(object())
