import numpy as np
import pytest

from eyetrajectoriespy import (
    functional_recovery_qualification_scenarios,
    functional_recovery_scenario_catalog_frame,
    functional_recovery_stress_scenarios,
)


def test_qualification_suite_is_small_deterministic_and_gated_by_role():
    scenarios = functional_recovery_qualification_scenarios(
        replicates=3,
        seed_start=5000,
    )
    assert [scenario.name for scenario in scenarios] == [
        "dense_gaussian",
        "dense_student_t",
        "native_sparse",
        "hierarchy_sources",
    ]
    assert all(scenario.replicates == 3 for scenario in scenarios)
    assert [scenario.seed_start for scenario in scenarios] == [
        5000,
        5100,
        5200,
        5300,
    ]
    assert all(
        dict(scenario.labels)["matrix_role"] == "qualification"
        for scenario in scenarios
    )
    assert all(
        dict(scenario.labels)["automatic_thresholds"] is True
        for scenario in scenarios
    )


def test_stress_suite_is_named_descriptive_and_not_ci_thresholded():
    scenarios = functional_recovery_stress_scenarios(
        replicates=7,
        seed_start=9000,
    )
    names = {scenario.name for scenario in scenarios}
    assert {
        "stress_very_sparse",
        "stress_unequal_sample_counts",
        "stress_center_clustered_times",
        "stress_boundary_poor_times",
        "stress_high_measurement_noise",
        "stress_nearly_tied_eigenvalues",
        "stress_heavy_tailed_scores",
        "stress_participant_heavy_hierarchy",
        "stress_trial_heavy_hierarchy",
        "stress_phase_variation",
        "stress_mcar_missingness",
        "stress_block_missingness",
        "stress_correlated_multichannel_noise",
    } == names
    assert all(scenario.replicates == 7 for scenario in scenarios)
    assert all(
        dict(scenario.labels)["matrix_role"] == "stress"
        for scenario in scenarios
    )
    assert all(
        dict(scenario.labels)["automatic_thresholds"] is False
        for scenario in scenarios
    )

    tied = next(
        scenario
        for scenario in scenarios
        if scenario.name == "stress_nearly_tied_eigenvalues"
    )
    assert tied.eigenvalues == (1.0, 0.9)
    assert (
        dict(tied.labels)["scientific_target"]
        == "fpca_subspace"
    )

    correlated = next(
        scenario
        for scenario in scenarios
        if scenario.name == "stress_correlated_multichannel_noise"
    )
    assert correlated.dimension_names == ("x", "y")
    np.testing.assert_allclose(
        correlated.measurement_noise_covariance,
        np.array([[0.04, 0.018], [0.018, 0.09]]),
    )


def test_scenario_catalog_separates_qualification_and_stress_roles():
    frame = functional_recovery_scenario_catalog_frame(
        qualification_replicates=2,
        stress_replicates=4,
    )
    assert set(frame["matrix_role"]) == {"qualification", "stress"}
    assert (
        frame.loc[
            frame["matrix_role"] == "qualification",
            "replicates",
        ]
        == 2
    ).all()
    assert (
        frame.loc[
            frame["matrix_role"] == "stress",
            "replicates",
        ]
        == 4
    ).all()
    assert not frame["description"].isna().any()


@pytest.mark.parametrize(
    "function",
    [
        functional_recovery_qualification_scenarios,
        functional_recovery_stress_scenarios,
    ],
)
def test_scenario_suite_replicates_fail_closed(function):
    with pytest.raises(ValueError, match="replicates"):
        function(replicates=0)
    with pytest.raises(TypeError, match="seed_start"):
        function(seed_start=1.5)
