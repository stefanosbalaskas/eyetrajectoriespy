"""Generate deterministic workflow-orchestration figures for the 1.2 docs."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import numpy as np
import pandas as pd

from eyetrajectoriespy import TrajectorySet, simulate_planar_trajectories
from eyetrajectoriespy.workflows import (
    FPCAWorkflowConfig,
    FunctionOnScalarWorkflowConfig,
    RecurrenceWorkflowConfig,
    run_fpca_workflow,
    run_function_on_scalar_workflow,
    run_recurrence_workflow,
    save_workflow_figure,
)


OUTPUT = Path("docs/assets/gallery")


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    matplotlib.rcParams["svg.hashsalt"] = "eyetrajectoriespy-1.2-workflows"

    gaze = simulate_planar_trajectories(
        n_participants=18,
        trials_per_participant=1,
        n_time=61,
        random_state=2201,
    )
    fpca = run_fpca_workflow(
        gaze,
        config=FPCAWorkflowConfig(
            n_components=2,
            scaling="dimension_sd",
        ),
    )
    save_workflow_figure(
        fpca,
        OUTPUT / "workflow-fpca-component.svg",
        plot="fpca_component",
        component=0,
        dimension=gaze.dimension_names[0],
    )

    condition = np.linspace(-1.0, 1.0, gaze.n_curves)
    fos = run_function_on_scalar_workflow(
        gaze,
        pd.DataFrame(
            {
                "curve_id": gaze.curve_ids,
                "condition": condition,
            }
        ),
        config=FunctionOnScalarWorkflowConfig(
            predictors=("condition",),
            dimensions=(gaze.dimension_names[0],),
        ),
    )
    save_workflow_figure(
        fos,
        OUTPUT / "workflow-function-on-scalar.svg",
        plot="function_on_scalar_coefficient",
        coefficient="condition",
        dimension=gaze.dimension_names[0],
    )

    time = np.arange(240, dtype=float) * 0.01
    signal = 0.5 + 0.25 * np.sin(2.0 * np.pi * 1.8 * time)
    nonlinear = TrajectorySet(
        time=time,
        values=signal[None, :, None],
        curve_ids=("recurrence-workflow-demo",),
        dimension_names=("x",),
        coordinate_system="arbitrary",
        time_unit="s",
    )
    recurrence = run_recurrence_workflow(
        nonlinear,
        config=RecurrenceWorkflowConfig(
            curve=0,
            dimensions=("x",),
            embedding_dimension=2,
            delay=2,
            radius=0.08,
            theiler_window=4,
            min_diagonal_length=2,
            min_vertical_length=2,
        ),
    )
    save_workflow_figure(
        recurrence,
        OUTPUT / "workflow-recurrence.svg",
        plot="recurrence",
    )


if __name__ == "__main__":
    main()
