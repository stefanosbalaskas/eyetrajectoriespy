"""Generate deterministic workflow-orchestration figures for the 1.2 docs."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
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
    workflow_decisions_frame,
    workflow_steps_frame,
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


    # Provenance charts summarize actual typed records, not benchmark or scientific
    # performance. Only workflow metadata with deterministic example inputs is used.
    routes = (("Dense FPCA", fpca), ("Function-on-scalar", fos), ("Recurrence", recurrence))
    sources = ("analyst", "audited_selector", "workflow_contract", "derived")
    labels = [label for label, _ in routes]
    bottom = np.zeros(len(routes), dtype=int)
    fig, ax = plt.subplots(figsize=(9.2, 4.4))
    for source in sources:
        heights = np.asarray(
            [
                int((workflow_decisions_frame(result.decisions)["source"] == source).sum())
                for _, result in routes
            ],
            dtype=int,
        )
        ax.bar(labels, heights, bottom=bottom, label=source.replace("_", " "))
        bottom += heights
    ax.set_title("Decision provenance in three synthetic workflows")
    ax.set_ylabel("Recorded decisions (count)")
    ax.legend(fontsize=8, ncol=2, frameon=False)
    fig.tight_layout()
    fig.savefig(
        OUTPUT / "workflow-audit-provenance.svg",
        format="svg",
        metadata={"Date": None},
    )
    plt.close(fig)

    # Horizontal positions encode *only step order*. Avoid non-deterministic
    # elapsed-time plots in the generated scientific documentation gallery.
    records = workflow_steps_frame(fpca.steps)
    orders = records["order"].to_numpy(dtype=int)
    fig, ax = plt.subplots(figsize=(10.0, 3.6))
    ax.plot(orders, np.zeros(len(orders)), alpha=0.6, linewidth=1.4)
    ax.scatter(orders, np.zeros(len(orders)), s=100, zorder=3)
    for order, row in zip(orders, records.itertuples(index=False), strict=True):
        ax.annotate(
            f"{row.name.replace('_', ' ')}\n({row.status})",
            (order, 0.0),
            xytext=(0, 18),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=8,
            rotation=12,
        )
    ax.set_xlim(float(orders.min()) - 0.6, float(orders.max()) + 0.6)
    ax.set_ylim(-0.35, 0.85)
    ax.set_xticks(orders)
    ax.set_yticks([])
    ax.set_xlabel("Recorded workflow step order (not elapsed time)")
    ax.set_title("Typed execution trail: synthetic FPCA workflow")
    for spine in ("left", "top", "right"):
        ax.spines[spine].set_visible(False)
    fig.tight_layout()
    fig.savefig(
        OUTPUT / "workflow-audit-steps.svg",
        format="svg",
        metadata={"Date": None},
    )
    plt.close(fig)


if __name__ == "__main__":
    main()
