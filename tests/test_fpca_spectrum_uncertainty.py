import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest

from eyetrajectoriespy import (
    FPCASpectrumUncertaintyResult,
    bootstrap_fpca_spectrum_uncertainty,
    fpca_spectrum_uncertainty_frame,
    fpca_spectrum_uncertainty_reporting_text,
    plot_fpca_spectrum_uncertainty,
    simulate_planar_trajectories,
)


def sample():
    return simulate_planar_trajectories(
        n_participants=12,
        trials_per_participant=2,
        n_time=31,
        random_state=51,
    )


def test_spectrum_uncertainty_is_reproducible_and_ordered():
    gaze = sample()
    first = bootstrap_fpca_spectrum_uncertainty(
        gaze,
        n_bootstrap=20,
        n_components=3,
        scaling="dimension_sd",
        confidence_level=0.95,
        random_state=7,
    )
    second = bootstrap_fpca_spectrum_uncertainty(
        gaze,
        n_bootstrap=20,
        n_components=3,
        scaling="dimension_sd",
        confidence_level=0.95,
        random_state=7,
    )
    assert isinstance(first, FPCASpectrumUncertaintyResult)
    assert first.bootstrap_eigenvalues.shape == (20, 3)
    assert first.bootstrap_explained_variance_ratio.shape == (20, 3)
    assert first.bootstrap_cumulative_variance_ratio.shape == (20, 3)
    assert first.assignments.shape == (20, 3)
    assert first.similarities.shape == (20, 3)
    assert first.n_bootstrap == 20
    assert first.n_components == 3
    assert np.all(first.eigenvalue_lower <= first.reference.explained_variance[:3])
    assert np.all(first.reference.explained_variance[:3] <= first.eigenvalue_upper)
    assert np.all(
        first.explained_variance_ratio_lower
        <= first.reference.explained_variance_ratio[:3]
    )
    assert np.all(
        first.reference.explained_variance_ratio[:3]
        <= first.explained_variance_ratio_upper
    )
    assert np.allclose(first.bootstrap_eigenvalues, second.bootstrap_eigenvalues)
    assert np.allclose(
        first.bootstrap_explained_variance_ratio,
        second.bootstrap_explained_variance_ratio,
    )
    assert np.all((first.similarities >= 0) & (first.similarities <= 1 + 1e-12))


def test_higher_confidence_is_no_narrower_under_same_draws():
    gaze = sample()
    low = bootstrap_fpca_spectrum_uncertainty(
        gaze,
        n_bootstrap=24,
        n_components=2,
        confidence_level=0.90,
        random_state=4,
    )
    high = bootstrap_fpca_spectrum_uncertainty(
        gaze,
        n_bootstrap=24,
        n_components=2,
        confidence_level=0.99,
        random_state=4,
    )
    assert np.all(
        (high.eigenvalue_upper - high.eigenvalue_lower)
        >= (low.eigenvalue_upper - low.eigenvalue_lower) - 1e-12
    )
    assert np.all(
        (high.explained_variance_ratio_upper - high.explained_variance_ratio_lower)
        >= (
            low.explained_variance_ratio_upper
            - low.explained_variance_ratio_lower
        )
        - 1e-12
    )


def test_family_scope_is_no_less_conservative_for_each_metric():
    gaze = sample()
    component = bootstrap_fpca_spectrum_uncertainty(
        gaze,
        n_bootstrap=24,
        n_components=3,
        simultaneous_scope="component",
        random_state=2,
    )
    family = bootstrap_fpca_spectrum_uncertainty(
        gaze,
        n_bootstrap=24,
        n_components=3,
        simultaneous_scope="family",
        random_state=2,
    )
    for family_values, component_values in (
        (family.eigenvalue_critical_values, component.eigenvalue_critical_values),
        (
            family.explained_variance_ratio_critical_values,
            component.explained_variance_ratio_critical_values,
        ),
        (
            family.cumulative_variance_ratio_critical_values,
            component.cumulative_variance_ratio_critical_values,
        ),
    ):
        assert np.allclose(family_values, family_values[0])
        assert np.all(family_values >= component_values - 1e-12)


def test_participant_bootstrap_and_frame_preserve_explicit_semantics():
    gaze = sample()
    result = bootstrap_fpca_spectrum_uncertainty(
        gaze,
        n_bootstrap=20,
        n_components=2,
        scaling="dimension_sd",
        resample_unit="participant",
        participant_column="participant_id",
        random_state=9,
    )
    assert result.resampling_unit == "participant"
    assert result.participant_column == "participant_id"
    assert (
        result.provenance["fpca_spectrum_uncertainty"]["joint_across_metrics"]
        is False
    )
    frame = fpca_spectrum_uncertainty_frame(result)
    assert len(frame) == 2
    assert {
        "component",
        "eigenvalue",
        "eigenvalue_lower",
        "eigenvalue_upper",
        "explained_variance_ratio",
        "cumulative_variance_ratio",
        "median_matched_abs_similarity",
    } <= set(frame.columns)
    assert np.allclose(
        result.bootstrap_cumulative_variance_ratio,
        np.cumsum(result.bootstrap_explained_variance_ratio, axis=1),
    )


def test_spectrum_uncertainty_contract_failures_are_explicit():
    gaze = sample()
    with pytest.raises(ValueError):
        bootstrap_fpca_spectrum_uncertainty(gaze, n_bootstrap=19)
    with pytest.raises(TypeError):
        bootstrap_fpca_spectrum_uncertainty(gaze, n_bootstrap=True)
    with pytest.raises(ValueError):
        bootstrap_fpca_spectrum_uncertainty(gaze, n_components=0)
    with pytest.raises(TypeError):
        bootstrap_fpca_spectrum_uncertainty(gaze, n_components=True)
    with pytest.raises(ValueError):
        bootstrap_fpca_spectrum_uncertainty(gaze, confidence_level=1.0)
    with pytest.raises(ValueError):
        bootstrap_fpca_spectrum_uncertainty(gaze, simultaneous_scope="all")
    with pytest.raises(ValueError):
        bootstrap_fpca_spectrum_uncertainty(
            gaze,
            resample_unit="participant",
        )
    with pytest.raises(ValueError):
        bootstrap_fpca_spectrum_uncertainty(
            gaze,
            resample_unit="curve",
            participant_column="participant_id",
        )
    with pytest.raises(ValueError):
        bootstrap_fpca_spectrum_uncertainty(gaze, resample_unit="other")


def test_reporting_and_plotting_expose_scope_and_limitations():
    gaze = sample()
    result = bootstrap_fpca_spectrum_uncertainty(
        gaze,
        n_bootstrap=20,
        n_components=2,
        simultaneous_scope="family",
        random_state=3,
    )
    text = fpca_spectrum_uncertainty_reporting_text(result)
    assert "familywise across the requested components within each spectrum metric" in text
    assert "rather than jointly across all three metrics" in text
    assert "not clipped" in text
    assert plot_fpca_spectrum_uncertainty(result, metric="eigenvalue") is not None
    assert plot_fpca_spectrum_uncertainty(
        result, metric="explained_variance_ratio"
    ) is not None
    assert plot_fpca_spectrum_uncertainty(
        result, metric="cumulative_variance_ratio"
    ) is not None
    with pytest.raises(ValueError):
        plot_fpca_spectrum_uncertainty(result, metric="unknown")
    plt.close("all")
