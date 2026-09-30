"""Two-stage and external-comparator fixtures for 0.12 sparse MFPCA sensitivity.

This validation runner does not create another public estimator. The two-stage
route is an internal benchmark: fit univariate sparse FPCA/PACE bases for x/y,
form the empirical covariance of concatenated marginal scores, and diagonalize
that covariance to obtain a joint basis. The direct public estimator remains
the canonical 0.12 method.

The same deterministic rho_xy=0.6 fixture can also be exported for mGSFPCA
0.2.2. No architecture winner or tuning value is selected here.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd

from eyetrajectoriespy import (
    FunctionalSimulationScenario,
    fit_sparse_fpca,
    fit_sparse_mfpca,
    functional_trapezoid_weights,
    simulate_functional_scenario,
)


GRID_SIZE = 51
RHO_XY = 0.6
MARGINAL_RANKS = (1, 2)
MEASUREMENT_ERROR_VARIANCE = (0.0009, 0.0009)


def _mean_planar(time: np.ndarray) -> np.ndarray:
    time = np.asarray(time, dtype=float)
    return np.column_stack(
        (
            0.50 + 0.04 * np.sin(np.pi * time),
            0.50 + 0.04 * np.cos(np.pi * time),
        )
    )


def _scalar_mode(frequency: int) -> Callable[[np.ndarray], np.ndarray]:
    def mode(time: np.ndarray) -> np.ndarray:
        time = np.asarray(time, dtype=float)
        return np.sqrt(2.0) * np.sin(frequency * np.pi * time)

    return mode


def _vector_mode(
    scalar: Callable[[np.ndarray], np.ndarray],
    loading: np.ndarray,
) -> Callable[[np.ndarray], np.ndarray]:
    loading_array = np.asarray(loading, dtype=float).copy()

    def mode(time: np.ndarray) -> np.ndarray:
        values = scalar(np.asarray(time, dtype=float))
        return values[:, None] * loading_array[None, :]

    return mode


def planar_rho_design(
    rho_xy: float,
) -> tuple[tuple[float, ...], tuple[Callable[[np.ndarray], np.ndarray], ...]]:
    rho = float(rho_xy)
    if not np.isfinite(rho) or rho <= -1.0 or rho >= 1.0:
        raise ValueError("rho_xy must satisfy -1 < rho_xy < 1")
    plus = np.array([1.0, 1.0]) / np.sqrt(2.0)
    minus = np.array([1.0, -1.0]) / np.sqrt(2.0)
    temporal = ((_scalar_mode(1), 1.0), (_scalar_mode(2), 0.45))
    channel = ((plus, 1.0 + rho), (minus, 1.0 - rho))
    pairs: list[
        tuple[float, Callable[[np.ndarray], np.ndarray]]
    ] = []
    for scalar, temporal_value in temporal:
        for loading, channel_value in channel:
            pairs.append(
                (
                    float(temporal_value * channel_value),
                    _vector_mode(scalar, loading),
                )
            )
    pairs.sort(key=lambda item: item[0], reverse=True)
    return (
        tuple(item[0] for item in pairs),
        tuple(item[1] for item in pairs),
    )


def _scenario(
    *,
    name: str,
    seed: int,
    n_participants: int = 30,
) -> FunctionalSimulationScenario:
    eigenvalues, _ = planar_rho_design(RHO_XY)
    return FunctionalSimulationScenario(
        name=name,
        truth_grid=np.linspace(0.0, 1.0, GRID_SIZE),
        eigenvalues=eigenvalues,
        n_participants=n_participants,
        dimension_names=("x", "y"),
        coordinate_system="normalized",
        time_unit="normalized",
        observation_design="irregular",
        samples_per_curve=(20, 32),
        irregular_time_design="uniform",
        measurement_noise_sd=(0.03, 0.03),
        replicates=1,
        seed_start=seed,
        labels={
            "validation": "0.12-comparator-sensitivity",
            "rho_xy": RHO_XY,
            "architecture_winner_selected": False,
        },
    )


def _simulate(*, seed: int = 15100, n_participants: int = 30):
    scenario = _scenario(
        name="sparse_mfpca_comparator_fixture",
        seed=seed,
        n_participants=n_participants,
    )
    _, eigenfunctions = planar_rho_design(RHO_XY)
    return simulate_functional_scenario(
        scenario,
        mean=_mean_planar,
        eigenfunctions=eigenfunctions,
    )


def _fit_direct(simulation):
    truth = simulation.truth
    return fit_sparse_mfpca(
        simulation.observations,
        dimensions=("x", "y"),
        n_components=len(truth.eigenvalues),
        evaluation_grid=np.asarray(truth.truth_grid, dtype=float),
        mean_bandwidth=0.20,
        covariance_bandwidth=0.28,
        measurement_error="diagonal",
        measurement_error_variance=MEASUREMENT_ERROR_VARIANCE,
        psd_action="project",
        score_failure_action="retain_nan",
        covariance_min_local_pairs=8,
    )


def _fit_marginal(simulation, dimension: str, rank: int):
    index = simulation.truth.dimension_names.index(dimension)
    return fit_sparse_fpca(
        simulation.observations,
        dimension=dimension,
        n_components=int(rank),
        evaluation_grid=np.asarray(
            simulation.truth.truth_grid,
            dtype=float,
        ),
        mean_bandwidth=0.20,
        covariance_bandwidth=0.28,
        noise_variance_method="fixed",
        measurement_error_variance=MEASUREMENT_ERROR_VARIANCE[index],
        psd_action="project",
        score_failure_action="retain_nan",
    )


def two_stage_benchmark(simulation, marginal_rank: int) -> dict[str, object]:
    """Construct the internal marginal-basis two-stage comparator."""

    rank = int(marginal_rank)
    if rank not in MARGINAL_RANKS:
        raise ValueError(
            f"marginal_rank must be one of {MARGINAL_RANKS}"
        )
    fit_x = _fit_marginal(simulation, "x", rank)
    fit_y = _fit_marginal(simulation, "y", rank)

    scores_x = np.asarray(fit_x.scores, dtype=float)
    scores_y = np.asarray(fit_y.scores, dtype=float)
    concatenated = np.column_stack([scores_x, scores_y])
    finite_rows = np.all(np.isfinite(concatenated), axis=1)
    if np.count_nonzero(finite_rows) < 3:
        raise RuntimeError(
            "too few complete marginal score rows for two-stage covariance"
        )
    centered = concatenated - np.nanmean(
        concatenated[finite_rows],
        axis=0,
        keepdims=True,
    )
    score_covariance = np.cov(
        centered[finite_rows],
        rowvar=False,
        ddof=1,
    )
    score_covariance = 0.5 * (
        score_covariance + score_covariance.T
    )
    values, vectors = np.linalg.eigh(score_covariance)
    order = np.argsort(values)[::-1]
    values = values[order]
    vectors = vectors[:, order]
    positive = values > 1e-12
    values = values[positive]
    vectors = vectors[:, positive]
    n_joint = min(2 * rank, values.size)
    values = values[:n_joint]
    vectors = vectors[:, :n_joint]

    grid = np.asarray(simulation.truth.truth_grid, dtype=float)
    joint_functions = np.zeros(
        (n_joint, grid.size, 2),
        dtype=float,
    )
    basis_x = np.asarray(fit_x.eigenfunctions, dtype=float)
    basis_y = np.asarray(fit_y.eigenfunctions, dtype=float)
    joint_functions[:, :, 0] = (
        vectors[:rank, :].T @ basis_x
    )
    joint_functions[:, :, 1] = (
        vectors[rank:, :].T @ basis_y
    )
    joint_scores = centered @ vectors
    mean = np.column_stack(
        [
            np.asarray(fit_x.mean, dtype=float),
            np.asarray(fit_y.mean, dtype=float),
        ]
    )

    cxx = np.einsum(
        "k,ks,kt->st",
        values,
        joint_functions[:, :, 0],
        joint_functions[:, :, 0],
        optimize=True,
    )
    cxy = np.einsum(
        "k,ks,kt->st",
        values,
        joint_functions[:, :, 0],
        joint_functions[:, :, 1],
        optimize=True,
    )
    cyy = np.einsum(
        "k,ks,kt->st",
        values,
        joint_functions[:, :, 1],
        joint_functions[:, :, 1],
        optimize=True,
    )
    reconstruction = mean[None, :, :] + np.einsum(
        "nk,ktd->ntd",
        joint_scores,
        joint_functions,
        optimize=True,
    )
    return {
        "marginal_rank": rank,
        "eigenvalues": values,
        "eigenfunctions": joint_functions,
        "scores": joint_scores,
        "mean": mean,
        "covariance_blocks": {
            "cxx": cxx,
            "cxy": cxy,
            "cyx": cxy.T,
            "cyy": cyy,
        },
        "reconstruction": reconstruction,
        "finite_score_rows": finite_rows,
        "score_covariance": score_covariance,
        "provenance": {
            "route": "two_stage_marginal_sparse_bases",
            "marginal_rank_x": rank,
            "marginal_rank_y": rank,
            "joint_basis_source": "empirical_covariance_of_concatenated_marginal_PACE_scores",
            "automatic_rank_selection": False,
            "architecture_winner_selected": False,
        },
    }


def _truth_blocks(truth) -> dict[str, np.ndarray]:
    functions = np.asarray(truth.eigenfunctions, dtype=float)
    values = np.asarray(truth.eigenvalues, dtype=float)
    return {
        "cxx": np.einsum(
            "k,ks,kt->st",
            values,
            functions[:, :, 0],
            functions[:, :, 0],
            optimize=True,
        ),
        "cxy": np.einsum(
            "k,ks,kt->st",
            values,
            functions[:, :, 0],
            functions[:, :, 1],
            optimize=True,
        ),
        "cyx": np.einsum(
            "k,ks,kt->st",
            values,
            functions[:, :, 1],
            functions[:, :, 0],
            optimize=True,
        ),
        "cyy": np.einsum(
            "k,ks,kt->st",
            values,
            functions[:, :, 1],
            functions[:, :, 1],
            optimize=True,
        ),
    }


def _normalize_functions(
    functions: np.ndarray,
    weights: np.ndarray,
) -> np.ndarray:
    array = np.asarray(functions, dtype=float).copy()
    norms = np.sqrt(
        np.einsum(
            "ktd,t,ktd->k",
            array,
            weights,
            array,
            optimize=True,
        )
    )
    if np.any(~np.isfinite(norms)) or np.any(norms <= 1e-12):
        raise ValueError("functional basis contains an invalid norm")
    return array / norms[:, None, None]


def _functional_subspace_cosines(
    first: np.ndarray,
    second: np.ndarray,
    weights: np.ndarray,
) -> np.ndarray:
    first_n = _normalize_functions(first, weights)
    second_n = _normalize_functions(second, weights)
    cross = np.einsum(
        "ktd,ltd,t->kl",
        first_n,
        second_n,
        weights,
        optimize=True,
    )
    return np.clip(
        np.linalg.svd(cross, compute_uv=False),
        0.0,
        1.0,
    )


def _score_subspace_cosines(
    first: np.ndarray,
    second: np.ndarray,
) -> np.ndarray:
    first_array = np.asarray(first, dtype=float)
    second_array = np.asarray(second, dtype=float)
    finite = np.all(np.isfinite(first_array), axis=1) & np.all(
        np.isfinite(second_array),
        axis=1,
    )
    if np.count_nonzero(finite) < 3:
        raise ValueError("too few finite rows for score-subspace comparison")
    first_centered = first_array[finite] - np.mean(
        first_array[finite],
        axis=0,
        keepdims=True,
    )
    second_centered = second_array[finite] - np.mean(
        second_array[finite],
        axis=0,
        keepdims=True,
    )
    q_first, _ = np.linalg.qr(first_centered)
    q_second, _ = np.linalg.qr(second_centered)
    return np.clip(
        np.linalg.svd(q_first.T @ q_second, compute_uv=False),
        0.0,
        1.0,
    )


def _block_ise(
    estimate: np.ndarray,
    truth: np.ndarray,
    weights: np.ndarray,
) -> float:
    pair_weights = np.outer(weights, weights)
    return float(
        np.sum(
            (np.asarray(estimate) - np.asarray(truth)) ** 2
            * pair_weights
        )
    )


def _reconstruction_ise(
    estimate: np.ndarray,
    truth: np.ndarray,
    weights: np.ndarray,
) -> float:
    error = np.sum(
        (np.asarray(estimate) - np.asarray(truth)) ** 2
        * weights[None, :, None],
        axis=(1, 2),
    )
    finite = np.isfinite(error)
    if not np.any(finite):
        return float("nan")
    return float(np.mean(error[finite]))


def two_stage_sensitivity() -> pd.DataFrame:
    simulation = _simulate()
    truth = simulation.truth
    direct = _fit_direct(simulation)
    weights = functional_trapezoid_weights(truth.truth_grid)
    truth_blocks = _truth_blocks(truth)
    direct_reconstruction = direct.mean[None, :, :] + np.einsum(
        "nk,ktd->ntd",
        direct.scores,
        direct.eigenfunctions,
        optimize=True,
    )
    rows: list[dict[str, object]] = []
    for rank in MARGINAL_RANKS:
        benchmark = two_stage_benchmark(simulation, rank)
        blocks = benchmark["covariance_blocks"]
        block_errors = {
            name: _block_ise(blocks[name], truth_blocks[name], weights)
            for name in ("cxx", "cxy", "cyx", "cyy")
        }
        truth_cosines = _functional_subspace_cosines(
            benchmark["eigenfunctions"],
            truth.eigenfunctions,
            weights,
        )
        direct_cosines = _functional_subspace_cosines(
            benchmark["eigenfunctions"],
            direct.eigenfunctions,
            weights,
        )
        truth_score_cosines = _score_subspace_cosines(
            benchmark["scores"],
            truth.scores,
        )
        direct_score_cosines = _score_subspace_cosines(
            benchmark["scores"],
            direct.scores,
        )
        rows.append(
            {
                "marginal_rank": rank,
                "joint_rank": len(benchmark["eigenvalues"]),
                "two_stage_covariance_ise": sum(block_errors.values()),
                "two_stage_cxx_ise": block_errors["cxx"],
                "two_stage_cxy_ise": block_errors["cxy"],
                "two_stage_cyy_ise": block_errors["cyy"],
                "two_stage_truth_subspace_min_cosine": float(
                    np.min(truth_cosines)
                ),
                "two_stage_direct_subspace_min_cosine": float(
                    np.min(direct_cosines)
                ),
                "two_stage_truth_score_subspace_min_cosine": float(
                    np.min(truth_score_cosines)
                ),
                "two_stage_direct_score_subspace_min_cosine": float(
                    np.min(direct_score_cosines)
                ),
                "two_stage_reconstruction_ise": _reconstruction_ise(
                    benchmark["reconstruction"],
                    truth.latent_on_truth_grid,
                    weights,
                ),
                "direct_reconstruction_ise": _reconstruction_ise(
                    direct_reconstruction,
                    truth.latent_on_truth_grid,
                    weights,
                ),
                "finite_score_fraction": float(
                    np.mean(benchmark["finite_score_rows"])
                ),
                "automatic_rank_selection": False,
                "architecture_winner_selected": False,
            }
        )
    return pd.DataFrame(rows)


def _write_long_fixture(simulation, output_dir: Path) -> None:
    for dimension_index, dimension in enumerate(("x", "y")):
        rows: list[dict[str, object]] = []
        for curve_id, time, values in zip(
            simulation.observations.curve_ids,
            simulation.observations.time,
            simulation.observations.values,
            strict=True,
        ):
            for time_value, value in zip(
                time,
                values[:, dimension_index],
                strict=True,
            ):
                rows.append(
                    {
                        "ID": curve_id,
                        "time": float(time_value),
                        "value": float(value),
                    }
                )
        pd.DataFrame(rows).to_csv(
            output_dir / f"external_fixture_{dimension}.csv",
            index=False,
        )


def write_external_fixture(output_dir: Path) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    simulation = _simulate()
    truth = simulation.truth
    direct = _fit_direct(simulation)
    _write_long_fixture(simulation, output_dir)

    pd.DataFrame(
        {
            "component": np.arange(1, direct.n_components + 1),
            "eigenvalue": direct.eigenvalues,
        }
    ).to_csv(
        output_dir / "native_eigenvalues.csv",
        index=False,
    )
    pd.DataFrame(
        {
            "ID": direct.curve_ids,
            **{
                f"score_{index + 1}": direct.scores[:, index]
                for index in range(direct.n_components)
            },
        }
    ).to_csv(
        output_dir / "native_scores.csv",
        index=False,
    )
    pd.DataFrame(direct.eigenfunctions[:, :, 0].T).to_csv(
        output_dir / "native_eigenfunctions_x.csv",
        index=False,
    )
    pd.DataFrame(direct.eigenfunctions[:, :, 1].T).to_csv(
        output_dir / "native_eigenfunctions_y.csv",
        index=False,
    )

    payload = {
        "schema_version": 1,
        "validation": "0.12 sparse MFPCA external comparator fixture",
        "rho_xy": RHO_XY,
        "truth_grid": np.asarray(truth.truth_grid, dtype=float).tolist(),
        "eigenvalues": np.asarray(truth.eigenvalues, dtype=float).tolist(),
        "eigenfunctions": np.asarray(
            truth.eigenfunctions,
            dtype=float,
        ).tolist(),
        "scores": np.asarray(truth.scores, dtype=float).tolist(),
        "curve_ids": list(simulation.observations.curve_ids),
        "measurement_error_covariance": np.asarray(
            truth.measurement_noise_covariance,
            dtype=float,
        ).tolist(),
        "native_fit": {
            "n_components": direct.n_components,
            "fit_method": direct.fit_method,
            "score_method": direct.score_method,
            "measurement_error_mode": direct.provenance["sparse_mfpca"][
                "measurement_error_mode"
            ],
        },
        "contract": {
            "equivalence_claim": False,
            "automatic_model_selection": False,
            "architecture_winner_selected": False,
        },
    }
    (output_dir / "external_fixture_truth.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        choices=("two-stage", "external-fixture", "all"),
        default="all",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("sparse-mfpca-comparator"),
    )
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    if args.mode in {"two-stage", "all"}:
        frame = two_stage_sensitivity()
        frame.to_csv(
            args.output_dir / "two_stage_sensitivity.csv",
            index=False,
        )
        payload = {
            "schema_version": 1,
            "evidence_type": "cross_implementation_sensitivity",
            "comparator": "internal_two_stage_marginal_sparse_bases",
            "rho_xy": RHO_XY,
            "marginal_ranks": list(MARGINAL_RANKS),
            "architecture_winner_selected": False,
            "automatic_rank_selection": False,
            "rows": frame.to_dict(orient="records"),
        }
        (args.output_dir / "two_stage_sensitivity.json").write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print("TWO_STAGE_SENSITIVITY")
        print(frame.to_string(index=False))

    if args.mode in {"external-fixture", "all"}:
        write_external_fixture(args.output_dir)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
