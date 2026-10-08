"""Real, de-identified public gaze usability case for experimental E1–E4.

CC BY-NC 4.0 third-party dataset; original gaze samples are NOT redistributed.
This is engineering usability evidence, never known-truth estimator validation.
Run: python examples/real_gaze_e1_e4_usability.py --output build/real-gaze-usability
"""
from __future__ import annotations

import argparse
from hashlib import sha1, sha256
from io import BytesIO
import json
from pathlib import Path
from time import perf_counter
from urllib.request import Request, urlopen

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from eyetrajectoriespy import TrajectorySet
from eyetrajectoriespy.workflows import (
    FPCAWorkflowConfig, PreprocessingPlan, PreprocessingStepConfig, run_fpca_workflow
)
from eyetrajectoriespy.workflows.experimental import (
    WorkflowSpecification, plot_workflow_preflight, plot_workflow_sensitivity,
    render_workflow_report, run_preprocessing_plan, run_workflow_preprocessed,
    run_workflow_sensitivity, workflow_preflight,
)

SOURCE_REPO = "DFKI-Interactive-Machine-Learning/Disagreement-Detection-Dataset-CHI-26"
SOURCE_COMMIT = "1a92e69487c862a80496d7a80c86e8f4f5a857bf"
SOURCE_REPOSITORY_URL = "https://github.com/" + SOURCE_REPO
LICENSE = "CC BY-NC 4.0"
END_MS = 480
STEP_MS = 4
# Predeclared first two publicly available trials for eight pseudonymous participants;
# source Git blob identities are immutable and verified independently of transport.
SOURCE_FILES = [
    [
        "A01_102281_False_False.csv",
        "0a3ab1a554e6f8076219b6376ee0c43bec3dca50"
    ],
    [
        "A01_106490_True_True.csv",
        "1f352ea5e6a9efbf44833ddf9dfdd80c981cf083"
    ],
    [
        "A02_102281_False_False.csv",
        "408624403138a43e229e31ebd97fe385b1c2357f"
    ],
    [
        "A02_106490_True_True.csv",
        "1d7229f12222cf38014b65326a036529c46e4a13"
    ],
    [
        "A03_102281_False_False.csv",
        "8f9f5e658d7c3a266b22ed43d3795522ef52781e"
    ],
    [
        "A03_106756_False_False.csv",
        "fbe7162ee8adbb5c2ab5a28204447e35e69ee64a"
    ],
    [
        "A04_102281_False_False.csv",
        "acee33f954ff8c3dad1f241f3626d5c2ab415fe9"
    ],
    [
        "A04_106646_True_False.csv",
        "3493abd125a73d64b8442f621e5c931f7f887f81"
    ],
    [
        "A05_102281_False_False.csv",
        "2e18c6067bd253f77e3ad5303121d35bac1aa6fb"
    ],
    [
        "A05_106490_True_True.csv",
        "85f913a612f1de2c56782c8e89b618599e51c56c"
    ],
    [
        "A06_106756_False_False.csv",
        "ac913f134ad75e33a1dd953f7c50ab91d245ce93"
    ],
    [
        "A06_109141_True_True.csv",
        "2c30f177b90ecd5ebaff475d22c471bc9a974fbc"
    ],
    [
        "A07_102281_False_False.csv",
        "627aa8ef1d9b4f8bf36092282e4be36814bd151d"
    ],
    [
        "A07_106646_False_False.csv",
        "4545e2b1963094459d09e304052e7734893970fc"
    ],
    [
        "A08_102281_False_False.csv",
        "b0700ae8429fc70a46c29389f2a44dbc3bcc8af7"
    ],
    [
        "A08_106490_True_True.csv",
        "4e35d3c00468d20515cf488f77861cc536174d06"
    ]
]

