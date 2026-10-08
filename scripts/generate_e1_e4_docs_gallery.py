"""Generate four source-derived E1-E4 website figures from typed result objects.

Uses a seeded teaching fixture, NOT empirical user data or a benchmark. Reuses
publicly exposed experimental composition and reporting; never hand draws a
hypothetical result or manufactures significance.
"""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

from eyetrajectoriespy import simulate_planar_trajectories
from eyetrajectoriespy.workflows import (
    FPCAWorkflowConfig, PreprocessingPlan, PreprocessingStepConfig,
    run_fpca_workflow,
)
from eyetrajectoriespy.workflows.experimental import (
    WorkflowSpecification, run_preprocessing_plan,
    run_workflow_preprocessed, workflow_preflight,
    plot_workflow_preflight, run_workflow_sensitivity,
    plot_workflow_sensitivity, render_workflow_report,
)

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "docs" / "assets" / "gallery"


def main() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    raw = simulate_planar_trajectories(
        n_participants=14, trials_per_participant=2, n_time=41, random_state=12024
    )
    # Inject limited missing positions into a COPY for the standalone QC
    # illustration, not the FPCA input; this is labeled as synthetic masking.
    qc_values = raw.values.copy()
    qc_values[0, 3:11, :] = np.nan
    qc_values[1, 8:13, 0] = np.nan
    qc = raw.with_values(qc_values, provenance_update={
        "illustrative_missingness_injected": True,
        "original_analysis_input_mutated": False,
    })
    preflight = workflow_preflight(qc, minimum_observed_per_dimension=10)
    ax = plot_workflow_preflight(preflight)
    ax.figure.savefig(ASSETS / "experimental-e2-missingness.svg", format="svg", bbox_inches="tight")
    plt.close(ax.figure)

    plan = PreprocessingPlan(steps=(
        PreprocessingStepConfig(
            function="smooth_trajectories",
            parameters={"method": "gaussian", "sigma": 0.75},
            scientific_effect="Opt-in mild Gaussian smoothing; examine saccade attenuation",
        ),
        PreprocessingStepConfig(
            function="normalize_time", parameters={"start": 0., "end": 1.},
            scientific_effect="Affine time scaling without interpolation",
        ),
    ))
    preprocessed = run_preprocessing_plan(raw, plan=plan)
    fig, ax = plt.subplots(figsize=(7.6, 3.6))
    for j in range(3):
        ax.plot(raw.time / raw.time[-1], raw.values[j, :, 0],
                linestyle="--", alpha=.45, label="Observed original" if j == 0 else None)
        ax.plot(preprocessed.data.time, preprocessed.data.values[j, :, 0],
                alpha=.85, label="After declared E1 plan" if j == 0 else None)
    ax.set(xlabel="Normalized position within the same observation window",
           ylabel="Horizontal gaze (normalized)",
           title="E1 actual preprocessing output (seeded teaching fixture)")
    ax.legend()
    fig.savefig(ASSETS / "experimental-e1-preprocessing.svg", format="svg", bbox_inches="tight")
    plt.close(fig)

    specs = tuple(
        WorkflowSpecification(
            f"retain-{k}", FPCAWorkflowConfig(n_components=k),
            "teaching_fixture_variance_fraction", "Declared rank sensitivity",
        )
        for k in (1, 2, 3, 999)
    )
    sensitivity = run_workflow_sensitivity(
        preprocessed.data, runner=run_fpca_workflow,
        specifications=specs, baseline_name="retain-2",
        metrics={"retained_variance_fraction":
                 lambda r: float(r.fit.explained_variance_ratio.sum())},
    )
    assert "retain-999" in sensitivity.errors
    ax = plot_workflow_sensitivity(sensitivity, metric="retained_variance_fraction")
    ax.figure.savefig(ASSETS / "experimental-e3-sensitivity.svg", format="svg", bbox_inches="tight")
    plt.close(ax.figure)

    fitted = run_workflow_preprocessed(
        raw, config=FPCAWorkflowConfig(n_components=2, preprocessing=plan),
        runner=run_fpca_workflow,
    )
    report_dir = ROOT / "build" / "docs-e1-e4-report"
    if report_dir.exists():
        # The generator is idempotent for the independently created temporary
        # build directory; the reporter itself remains strict about overwrites.
        import shutil
        shutil.rmtree(report_dir)
    artifact = render_workflow_report(
        fitted, report_dir,
        title="Synthetic teaching example: E1–E4 reproducible report",
        preflight=workflow_preflight(raw, minimum_observed_per_dimension=10),
        figures={
            "e1-transformation": ASSETS / "experimental-e1-preprocessing.svg",
            "e2-injected-missingness-demo": ASSETS / "experimental-e2-missingness.svg",
            "e3-descriptive-sensitivity": ASSETS / "experimental-e3-sensitivity.svg",
        },
        limitations=(
            "Seeded pedagogical trajectories and an independent illustrative injected-missingness QC copy.",
            "Figures are descriptive; no new inferential uncertainty or psychological interpretation.",
        ),
    )
    counts = [len(fitted.steps), len(fitted.decisions), len(artifact.files_sha256)]
    fig, ax = plt.subplots(figsize=(7.6, 3.3))
    ax.barh(["Recorded workflow steps", "Recorded decisions", "Hashed report files"], counts)
    ax.set(xlabel="Count in actual typed workflow/report object",
           title="E4 reproducibility evidence manifest (seeded teaching fixture)")
    for idx, value in enumerate(counts):
        ax.text(value + .1, idx, str(value), va="center")
    ax.set_xlim(0, max(counts) + 2)
    fig.savefig(ASSETS / "experimental-e4-evidence.svg", format="svg", bbox_inches="tight")
    plt.close(fig)
    expected = ["experimental-e1-preprocessing.svg", "experimental-e2-missingness.svg",
                "experimental-e3-sensitivity.svg", "experimental-e4-evidence.svg"]
    for filename in expected:
        assert (ASSETS / filename).stat().st_size > 400
    print(f"PASS 4 generated E1–E4 scientific gallery figures, E4 hashed report files={counts[-1]}")


if __name__ == "__main__":
    main()
