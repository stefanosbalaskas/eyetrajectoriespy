"""Hypothesis testing from heteroscedastic Gaussian FPCR wild-bootstrap roots."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .types import FPCAWildBootstrapFamilyTestResult, FPCAWildBootstrapProjectionResult


def _validate_null_values(null_values, *, n_targets: int) -> np.ndarray:
    raw = np.asarray(null_values)
    if raw.dtype.kind == "b":
        raise TypeError("null_values must be numeric, not boolean")
    try:
        values = np.asarray(null_values, dtype=float)
    except (TypeError, ValueError) as exc:
        raise TypeError("null_values must be numeric") from exc
    if values.ndim == 0:
        values = np.repeat(float(values), n_targets)
    elif values.shape != (n_targets,):
        raise ValueError(
            "null_values must be a scalar or contain exactly one value per target"
        )
    if not np.all(np.isfinite(values)):
        raise ValueError("null_values must contain only finite values")
    return np.asarray(values, dtype=float)


def _bootstrap_tail_probability(
    exceedances: np.ndarray | int,
    *,
    n_bootstrap: int,
    correction: str,
):
    if correction == "plus_one":
        return (np.asarray(exceedances, dtype=float) + 1.0) / float(n_bootstrap + 1)
    if correction == "none":
        return np.asarray(exceedances, dtype=float) / float(n_bootstrap)
    raise ValueError("pvalue_correction must be 'plus_one' or 'none'")


def fpca_wild_bootstrap_projection_family_test(
    result: FPCAWildBootstrapProjectionResult,
    *,
    null_values=0.0,
    significance_level: float = 0.05,
    pvalue_correction: str = "plus_one",
) -> FPCAWildBootstrapFamilyTestResult:
    """Test a fixed family of centered FPCR projection null hypotheses.

    This post-processing function reuses the studentized wild-bootstrap roots
    stored in the supplied result. No FPCA fit, score regression, residual
    calculation, multiplier draw, or bootstrap replicate is rerun.

    Marginal tail probabilities use each target's absolute studentized roots.
    Single-step adjusted probabilities use the replicate-wise maximum absolute
    studentized root across the complete declared target family.

    The default plus-one correction avoids zero Monte Carlo p-values. Strong
    family-wise error control for arbitrary subsets of null hypotheses is not
    claimed without additional subset-pivotality conditions.
    """

    if not isinstance(result, FPCAWildBootstrapProjectionResult):
        raise TypeError("result must be an FPCAWildBootstrapProjectionResult")
    if isinstance(significance_level, bool) or not isinstance(
        significance_level, (int, float, np.integer, np.floating)
    ):
        raise TypeError("significance_level must be numeric")
    significance_level = float(significance_level)
    if not np.isfinite(significance_level) or not 0.0 < significance_level < 1.0:
        raise ValueError("significance_level must lie in (0, 1)")
    if pvalue_correction not in {"plus_one", "none"}:
        raise ValueError("pvalue_correction must be 'plus_one' or 'none'")

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

    null = _validate_null_values(null_values, n_targets=result.n_targets)
    difference = reference - null
    se_scale = max(1.0, float(np.max(standard_error)) if standard_error.size else 1.0)
    positive = standard_error > np.finfo(float).eps * se_scale
    difference_scale = max(
        1.0,
        float(np.max(np.abs(reference))) if reference.size else 1.0,
        float(np.max(np.abs(null))) if null.size else 1.0,
    )
    tolerance = 100.0 * np.finfo(float).eps * difference_scale
    observed = np.zeros_like(difference)
    np.divide(difference, standard_error, out=observed, where=positive)
    degenerate = (~positive) & (np.abs(difference) > tolerance)
    if np.any(degenerate):
        bad = np.flatnonzero(degenerate).tolist()
        raise RuntimeError(
            "zero reference standard error with a non-zero null discrepancy for "
            f"target index/indices {bad[:8]}"
        )

    absolute_roots = np.abs(roots)
    absolute_observed = np.abs(observed)
    max_statistics = np.max(absolute_roots, axis=1)
    global_statistic = float(np.max(absolute_observed))
    targetwise_exceedances = np.sum(absolute_roots >= absolute_observed[None, :], axis=0)
    adjusted_exceedances = np.sum(max_statistics[:, None] >= absolute_observed[None, :], axis=0)
    global_exceedances = int(np.sum(max_statistics >= global_statistic))
    targetwise_p = np.asarray(_bootstrap_tail_probability(
        targetwise_exceedances, n_bootstrap=result.n_bootstrap, correction=pvalue_correction
    ), dtype=float)
    adjusted_p = np.asarray(_bootstrap_tail_probability(
        adjusted_exceedances, n_bootstrap=result.n_bootstrap, correction=pvalue_correction
    ), dtype=float)
    global_p = float(_bootstrap_tail_probability(
        global_exceedances, n_bootstrap=result.n_bootstrap, correction=pvalue_correction
    ))

    base_settings = result.provenance.get("fpca_wild_bootstrap_projection", {})
    minimum_p = 1.0 / (result.n_bootstrap + 1.0) if pvalue_correction == "plus_one" else 0.0
    return FPCAWildBootstrapFamilyTestResult(
        projection_result=result,
        null_values=null,
        observed_statistics=np.asarray(observed, dtype=float),
        targetwise_p_values=targetwise_p,
        adjusted_p_values=adjusted_p,
        max_statistics=np.asarray(max_statistics, dtype=float),
        global_statistic=global_statistic,
        global_p_value=global_p,
        reject_targetwise=np.asarray(targetwise_p <= significance_level, dtype=bool),
        reject_familywise=np.asarray(adjusted_p <= significance_level, dtype=bool),
        reject_global=bool(global_p <= significance_level),
        significance_level=significance_level,
        pvalue_correction=pvalue_correction,
        provenance={
            **dict(result.provenance),
            "fpca_wild_bootstrap_family_test": {
                "method": "single_step_max_abs_studentized_root",
                "family": "gaussian",
                "estimand": "centered_projection_relative_to_training_functional_mean",
                "alternative": "two_sided",
                "global_null": "all_target_projections_equal_supplied_null_values",
                "n_targets": result.n_targets,
                "family_definition": "all_fixed_targets_in_base_projection_result",
                "significance_level": significance_level,
                "pvalue_correction": pvalue_correction,
                "minimum_attainable_p": minimum_p,
                "bootstrap_roots_reused": True,
                "bootstrap_rerun": False,
                "null_enforced_bootstrap": False,
                "studentization": base_settings.get("studentization"),
                "multiplier": result.multiplier,
                "residual_components_k": result.residual_components,
                "pseudo_truth_components_g": result.residual_components,
                "inference_components_h": result.inference_components,
                "single_step_familywise_adjustment": True,
                "strong_fwer_for_arbitrary_subset_nulls_claimed": False,
                "subset_pivotality_assumed_by_package": False,
                "future_outcome_test": False,
                "clustered_wild_bootstrap": False,
                "component_selection_uncertainty_included": False,
            },
        },
    )


def fpca_wild_bootstrap_family_test_frame(
    result: FPCAWildBootstrapFamilyTestResult,
) -> pd.DataFrame:
    """Return target-level fixed-family wild-bootstrap test summaries."""
    if not isinstance(result, FPCAWildBootstrapFamilyTestResult):
        raise TypeError("result must be an FPCAWildBootstrapFamilyTestResult")
    base = result.projection_result
    return pd.DataFrame({
        "curve_id": base.target_curve_ids,
        "reference_projection": base.reference_projection,
        "null_value": result.null_values,
        "heteroscedastic_se": base.reference_se,
        "observed_statistic": result.observed_statistics,
        "targetwise_p_value": result.targetwise_p_values,
        "adjusted_p_value": result.adjusted_p_values,
        "reject_targetwise": result.reject_targetwise,
        "reject_familywise": result.reject_familywise,
        "global_statistic": np.repeat(result.global_statistic, result.n_targets),
        "global_p_value": np.repeat(result.global_p_value, result.n_targets),
    })
