"""Workflow-level plotting composed from canonical package plotting APIs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from ..generalized_function_on_scalar import (
    plot_generalized_function_on_scalar_coefficients,
)
from ..nonlinear_plotting import plot_recurrence
from ..plotting import (
    plot_fpca_component,
    plot_function_on_scalar_coefficients,
    plot_functional_mixed_effects_coefficient,
    plot_sparse_fpca_component,
)
from ..sparse_multivariate_plotting import plot_sparse_mfpca_component
from ._dense_regression import (
    FPCAWorkflowResult,
    FunctionOnScalarWorkflowResult,
    FunctionalMixedEffectsWorkflowResult,
    GeneralizedFunctionalWorkflowResult,
)
from ._recurrence import RecurrenceWorkflowResult
from ._sparse_fpca import SparseFPCAWorkflowResult
from ._sparse_mfpca import SparseMFPCAWorkflowResult


SUPPORTED_WORKFLOW_PLOTS = (
    "fpca_component",
    "sparse_fpca_component",
    "sparse_mfpca_component",
    "function_on_scalar_coefficient",
    "functional_mixed_effects_coefficient",
    "generalized_functional_coefficient",
    "recurrence",
)


def _require_component(component: int | None) -> int:
    if component is None:
        raise ValueError("component must be supplied explicitly for this plot")
    if isinstance(component, bool) or not isinstance(component, (int, np.integer)):
        raise TypeError("component must be an integer")
    return int(component)


def _require_coefficient(coefficient: str | int | None) -> str | int:
    if coefficient is None:
        raise ValueError("coefficient must be supplied explicitly for this plot")
    if isinstance(coefficient, bool) or not isinstance(
        coefficient,
        (str, int, np.integer),
    ):
        raise TypeError("coefficient must be a name or integer index")
    return int(coefficient) if isinstance(coefficient, np.integer) else coefficient


def plot_workflow_result(
    result: Any,
    *,
    plot: str,
    component: int | None = None,
    dimension: str | None = None,
    coefficient: str | int | None = None,
    sd_multiplier: float = 2.0,
    max_points: int | None = 200_000,
    ax=None,
    axes=None,
):
    """Render one explicitly named canonical plot for a workflow result.

    The workflow layer performs only type/argument dispatch. It does not select
    a component, coefficient, dimension, plot type, or scientific diagnostic.
    """

    if plot not in SUPPORTED_WORKFLOW_PLOTS:
        raise ValueError(
            f"plot must be one of {SUPPORTED_WORKFLOW_PLOTS!r}; "
            "no fallback plot is selected automatically"
        )

    if plot == "fpca_component":
        if not isinstance(result, FPCAWorkflowResult):
            raise TypeError("fpca_component requires an FPCAWorkflowResult")
        component_index = _require_component(component)
        if dimension is None and len(result.fit.dimension_names) > 1:
            raise ValueError(
                "dimension must be supplied explicitly for multivariate FPCA"
            )
        return plot_fpca_component(
            result.fit,
            component=component_index,
            dimension=dimension,
            sd_multiplier=sd_multiplier,
            ax=ax,
        )

    if plot == "sparse_fpca_component":
        if not isinstance(result, SparseFPCAWorkflowResult):
            raise TypeError(
                "sparse_fpca_component requires a SparseFPCAWorkflowResult"
            )
        return plot_sparse_fpca_component(
            result.fit,
            component=_require_component(component),
            sd_multiplier=sd_multiplier,
            ax=ax,
        )

    if plot == "sparse_mfpca_component":
        if not isinstance(result, SparseMFPCAWorkflowResult):
            raise TypeError(
                "sparse_mfpca_component requires a SparseMFPCAWorkflowResult"
            )
        return plot_sparse_mfpca_component(
            result.fit,
            component=_require_component(component),
            sd_multiplier=sd_multiplier,
            axes=axes,
        )

    if plot == "function_on_scalar_coefficient":
        if not isinstance(result, FunctionOnScalarWorkflowResult):
            raise TypeError(
                "function_on_scalar_coefficient requires a "
                "FunctionOnScalarWorkflowResult"
            )
        coefficient_value = _require_coefficient(coefficient)
        if dimension is None and len(result.fit.dimension_names) > 1:
            raise ValueError(
                "dimension must be supplied explicitly for a multivariate "
                "function-on-scalar fit"
            )
        return plot_function_on_scalar_coefficients(
            result.fit,
            coefficient=coefficient_value,
            dimension=dimension,
            ax=ax,
        )

    if plot == "functional_mixed_effects_coefficient":
        if not isinstance(result, FunctionalMixedEffectsWorkflowResult):
            raise TypeError(
                "functional_mixed_effects_coefficient requires a "
                "FunctionalMixedEffectsWorkflowResult"
            )
        return plot_functional_mixed_effects_coefficient(
            result.fit,
            coefficient=_require_coefficient(coefficient),
            ax=ax,
        )

    if plot == "generalized_functional_coefficient":
        if not isinstance(result, GeneralizedFunctionalWorkflowResult):
            raise TypeError(
                "generalized_functional_coefficient requires a "
                "GeneralizedFunctionalWorkflowResult"
            )
        coefficient_value = _require_coefficient(coefficient)
        if not isinstance(coefficient_value, str):
            raise TypeError(
                "generalized functional coefficient plots require an explicit "
                "coefficient name"
            )
        return plot_generalized_function_on_scalar_coefficients(
            result.fit,
            coefficient=coefficient_value,
            ax=ax,
        )

    if plot == "recurrence":
        if not isinstance(result, RecurrenceWorkflowResult):
            raise TypeError("recurrence requires a RecurrenceWorkflowResult")
        return plot_recurrence(
            result.recurrence,
            max_points=max_points,
            ax=ax,
        )

    raise RuntimeError("unreachable workflow plot dispatch")


def save_workflow_figure(
    result: Any,
    path: str | Path,
    *,
    plot: str,
    dpi: int = 150,
    close: bool = True,
    **plot_kwargs: Any,
) -> Path:
    """Save an explicitly requested workflow plot with deterministic metadata."""

    if isinstance(dpi, bool) or not isinstance(dpi, (int, np.integer)) or int(dpi) < 1:
        raise ValueError("dpi must be a positive integer")
    destination = Path(path)
    if destination.suffix.lower() not in {".png", ".svg", ".pdf"}:
        raise ValueError("workflow figure path must end in .png, .svg, or .pdf")
    destination.parent.mkdir(parents=True, exist_ok=True)

    plotted = plot_workflow_result(
        result,
        plot=plot,
        **plot_kwargs,
    )
    if isinstance(plotted, np.ndarray):
        flattened = np.asarray(plotted, dtype=object).reshape(-1)
        if flattened.size == 0 or not hasattr(flattened[0], "figure"):
            raise TypeError("canonical plot did not return Matplotlib axes")
        figure = flattened[0].figure
    elif hasattr(plotted, "figure"):
        figure = plotted.figure
    else:
        raise TypeError("canonical plot did not return Matplotlib axes")

    metadata = {"Date": None} if destination.suffix.lower() == ".svg" else None
    figure.savefig(destination, dpi=int(dpi), metadata=metadata)
    if close:
        import matplotlib.pyplot as plt

        plt.close(figure)
    return destination
