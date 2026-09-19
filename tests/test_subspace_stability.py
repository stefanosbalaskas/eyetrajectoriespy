from dataclasses import replace

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest

from eyetrajectoriespy import (
    bootstrap_fpca_subspace_stability,
    compare_fpca_subspaces,
    fit_mfpca,
    fpca_eigengap_reporting_text,
    fpca_eigenvalue_gap_table,
    fpca_subspace_stability_reporting_text,
    plot_fpca_subspace_stability,
    simulate_planar_trajectories,
    summarise_fpca_subspace_stability,
)


def sample():
    return simulate_planar_trajectories(
        n_participants=10,
        trials_per_participant=3,
        n_time=41,
        random_state=27,
    )


def test_rotated_near_tied_pair_has_identical_two_dimensional_subspace():
    gaze = sample()
    fit = fit_mfpca(gaze, n_components=3, scaling="dimension_sd")

    angle = np.pi / 4.0
    rotation = np.array(
        [
            [np.cos(angle), -np.sin(angle)],
            [np.sin(angle), np.cos(angle)],
        ]
    )
    components = fit.components.copy()
    components[:2] = np.einsum("ab,btd->atd", rotation, fit.components[:2])
    scores = fit.scores.copy()
    scores[:, :2] = fit.scores[:, :2] @ rotation.T
    rotated = replace(fit, components=components, scores=scores)

    one_dimensional = compare_fpca_subspaces(
        fit,
        rotated,
        start_component=0,
        n_components=1,
    )
    two_dimensional = compare_fpca_subspaces(
        fit,
        rotated,
        start_component=0,
        n_components=2,
    )

    assert one_dimensional.principal_cosines[0] == pytest.approx(np.sqrt(0.5))
    assert one_dimensional.normalized_projector_distance > 0.6
    assert np.allclose(two_dimensional.principal_cosines, 1.0, atol=1e-8)
    assert np.allclose(two_dimensional.principal_angles_degrees, 0.0, atol=1e-6)
    assert two_dimensional.normalized_projector_distance == pytest.approx(0.0, abs=1e-7)


def test_eigengap_table_requires_explicit_threshold_for_near_tie_flag():
    gaze = sample()
    fit = fit_mfpca(gaze, n_components=3, scaling="dimension_sd")
    custom = replace(
        fit,
        explained_variance=np.array([4.0, 3.9, 1.0]),
    )

    plain = fpca_eigenvalue_gap_table(custom)
    assert "near_tie_flag" not in plain.columns
    assert plain.iloc[0]["relative_gap"] == pytest.approx(0.025)
    assert plain.iloc[0]["next_to_current_ratio"] == pytest.approx(0.975)

    flagged = fpca_eigenvalue_gap_table(
        custom,
        relative_gap_threshold=0.05,
    )
    assert bool(flagged.iloc[0]["near_tie_flag"])
    assert not bool(flagged.iloc[1]["near_tie_flag"])


def test_subspace_bootstrap_is_reproducible():
    gaze = sample()
    first = bootstrap_fpca_subspace_stability(
        gaze,
        start_component=0,
        n_components=2,
        n_bootstrap=8,
        scaling="dimension_sd",
        random_state=11,
    )
    second = bootstrap_fpca_subspace_stability(
        gaze,
        start_component=0,
        n_components=2,
        n_bootstrap=8,
        scaling="dimension_sd",
        random_state=11,
    )

    assert first.principal_cosines.shape == (8, 2)
    assert first.principal_angles_degrees.shape == (8, 2)
    assert np.all((first.principal_cosines >= 0) & (first.principal_cosines <= 1))
    assert np.all((first.normalized_projector_distance >= 0))
    assert np.all((first.normalized_projector_distance <= 1 + 1e-12))
    assert np.allclose(first.principal_cosines, second.principal_cosines)
    assert np.allclose(
        first.normalized_projector_distance,
        second.normalized_projector_distance,
    )


