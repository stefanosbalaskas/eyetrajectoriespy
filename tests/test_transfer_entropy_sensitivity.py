import matplotlib
matplotlib.use("Agg")

import numpy as np
import pytest

from eyetrajectoriespy import (
    discrete_transfer_entropy,
    transfer_entropy_circular_shift_test,
)
from eyetrajectoriespy.transfer_entropy_sensitivity import (
    TransferEntropySensitivityResult,
    plot_transfer_entropy_sensitivity,
    transfer_entropy_parameter_sensitivity,
    transfer_entropy_parameter_sensitivity_reporting_text,
)


def _directional_data(n=1400):
    rng = np.random.default_rng(42)
    source = rng.integers(0, 2, size=n)
    target = np.zeros(n, dtype=int)
    noise = rng.random(n) < 0.08
    target[1:] = np.bitwise_xor(source[:-1], noise[1:].astype(int))
    return source, target


def test_sensitivity_evaluates_full_cartesian_grid_and_matches_base_estimator():
    source, target = _directional_data()
    result = transfer_entropy_parameter_sensitivity(
        source,
        target,
        target_histories=(1, 2),
        source_histories=(1, 2),
        source_lags=(1, 2, 3),
    )

    assert isinstance(result, TransferEntropySensitivityResult)
    assert result.n_specifications == 12
    assert result.parameter_columns == (
        "target_history",
        "source_history",
        "source_lag",
    )
    assert result.has_surrogate_inference is False
    assert result.shifts is None
    assert result.provenance["automatic_specification_ranking"] is False
    assert result.provenance["failed_specification_policy"] == "raise"
    assert result.table["specification_id"].tolist() == list(range(12))

    for row in result.table.itertuples(index=False):
        direct = discrete_transfer_entropy(
            source,
            target,
            target_history=row.target_history,
            source_history=row.source_history,
            source_lag=row.source_lag,
        )
        assert row.transfer_entropy_bits == pytest.approx(
            direct.transfer_entropy_bits
        )
        assert row.n_effective == direct.n_effective
        assert row.n_joint_histories == direct.n_joint_histories
        assert row.singleton_joint_history_fraction == pytest.approx(
            direct.singleton_joint_history_fraction
        )
        assert row.mean_joint_history_count == pytest.approx(
            direct.n_effective / direct.n_joint_histories
        )
        assert np.isnan(row.surrogate_mean_bits)

    assert set(result.summary_table["metric"]) == set(result.metric_columns)


def test_correct_declared_lag_has_larger_te_for_delayed_synthetic_coupling():
    source, target = _directional_data()
    result = transfer_entropy_parameter_sensitivity(
        source,
        target,
        target_histories=(1,),
        source_histories=(1,),
        source_lags=(1, 2, 3, 4),
    )
    table = result.table.set_index("source_lag")
    assert table.loc[1, "transfer_entropy_bits"] > 0.5
    assert table.loc[1, "transfer_entropy_bits"] > table.loc[2, "transfer_entropy_bits"]
    assert table.loc[1, "transfer_entropy_bits"] > table.loc[3, "transfer_entropy_bits"]
    assert table.loc[1, "transfer_entropy_bits"] > table.loc[4, "transfer_entropy_bits"]


def test_surrogate_sensitivity_reuses_exact_same_shift_set_for_every_specification():
    source, target = _directional_data()
    shifts = tuple(range(40, 60))
    result = transfer_entropy_parameter_sensitivity(
        source,
        target,
        target_histories=(1, 2),
        source_histories=(1,),
        source_lags=(1, 2),
        shifts=shifts,
    )

    assert result.has_surrogate_inference is True
    np.testing.assert_array_equal(result.shifts, shifts)
    assert (result.table["n_shifts"] == len(shifts)).all()
    np.testing.assert_allclose(
        result.table["p_value_resolution"].to_numpy(dtype=float),
        1 / (len(shifts) + 1),
    )
    assert "surrogate_centered_transfer_entropy_bits" in result.metric_columns
    assert "upper_tail_p_value" in result.metric_columns

    for row in result.table.itertuples(index=False):
        direct = transfer_entropy_circular_shift_test(
            source,
            target,
            target_history=row.target_history,
            source_history=row.source_history,
            source_lag=row.source_lag,
            shifts=shifts,
        )
        assert row.surrogate_mean_bits == pytest.approx(
            direct.surrogate_mean_bits
        )
        assert row.surrogate_centered_transfer_entropy_bits == pytest.approx(
            direct.surrogate_centered_transfer_entropy_bits
        )
        assert row.upper_tail_p_value == pytest.approx(
            direct.upper_tail_p_value
        )


