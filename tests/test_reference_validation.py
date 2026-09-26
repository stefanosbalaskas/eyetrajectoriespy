import math
from collections import Counter

import numpy as np
import pandas as pd
import pytest
import statsmodels.api as sm
from scipy.sparse import csr_matrix
from statsmodels.regression.mixed_linear_model import MixedLM

from eyetrajectoriespy import (
    RecurrenceResult,
    TrajectorySet,
    discrete_frechet_distance,
    discrete_transfer_entropy,
    dynamic_time_warping_distance,
    fit_fpca,
    fit_functional_mixed_effects_regression,
    fit_generalized_function_on_scalar_regression,
    rqa_metrics,
)


def _linear_basis(time):
    time = np.asarray(time, dtype=float)
    start = float(time[0])
    stop = float(time[-1])
    scaled = (time - start) / (stop - start)
    return np.column_stack((1.0 - scaled, scaled))


def _expanded_fixed_design(scalar_design, basis):
    repeated_basis = np.tile(basis, (scalar_design.shape[0], 1))
    blocks = [
        np.repeat(scalar_design[:, index], basis.shape[0])[:, None]
        * repeated_basis
        for index in range(scalar_design.shape[1])
    ]
    return np.column_stack(blocks)


def test_reference_fpca_rank_one_analytical_truth():
    time = np.array([0.0, 0.25, 1.0])
    weights = np.array([0.125, 0.5, 0.375])
    raw_shape = np.array([1.0, -1.0, 0.5])
    phi = raw_shape / np.sqrt(np.sum(weights * raw_shape**2))
    coefficients = np.array([-3.0, -1.0, 1.0, 3.0])
    values = coefficients[:, None] * phi[None, :]

    trajectories = TrajectorySet(
        time=time,
        values=values[:, :, None],
        curve_ids=tuple(f"C{i}" for i in range(values.shape[0])),
        dimension_names=("signal",),
        metadata=pd.DataFrame(index=np.arange(values.shape[0])),
        coordinate_system="arbitrary",
        time_unit="s",
    )
    result = fit_fpca(trajectories, n_components=1, scaling="none")

    # For a unit-functional-norm rank-one process X_i(t)=a_i phi(t),
    # the only non-zero FPCA eigenvalue is the sample variance of a_i.
    expected_eigenvalue = np.var(coefficients, ddof=1)
    assert result.explained_variance[0] == pytest.approx(
        expected_eigenvalue,
        rel=1e-12,
        abs=1e-12,
    )

    estimated = result.components[0, :, 0]
    signed_similarity = np.sum(weights * estimated * phi)
    assert abs(signed_similarity) == pytest.approx(1.0, abs=1e-12)

    reconstructed = (
        result.mean[None, :, :]
        + result.scores[:, :1, None, None] * result.components[None, :1, :, :]
    ).sum(axis=1)
    np.testing.assert_allclose(
        reconstructed[:, :, 0],
        values,
        rtol=1e-12,
        atol=1e-12,
    )


def _mixed_reference_data(seed=560):
    rng = np.random.default_rng(seed)
    n_participants = 14
    trials_per_participant = 3
    time = np.linspace(0.0, 1.0, 5)
    basis = _linear_basis(time)

    participants = np.repeat(
        [f"P{i:02d}" for i in range(n_participants)],
        trials_per_participant,
    )
    condition = np.tile(np.array([0.0, 0.5, 1.0]), n_participants)
    fixed_intercept = np.array([0.25, 0.45]) @ basis.T
    fixed_condition = np.array([0.15, 0.55]) @ basis.T

    random_coefficients = rng.multivariate_normal(
        mean=np.zeros(2),
        cov=np.array([[0.035, 0.006], [0.006, 0.020]]),
        size=n_participants,
    )

    values = []
    for participant_index in range(n_participants):
        random_function = random_coefficients[participant_index] @ basis.T
        for trial_index in range(trials_per_participant):
            curve_index = participant_index * trials_per_participant + trial_index
            y = (
                fixed_intercept
                + condition[curve_index] * fixed_condition
                + random_function
                + rng.normal(0.0, 0.045, size=time.size)
            )
            values.append(y[:, None])

    trajectories = TrajectorySet(
        time=time,
        values=np.asarray(values),
        curve_ids=tuple(f"M{i:03d}" for i in range(len(values))),
        dimension_names=("response",),
        metadata=pd.DataFrame({"participant_id": participants}),
        coordinate_system="arbitrary",
        time_unit="s",
    )
    design = pd.DataFrame(
        {
            "curve_id": trajectories.curve_ids,
            "condition": condition,
        }
    )
    return trajectories, design, participants, condition, basis