def _json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _fetch(name: str, blob: str) -> tuple[pd.DataFrame, dict]:
    url = (
        f"https://raw.githubusercontent.com/{SOURCE_REPO}/{SOURCE_COMMIT}"
        f"/Gaze_Data_Events_Extracted/{name}"
    )
    request = Request(url, headers={"User-Agent": "eyetrajectoriespy-research-usability"})
    with urlopen(request, timeout=45) as response:
        payload = response.read(1_500_001)
    if len(payload) > 1_500_000:
        raise RuntimeError("Unexpected oversized upstream trial; refusing silent truncation")
    git_header = f"blob {len(payload)}\0".encode()
    actual_blob = sha1(git_header + payload).hexdigest()
    if actual_blob != blob:
        raise RuntimeError(f"Upstream source identity drift for {name}")
    frame = pd.read_csv(BytesIO(payload), usecols=["timestamp", "x", "y"])
    frame = frame.apply(pd.to_numeric, errors="coerce")
    if frame["timestamp"].isna().any():
        raise ValueError(f"Missing event timestamps in {name}")
    if frame["timestamp"].duplicated().any() or not frame["timestamp"].is_monotonic_increasing:
        raise ValueError(f"Nonunique or unsorted source timestamps in {name}")
    return frame, {"source_git_blob": actual_blob, "source_sha256": sha256(payload).hexdigest(),
                   "source_rows": len(frame), "source_bytes": len(payload)}


