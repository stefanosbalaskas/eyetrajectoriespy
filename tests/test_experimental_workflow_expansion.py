"""E1-E4 exploratory acceptance tests: no implicit science and no RC1 promotion."""

from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
import pytest

from eyetrajectoriespy import simulate_planar_trajectories
from eyetrajectoriespy.types import IrregularTrajectorySet
from eyetrajectoriespy.workflows import (
    FPCAWorkflowConfig, PreprocessingPlan, PreprocessingStepConfig, run_fpca_workflow,
)
from eyetrajectoriespy.workflows.experimental import (
    WorkflowSpecification, plot_workflow_sensitivity,
    render_workflow_report, run_preprocessing_plan,
    run_workflow_preprocessed, run_workflow_sensitivity, workflow_preflight,
)


@pytest.fixture
def gaze():
    return simulate_planar_trajectories(
        n_participants=8, trials_per_participant=2, n_time=31, random_state=9
    )


def _smooth_plan():
    return PreprocessingPlan(steps=(
        PreprocessingStepConfig(
            function="smooth_trajectories",
            parameters={"method": "gaussian", "sigma": 1.0},
            scientific_effect="Attenuates high-frequency within-trial variation",
        ),
        PreprocessingStepConfig(
            function="normalize_time", parameters={"start": 0.0, "end": 1.0},
            scientific_effect="Remaps absolute seconds to a normalized domain",
        ),
    ))


def test_empty_plan_is_identity_and_never_dense_converts(gaze):
    out = run_preprocessing_plan(gaze, plan=PreprocessingPlan())
    assert out.data is gaze
    assert out.steps == ()
    assert out.provenance["preprocessing_executed"] is False


def test_e1_order_units_audit_warnings_and_curve_retention(gaze):
    outcome = run_preprocessing_plan(gaze, plan=_smooth_plan())
    assert len(outcome.steps) == 2
    assert outcome.steps[0].function == "smooth_trajectories"
    assert outcome.steps[0].warnings
    assert outcome.audit["n_curves_after"].eq(gaze.n_curves).all()
    assert outcome.data.time_unit == "normalized"
    assert outcome.data.coordinate_system == "normalized"
    assert np.allclose(outcome.data.time[[0, -1]], [0.0, 1.0])
    assert np.isfinite(outcome.data.values).sum() == np.isfinite(gaze.values).sum()
    assert outcome.data.curve_ids == gaze.curve_ids


def test_e1_unknown_operator_and_coordinate_unit_fail_closed(gaze):
    with pytest.raises(ValueError, match="Unsupported"):
        run_preprocessing_plan(gaze, plan=PreprocessingPlan((
            PreprocessingStepConfig("unqualified_transform", {}, "Unqualified"),)))
    with pytest.raises(ValueError, match="pixel"):
        run_preprocessing_plan(gaze, plan=PreprocessingPlan((
            PreprocessingStepConfig(
                "normalize_coordinates", {"width": 1920, "height": 1080}, "Pixels to unit",
            ),)))


def test_e1_registration_preserves_full_warp_arrays(gaze):
    plan = PreprocessingPlan((
        PreprocessingStepConfig(
            "register_to_landmarks",
            {
                "observed_landmarks": np.full((gaze.n_curves, 1), 0.74),
                "reference_landmarks": np.array([0.85]),
            },
            "Re-align analyst-identified temporal landmarks",
        ),
    ))
    out = run_preprocessing_plan(gaze, plan=plan)
    assert len(out.phase_results) == 1
    assert out.phase_results[0].warping_functions.shape == (gaze.n_curves, gaze.n_time)
    assert any("phase" in item.lower() for item in out.steps[0].warnings)
    assert out.provenance["phase_warping_retained"]


def test_e1_irregular_never_silently_interpolates(gaze):
    irregular = IrregularTrajectorySet(
        time=(gaze.time[::2].copy(), gaze.time[1::2].copy()),
        values=(gaze.values[0, ::2].copy(), gaze.values[1, 1::2].copy()),
        curve_ids=("a", "b"), dimension_names=("x", "y"),
        coordinate_system="normalized", time_unit="s",
    )
    assert run_preprocessing_plan(irregular, plan=PreprocessingPlan()).data is irregular
    with pytest.raises(ValueError, match="no implicit densification"):
        run_preprocessing_plan(irregular, plan=_smooth_plan())


def test_e1_dense_composition_preserves_full_original_plan(gaze):
    cfg = FPCAWorkflowConfig(n_components=2, preprocessing=_smooth_plan())
    with pytest.raises(ValueError, match="empty preprocessing"):
        run_fpca_workflow(gaze, config=cfg)
    fitted = run_workflow_preprocessed(gaze, config=cfg, runner=run_fpca_workflow)
    assert fitted.config is cfg
    assert [step.function for step in fitted.steps] == [
        "smooth_trajectories", "normalize_time", "fit_fpca"
    ]
    assert fitted.provenance["preprocessing_executed"] is True
    assert "preprocessing_plan" in fitted.decisions
    assert len(fitted.tables["preprocessing_audit"]) == 2