def test_reference_mixed_effects_matches_independent_stacked_mixedlm():
    trajectories, design, participants, condition, basis = (
        _mixed_reference_data()
    )
    result = fit_functional_mixed_effects_regression(
        trajectories,
        design,
        predictors=("condition",),
        participant_column="participant_id",
        dimension="response",
        fixed_basis_size=2,
        random_basis_size=2,
        spline_degree=1,
        reml=True,
        method="lbfgs",
        maxiter=500,
    )

    scalar_design = np.column_stack(
        (np.ones(condition.size, dtype=float), condition)
    )
    fixed_exog = _expanded_fixed_design(scalar_design, basis)
    random_exog = np.tile(basis, (condition.size, 1))
    endog = trajectories.values[:, :, 0].reshape(-1)
    groups = np.repeat(participants.astype(str), trajectories.n_time)

    direct = MixedLM(
        endog=endog,
        exog=fixed_exog,
        groups=groups,
        exog_re=random_exog,
        use_sqrt=True,
        missing="raise",
    ).fit(
        reml=True,
        method="lbfgs",
        maxiter=500,
        disp=False,
    )
    assert direct.converged

    np.testing.assert_allclose(
        result.fixed_basis_coefficients.reshape(-1),
        np.asarray(direct.fe_params, dtype=float),
        rtol=1e-8,
        atol=1e-9,
    )
    np.testing.assert_allclose(
        result.random_effect_covariance,
        np.asarray(direct.cov_re, dtype=float),
        rtol=1e-7,
        atol=1e-9,
    )
    assert result.residual_variance == pytest.approx(
        float(direct.scale),
        rel=1e-8,
        abs=1e-10,
    )
    assert result.log_likelihood == pytest.approx(
        float(direct.llf),
        rel=1e-9,
        abs=1e-9,
    )


def _poisson_exposure_reference_data(seed=561):
    rng = np.random.default_rng(seed)
    n_participants = 18
    trials_per_participant = 2
    time = np.array([0.0, 0.5, 1.0])
    basis = _linear_basis(time)

    participants = np.repeat(
        [f"P{i:02d}" for i in range(n_participants)],
        trials_per_participant,
    )
    condition = np.tile(np.array([0.0, 1.0]), n_participants)
    scalar_design = np.column_stack(
        (np.ones(condition.size, dtype=float), condition)
    )
    beta = np.array([[0.10, 0.25], [0.30, 0.05]])
    coefficient_functions = beta @ basis.T
    eta_rate = scalar_design @ coefficient_functions

    curve_scale = 0.75 + 0.5 * (
        np.arange(condition.size, dtype=float) % 4
    ) / 3.0
    exposure = curve_scale[:, None] * np.array([0.8, 1.0, 1.25])[None, :]
    mean_count = exposure * np.exp(eta_rate)
    counts = rng.poisson(mean_count).astype(float)

    trajectories = TrajectorySet(
        time=time,
        values=counts[:, :, None],
        curve_ids=tuple(f"G{i:03d}" for i in range(counts.shape[0])),
        dimension_names=("count",),
        metadata=pd.DataFrame({"participant_id": participants}),
        coordinate_system="arbitrary",
        time_unit="s",
    )
    design = pd.DataFrame(
        {
            "curve_id": trajectories.curve_ids,
            "condition": condition,
        }
    )
    return trajectories, design, participants, scalar_design, exposure, basis


def test_reference_poisson_exposure_matches_direct_stacked_gee():
    (
        trajectories,
        design,
        participants,
        scalar_design,
        exposure,
        basis,
    ) = _poisson_exposure_reference_data()

    result = fit_generalized_function_on_scalar_regression(
        trajectories,
        design,
        predictors=("condition",),
        participant_column="participant_id",
        dimension="count",
        family="poisson",
        exposure=exposure,
        exposure_units="seconds",
        basis_size=2,
        spline_degree=1,
    )

    exog = _expanded_fixed_design(scalar_design, basis)
    endog = trajectories.values[:, :, 0].reshape(-1)
    groups = np.repeat(participants.astype(str), trajectories.n_time)
    direct = sm.GEE(
        endog,
        exog,
        groups=groups,
        family=sm.families.Poisson(),
        cov_struct=sm.cov_struct.Independence(),
        exposure=exposure.reshape(-1),
    ).fit(
        maxiter=100,
        ctol=1e-8,
        cov_type="robust",
    )

    np.testing.assert_allclose(
        result.basis_coefficients.reshape(-1),
        np.asarray(direct.params, dtype=float),
        rtol=1e-9,
        atol=1e-10,
    )
    np.testing.assert_allclose(
        result.parameter_covariance,
        np.asarray(direct.cov_params(), dtype=float),
        rtol=1e-8,
        atol=1e-10,
    )

    direct_eta_rate = (exog @ np.asarray(direct.params)).reshape(
        trajectories.n_curves,
        trajectories.n_time,
    )
    direct_rate = np.exp(direct_eta_rate)
    np.testing.assert_allclose(
        result.rate_functions,
        direct_rate,
        rtol=1e-10,
        atol=1e-12,
    )
    np.testing.assert_allclose(
        result.mean_functions,
        exposure * direct_rate,
        rtol=1e-10,
        atol=1e-12,
    )