def test_participant_subspace_bootstrap_and_summary():
    gaze = sample()
    result = bootstrap_fpca_subspace_stability(
        gaze,
        start_component=0,
        n_components=2,
        n_bootstrap=6,
        scaling="dimension_sd",
        resample_unit="participant",
        participant_column="participant_id",
        random_state=4,
    )
    summary = summarise_fpca_subspace_stability(result)

    assert result.resampling_unit == "participant"
    assert result.component_indices == (0, 1)
    assert summary.iloc[0]["component_start"] == 1
    assert summary.iloc[0]["component_end"] == 2
    assert 0 <= summary.iloc[0]["median_min_principal_cosine"] <= 1
    assert 0 <= summary.iloc[0]["median_normalized_projector_distance"] <= 1


def test_subspace_contract_errors():
    gaze = sample()
    fit = fit_mfpca(gaze, n_components=3, scaling="dimension_sd")

    with pytest.raises(TypeError):
        compare_fpca_subspaces(fit, fit, start_component=True)
    with pytest.raises(ValueError):
        compare_fpca_subspaces(fit, fit, start_component=-1)
    with pytest.raises(ValueError):
        compare_fpca_subspaces(fit, fit, n_components=0)
    with pytest.raises(ValueError):
        compare_fpca_subspaces(fit, fit, start_component=2, n_components=2)

    shifted = replace(fit, time=fit.time + 0.01)
    with pytest.raises(ValueError, match="time grid"):
        compare_fpca_subspaces(fit, shifted, n_components=2)

    different_coordinate = replace(fit, coordinate_system="pixels")
    with pytest.raises(ValueError, match="coordinate system"):
        compare_fpca_subspaces(fit, different_coordinate, n_components=2)

    with pytest.raises(ValueError):
        bootstrap_fpca_subspace_stability(gaze, n_bootstrap=1)
    with pytest.raises(ValueError):
        bootstrap_fpca_subspace_stability(gaze, resample_unit="participant")
    with pytest.raises(ValueError):
        bootstrap_fpca_subspace_stability(gaze, resample_unit="bad")
    with pytest.raises(ValueError):
        bootstrap_fpca_subspace_stability(
            gaze,
            start_component=28,
            n_components=2,
        )

    with pytest.raises(ValueError):
        summarise_fpca_subspace_stability(
            bootstrap_fpca_subspace_stability(
                gaze,
                n_bootstrap=3,
                n_components=2,
            ),
            interval=(0.9, 0.1),
        )


def test_eigengap_contract_errors():
    gaze = sample()
    fit = fit_mfpca(gaze, n_components=3)

    with pytest.raises(ValueError):
        fpca_eigenvalue_gap_table(
            replace(fit, explained_variance=np.array([1.0])),
        )
    with pytest.raises(ValueError):
        fpca_eigenvalue_gap_table(
            replace(fit, explained_variance=np.array([1.0, 2.0, 0.5])),
        )
    with pytest.raises(ValueError):
        fpca_eigenvalue_gap_table(
            fit,
            relative_gap_threshold=1.0,
        )


def test_subspace_reporting_and_plotting():
    gaze = sample()
    fit = fit_mfpca(gaze, n_components=3, scaling="dimension_sd")
    gap_text = fpca_eigengap_reporting_text(
        fit,
        relative_gap_threshold=0.10,
    )
    assert "smallest adjacent retained FPCA eigengap" in gap_text
    assert "pre-specified" in gap_text

    stability = bootstrap_fpca_subspace_stability(
        gaze,
        n_components=2,
        n_bootstrap=5,
        scaling="dimension_sd",
        random_state=13,
    )
    text = fpca_subspace_stability_reporting_text(stability)
    assert "principal cosine" in text
    assert "individual FPC labels" in text

    assert plot_fpca_subspace_stability(stability) is not None
    assert plot_fpca_subspace_stability(
        stability,
        metric="max_principal_angle_degrees",
    ) is not None
    assert plot_fpca_subspace_stability(
        stability,
        metric="min_principal_cosine",
    ) is not None
    with pytest.raises(ValueError):
        plot_fpca_subspace_stability(stability, metric="bad")
    plt.close("all")
