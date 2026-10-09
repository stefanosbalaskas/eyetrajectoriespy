import pandas as pd
import pytest

from eyetrajectoriespy._gaze_hand_attraction_research import (
    describe_gaze_hand_attraction,
)


def _data():
    return pd.DataFrame({
        "participant_id": ["p1", "p1"],
        "trial_id": ["t1", "t1"],
        "time_s": [0.0, .01],
        "gaze_x": [1.0, 0.0], "gaze_y": [0., 0.], "gaze_z": [0., 0.],
        "hand_x": [0.0, 1.0], "hand_y": [0., 0.], "hand_z": [0., 0.],
        "target_x": [1., 1.], "target_y": [0., 0.], "target_z": [0., 0.],
        "distractor_x": [0., 0.], "distractor_y": [0., 0.], "distractor_z": [0., 0.],
    })


def test_signed_relative_proximity_is_geometry_only():
    result = describe_gaze_hand_attraction(_data(), shared_clock_certified=True)
    assert result["gaze_relative_target_proximity"].tolist() == [1., -1.]
    assert result["hand_relative_target_proximity"].tolist() == [-1., 1.]
    assert result.attrs["status"] == "experimental_descriptive_geometry"


def test_rejects_uncertified_clocks_and_same_targets():
    with pytest.raises(ValueError, match="shared clock"):
        describe_gaze_hand_attraction(_data())
    d = _data()
    d["distractor_x"] = d["target_x"]
    with pytest.raises(ValueError, match="must differ"):
        describe_gaze_hand_attraction(d, shared_clock_certified=True)
