from dataclasses import replace

import numpy as np
import pandas as pd
import pytest

from eyetrajectoriespy import (
    FunctionalSimulationScenario,
    SparseMFPCAResult,
    evaluate_sparse_mfpca_recovery,
    functional_recovery_assessment_frame,
    functional_trapezoid_weights,
    simulate_functional_scenario,
)


def _mean(time):
    time = np.asarray(time, dtype=float)
    return np.column_stack(
        [
            0.20 + 0.05 * time,
            0.35 - 0.03 * time,
        ]
    )


def _u(time):
    time = np.asarray(time, dtype=float)
    return np.sqrt(2.0) * np.sin(np.pi * time)


def _v(time):
    time = np.asarray(time, dtype=float)
    return np.sqrt(2.0) * np.sin(2.0 * np.pi * time)


def _axis_x(time):
    values = _u(time)
    return np.column_stack([values, np.zeros_like(values)])


def _axis_y(time):
    values = _u(time)
    return np.column_stack([np.zeros_like(values), values])


def _asym_plus(time):
    return np.column_stack([_u(time), _v(time)]) / np.sqrt(2.0)


def _asym_minus(time):
    return np.column_stack([_u(time), -_v(time)]) / np.sqrt(2.0)


def _simulate(eigenvalues, eigenfunctions, *, noise_covariance=None):
    grid = np.linspace(0.0, 1.0, 41)
    scenario = FunctionalSimulationScenario(
        name="sparse-mfpca-recovery-test",
        truth_grid=grid,
        eigenvalues=eigenvalues,
        n_participants=24,
        dimension_names=("x", "y"),
        coordinate_system="normalized",
        time_unit="normalized",
        observation_design="irregular",
        samples_per_curve=(14, 18),
        measurement_noise_sd=(
            0.0 if noise_covariance is not None else (0.0, 0.0)
        ),
        measurement_noise_covariance=noise_covariance,
        replicates=1,
        seed_start=923,
    )
    return simulate_functional_scenario(
        scenario,
        mean=_mean,
        eigenfunctions=eigenfunctions,
    )


def _truth_blocks(truth):
    values = np.asarray(truth.eigenvalues, dtype=float)
    functions = np.asarray(truth.eigenfunctions, dtype=float)
    x = functions[:, :, 0]
    y = functions[:, :, 1]
    return {
        "cxx": np.einsum("k,ks,kt->st", values, x, x),
        "cxy": np.einsum("k,ks,kt->st", values, x, y),
        "cyx": np.einsum("k,ks,kt->st", values, y, x),
        "cyy": np.einsum("k,ks,kt->st", values, y, y),
    }


def _exact_result(simulation, *, eigenfunctions=None, scores=None):
    truth = simulation.truth
    grid = truth.truth_grid
    weights = functional_trapezoid_weights(grid)
    functions = (
        truth.eigenfunctions.copy()
        if eigenfunctions is None
        else np.asarray(eigenfunctions, dtype=float)
    )
    fitted_scores = (
        truth.scores.copy()
        if scores is None
        else np.asarray(scores, dtype=float)
    )
    blocks = _truth_blocks(truth)
    n_components = functions.shape[0]
    diagnostics = pd.DataFrame(
        {
            "curve_id": [
                f"curve-{index}" for index in range(truth.scores.shape[0])
            ],
            "status_code": ["ok"] * truth.scores.shape[0],
            "condition_number": np.linspace(
                5.0,
                20.0,
                truth.scores.shape[0],
            ),
        }
    )
    return SparseMFPCAResult(
        scores=fitted_scores,
        eigenvalues=truth.eigenvalues[:n_components].copy(),
        eigenfunctions=functions,
        mean=truth.mean.copy(),
        evaluation_grid=grid.copy(),
        dimensions=("x", "y"),
        curve_ids=tuple(
            f"curve-{index}" for index in range(truth.scores.shape[0])
        ),
        metadata=truth.metadata.reset_index(drop=True).copy(),
        coordinate_system=truth.coordinate_system,
        time_unit=truth.time_unit,
        n_components=n_components,
        quadrature_weights=weights,
        smoothed_cxx=blocks["cxx"].copy(),
        smoothed_cxy=blocks["cxy"].copy(),
        smoothed_cyx=blocks["cyx"].copy(),
        smoothed_cyy=blocks["cyy"].copy(),
        covariance_cxx=blocks["cxx"].copy(),
        covariance_cxy=blocks["cxy"].copy(),
        covariance_cyx=blocks["cyx"].copy(),
        covariance_cyy=blocks["cyy"].copy(),
        measurement_error_covariance=(
            truth.measurement_noise_covariance.copy()
        ),
        score_diagnostics=diagnostics,
        mean_support_counts=np.ones((grid.size, 2), dtype=int),
        covariance_support_counts={
            "cxx": np.ones((grid.size, grid.size), dtype=int),
            "cxy": np.ones((grid.size, grid.size), dtype=int),
            "cyy": np.ones((grid.size, grid.size), dtype=int),
        },
        covariance_pair_counts={"xx": 100, "xy": 100, "yy": 100},
        covariance_diagnostics={
            "applied_action": "none",
            "relative_operator_correction_frobenius_norm": 0.0,
        },
        fit_method="direct_sparse_block_covariance",
        score_method="joint_PACE",
        provenance={
            "sparse_mfpca": {
                "measurement_error_mode": "fixed_matrix",
            }
        },
    )


