"""Tests for a truly paired rank-two observation-schedule experiment."""
from hashlib import sha256
import json
import numpy as np
import pytest

pytest.importorskip("arviz")
from scripts.run_b6_b7_rank2_controlled_observation_r4 import (
    SEED, PARTICIPANT_COUNTS, paired_cases, verify_matched_case_design, write_case,
)


@pytest.mark.parametrize("n", PARTICIPANT_COUNTS)
def test_exact_same_latent_parameters_and_x_values_under_both_schedules(n):
    cases = paired_cases(SEED, n)
    check = verify_matched_case_design(cases)
    assert check["matched_design_verified"]
    assert check["x_observations_identical"]
    assert check["population_covariance_identical"]
    assert check["participants_with_modified_y_schedule"] == n
    assert check["y_observation_counts_identical"]
    assert all(not np.isnan(a).any() for a in cases["paired"].gaze.values)
    assert all(np.isnan(a).any() for a in cases["asynchronous"].gaze.values)


def test_four_person_sample_is_nested_within_twelve_person_sample():
    small = paired_cases(SEED, 4)
    large = paired_cases(SEED, 12)
    for design in ("paired", "asynchronous"):
        a, b = small[design], large[design]
        assert np.array_equal(a.mean, b.mean)
        assert np.array_equal(a.loading, b.loading)
        for j in range(4):
            assert np.array_equal(a.gaze.time[j], b.gaze.time[j])
            assert np.array_equal(a.gaze.values[j], b.gaze.values[j], equal_nan=True)


def test_disallowed_levels_rejected():
    with pytest.raises(ValueError, match="participant count"):
        paired_cases(SEED, 8)


def test_failure_and_screen_failure_evidence_are_different(tmp_path):
    failure = {"status": "failed", "design": "asynchronous", "participants": 4}
    write_case(failure, tmp_path/"failed")
    goodfit_bad_screen = {"status": "ok", "design": "paired", "participants": 4,
        "reference_checks": {"all_identified_functionals_pass_exploratory_screen": False}}
    write_case(goodfit_bad_screen, tmp_path/"screen")
    f = json.loads((tmp_path/"failed"/"evidence.json").read_text())
    s = json.loads((tmp_path/"screen"/"evidence.json").read_text())
    assert f["fitting_exceptions"] == 1 and f["screen_failures"] is None
    assert s["fitting_exceptions"] == 0 and s["screen_failures"] == 1
    assert not f["release_authorized"] and not s["release_authorized"]
    for folder in (tmp_path/"failed", tmp_path/"screen"):
        for line in (folder/"SHA256SUMS").read_text().splitlines():
            digest, name = line.split("  ")
            assert sha256((folder/name).read_bytes()).hexdigest() == digest
