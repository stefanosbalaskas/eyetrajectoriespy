"""Installed-package product qualification for the 1.2 workflow layer.

The harness uses deterministic realistic synthetic eye-tracking fixtures. They
are not empirical human observations. The script imports only supported package
and eyetrajectoriespy.workflows surfaces and is intended to run from an
installed wheel outside the source checkout.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import time

import numpy as np
import pandas as pd

import eyetrajectoriespy as et
from eyetrajectoriespy.workflows import (
    FPCAWorkflowConfig,
    FunctionOnScalarWorkflowConfig,
    FunctionalMixedEffectsWorkflowConfig,
    GeneralizedFunctionalWorkflowConfig,
    RecurrenceWorkflowConfig,
    SparseFPCAWorkflowConfig,
    SparseMFPCAAsyncWorkflowConfig,
    SparseMFPCAWorkflowConfig,
    SparseMultilevelWorkflowConfig,
    SparsePredictionWorkflowConfig,
    export_workflow_bundle,
    run_fpca_workflow,
    run_function_on_scalar_workflow,
    run_functional_mixed_effects_workflow,
    run_generalized_functional_workflow,
    run_recurrence_workflow,
    run_sparse_fpca_workflow,
    run_sparse_mfpca_async_workflow,
    run_sparse_mfpca_workflow,
    run_sparse_multilevel_workflow,
    run_sparse_prediction_workflow,
    save_workflow_figure,
    workflow_decisions_frame,
    workflow_reporting_text,
    workflow_steps_frame,
    workflow_summary_frame,
)


SYNTHETIC_LABEL = (
    "deterministic realistic synthetic eye-tracking surrogate; "
    "not empirical human data"
)


def _write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _timed(call):
    started = time.perf_counter()
    value = call()
    return value, float(time.perf_counter() - started)


def _dense_fixture(seed: int = 12026):
    rng = np.random.default_rng(seed)
    time_grid = np.linspace(0.0, 2.0, 41)
    participants = []
    conditions = []
    values = []
    curve_ids = []
    for participant_index in range(12):
        participant = f"D{participant_index:02d}"
        participant_shift = rng.normal(0.0, 0.025, size=2)
        for trial, condition in enumerate((0.0, 1.0, 0.5)):
            curve_ids.append(f"{participant}|{trial}")
            participants.append(participant)
            conditions.append(condition)
            x = (
                0.48
                + participant_shift[0]
                + 0.08 * np.sin(np.pi * time_grid)
                + condition * 0.04 * np.sin(2.0 * np.pi * time_grid)
                + rng.normal(0.0, 0.01, size=time_grid.size)
            )
            y = (
                0.52
                + participant_shift[1]
                + 0.07 * np.cos(np.pi * time_grid)
                - condition * 0.035 * np.sin(2.0 * np.pi * time_grid)
                + rng.normal(0.0, 0.01, size=time_grid.size)
            )
            values.append(np.column_stack((x, y)))
    trajectories = et.TrajectorySet(
        time=time_grid,
        values=np.asarray(values),
        curve_ids=tuple(curve_ids),
        dimension_names=("x", "y"),
        metadata=pd.DataFrame({"participant_id": participants}),
        coordinate_system="normalized",
        time_unit="s",
        provenance={"synthetic": True, "purpose": "1.2-workflow-product-qualification"},
    )
    design = pd.DataFrame(
        {
            "curve_id": trajectories.curve_ids,
            "condition": conditions,
        }
    )
    return trajectories, design


def _binary_fixture(seed: int = 12027):
    rng = np.random.default_rng(seed)
    time_grid = np.linspace(0.0, 1.0, 7)
    participants = np.repeat([f"G{i:02d}" for i in range(14)], 3)
    condition = np.tile(np.array([-0.7, 0.0, 0.7]), 14)
    eta = (
        (-0.35 + 0.30 * time_grid)[None, :]
        + condition[:, None] * (0.75 - 0.20 * time_grid)[None, :]
    )
    probability = 1.0 / (1.0 + np.exp(-eta))
    response = rng.binomial(1, probability).astype(float)
    trajectories = et.TrajectorySet(
        time=time_grid,
        values=response[:, :, None],
        curve_ids=tuple(f"G{i:03d}" for i in range(response.shape[0])),
        dimension_names=("target_aoi",),
        metadata=pd.DataFrame({"participant_id": participants}),
        coordinate_system="unknown",
        time_unit="s",
        provenance={"synthetic": True, "purpose": "1.2-workflow-product-qualification"},
    )
    design = pd.DataFrame(
        {
            "curve_id": trajectories.curve_ids,
            "condition": condition,
        }
    )
    return trajectories, design


def _irregular_univariate(seed: int = 12028):
    rng = np.random.default_rng(seed)
    times = []
    values = []
    participants = []
    for index in range(18):
        t = np.r_[0.0, np.sort(rng.uniform(0.05, 0.95, 10)), 1.0]
        z1, z2 = rng.normal(size=2)
        x = (
            0.45
            + 0.08 * t
            + 0.10 * z1 * np.sin(np.pi * t)
            + 0.05 * z2 * np.sin(2.0 * np.pi * t)
            + rng.normal(0.0, 0.02, size=t.size)
        )
        times.append(t)
        values.append(x[:, None])
        participants.append(f"U{index:02d}")
    return et.IrregularTrajectorySet(
        time=tuple(times),
        values=tuple(values),
        curve_ids=tuple(f"U{index:02d}" for index in range(18)),
        dimension_names=("x",),
        metadata=pd.DataFrame({"participant_id": participants}),
        coordinate_system="normalized",
        time_unit="s",
        provenance={"synthetic": True, "raw_interpolation": False},
    )


def _irregular_paired(seed: int = 12029):
    rng = np.random.default_rng(seed)
    times = []
    values = []
    participants = []
    for index in range(18):
        t = np.r_[0.0, np.sort(rng.uniform(0.05, 0.95, 10)), 1.0]
        z1, z2 = rng.normal(size=2)
        x = 0.46 + 0.06 * t + 0.10 * z1 * np.sin(np.pi * t)
        y = 0.54 - 0.04 * t + 0.08 * z1 * np.cos(np.pi * t)
        x += 0.04 * z2 * np.sin(2.0 * np.pi * t)
        y -= 0.05 * z2 * np.sin(2.0 * np.pi * t)
        observed = np.column_stack((x, y))
        observed += rng.normal(0.0, 0.02, size=observed.shape)
        times.append(t)
        values.append(observed)
        participants.append(f"P{index:02d}")
    return et.IrregularTrajectorySet(
        time=tuple(times),
        values=tuple(values),
        curve_ids=tuple(f"P{index:02d}" for index in range(18)),
        dimension_names=("x", "y"),
        metadata=pd.DataFrame({"participant_id": participants}),
        coordinate_system="normalized",
        time_unit="s",
        provenance={"synthetic": True, "raw_interpolation": False},
    )


def _irregular_async():
    union = np.linspace(0.0, 1.0, 9)
    x_mask = np.array([True, False, True, True, False, True, True, False, True])
    y_mask = np.array([True, True, False, True, True, False, True, True, True])
    times = []
    values = []
    participants = []
    for index in range(18):
        z1 = -1.4 + 2.8 * index / 17.0
        z2 = np.cos(0.7 * (index + 1))
        x = 0.45 + 0.10 * z1 * np.sin(np.pi * union) + 0.04 * z2 * np.cos(2 * np.pi * union)
        y = 0.55 + 0.08 * z1 * np.cos(np.pi * union) + 0.04 * z2 * np.sin(2 * np.pi * union)
        observed = np.full((union.size, 2), np.nan)
        observed[x_mask, 0] = x[x_mask]
        observed[y_mask, 1] = y[y_mask]
        times.append(union.copy())
        values.append(observed)
        participants.append(f"A{index // 3:02d}")
    return et.IrregularTrajectorySet(
        time=tuple(times),
        values=tuple(values),
        curve_ids=tuple(f"A{index:02d}" for index in range(18)),
        dimension_names=("x", "y"),
        metadata=pd.DataFrame({"participant_id": participants}),
        coordinate_system="normalized",
        time_unit="s",
        provenance={
            "synthetic": True,
            "raw_interpolation": False,
            "nearest_neighbour_synchronization": False,
        },
    )


def _multilevel_fixture(seed: int = 12030):
    rng = np.random.default_rng(seed)
    times = []
    values = []
    ids = []
    participants = []
    participant_score = np.linspace(-1.2, 1.2, 12)
    for participant in range(12):
        for trial in range(2):
            t = np.r_[0.0, np.sort(rng.uniform(0.05, 0.95, 9)), 1.0]
            trial_score = rng.normal(0.0, 0.4)
            x = (
                0.2
                + 0.1 * t
                + participant_score[participant] * np.sin(np.pi * t)
                + trial_score * np.sin(2.0 * np.pi * t)
                + rng.normal(0.0, 0.08, size=t.size)
            )
            times.append(t)
            values.append(x[:, None])
            ids.append(f"M{participant:02d}|{trial}")
            participants.append(f"M{participant:02d}")
    return et.IrregularTrajectorySet(
        time=tuple(times),
        values=tuple(values),
        curve_ids=tuple(ids),
        dimension_names=("x",),
        metadata=pd.DataFrame({"participant_id": participants}),
        coordinate_system="normalized",
        time_unit="s",
        provenance={"synthetic": True, "raw_interpolation": False},
    )


def _prediction_roles():
    grid = np.asarray([0.0, 0.25, 0.5, 0.75, 1.0])

    def build(ids, scores):
        arrays = []
        for score in scores:
            x = (
                0.2
                + 0.1 * grid
                + float(score) * np.sin(np.pi * grid)
                + 0.12 * float(score) * np.sin(2.0 * np.pi * grid)
            )
            arrays.append(x[:, None])
        return et.IrregularTrajectorySet(
            time=tuple(grid.copy() for _ in ids),
            values=tuple(arrays),
            curve_ids=tuple(ids),
            dimension_names=("x",),
            metadata=pd.DataFrame(
                {"participant_id": [f"participant-{value}" for value in ids]}
            ),
            coordinate_system="normalized",
            time_unit="s",
            provenance={"synthetic": True, "raw_interpolation": False},
        )

    training = build(
        tuple(f"train-{i}" for i in range(14)),
        np.linspace(-1.5, 1.5, 14),
    )
    calibration = build(
        tuple(f"cal-{i}" for i in range(5)),
        (-1.0, -0.4, 0.1, 0.6, 1.1),
    )
    target = build(("target-0",), (0.3,))
    return training, calibration, target


def _retain(name: str, result, root: Path, seconds: float) -> dict[str, object]:
    route = root / name
    route.mkdir(parents=True, exist_ok=True)
    workflow_summary_frame(result).to_csv(route / "summary.csv", index=False)
    workflow_steps_frame(result.steps).to_csv(route / "steps.csv", index=False)
    workflow_decisions_frame(result.decisions).to_csv(
        route / "decisions.csv",
        index=False,
    )
    (route / "workflow-reporting.txt").write_text(
        workflow_reporting_text(result) + "\n",
        encoding="utf-8",
    )
    return {
        "workflow_contract": result.workflow_contract,
        "step_count": len(result.steps),
        "decision_count": len(result.decisions),
        "runtime_seconds": seconds,
        "warnings": int(sum(len(step.warnings) for step in result.steps)),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--expected-version", required=True)
    args = parser.parse_args()
    root = args.output_dir
    root.mkdir(parents=True, exist_ok=True)

    if et.__version__ != args.expected_version:
        raise RuntimeError(
            f"installed version {et.__version__!r} != expected "
            f"{args.expected_version!r}"
        )

    dense, dense_design = _dense_fixture()
    binary, binary_design = _binary_fixture()
    univariate = _irregular_univariate()
    paired = _irregular_paired()
    asynchronous = _irregular_async()
    multilevel = _multilevel_fixture()
    proper, calibration, target = _prediction_roles()

    results = {}

    fpca, seconds = _timed(
        lambda: run_fpca_workflow(
            dense,
            config=FPCAWorkflowConfig(
                n_components=3,
                scaling="dimension_sd",
            ),
        )
    )
    results["fpca"] = _retain("fpca", fpca, root, seconds)

    fos, seconds = _timed(
        lambda: run_function_on_scalar_workflow(
            dense,
            dense_design,
            config=FunctionOnScalarWorkflowConfig(
                predictors=("condition",),
                dimensions=("x",),
            ),
        )
    )
    results["function_on_scalar"] = _retain(
        "function-on-scalar",
        fos,
        root,
        seconds,
    )

    mixed, seconds = _timed(
        lambda: run_functional_mixed_effects_workflow(
            dense,
            dense_design,
            config=FunctionalMixedEffectsWorkflowConfig(
                predictors=("condition",),
                participant_column="participant_id",
                dimension="x",
                fixed_basis_size=2,
                random_basis_size=2,
                spline_degree=1,
                maxiter=300,
            ),
        )
    )
    results["functional_mixed_effects"] = _retain(
        "functional-mixed-effects",
        mixed,
        root,
        seconds,
    )

    generalized, seconds = _timed(
        lambda: run_generalized_functional_workflow(
            binary,
            binary_design,
            config=GeneralizedFunctionalWorkflowConfig(
                predictors=("condition",),
                participant_column="participant_id",
                dimension="target_aoi",
                family="binomial",
                basis_size=2,
                spline_degree=1,
            ),
        )
    )
    results["generalized_functional"] = _retain(
        "generalized-functional",
        generalized,
        root,
        seconds,
    )

    sparse_fpca, seconds = _timed(
        lambda: run_sparse_fpca_workflow(
            univariate,
            config=SparseFPCAWorkflowConfig(
                dimension="x",
                n_components=2,
                evaluation_grid=tuple(np.linspace(0.0, 1.0, 21)),
                mean_bandwidth=0.25,
                covariance_bandwidth=0.35,
                noise_variance_method="fixed",
                measurement_error_variance=0.0004,
                psd_action="project",
                score_failure_action="retain_nan",
            ),
        )
    )
    results["sparse_fpca"] = _retain(
        "sparse-fpca",
        sparse_fpca,
        root,
        seconds,
    )

    sparse_mfpca, seconds = _timed(
        lambda: run_sparse_mfpca_workflow(
            paired,
            config=SparseMFPCAWorkflowConfig(
                n_components=2,
                evaluation_grid=tuple(np.linspace(0.0, 1.0, 21)),
                mean_bandwidth=0.28,
                covariance_bandwidth=0.40,
                measurement_error="diagonal",
                measurement_error_variance=(0.0004, 0.0004),
                psd_action="project",
                score_failure_action="retain_nan",
            ),
        )
    )
    results["sparse_mfpca"] = _retain(
        "sparse-mfpca",
        sparse_mfpca,
        root,
        seconds,
    )

    async_mfpca, seconds = _timed(
        lambda: run_sparse_mfpca_async_workflow(
            asynchronous,
            config=SparseMFPCAAsyncWorkflowConfig(
                n_components=1,
                evaluation_grid=tuple(np.linspace(0.0, 1.0, 9)),
                mean_bandwidth=0.40,
                covariance_bandwidth=0.50,
                measurement_error="fixed_matrix",
                measurement_error_covariance=np.array(
                    [[0.02, 0.003], [0.003, 0.02]]
                ),
                psd_action="project",
                score_failure_action="retain_nan",
            ),
        )
    )
    results["sparse_mfpca_async"] = _retain(
        "sparse-mfpca-async",
        async_mfpca,
        root,
        seconds,
    )

    sparse_multilevel, seconds = _timed(
        lambda: run_sparse_multilevel_workflow(
            multilevel,
            config=SparseMultilevelWorkflowConfig(
                dimension="x",
                participant_column="participant_id",
                participant_components=1,
                trial_components=1,
                evaluation_grid=tuple(np.linspace(0.10, 0.90, 9)),
                mean_bandwidth=0.35,
                total_covariance_bandwidth=0.45,
                between_covariance_bandwidth=0.45,
                analysis_support_action="restrict",
                noise_variance_method="fixed",
                measurement_error_variance=0.0064,
                psd_action="project",
                score_ridge=1e-6,
            ),
        )
    )
    results["sparse_multilevel"] = _retain(
        "sparse-multilevel",
        sparse_multilevel,
        root,
        seconds,
    )

    prediction, seconds = _timed(
        lambda: run_sparse_prediction_workflow(
            proper,
            calibration,
            target,
            config=SparsePredictionWorkflowConfig(
                training=SparseFPCAWorkflowConfig(
                    dimension="x",
                    n_components=1,
                    evaluation_grid=(0.0, 0.25, 0.5, 0.75, 1.0),
                    mean_bandwidth=0.50,
                    covariance_bandwidth=0.55,
                    noise_variance_method="fixed",
                    measurement_error_variance=0.02,
                    psd_action="project",
                    score_failure_action="retain_nan",
                ),
                history_cutoff=0.5,
                prediction_grid=(0.75, 1.0),
                alpha=0.4,
            ),
        )
    )
    results["sparse_prediction"] = _retain(
        "sparse-prediction",
        prediction,
        root,
        seconds,
    )

    recurrence, seconds = _timed(
        lambda: run_recurrence_workflow(
            dense,
            config=RecurrenceWorkflowConfig(
                curve=dense.curve_ids[0],
                dimensions=("x", "y"),
                embedding_dimension=2,
                delay=2,
                radius=0.12,
                theiler_window=2,
                min_diagonal_length=2,
                min_vertical_length=2,
            ),
        )
    )
    results["recurrence"] = _retain(
        "recurrence",
        recurrence,
        root,
        seconds,
    )

    export_workflow_bundle(fpca, root / "fpca" / "bundle")
    export_workflow_bundle(
        sparse_mfpca,
        root / "sparse-mfpca" / "bundle",
    )
    export_workflow_bundle(
        recurrence,
        root / "recurrence" / "bundle",
    )

    save_workflow_figure(
        fpca,
        root / "fpca" / "component-1-x.svg",
        plot="fpca_component",
        component=0,
        dimension="x",
    )
    save_workflow_figure(
        sparse_mfpca,
        root / "sparse-mfpca" / "component-1.svg",
        plot="sparse_mfpca_component",
        component=0,
    )
    save_workflow_figure(
        fos,
        root / "function-on-scalar" / "condition.svg",
        plot="function_on_scalar_coefficient",
        coefficient="condition",
        dimension="x",
    )
    save_workflow_figure(
        recurrence,
        root / "recurrence" / "recurrence.svg",
        plot="recurrence",
    )

    expected_contracts = {
        "fpca:v1",
        "function_on_scalar:v1",
        "functional_mixed_effects:v1",
        "generalized_functional:v1",
        "sparse_fpca:v1",
        "sparse_mfpca:v1",
        "sparse_mfpca_async:v1",
        "sparse_multilevel:v1",
        "sparse_prediction:v1",
        "recurrence:v1",
    }
    observed_contracts = {
        record["workflow_contract"] for record in results.values()
    }
    if observed_contracts != expected_contracts:
        raise RuntimeError(
            f"workflow contract mismatch: {sorted(observed_contracts)!r}"
        )

    total_seconds = float(sum(record["runtime_seconds"] for record in results.values()))
    summary = {
        "schema_version": 1,
        "programme": "1.2-workflow-installed-product-qualification",
        "package_version": et.__version__,
        "input_kind": SYNTHETIC_LABEL,
        "empirical_human_data": False,
        "installed_package_execution": True,
        "repository_private_helpers_used": False,
        "workflow_contracts": sorted(observed_contracts),
        "workflow_count": len(results),
        "results": results,
        "runtime_seconds_total": total_seconds,
        "release_blocking_friction_count": 0,
        "friction": [],
    }
    _write_json(root / "summary.json", summary)
    print(
        "1.2 workflow installed-product qualification OK: "
        f"{len(results)} workflows; {total_seconds:.3f}s total"
    )


if __name__ == "__main__":
    main()