def test_sparse_mfpca_recovery_is_block_aware_for_asymmetric_cross_covariance():
    simulation = _simulate(
        (1.20, 0.45),
        (_asym_plus, _asym_minus),
    )
    truth = simulation.truth
    blocks = _truth_blocks(truth)
    assert not np.allclose(blocks["cxy"], blocks["cxy"].T)
    np.testing.assert_allclose(blocks["cyx"], blocks["cxy"].T)

    assessment = evaluate_sparse_mfpca_recovery(
        _exact_result(simulation),
        truth,
    )
    frame = functional_recovery_assessment_frame(assessment)
    block = frame.loc[
        frame["metric"] == "covariance_block_ise",
        ["source", "value"],
    ].set_index("source")["value"]

    assert set(block.index) == {"cxx", "cxy", "cyx", "cyy"}
    np.testing.assert_allclose(block.to_numpy(), 0.0, atol=1e-12)
    covariance_ise = frame.loc[
        frame["metric"] == "covariance_ise", "value"
    ].iloc[0]
    assert covariance_ise == pytest.approx(0.0, abs=1e-12)
    assert assessment.provenance["covariance_recovery"] == (
        "named_block_quadrature_ise"
    )


def test_joint_covariance_ise_is_sum_of_named_block_errors():
    simulation = _simulate(
        (1.20, 0.45),
        (_asym_plus, _asym_minus),
    )
    exact = _exact_result(simulation)
    perturbation = np.full_like(exact.covariance_cxy, 0.05)
    modified = SparseMFPCAResult(
        **{
            **exact.__dict__,
            "covariance_cxy": exact.covariance_cxy + perturbation,
            "covariance_cyx": (
                exact.covariance_cxy + perturbation
            ).T,
        }
    )
    assessment = evaluate_sparse_mfpca_recovery(
        modified,
        simulation.truth,
    )
    frame = functional_recovery_assessment_frame(assessment)
    blocks = frame.loc[
        frame["metric"] == "covariance_block_ise",
        ["source", "value"],
    ].set_index("source")["value"]
    joint = float(
        frame.loc[
            frame["metric"] == "covariance_ise",
            "value",
        ].iloc[0]
    )

    assert blocks["cxx"] == pytest.approx(0.0, abs=1e-12)
    assert blocks["cyy"] == pytest.approx(0.0, abs=1e-12)
    assert blocks["cxy"] > 0
    assert blocks["cyx"] == pytest.approx(blocks["cxy"])
    assert joint == pytest.approx(
        blocks["cxx"]
        + blocks["cxy"]
        + blocks["cyx"]
        + blocks["cyy"]
    )
    assert joint == pytest.approx(2.0 * blocks["cxy"])