@pytest.mark.parametrize(
    "name,kwargs,error",
    [
        (
            "target_histories",
            dict(
                target_histories=(),
                source_histories=(1,),
                source_lags=(1,),
            ),
            ValueError,
        ),
        (
            "source_histories",
            dict(
                target_histories=(1,),
                source_histories="1,2",
                source_lags=(1,),
            ),
            TypeError,
        ),
        (
            "source_lags",
            dict(
                target_histories=(1,),
                source_histories=(1,),
                source_lags=(1, 1),
            ),
            ValueError,
        ),
        (
            "target_histories",
            dict(
                target_histories=(True,),
                source_histories=(1,),
                source_lags=(1,),
            ),
            TypeError,
        ),
        (
            "source_histories",
            dict(
                target_histories=(1,),
                source_histories=(0,),
                source_lags=(1,),
            ),
            ValueError,
        ),
    ],
)
def test_sensitivity_grid_validation_fails_closed(name, kwargs, error):
    source, target = _directional_data(100)
    with pytest.raises(error, match=name):
        transfer_entropy_parameter_sensitivity(source, target, **kwargs)


def test_invalid_declared_specification_aborts_with_combination_identified():
    source = np.array([0, 1, 0, 1, 0], dtype=int)
    target = np.array([0, 0, 1, 0, 1], dtype=int)

    with pytest.raises(
        ValueError,
        match=r"target_history=6, source_history=1, source_lag=1",
    ):
        transfer_entropy_parameter_sensitivity(
            source,
            target,
            target_histories=(1, 6),
            source_histories=(1,),
            source_lags=(1,),
        )


def test_continuous_inputs_are_not_silently_discretized():
    source = np.array([0.1, 0.2, 0.3, 0.4])
    target = np.array([0.2, 0.1, 0.4, 0.3])
    with pytest.raises(ValueError, match="discretize explicitly upstream"):
        transfer_entropy_parameter_sensitivity(
            source,
            target,
            target_histories=(1,),
            source_histories=(1,),
            source_lags=(1,),
        )


def test_plot_requires_explicit_slice_and_never_hidden_average():
    source, target = _directional_data()
    result = transfer_entropy_parameter_sensitivity(
        source,
        target,
        target_histories=(1, 2),
        source_histories=(1, 2),
        source_lags=(1, 2, 3),
    )

    with pytest.raises(ValueError, match="refuses hidden averaging"):
        plot_transfer_entropy_sensitivity(
            result,
            parameter="source_lag",
        )

    ax = plot_transfer_entropy_sensitivity(
        result,
        parameter="source_lag",
        filters={"target_history": 1, "source_history": 1},
    )
    assert ax.get_xlabel() == "source lag"
    assert ax.get_ylabel() == "transfer entropy bits"

    with pytest.raises(ValueError, match="must not include"):
        plot_transfer_entropy_sensitivity(
            result,
            parameter="source_lag",
            filters={"source_lag": 1},
        )
    with pytest.raises(KeyError, match="Unknown sensitivity filter"):
        plot_transfer_entropy_sensitivity(
            result,
            parameter="source_lag",
            filters={"unknown": 1},
        )
    with pytest.raises(ValueError, match="selected no specifications"):
        plot_transfer_entropy_sensitivity(
            result,
            parameter="source_lag",
            filters={"target_history": 99, "source_history": 1},
        )


def test_plot_and_reporting_validation_and_scope_language():
    source, target = _directional_data()
    result = transfer_entropy_parameter_sensitivity(
        source,
        target,
        target_histories=(1,),
        source_histories=(1,),
        source_lags=(1, 2),
        shifts=range(40, 50),
    )

    text = transfer_entropy_parameter_sensitivity_reporting_text(result)
    assert "predeclared combinations" in text
    assert "same 10 analyst-declared circular source shifts" in text
    assert "no specification was selected or ranked automatically" in text
    assert "not multiplicity-adjusted causal evidence" in text

    with pytest.raises(TypeError):
        transfer_entropy_parameter_sensitivity_reporting_text(object())
    with pytest.raises(TypeError):
        plot_transfer_entropy_sensitivity(
            object(),
            parameter="source_lag",
        )
    with pytest.raises(KeyError, match="metric must be one of"):
        plot_transfer_entropy_sensitivity(
            result,
            parameter="source_lag",
            metric="not_a_metric",
        )
    with pytest.raises(KeyError, match="parameter must be one of"):
        plot_transfer_entropy_sensitivity(
            result,
            parameter="not_a_parameter",
        )
    with pytest.raises(TypeError, match="filter value"):
        plot_transfer_entropy_sensitivity(
            result,
            parameter="source_lag",
            filters={"target_history": True},
        )
