"""Familywise post-calibration for heteroscedastic Gaussian FPCR wild bootstrap."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .types import (
    FPCAWildBootstrapProjectionResult,
    FPCAWildBootstrapSimultaneousResult,
)


def fpca_wild_bootstrap_projection_simultaneous_interval(
    result: FPCAWildBootstrapProjectionResult,
    *,
    confidence_level: float | None = None,
) -> FPCAWildBootstrapSimultaneousResult:
    """Calibrate one max-|t| critical value across all fixed target projections.

    The function is a post-calibration layer. It reuses the studentized roots
    produced by :func:`wild_bootstrap_fpca_projection` and does not rerun FPCA,
    score regression, residual estimation, or wild multiplier generation.

    The simultaneous family is exactly the complete set of fixed targets stored
    in ``result``. To define a different family, create the base wild-bootstrap
    result with that target set before calling this function.
    """

    if not isinstance(result, FPCAWildBootstrapProjectionResult):
        raise TypeError("result must be an FPCAWildBootstrapProjectionResult")

    level = result.confidence_level if confidence_level is None else confidence_level
    if isinstance(level, bool) or not isinstance(level, (int, float, np.integer, np.floating)):
        raise TypeError("confidence_level must be numeric")
    level = float(level)
    if not np.isfinite(level) or not 0.0 < level < 1.0:
        raise ValueError("confidence_level must lie in (0, 1)")

    roots = np.asarray(result.studentized_roots, dtype=float)
    expected = (result.n_bootstrap, result.n_targets)
    if roots.shape != expected:
        raise ValueError("studentized_roots shape is inconsistent with the base result")
    if not np.all(np.isfinite(roots)):
        raise ValueError("studentized_roots must contain only finite values")

    reference = np.asarray(result.reference_projection, dtype=float)
    standard_error = np.asarray(result.reference_se, dtype=float)
    if reference.shape != (result.n_targets,) or standard_error.shape != (result.n_targets,):
        raise ValueError("reference projection arrays are inconsistent with the base result")
    if not np.all(np.isfinite(reference)):
        raise ValueError("reference projections must contain only finite values")
    if not np.all(np.isfinite(standard_error)) or np.any(standard_error < 0.0):
        raise ValueError("reference standard errors must be finite and non-negative")

    absolute_roots = np.abs(roots)
    targetwise_critical_values = np.quantile(
        absolute_roots,
        level,
        axis=0,
        method="higher",
    )
    max_statistics = np.max(absolute_roots, axis=1)
    critical_value = float(
        np.quantile(max_statistics, level, method="higher")
    )

    lower = reference - critical_value * standard_error
    upper = reference + critical_value * standard_error

    base_settings = result.provenance.get(
        "fpca_wild_bootstrap_projection", {}
    )
    return FPCAWildBootstrapSimultaneousResult(
        projection_result=result,
        targetwise_critical_values=np.asarray(targetwise_critical_values, dtype=float),
        critical_value=critical_value,
        max_statistics=np.asarray(max_statistics, dtype=float),
        lower=np.asarray(lower, dtype=float),
        upper=np.asarray(upper, dtype=float),
        confidence_level=level,
        provenance={
            **dict(result.provenance),
            "fpca_wild_bootstrap_simultaneous": {
                "method": "postcalibrated_max_abs_studentized_root",
                "family": "gaussian",
                "estimand": "centered_projection_relative_to_training_functional_mean",
                "confidence_level": level,
                "n_targets": result.n_targets,
                "family_definition": "all_fixed_targets_in_base_projection_result",
                "bootstrap_roots_reused": True,
                "bootstrap_rerun": False,
                "studentization": base_settings.get("studentization"),
                "multiplier": result.multiplier,
                "residual_components_k": result.residual_components,
                "pseudo_truth_components_g": result.residual_components,
                "inference_components_h": result.inference_components,
                "simultaneous_across_targets": True,
                "future_outcome_prediction_interval": False,
                "clustered_wild_bootstrap": False,
                "component_selection_uncertainty_included": False,
            },
        },
    )


def fpca_wild_bootstrap_simultaneous_frame(
    result: FPCAWildBootstrapSimultaneousResult,
) -> pd.DataFrame:
    """Return target-wise and familywise wild-bootstrap interval summaries."""

    if not isinstance(result, FPCAWildBootstrapSimultaneousResult):
        raise TypeError("result must be an FPCAWildBootstrapSimultaneousResult")
    base = result.projection_result
    targetwise_lower = (
        base.reference_projection - result.targetwise_critical_values * base.reference_se
    )
    targetwise_upper = (
        base.reference_projection + result.targetwise_critical_values * base.reference_se
    )
    return pd.DataFrame(
        {
            "curve_id": base.target_curve_ids,
            "reference_projection": base.reference_projection,
            "heteroscedastic_se": base.reference_se,
            "targetwise_critical_value": result.targetwise_critical_values,
            "familywise_critical_value": np.repeat(result.critical_value, result.n_targets),
            "targetwise_lower": targetwise_lower,
            "targetwise_upper": targetwise_upper,
            "simultaneous_lower": result.lower,
            "simultaneous_upper": result.upper,
        }
    )