def test_tied_truth_uses_subspace_and_procrustes_not_component_score_metrics():
    simulation = _simulate(
        (1.0, 1.0),
        (_axis_x, _axis_y),
    )
    truth = simulation.truth
    angle = np.deg2rad(37.0)
    rotation = np.array(
        [
            [np.cos(angle), -np.sin(angle)],
            [np.sin(angle), np.cos(angle)],
        ]
    )
    rotated_functions = np.einsum(
        "ab,btd->atd",
        rotation.T,
        truth.eigenfunctions,
    )
    rotated_scores = truth.scores @ rotation

    assessment = evaluate_sparse_mfpca_recovery(
        _exact_result(
            simulation,
            eigenfunctions=rotated_functions,
            scores=rotated_scores,
        ),
        truth,
    )
    frame = functional_recovery_assessment_frame(assessment)

    assert not (
        frame["metric"] == "component_absolute_similarity"
    ).any()
    assert not (frame["metric"] == "score_correlation").any()
    assert not (frame["metric"] == "score_rmse").any()

    tied = frame.loc[
        frame["source"] == "truth_components_1_2"
    ]
    cosines = tied.loc[
        tied["metric"] == "subspace_principal_cosine",
        "value",
    ].to_numpy()
    np.testing.assert_allclose(cosines, 1.0, atol=1e-12)
    procrustes = tied.loc[
        tied["metric"] == "score_subspace_procrustes_rmse",
        "value",
    ].iloc[0]
    assert procrustes == pytest.approx(0.0, abs=1e-12)
    assert assessment.provenance[
        "component_metrics_omitted_for_tied_eigenspaces"
    ] is True


def test_separated_truth_retains_component_score_recovery_metrics():
    simulation = _simulate(
        (1.25, 0.55),
        (_asym_plus, _asym_minus),
    )
    assessment = evaluate_sparse_mfpca_recovery(
        _exact_result(simulation),
        simulation.truth,
    )
    frame = functional_recovery_assessment_frame(assessment)

    assert (
        frame["metric"] == "component_absolute_similarity"
    ).sum() == 2
    assert (frame["metric"] == "score_correlation").sum() == 2
    assert (frame["metric"] == "score_rmse").sum() == 2
    assert not (
        frame["metric"] == "score_subspace_procrustes_rmse"
    ).any()


def test_measurement_error_truth_is_provenance_not_recovery_metric():
    covariance = np.array(
        [
            [0.0009, 0.0003],
            [0.0003, 0.0016],
        ]
    )
    simulation = _simulate(
        (1.20, 0.45),
        (_asym_plus, _asym_minus),
        noise_covariance=covariance,
    )
    assessment = evaluate_sparse_mfpca_recovery(
        _exact_result(simulation),
        simulation.truth,
    )
    frame = functional_recovery_assessment_frame(assessment)

    assert assessment.provenance[
        "measurement_error_truth_supplied"
    ] is True
    assert assessment.provenance[
        "measurement_error_recovery_metric_reported"
    ] is False
    assert not frame["metric"].str.startswith(
        "noise_variance"
    ).any()


def test_sparse_mfpca_recovery_rejects_partial_tied_truth_eigenspace():
    simulation = _simulate(
        (1.0, 1.0),
        (_axis_x, _axis_y),
    )
    exact = _exact_result(simulation)
    partial = SparseMFPCAResult(
        **{
            **exact.__dict__,
            "scores": exact.scores[:, :1],
            "eigenvalues": exact.eigenvalues[:1],
            "eigenfunctions": exact.eigenfunctions[:1],
            "n_components": 1,
        }
    )
    with pytest.raises(ValueError, match="split a tied truth eigenspace"):
        evaluate_sparse_mfpca_recovery(
            partial,
            simulation.truth,
        )


