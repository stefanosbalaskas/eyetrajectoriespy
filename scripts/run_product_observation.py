"""Run post-0.12 external-researcher-style product observations.

The harness deliberately uses only top-level public eyetrajectoriespy APIs.
Input tables are deterministic, redistributable gaze surrogates with realistic
normalized screen coordinates, participant/trial metadata and sampling
patterns.  They are not empirical human observations and are labelled as such.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from eyetrajectoriespy import (
    capture_environment,
    export_portable_result,
    fit_mfpca,
    fit_sparse_mfpca,
    fpca_reporting_text,
    fpca_score_frame,
    from_irregular_long_dataframe_native,
    from_long_dataframe,
    load_portable_result,
    plot_fpca_component,
    plot_sparse_mfpca_component,
    plot_sparse_mfpca_covariance_blocks,
    plot_sparse_mfpca_score_diagnostics,
    sparse_mfpca_reporting_text,
    sparse_mfpca_score_frame,
)


def _dense_surrogate() -> pd.DataFrame:
    rng = np.random.default_rng(10012026)
    time = np.linspace(0.0, 2.0, 81)
    rows: list[dict[str, object]] = []
    for participant_index in range(28):
        participant = f"P{participant_index + 1:02d}"
        px, py = rng.normal(0.0, 0.025, size=2)
        amplitude = rng.normal(1.0, 0.08)
        for trial, condition in enumerate(("baseline", "search"), start=1):
            search = float(condition == "search")
            phase = rng.normal(0.0, 0.035)
            x = (
                0.48
                + px
                + amplitude * 0.12 * np.sin(np.pi * (time + phase))
                + search * 0.065 * np.sin(2.0 * np.pi * time)
                + rng.normal(0.0, 0.012, size=time.size)
            )
            y = (
                0.52
                + py
                + amplitude * 0.10 * np.cos(np.pi * (time + phase))
                - search * 0.050 * np.sin(2.0 * np.pi * time)
                + rng.normal(0.0, 0.012, size=time.size)
            )
            x = np.clip(x, 0.02, 0.98)
            y = np.clip(y, 0.02, 0.98)
            for t, x_value, y_value in zip(time, x, y, strict=True):
                rows.append(
                    {
                        "participant_id": participant,
                        "trial_id": trial,
                        "condition": condition,
                        "time_s": float(t),
                        "x": float(x_value),
                        "y": float(y_value),
                    }
                )
    return pd.DataFrame(rows)


def _sparse_surrogate() -> pd.DataFrame:
    rng = np.random.default_rng(12012026)
    rows: list[dict[str, object]] = []
    for participant_index in range(36):
        participant = f"P{participant_index + 1:02d}"
        n_observations = int(rng.integers(9, 15))
        interior = np.sort(rng.uniform(0.04, 1.96, n_observations - 2))
        time = np.r_[0.0, interior, 2.0]
        z1, z2 = rng.normal(size=2)
        x = (
            0.46
            + 0.035 * time
            + 0.115 * z1 * np.sin(np.pi * time / 2.0)
            + 0.050 * z2 * np.sin(np.pi * time)
        )
        y = (
            0.53
            - 0.030 * time
            + 0.085 * z1 * np.cos(np.pi * time / 2.0)
            - 0.070 * z2 * np.sin(np.pi * time)
        )
        xy = np.column_stack((x, y)) + rng.normal(
            0.0, 0.025, size=(time.size, 2)
        )
        xy = np.clip(xy, 0.02, 0.98)
        for t, (x_value, y_value) in zip(time, xy, strict=True):
            rows.append(
                {
                    "participant_id": participant,
                    "trial_id": 1,
                    "condition": "free-view",
                    "time_s": float(t),
                    "x": float(x_value),
                    "y": float(y_value),
                }
            )
    return pd.DataFrame(rows)


def _save_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _capture_common_grid_failure(data: pd.DataFrame) -> dict[str, str]:
    broken = data.copy()
    first_curve = (broken["participant_id"] == "P01") & (broken["trial_id"] == 1)
    drop_index = broken.loc[first_curve].index[len(broken.loc[first_curve]) // 2]
    broken = broken.drop(index=drop_index)
    try:
        from_long_dataframe(
            broken,
            curve_columns=("participant_id", "trial_id"),
            time_column="time_s",
            value_columns=("x", "y"),
            metadata_columns=("condition",),
            coordinate_system="normalized",
            time_unit="s",
        )
    except Exception as exc:  # evidence capture: exact public failure type/message
        return {"type": type(exc).__name__, "message": str(exc)}
    raise RuntimeError("common-grid ingestion unexpectedly repaired irregular input")


def run_dense(output: Path) -> dict[str, object]:
    route = output / "dense"
    route.mkdir(parents=True, exist_ok=True)
    raw = _dense_surrogate()
    raw.to_csv(route / "input_long.csv", index=False)

    trajectories = from_long_dataframe(
        raw,
        curve_columns=("participant_id", "trial_id"),
        time_column="time_s",
        value_columns=("x", "y"),
        metadata_columns=("condition",),
        coordinate_system="normalized",
        time_unit="s",
        provenance={"observation": "post-0.12-real-use", "synthetic": True},
    )
    fit = fit_mfpca(trajectories, n_components=3, scaling="dimension_sd")
    scores = fpca_score_frame(fit)
    scores.to_csv(route / "scores.csv", index=False)
    reporting = fpca_reporting_text(fit)
    (route / "reporting.txt").write_text(reporting + "\n", encoding="utf-8")

    ax = plot_fpca_component(fit, component=0, dimension="x")
    ax.figure.savefig(route / "component-1-x.svg", metadata={"Date": None})
    plt.close(ax.figure)

    portable_dir = export_portable_result(
        fit,
        route / "portable-result",
        include_environment=True,
    )
    snapshot = load_portable_result(portable_dir)
    failure = _capture_common_grid_failure(raw)
    evidence: dict[str, object] = {
        "route": "dense-common-grid-mfpca",
        "input_kind": "deterministic realistic synthetic gaze surrogate",
        "empirical_human_data": False,
        "public_api_only": True,
        "n_rows": int(len(raw)),
        "n_curves": int(trajectories.n_curves),
        "n_time": int(trajectories.n_time),
        "dimensions": list(trajectories.dimension_names),
        "n_components": int(fit.n_components),
        "explained_variance_ratio": [
            float(value) for value in fit.explained_variance_ratio
        ],
        "score_rows": int(len(scores)),
        "reporting_nonempty": bool(reporting.strip()),
        "portable_result_type": snapshot.result_type,
        "portable_nonportable_fields": list(snapshot.nonportable_fields),
        "portable_package_version_match": bool(snapshot.package_version_match),
        "failure_observation": {
            "scenario": "one curve no longer shares the declared common grid",
            "expected_behavior": "explicit failure; no silent interpolation",
            "observed": failure,
        },
        "friction": [],
    }
    _save_json(route / "observation.json", evidence)
    return evidence


def run_sparse(output: Path) -> dict[str, object]:
    route = output / "sparse-planar"
    route.mkdir(parents=True, exist_ok=True)
    raw = _sparse_surrogate()
    raw.to_csv(route / "input_long.csv", index=False)

    irregular = from_irregular_long_dataframe_native(
        raw,
        curve_columns=("participant_id", "trial_id"),
        time_column="time_s",
        value_columns=("x", "y"),
        metadata_columns=("condition",),
        coordinate_system="normalized",
        time_unit="s",
        provenance={"observation": "post-0.12-real-use", "synthetic": True},
    )
    fit = fit_sparse_mfpca(
        irregular,
        dimensions=("x", "y"),
        n_components=2,
        evaluation_grid=np.linspace(0.0, 2.0, 51),
        mean_bandwidth=0.32,
        covariance_bandwidth=0.46,
        measurement_error="diagonal",
        measurement_error_variance=(0.000625, 0.000625),
        psd_action="project",
        score_ridge=0.0,
        score_failure_action="retain_nan",
    )
    scores = sparse_mfpca_score_frame(fit)
    scores.to_csv(route / "scores.csv", index=False)
    reporting = sparse_mfpca_reporting_text(fit)
    (route / "reporting.txt").write_text(reporting + "\n", encoding="utf-8")

    axes = plot_sparse_mfpca_component(fit, component=0)
    axes[0].figure.savefig(route / "component-1.svg", metadata={"Date": None})
    plt.close(axes[0].figure)
    covariance_axes = plot_sparse_mfpca_covariance_blocks(fit, stage="used")
    covariance_axes.flat[0].figure.savefig(
        route / "covariance-blocks.svg", metadata={"Date": None}
    )
    plt.close(covariance_axes.flat[0].figure)
    diagnostic_ax = plot_sparse_mfpca_score_diagnostics(fit)
    diagnostic_ax.figure.savefig(
        route / "score-diagnostics.svg", metadata={"Date": None}
    )
    plt.close(diagnostic_ax.figure)

    portable_dir = export_portable_result(
        fit,
        route / "portable-result",
        include_environment=True,
    )
    snapshot = load_portable_result(portable_dir)
    status_counts = {
        str(key): int(value)
        for key, value in fit.score_diagnostics["status_code"].value_counts().items()
    }
    observation_counts = [len(time) for time in irregular.time]
    evidence: dict[str, object] = {
        "route": "native-sparse-planar-mfpca-joint-pace",
        "input_kind": "deterministic realistic synthetic gaze surrogate",
        "empirical_human_data": False,
        "public_api_only": True,
        "raw_interpolation_performed": False,
        "n_rows": int(len(raw)),
        "n_curves": int(irregular.n_curves),
        "native_observations_min": int(min(observation_counts)),
        "native_observations_max": int(max(observation_counts)),
        "dimensions": list(irregular.dimension_names),
        "n_components": int(fit.n_components),
        "score_rows": int(len(scores)),
        "score_status_counts": status_counts,
        "all_scores_finite": bool(np.isfinite(fit.scores).all()),
        "reporting_nonempty": bool(reporting.strip()),
        "portable_result_type": snapshot.result_type,
        "portable_nonportable_fields": list(snapshot.nonportable_fields),
        "portable_package_version_match": bool(snapshot.package_version_match),
        "friction": [],
    }
    _save_json(route / "observation.json", evidence)
    return evidence


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path("build/product-observation"))
    parser.add_argument("--route", choices=("dense", "sparse", "all"), default="all")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    results: dict[str, object] = {}
    if args.route in {"dense", "all"}:
        results["dense"] = run_dense(args.output_dir)
    if args.route in {"sparse", "all"}:
        results["sparse"] = run_sparse(args.output_dir)

    environment = capture_environment()
    _save_json(args.output_dir / "environment.json", environment)
    summary = {
        "schema_version": 1,
        "programme": "post-0.12-product-observation-and-1.0-readiness",
        "scope": "external-researcher-style public-API observation",
        "empirical_human_data": False,
        "results": results,
    }
    _save_json(args.output_dir / "summary.json", summary)
    print(
        "product observation OK: "
        + ", ".join(sorted(results))
        + "; public APIs only; no estimator changes"
    )


if __name__ == "__main__":
    main()
