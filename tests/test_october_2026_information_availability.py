import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from research.october_2026.information_availability import (  # noqa: E402
    certify_preprocessing_availability,
)


def test_future_normalization_is_not_first_use_valid():
    fits = pd.DataFrame({
        "transform_id": ["scaler"] * 3,
        "source_participant": ["heldout"] * 3,
        "source_time_s": [0, 5, 10],
    })
    pred = pd.DataFrame({
        "transform_id": ["scaler"],
        "target_participant": ["heldout"],
        "prediction_time_s": [4],
    })
    a = certify_preprocessing_availability(
        fits, pred, training_participants=["training"], mode="online")
    assert not bool(a.iloc[0].deployment_valid)
    assert a.iloc[0].future_target_fit_uses == 2
    assert not certify_preprocessing_availability(
        fits, pred, training_participants=["training"],
        mode="retrospective").iloc[0].deployment_valid


def test_training_population_provenance_is_valid():
    fits = pd.DataFrame({
        "transform_id": ["scale"] * 2,
        "source_participant": ["train1", "train2"],
        "source_time_s": [3., 4.],
    })
    preds = pd.DataFrame({
        "transform_id": ["scale"], "target_participant": ["test"],
        "prediction_time_s": [0.],
    })
    a = certify_preprocessing_availability(
        fits, preds, training_participants=["train1", "train2"],
        mode="training_population")
    assert bool(a.iloc[0].deployment_valid)


def test_pretask_calibration_and_bad_mode():
    fits = pd.DataFrame({
        "transform_id": ["norm"] * 2, "source_participant": ["test"] * 2,
        "source_time_s": [-3., -1.],
    })
    preds = pd.DataFrame({
        "transform_id": ["norm"], "target_participant": ["test"],
        "prediction_time_s": [0.],
    })
    a = certify_preprocessing_availability(
        fits, preds, training_participants=["train"],
        mode="prior_baseline")
    assert bool(a.iloc[0].deployment_valid)
    with pytest.raises(ValueError, match="mode"):
        certify_preprocessing_availability(
            fits, preds, training_participants=["train"], mode="impossible")