def test_sparse_mfpca_recovery_fails_closed_on_public_contract_mismatches():
    simulation = _simulate(
        (1.20, 0.45),
        (_asym_plus, _asym_minus),
    )
    truth = simulation.truth
    exact = _exact_result(simulation)

    with pytest.raises(TypeError, match="SparseMFPCAResult"):
        evaluate_sparse_mfpca_recovery(object(), truth)
    with pytest.raises(TypeError, match="FunctionalSimulationTruth"):
        evaluate_sparse_mfpca_recovery(exact, object())

    with pytest.raises(ValueError, match="dimension names/order"):
        evaluate_sparse_mfpca_recovery(
            replace(exact, dimensions=("y", "x")),
            truth,
        )

    one_dimension_truth = replace(
        truth,
        dimension_names=("x",),
    )
    with pytest.raises(ValueError, match="exactly two dimensions"):
        evaluate_sparse_mfpca_recovery(
            replace(exact, dimensions=("x",)),
            one_dimension_truth,
        )

    with pytest.raises(ValueError, match="mean.*identical shape"):
        evaluate_sparse_mfpca_recovery(
            replace(exact, mean=exact.mean[:, :1]),
            truth,
        )

    with pytest.raises(ValueError, match="eigenfunctions"):
        evaluate_sparse_mfpca_recovery(
            replace(
                exact,
                eigenfunctions=exact.eigenfunctions[:, :, :1],
            ),
            truth,
        )

    with pytest.raises(ValueError, match="eigenvalues"):
        evaluate_sparse_mfpca_recovery(
            replace(exact, eigenvalues=exact.eigenvalues[:1]),
            truth,
        )

    with pytest.raises(ValueError, match="scores"):
        evaluate_sparse_mfpca_recovery(
            replace(exact, scores=exact.scores[:, :1]),
            truth,
        )

    with pytest.raises(ValueError, match="quadrature weights"):
        evaluate_sparse_mfpca_recovery(
            replace(
                exact,
                quadrature_weights=2.0 * exact.quadrature_weights,
            ),
            truth,
        )


def test_sparse_mfpca_recovery_fails_closed_on_invalid_covariance_blocks():
    simulation = _simulate(
        (1.20, 0.45),
        (_asym_plus, _asym_minus),
    )
    truth = simulation.truth
    exact = _exact_result(simulation)

    with pytest.raises(ValueError, match="match the truth-grid geometry"):
        evaluate_sparse_mfpca_recovery(
            replace(
                exact,
                covariance_cxy=exact.covariance_cxy[:-1, :],
            ),
            truth,
        )

    nonfinite = exact.covariance_cxy.copy()
    nonfinite[0, 0] = np.nan
    with pytest.raises(ValueError, match="must be finite"):
        evaluate_sparse_mfpca_recovery(
            replace(exact, covariance_cxy=nonfinite),
            truth,
        )


def test_sparse_mfpca_recovery_handles_missing_optional_diagnostics_explicitly():
    simulation = _simulate(
        (1.20, 0.45),
        (_asym_plus, _asym_minus),
    )
    exact = _exact_result(simulation)
    result = replace(
        exact,
        score_diagnostics=pd.DataFrame(),
        covariance_diagnostics={},
    )
    assessment = evaluate_sparse_mfpca_recovery(
        result,
        simulation.truth,
    )
    frame = functional_recovery_assessment_frame(assessment)

    failure = frame.loc[
        frame["metric"] == "score_failure_rate",
        "value",
    ].iloc[0]
    assert failure == pytest.approx(0.0)
    assert not (frame["metric"] == "psd_repair_applied").any()
    assert not (
        frame["metric"] == "psd_relative_operator_correction"
    ).any()


def test_tied_recovery_retains_subspace_when_scores_are_not_recoverable():
    simulation = _simulate(
        (1.0, 1.0),
        (_axis_x, _axis_y),
    )
    exact = _exact_result(simulation)
    sparse_scores = np.full_like(exact.scores, np.nan)

    assessment = evaluate_sparse_mfpca_recovery(
        replace(exact, scores=sparse_scores),
        simulation.truth,
    )
    frame = functional_recovery_assessment_frame(assessment)

    assert not (
        frame["metric"] == "score_subspace_procrustes_rmse"
    ).any()
    assert (
        frame["metric"] == "subspace_principal_cosine"
    ).any()
    assert not (
        frame["metric"] == "reconstruction_ise"
    ).any()


def test_measurement_error_truth_supplied_flag_can_be_false_without_fake_metric():
    covariance = np.array(
        [
            [0.0009, 0.0003],
            [0.0003, 0.0016],
        ]
    )
    simulation = _simulate(
        (1.20, 0.45),
        (_asym_plus, _asym_minus),
        noise_covariance=covariance,
    )
    exact = _exact_result(simulation)
    assessment = evaluate_sparse_mfpca_recovery(
        replace(
            exact,
            measurement_error_covariance=np.diag(
                np.diag(covariance)
            ),
        ),
        simulation.truth,
    )
    frame = functional_recovery_assessment_frame(assessment)

    assert assessment.provenance[
        "measurement_error_truth_supplied"
    ] is False
    assert not frame["metric"].str.startswith(
        "noise_variance"
    ).any()