def test_e2_missingness_low_support_never_removes_curves(gaze):
    modified = gaze.values.copy()
    modified[0, :, 0] = np.nan
    data = gaze.with_values(modified)
    out = workflow_preflight(data, minimum_observed_per_dimension=3)
    assert out.ready
    assert len(out.curve_support) == gaze.n_curves
    assert out.summary.iloc[0]["missing_values"] == gaze.n_time
    assert out.summary.iloc[0]["low_support_curves"] == 1
    assert out.warnings
    assert out.provenance["automatic_exclusions"] is False
    assert np.isnan(data.values[0, :, 0]).all()


def test_e2_sparse_layout_and_common_grid_requirement(gaze):
    irregular = IrregularTrajectorySet(
        time=(gaze.time[:9], gaze.time[::3]),
        values=(gaze.values[0, :9], gaze.values[1, ::3]),
        curve_ids=("a", "b"), dimension_names=("x", "y"),
    )
    out = workflow_preflight(irregular, require_common_grid=True)
    assert not out.ready
    assert out.layout == "irregular"
    assert out.curve_support["n_samples"].tolist() == [9, 11]
    assert out.blocking_issues


def test_e2_hierarchy_counts_and_incompatible_dimension(gaze):
    out = workflow_preflight(gaze, required_dimensions=("x", "pupil"))
    assert not out.ready
    assert "pupil" in str(out.blocking_issues)
    assert out.summary.iloc[0]["n_participants"] == 8
    assert out.participant_support["n_trials"].eq(2).all()


def _specs():
    return (
        WorkflowSpecification("k1", FPCAWorkflowConfig(n_components=1),
                              "eigenvalue_retention", "Minimal retained subspace"),
        WorkflowSpecification("k2", FPCAWorkflowConfig(n_components=2),
                              "eigenvalue_retention", "Expanded retained subspace"),
    )


def test_e3_declared_specs_with_baseline_deltas(gaze):
    out = run_workflow_sensitivity(
        gaze, runner=run_fpca_workflow, specifications=_specs(),
        baseline_name="k1",
        metrics={"explained": lambda r: float(r.fit.explained_variance_ratio.sum())},
    )
    assert len(out.outcomes) == 2
    assert not out.errors
    assert out.metric_frame.iloc[0]["explained_delta_from_baseline"] == pytest.approx(0)
    assert out.metric_frame.iloc[1]["explained"] >= out.metric_frame.iloc[0]["explained"]
    assert out.provenance["automatic_model_selection"] is False
    ax = plot_workflow_sensitivity(out, metric="explained")
    assert ax.get_ylabel().startswith("explained")


def test_e3_retains_failed_configuration(gaze):
    bad = WorkflowSpecification("bad", FPCAWorkflowConfig(n_components=5000),
                                "eigenvalue_retention", "Deliberate invalid stress")
    out = run_workflow_sensitivity(
        gaze, runner=run_fpca_workflow, specifications=(*_specs(), bad),
        baseline_name="k1", metrics={"explained": lambda r: float(r.fit.explained_variance_ratio.sum())},
    )
    assert "bad" in out.errors
    assert out.specifications.set_index("specification").loc["bad", "status"] == "failed"
    assert np.isnan(out.metric_frame.set_index("specification").loc["bad", "explained"])


def test_e3_rejects_incompatible_estimands_before_running(gaze):
    incompatible = replace(_specs()[1], estimand_id="another_population")
    with pytest.raises(ValueError, match="estimands"):
        run_workflow_sensitivity(
            gaze, runner=run_fpca_workflow, specifications=(_specs()[0], incompatible),
            baseline_name="k1", metrics={"explained": lambda r: 0.5},
        )


def test_e4_markdown_sha256_and_no_invented_p_values(gaze, tmp_path):
    fitted = run_fpca_workflow(gaze, config=FPCAWorkflowConfig(n_components=2))
    figure = tmp_path / "curve.svg"
    figure.write_text("<svg xmlns='http://www.w3.org/2000/svg'></svg>", encoding="utf-8")
    product = render_workflow_report(
        fitted, tmp_path / "md-report", title="Synthetic gaze FPCA",
        figures={"component": figure},
        limitations=("This is synthetic demonstration data.",),
        figure_captions={"component": "Demonstration figure in normalized coordinates."},
        preflight=workflow_preflight(gaze),
    )
    text = product.report_path.read_text()
    assert "## Methods" in text and "## Results" in text
    assert "## Sample accounting" in text
    assert (product.report_path.parent / "evidence" / "preflight_summary.csv").is_file()
    assert "This is synthetic demonstration data." in text
    assert "Demonstration figure" in text
    assert (product.report_path.parent / "evidence" / "config.json").exists() is False
    manifest = json.loads(product.manifest_path.read_text())
    assert manifest["auto_inference"] is False
    for rel, digest in product.files_sha256.items():
        assert sha256((product.report_path.parent / rel).read_bytes()).hexdigest() == digest
    with pytest.raises(FileExistsError):
        render_workflow_report(fitted, product.report_path.parent)


def test_e4_html_escapes_analyst_text(gaze, tmp_path):
    fitted = run_fpca_workflow(gaze, config=FPCAWorkflowConfig(n_components=2))
    report = render_workflow_report(
        fitted, tmp_path / "html", title="<Untrusted user title>", format="html",
        limitations=("<script>alert('no')</script>",),
    )
    source = report.report_path.read_text()
    assert "<script>" not in source
    assert "&lt;script&gt;" in source
    assert "&lt;Untrusted user title&gt;" in source