def _load() -> tuple[TrajectorySet, pd.DataFrame, list[dict]]:
    samples = []
    metadata = []
    accounting = []
    grid_ms = np.arange(0, END_MS + 1, STEP_MS, dtype=int)
    for ordinal, (name, git_blob) in enumerate(SOURCE_FILES):
        frame, fingerprint = _fetch(name, git_blob)
        participant = f"participant-{ordinal // 2 + 1:02d}"
        trial = f"trial-{ordinal % 2 + 1}"
        key = participant + "-" + trial
        window = frame.loc[frame.timestamp.between(0, END_MS)].copy()
        # This is an explicit exact-timestamp intersection, NOT interpolation.
        observed_t = window["timestamp"].to_numpy(float)
        indices = np.rint(observed_t / STEP_MS).astype(int)
        if not np.allclose(observed_t, indices * STEP_MS, atol=1e-7, rtol=0):
            raise ValueError("Unexpected non-grid timestamp; no nearest-neighbour fill allowed")
        values = np.full((len(grid_ms), 2), np.nan)
        values[indices, :] = window[["x", "y"]].to_numpy(float)
        samples.append(values)
        metadata.append({"participant_id": participant, "trial_id": trial})
        complete = bool(np.isfinite(values).all())
        accounting.append({
            "curve_id": key, "source_blob_sha1": fingerprint["source_git_blob"],
            "source_sha256": fingerprint["source_sha256"],
            "upstream_source_rows": fingerprint["source_rows"],
            "source_bytes": fingerprint["source_bytes"],
            "input_rows_in_window": len(window), "expected_grid_rows": len(grid_ms),
            "observed_coordinate_values": int(np.isfinite(values).sum()),
            "missing_coordinate_values": int((~np.isfinite(values)).sum()),
            "complete_case_selected": complete,
            "not_selected_reason": "" if complete else "incomplete prespecified 0–480 ms window",
        })
    original = TrajectorySet(
        time=grid_ms.astype(float) / 1000,
        values=np.stack(samples),
        curve_ids=tuple(f"participant-{i//2+1:02d}-trial-{i%2+1}" for i in range(len(samples))),
        dimension_names=("x", "y"),
        metadata=pd.DataFrame(metadata),
        coordinate_system="pixels",
        time_unit="s",
        provenance={
            "source_kind": "authentic_published_observations",
            "upstream_commit": SOURCE_COMMIT,
            "redistributed_raw_samples": False,
            "time_window_ms": [0, END_MS], "exact_timestamp_matching_no_interpolation": True,
        },
    )
    eligible = np.asarray([row["complete_case_selected"] for row in accounting])
    if eligible.sum() < 10 or len(set(np.array(original.metadata["participant_id"])[eligible])) < 6:
        raise RuntimeError("Prespecified complete-case threshold not met; no hidden imputation")
    analysis = TrajectorySet(
        time=original.time.copy(),
        values=original.values[eligible].copy(),
        curve_ids=tuple(cid for cid, ok in zip(original.curve_ids, eligible) if ok),
        dimension_names=original.dimension_names,
        metadata=original.metadata.loc[eligible].reset_index(drop=True),
        coordinate_system=original.coordinate_system,
        time_unit=original.time_unit,
        provenance={**original.provenance, "selection": "explicit_complete_case_window",
                    "n_input": len(accounting), "n_analysis": int(eligible.sum())},
    )
    return analysis, original, accounting


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("build/real-gaze-usability"))
    output = parser.parse_args().output
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        raise FileExistsError("Use an empty output directory; refuse to overwrite evidence")
    durations: dict[str, float] = {}
    started = perf_counter()
    t0 = perf_counter()
    analysis, original, accounting = _load()
    durations["pinned_upstream_acquisition_and_alignment"] = perf_counter() - t0
    audit = pd.DataFrame(accounting)
    audit.to_csv(output / "input-selection-audit.csv", index=False)
    _json(output / "data-source-and-fingerprints.json", {
        "origin": SOURCE_REPOSITORY_URL, "git_commit": SOURCE_COMMIT,
        "licence": LICENSE, "license_url": "https://creativecommons.org/licenses/by-nc/4.0/",
        "nature": "real de-identified published gaze; no private health or outcome data",
        "raw_gaze_redistributed": False,
        "selection": "First two prespecified public trials for eight participants; "
                     "include only complete 0–480 ms trajectories for dense FPCA; "
                     "no interpolation; all exclusions explicitly recorded",
        "inputs": accounting,
    })
    t0 = perf_counter()
    preflight = workflow_preflight(
        original, minimum_observed_per_dimension=30,
        participant_column="participant_id", trial_column="trial_id",
        required_dimensions=("x", "y"), require_common_grid=True,
    )
    assert preflight.ready
    preflight.summary.to_csv(output / "preflight-original-summary.csv", index=False)
    preflight.curve_support.to_csv(output / "preflight-original-support.csv", index=False)
    durations["preflight"] = perf_counter() - t0

    plan = PreprocessingPlan(steps=(
        PreprocessingStepConfig(
            function="smooth_trajectories",
            parameters={"method": "gaussian", "sigma": 0.75},
            scientific_effect="Mild opt-in smoothing; may attenuate saccades; compare raw trajectories",
        ),
        PreprocessingStepConfig(
            function="normalize_time", parameters={"start": 0.0, "end": 1.0},
            scientific_effect="Affine time representation of same 0–480 ms window; no interpolation",
        ),
    ))
    t0 = perf_counter()
    transformed = run_preprocessing_plan(analysis, plan=plan)
    transformed.audit.to_csv(output / "preprocessing-audit.csv", index=False)
    fitted = run_workflow_preprocessed(
        analysis, config=FPCAWorkflowConfig(n_components=2, preprocessing=plan),
        runner=run_fpca_workflow,
    )
    durations["preprocessing_and_fitting"] = perf_counter() - t0

    t0 = perf_counter()
    specs = tuple(
        WorkflowSpecification(f"retained-{k}", FPCAWorkflowConfig(n_components=k),
                              "observed_gaze_variance_fraction", "Declared component-count sensitivity")
        for k in (1, 2, 3, 999)
    )
    sensitivity = run_workflow_sensitivity(
        transformed.data, runner=run_fpca_workflow,
        specifications=specs, baseline_name="retained-2",
        metrics={"variance_fraction": lambda r: float(r.fit.explained_variance_ratio.sum())},
    )
    if "retained-999" not in sensitivity.errors:
        raise RuntimeError("Deliberately infeasible sensitivity fit should be recorded as failure")
    sensitivity.specifications.to_csv(output / "sensitivity-specifications.csv", index=False)
    sensitivity.metric_frame.to_csv(output / "sensitivity-values.csv", index=False)
    durations["sensitivity"] = perf_counter() - t0

    t0 = perf_counter()
    ax = plot_workflow_preflight(preflight)
    missing_fig = output / "preflight-missingness.svg"
    ax.figure.savefig(missing_fig, format="svg", bbox_inches="tight")
    plt.close(ax.figure)
    ax = plot_workflow_sensitivity(sensitivity, metric="variance_fraction")
    sensitivity_fig = output / "sensitivity-stability.svg"
    ax.figure.savefig(sensitivity_fig, format="svg", bbox_inches="tight")
    plt.close(ax.figure)
    fig, ax = plt.subplots(figsize=(8, 4))
    for i in range(min(4, analysis.n_curves)):
        ax.plot(analysis.time / float(analysis.time[-1]), analysis.values[i, :, 0],
                alpha=0.55, linestyle="--", label="Before" if i == 0 else None)
        ax.plot(transformed.data.time, transformed.data.values[i, :, 0],
                alpha=0.85, label="After" if i == 0 else None)
    ax.set(xlabel="Normalized position within the same 480 ms window",
           ylabel="Horizontal gaze (pixels)", title="E1: declared smoothing on real traces")
    ax.legend()
    before_after = output / "preprocessing-before-after.svg"
    fig.savefig(before_after, format="svg", bbox_inches="tight")
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(8, 2.7))
    ax.barh(["Observed trial windows", "Dense model sample"],
            [original.n_curves, analysis.n_curves])
    ax.set(xlabel="Trial windows (not independent participants)",
           title="Observed accounting; all exclusions are explicit")
    evidence_fig = output / "report-sample-accounting.svg"
    fig.savefig(evidence_fig, format="svg", bbox_inches="tight")
    plt.close(fig)
    durations["figure_generation"] = perf_counter() - t0

    t0 = perf_counter()
    report = render_workflow_report(
        fitted, output / "scientific-report",
        title="Published human gaze data: E1–E4 research usability case (descriptive)",
        figures={
            "preprocessing-before-after": before_after,
            "preflight-missingness": missing_fig,
            "sensitivity-stability": sensitivity_fig,
            "sample-accounting": evidence_fig,
        },
        figure_captions={
            "preprocessing-before-after": "Same measured gaze traces before and after explicitly declared smoothing.",
            "preflight-missingness": "Original trial windows including those not eligible for complete-case dense FPCA.",
            "sensitivity-stability": "Retained-variance sensitivity; the infeasible fit is a failure, never a zero estimate.",
            "sample-accounting": "All sampled trial windows versus the explicitly selected complete-case analysis subset.",
        },
        preflight=preflight,
        limitations=(
            "Authentic third-party gaze, but this is a software usability study, not known-truth estimator recovery.",
            "Selected first two published trials for eight participants; no inferential or population-generalization claims.",
            "The prespecified complete-case window may induce selection bias; missing trials are explicitly accounted.",
            "Gaussian smoothing may attenuate saccades; FPCA modes are not psychological attention constructs.",
            "Source data are CC BY-NC 4.0; original recordings are not redistributed.",
        ),
    )
    durations["report"] = perf_counter() - t0
    durations["total"] = perf_counter() - started
    _json(output / "usability-evidence.json", {
        "status": "empirical_observed_data_workflow_executed_not_oracle_validation",
        "source_commit": SOURCE_COMMIT, "license": LICENSE,
        "participant_count_input": int(original.metadata.participant_id.nunique()),
        "participant_count_model": int(analysis.metadata.participant_id.nunique()),
        "trial_windows_input": original.n_curves,
        "trial_windows_model": analysis.n_curves,
        "trial_windows_not_selected": original.n_curves - analysis.n_curves,
        "missing_values_original": int((~np.isfinite(original.values)).sum()),
        "missing_values_model": int((~np.isfinite(analysis.values)).sum()),
        "preflight_blocking_issues": list(preflight.blocking_issues),
        "preflight_warnings": list(preflight.warnings),
        "failed_sensitivity_specs": sorted(sensitivity.errors),
        "runtime_seconds": {key: round(value, 5) for key, value in durations.items()},
        "scientific_report_sha256": sha256(report.report_path.read_bytes()).hexdigest(),
        "fabricated_inferential_results": False, "original_raw_data_redistributed": False,
    })
    print(f"PASS empirical E1-E4 usability: {original.n_curves} selected trials, "
          f"{analysis.n_curves} fitted complete-case trials, "
          f"one deliberately failed sensitivity; report {report.report_path}")


if __name__ == "__main__":
    main()
