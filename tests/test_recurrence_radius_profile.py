import numpy as np
import pytest

from eyetrajectoriespy import (
    TrajectorySet,
    delay_embed_trajectory,
    recurrence_matrix,
    recurrence_radius_profile,
)


def _scalar(values, *, time=None):
    values = np.asarray(values, dtype=float)
    if time is None:
        time = np.arange(values.size, dtype=float)
    return TrajectorySet(
        time=np.asarray(time, dtype=float),
        values=values[None, :, None],
        curve_ids=("c1",),
        dimension_names=("x",),
        time_unit="samples",
        coordinate_system="arbitrary",
    )


def test_radius_profile_matches_hand_pairwise_distance_cdf():
    data = _scalar([0.0, 1.0, 3.0])
    result = recurrence_radius_profile(
        data,
        curve=0,
        radii=(0.5, 1.0, 2.0, 3.0),
        dimensions=("x",),
    )

    assert result.eligible_pair_count == 3
    assert result.n_radii == 4
    np.testing.assert_array_equal(
        result.table["cumulative_recurrent_pairs"].to_numpy(),
        np.array([0, 1, 2, 3]),
    )
    np.testing.assert_allclose(
        result.table["recurrence_rate"].to_numpy(),
        np.array([0.0, 1 / 3, 2 / 3, 1.0]),
    )
    np.testing.assert_array_equal(
        result.table["shell_pair_count"].to_numpy(),
        np.array([0, 1, 1, 1]),
    )
    np.testing.assert_allclose(
        result.table["shell_pair_fraction"].to_numpy(),
        np.array([0.0, 1 / 3, 1 / 3, 1 / 3]),
    )
    assert np.isnan(result.table.loc[0, "previous_radius"])
    assert result.table.loc[1, "previous_radius"] == pytest.approx(0.5)
    assert result.provenance["distance_matrix_materialized"] is False
    assert result.provenance["automatic_radius_selection"] is False
    assert result.provenance["full_distance_distribution_captured"] is True


def test_radius_profile_applies_same_theiler_denominator_and_exclusion():
    data = _scalar([0.0, 1.0, 3.0])
    result = recurrence_radius_profile(
        data,
        curve=0,
        radii=(1.0, 2.0, 3.0),
        theiler_window=1,
        dimensions=("x",),
    )

    assert result.eligible_pair_count == 1
    np.testing.assert_array_equal(
        result.table["cumulative_recurrent_pairs"].to_numpy(),
        np.array([0, 0, 1]),
    )
    np.testing.assert_array_equal(
        result.table["excluded_theiler_pairs_within_radius"].to_numpy(),
        np.array([1, 2, 2]),
    )
    np.testing.assert_allclose(
        result.table["recurrence_rate"].to_numpy(),
        np.array([0.0, 0.0, 1.0]),
    )


def test_radius_profile_first_shell_includes_zero_distance_pairs():
    data = _scalar([0.0, 0.0, 1.0])
    result = recurrence_radius_profile(
        data,
        curve=0,
        radii=(0.1, 1.0),
        dimensions=("x",),
    )

    np.testing.assert_array_equal(
        result.table["shell_pair_count"].to_numpy(),
        np.array([1, 2]),
    )
    np.testing.assert_allclose(
        result.table["recurrence_rate"].to_numpy(),
        np.array([1 / 3, 1.0]),
    )


@pytest.mark.parametrize("theiler", [0, 1, 2])
def test_radius_profile_matches_recurrence_matrix_at_every_declared_radius(theiler):
    data = _scalar(np.sin(np.linspace(0.0, 4.0 * np.pi, 40)))
    radii = (0.05, 0.10, 0.20, 0.40)
    profile = recurrence_radius_profile(
        data,
        curve=0,
        radii=radii,
        theiler_window=theiler,
        dimensions=("x",),
    )

    expected = []
    for radius in radii:
        recurrence = recurrence_matrix(
            data,
            curve=0,
            radius=radius,
            theiler_window=theiler,
            dimensions=("x",),
        )
        expected.append(recurrence.achieved_recurrence_rate)

    np.testing.assert_allclose(
        profile.table["recurrence_rate"].to_numpy(),
        np.asarray(expected),
        rtol=0,
        atol=0,
    )


def test_radius_profile_supports_delay_embedded_state_without_dimensions_argument():
    data = _scalar(np.sin(np.linspace(0.0, 6.0 * np.pi, 60)))
    embedding = delay_embed_trajectory(
        data,
        embedding_dimension=3,
        delay=2,
        dimensions=("x",),
    )
    result = recurrence_radius_profile(
        embedding,
        curve=0,
        radii=(0.1, 0.2, 0.4),
        theiler_window=2,
    )

    assert result.state_dimension == 3
    assert result.provenance["source_kind"] == "DelayEmbeddingResult"
    assert result.provenance["embedding_dimension"] == 3
    assert result.provenance["delay_samples"] == 2


def test_radius_profile_requires_explicit_dimensions_for_raw_trajectory():
    data = _scalar([0.0, 1.0, 0.0, 1.0])
    with pytest.raises(ValueError, match="dimensions must be supplied explicitly"):
        recurrence_radius_profile(
            data,
            curve=0,
            radii=(0.1, 0.2),
        )


@pytest.mark.parametrize(
    "radii, match",
    [
        ((0.1,), "at least two"),
        ((0.2, 0.1), "strictly increasing"),
        ((0.1, 0.1), "strictly increasing"),
        ((0.0, 0.1), "positive finite"),
        ((0.1, np.inf), "positive finite"),
    ],
)
def test_radius_profile_rejects_invalid_radius_grids(radii, match):
    data = _scalar([0.0, 1.0, 2.0, 3.0])
    with pytest.raises(ValueError, match=match):
        recurrence_radius_profile(
            data,
            curve=0,
            radii=radii,
            dimensions=("x",),
        )


def test_radius_profile_requires_non_string_radius_sequence():
    data = _scalar([0.0, 1.0, 2.0, 3.0])
    with pytest.raises(TypeError, match="non-string"):
        recurrence_radius_profile(
            data,
            curve=0,
            radii="0.1,0.2",
            dimensions=("x",),
        )


def test_radius_profile_reports_partial_distribution_coverage():
    data = _scalar([0.0, 1.0, 3.0])
    result = recurrence_radius_profile(
        data,
        curve=0,
        radii=(0.25, 0.5),
        dimensions=("x",),
    )
    assert result.provenance["maximum_radius_coverage_fraction"] == pytest.approx(0.0)
    assert result.provenance["full_distance_distribution_captured"] is False


def test_radius_profile_fails_when_theiler_leaves_no_eligible_pairs():
    data = _scalar([0.0, 1.0, 2.0, 3.0])
    with pytest.raises(ValueError, match="no eligible recurrence pairs"):
        recurrence_radius_profile(
            data,
            curve=0,
            radii=(0.5, 1.0),
            theiler_window=3,
            dimensions=("x",),
        )