def test_reference_frechet_and_dtw_have_hand_computable_optima():
    a = np.array([[0.0], [1.0], [2.0]])
    b = np.array([[0.0], [2.0]])

    frechet = discrete_frechet_distance(a, b, return_coupling=True)
    assert frechet.distance == pytest.approx(1.0, abs=0.0)
    assert np.max(frechet.local_distances) == pytest.approx(1.0, abs=0.0)

    dtw = dynamic_time_warping_distance(
        a,
        b,
        step_pattern="symmetric1",
        return_path=True,
    )
    assert dtw.raw_distance == pytest.approx(1.0, abs=0.0)
    assert dtw.distance == pytest.approx(1.0, abs=0.0)
    assert np.sum(dtw.weighted_local_costs) == pytest.approx(1.0, abs=0.0)

    dtw2 = dynamic_time_warping_distance(
        a,
        b,
        step_pattern="symmetric2",
        normalize=True,
        return_path=True,
    )
    assert dtw2.raw_distance == pytest.approx(1.0, abs=0.0)
    assert dtw2.normalization_denominator == pytest.approx(5.0, abs=0.0)
    assert dtw2.distance == pytest.approx(0.2, abs=1e-15)


def test_reference_rqa_matches_hand_counted_cross_recurrence():
    matrix = csr_matrix(
        np.array(
            [
                [1, 0, 0, 0],
                [0, 1, 0, 0],
                [0, 0, 1, 0],
                [0, 0, 0, 0],
            ],
            dtype=bool,
        )
    )
    recurrence = RecurrenceResult(
        matrix=matrix,
        time_a=np.arange(4, dtype=float),
        time_b=np.arange(4, dtype=float),
        source_curve_ids=("a", "b"),
        radius=0.0,
        target_recurrence_rate=None,
        achieved_recurrence_rate=3 / 16,
        metric="euclidean",
        theiler_window_samples=0,
        kind="cross",
        state_dimension=1,
        time_unit="samples",
        provenance={
            "recurrence_rate_denominator": "all_cross_state_pairs",
        },
    )

    result = rqa_metrics(
        recurrence,
        min_diagonal_length=2,
        min_vertical_length=2,
    )
    assert result.recurrence_rate == pytest.approx(3 / 16, abs=0.0)
    assert result.determinism == pytest.approx(1.0, abs=0.0)
    assert result.mean_diagonal_length == pytest.approx(3.0, abs=0.0)
    assert result.max_diagonal_length == 3
    assert result.n_diagonal_lines == 1
    assert result.diagonal_entropy == pytest.approx(0.0, abs=0.0)
    assert result.laminarity == pytest.approx(0.0, abs=0.0)
    assert math.isnan(result.trapping_time)
    assert result.max_vertical_length == 0
    assert result.n_vertical_lines == 0


def _manual_te_from_counts(source, target):
    records = [
        (int(target[t]), int(target[t - 1]), int(source[t - 1]))
        for t in range(1, len(source))
    ]
    transition = Counter(records)
    joint_history = Counter((yp, xp) for _, yp, xp in records)
    target_transition = Counter((yt, yp) for yt, yp, _ in records)
    target_history = Counter(yp for _, yp, _ in records)

    total = len(records)
    value = 0.0
    for (yt, yp, xp), count in transition.items():
        probability = count / total
        ratio = (
            count * target_history[yp]
            / (joint_history[(yp, xp)] * target_transition[(yt, yp)])
        )
        value += probability * math.log2(ratio)
    return value


def test_reference_transfer_entropy_matches_exact_contingency_calculation():
    source = np.array([0, 0, 1, 1, 0], dtype=int)
    target = np.array([1, 0, 0, 1, 1], dtype=int)

    expected = _manual_te_from_counts(source, target)
    assert expected == pytest.approx(1.0, abs=0.0)

    result = discrete_transfer_entropy(
        source,
        target,
        target_history=1,
        source_history=1,
        source_lag=1,
    )
    assert result.transfer_entropy_bits == pytest.approx(
        expected,
        rel=0.0,
        abs=1e-15,
    )
    np.testing.assert_allclose(
        result.local_transfer_entropy_bits,
        np.ones(4),
        rtol=0.0,
        atol=1e-15,
    )
