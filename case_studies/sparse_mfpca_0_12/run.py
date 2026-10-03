"""Run the canonical sparse-planar MFPCA reproducibility case study.

Only top-level public eyetrajectoriespy APIs are used.  The script reads the
frozen redistributable surrogate, fits the 0.12 sparse planar workflow,
produces manuscript-oriented outputs, exports a portable result, and verifies
stable scientific invariants recorded in ``expected.json``.
"""

from __future__ import annotations

import argparse
import hashlib
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
    fit_sparse_mfpca,
    from_irregular_long_dataframe_native,
    load_portable_result,
    plot_sparse_mfpca_component,
    plot_sparse_mfpca_covariance_blocks,
    plot_sparse_mfpca_score_diagnostics,
    sparse_mfpca_reporting_text,
    sparse_mfpca_score_frame,
)


ROOT = Path(__file__).resolve().parent


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run(data_path: Path, output_dir: Path) -> dict[str, object]:
    expected = json.loads((ROOT / "expected.json").read_text(encoding="utf-8"))
    actual_data_sha = _sha256(data_path)
    if actual_data_sha != expected["data_sha256"]:
        raise RuntimeError(
            "case-study input checksum mismatch: "
            f"expected={expected['data_sha256']}, actual={actual_data_sha}"
        )

    samples = pd.read_csv(data_path)
    irregular = from_irregular_long_dataframe_native(
        samples,
        curve_columns=("participant_id", "trial_id"),
        time_column="time_s",
        value_columns=("x", "y"),
        metadata_columns=("condition",),
        coordinate_system="normalized",
        time_unit="s",
        provenance={
            "case_study": "sparse_mfpca_0_12",
            "synthetic": True,
            "data_sha256": actual_data_sha,
        },
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

    output_dir.mkdir(parents=True, exist_ok=True)
    scores = sparse_mfpca_score_frame(fit)
    scores.to_csv(output_dir / "scores.csv", index=False)
    reporting = sparse_mfpca_reporting_text(fit)
    (output_dir / "reporting.txt").write_text(reporting + "\n", encoding="utf-8")

    component_axes = plot_sparse_mfpca_component(fit, component=0)
    component_axes[0].figure.savefig(
        output_dir / "component-1.svg", metadata={"Date": None}
    )
    plt.close(component_axes[0].figure)

    covariance_axes = plot_sparse_mfpca_covariance_blocks(fit, stage="used")
    covariance_axes.flat[0].figure.savefig(
        output_dir / "covariance-blocks.svg", metadata={"Date": None}
    )
    plt.close(covariance_axes.flat[0].figure)

    diagnostic_ax = plot_sparse_mfpca_score_diagnostics(fit)
    diagnostic_ax.figure.savefig(
        output_dir / "score-diagnostics.svg", metadata={"Date": None}
    )
    plt.close(diagnostic_ax.figure)

    portable_dir = export_portable_result(
        fit,
        output_dir / "portable-result",
        include_environment=True,
    )
    snapshot = load_portable_result(portable_dir)

    status_counts = {
        str(key): int(value)
        for key, value in fit.score_diagnostics["status_code"].value_counts().items()
    }
    observation_counts = [len(time) for time in irregular.time]
    summary: dict[str, object] = {
        "case_study": "sparse_mfpca_0_12",
        "data_sha256": actual_data_sha,
        "empirical_human_data": False,
        "public_api_only": True,
        "raw_interpolation_performed": False,
        "n_rows": int(len(samples)),
        "n_curves": int(irregular.n_curves),
        "native_observations_min": int(min(observation_counts)),
        "native_observations_max": int(max(observation_counts)),
        "n_components": int(fit.n_components),
        "eigenvalues": [float(value) for value in fit.eigenvalues],
        "score_rows": int(len(scores)),
        "score_status_counts": status_counts,
        "all_scores_finite": bool(np.isfinite(fit.scores).all()),
        "reporting_nonempty": bool(reporting.strip()),
        "portable_result_type": snapshot.result_type,
        "portable_nonportable_fields": list(snapshot.nonportable_fields),
        "portable_package_version_match": bool(snapshot.package_version_match),
        "figures": [
            "component-1.svg",
            "covariance-blocks.svg",
            "score-diagnostics.svg",
        ],
    }

    for key in (
        "n_rows",
        "n_curves",
        "native_observations_min",
        "native_observations_max",
        "n_components",
        "score_rows",
        "score_status_counts",
        "portable_result_type",
        "portable_nonportable_fields",
    ):
        if summary[key] != expected[key]:
            raise RuntimeError(
                f"case-study invariant {key!r} changed: "
                f"expected={expected[key]!r}, actual={summary[key]!r}"
            )

    if not summary["all_scores_finite"]:
        raise RuntimeError("case-study joint-PACE scores are not all finite")
    if not summary["reporting_nonempty"]:
        raise RuntimeError("case-study reporting text is empty")
    if not summary["portable_package_version_match"]:
        raise RuntimeError("portable snapshot package version does not match")

    actual_eigenvalues = np.asarray(summary["eigenvalues"], dtype=float)
    expected_eigenvalues = np.asarray(expected["reference_eigenvalues"], dtype=float)
    np.testing.assert_allclose(
        actual_eigenvalues,
        expected_eigenvalues,
        rtol=float(expected["eigenvalue_rtol"]),
        atol=float(expected["eigenvalue_atol"]),
    )
    for text in expected["reporting_required_substrings"]:
        if text not in reporting:
            raise RuntimeError(f"reporting contract missing substring: {text!r}")

    _write_json(output_dir / "summary.json", summary)
    _write_json(output_dir / "environment.json", capture_environment())
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data",
        type=Path,
        default=ROOT / "data" / "input_long.csv",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("build/case-study-sparse-mfpca-0.12"),
    )
    args = parser.parse_args()
    summary = run(args.data, args.output_dir)
    print(
        "case study OK: "
        f"{summary['n_curves']} curves, {summary['score_status_counts']}, "
        f"data_sha256={summary['data_sha256']}"
    )


if __name__ == "__main__":
    main()
