"""Complete synthetic E1-E4 workflow acceptance demonstration.

Scientific outputs remain synthetic; no inferential claim is manufactured.
Run this from an experimental-source checkout, not the stable PyPI package.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from eyetrajectoriespy import simulate_planar_trajectories
from eyetrajectoriespy.workflows import FPCAWorkflowConfig, PreprocessingPlan, PreprocessingStepConfig, run_fpca_workflow
from eyetrajectoriespy.workflows.experimental import (
    WorkflowSpecification,
    plot_workflow_preflight,
    plot_workflow_sensitivity,
    render_workflow_report,
    run_preprocessing_plan,
    run_workflow_preprocessed,
    run_workflow_sensitivity,
    workflow_preflight,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("build/experimental-e1-e4"))
    output = parser.parse_args().output
    output.mkdir(parents=True, exist_ok=True)

    gaze = simulate_planar_trajectories(
        n_participants=18, trials_per_participant=3, n_time=51, random_state=20261008
    )
    preflight = workflow_preflight(gaze, minimum_observed_per_dimension=5)
    if not preflight.ready:
        raise RuntimeError(f"Synthetic fixture is incompatible: {preflight.blocking_issues}")
    preflight.summary.to_csv(output / "preflight-summary.csv", index=False)
    preflight.curve_support.to_csv(output / "curve-support.csv", index=False)
    preflight.participant_support.to_csv(output / "participant-support.csv", index=False)
    qc_ax = plot_workflow_preflight(preflight)
    preflight_figure = output / "preflight-missingness.svg"
    qc_ax.figure.savefig(preflight_figure, format="svg", bbox_inches="tight")

    plan = PreprocessingPlan(steps=(
        PreprocessingStepConfig(
            function="smooth_trajectories",
            parameters={"method": "gaussian", "sigma": 0.75},
            scientific_effect="Analyst-declared mild smoothing, with transition attenuation caution",
        ),
        PreprocessingStepConfig(
            function="normalize_time",
            parameters={"start": 0.0, "end": 1.0},
            scientific_effect="Normalize 2-second synthetic time to unit interval",
        ),
    ))
    preprocessed = run_preprocessing_plan(gaze, plan=plan)
    preprocessed.audit.to_csv(output / "preprocessing-audit.csv", index=False)
    fitted = run_workflow_preprocessed(
        gaze, config=FPCAWorkflowConfig(n_components=2, preprocessing=plan),
        runner=run_fpca_workflow,
    )
    assert fitted.provenance["preprocessing_executed"] is True

    specs = (
        WorkflowSpecification("retain-1", FPCAWorkflowConfig(n_components=1),
                              "synthetic_explained_variance", "One retained component"),
        WorkflowSpecification("retain-2", FPCAWorkflowConfig(n_components=2),
                              "synthetic_explained_variance", "Two retained components"),
        WorkflowSpecification("retain-3", FPCAWorkflowConfig(n_components=3),
                              "synthetic_explained_variance", "Three retained components"),
    )
    sensitivity = run_workflow_sensitivity(
        preprocessed.data, runner=run_fpca_workflow, specifications=specs,
        baseline_name="retain-2",
        metrics={"explained_variance_ratio_sum": lambda r: float(r.fit.explained_variance_ratio.sum())},
        conclusions={"multiple_components": lambda r: r.fit.n_components > 1},
    )
    sensitivity.specifications.to_csv(output / "sensitivity-specifications.csv", index=False)
    sensitivity.metric_frame.to_csv(output / "sensitivity-descriptive-metrics.csv", index=False)
    ax = plot_workflow_sensitivity(sensitivity, metric="explained_variance_ratio_sum")
    figure = output / "sensitivity-stability.svg"
    ax.figure.savefig(figure, format="svg", bbox_inches="tight")

    report = render_workflow_report(
        fitted, output / "scientific-report", title="Synthetic planar-gaze FPCA demonstration",
        figures={"sensitivity-stability": figure, "preflight-missingness": preflight_figure},
        figure_captions={
            "preflight-missingness": "Descriptive observed-sample missingness by curve; no automated exclusion.",
            "sensitivity-stability": "Descriptive retained-variance fraction across analyst-declared FPCA component counts; no inference."
        },
        preflight=preflight,
        limitations=(
            "Entirely deterministic simulated gaze data; not empirical participant evidence.",
            "Smoothing and time normalization may alter process interpretation and temporal estimands.",
        ),
    )
    assert report.report_path.is_file()
    assert report.manifest_path.is_file()
    print(f"PASS E1-E4 synthetic installed-path case: {report.manifest_path}")


if __name__ == "__main__":
    main()
