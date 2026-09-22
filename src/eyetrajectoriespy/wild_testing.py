"""Hypothesis testing from heteroscedastic Gaussian FPCR wild-bootstrap roots."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import beta

from .types import (
    FPCAWildBootstrapFamilyTestResult,
    FPCAWildBootstrapMonteCarloDiagnosticResult,
    FPCAWildBootstrapProjectionResult,
)


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


def _exact_binomial_interval(
    exceedances: np.ndarray | int,
    *,
    n_bootstrap: int,
    confidence_level: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Return Clopper-Pearson intervals for bootstrap exceedance probabilities."""

    counts = np.asarray(exceedances, dtype=int)
    alpha = 1.0 - confidence_level
    lower = np.zeros(counts.shape, dtype=float)
    upper = np.ones(counts.shape, dtype=float)

    positive = counts > 0
    if np.any(positive):
        lower[positive] = beta.ppf(
            alpha / 2.0,
            counts[positive],
            n_bootstrap - counts[positive] + 1,
        )
    below_maximum = counts < n_bootstrap
    if np.any(below_maximum):
        upper[below_maximum] = beta.ppf(
            1.0 - alpha / 2.0,
            counts[below_maximum] + 1,
            n_bootstrap - counts[below_maximum],
        )
    return lower, upper


def _decision_stability(
    lower: np.ndarray,
    upper: np.ndarray,
    *,
    rejected: np.ndarray,
    significance_level: float,
) -> np.ndarray:
    """Flag whether Monte Carlo uncertainty stays on the reported decision side."""

    rejected = np.asarray(rejected, dtype=bool)
    return np.where(
        rejected,
        upper < significance_level,
        lower > significance_level,
    )


def fpca_wild_bootstrap_family_test_monte_carlo_diagnostics(
    result: FPCAWildBootstrapFamilyTestResult,
    *,
    confidence_level: float = 0.95,
) -> FPCAWildBootstrapMonteCarloDiagnosticResult:
    """Quantify finite-bootstrap Monte Carlo precision for family-test tail counts.

    The diagnostic reuses the already retained bootstrap roots and does not
    redraw multipliers or refit any model. Exact Clopper-Pearson intervals
    describe uncertainty in the binomial exceedance probabilities induced by
    a finite number of bootstrap replicates. They are Monte Carlo diagnostics,
    not confidence intervals for the scientific estimand and not stronger
    family-wise error guarantees.

    Decision-stability flags are conservative diagnostics: a reported rejection
    is stable only when the complete Monte Carlo interval lies below alpha; a
    reported non-rejection is stable only when the complete interval lies above
    alpha. A False flag therefore means that the finite-resample precision is
    insufficient to separate the tail probability from alpha at the requested
    diagnostic confidence level. It does not reverse the original test result.
    """

    if not isinstance(result, FPCAWildBootstrapFamilyTestResult):
        raise TypeError("result must be an FPCAWildBootstrapFamilyTestResult")
    if isinstance(confidence_level, bool) or not isinstance(
        confidence_level, (int, float, np.integer, np.floating)
    ):
        raise TypeError("confidence_level must be numeric")
    confidence_level = float(confidence_level)
    if not np.isfinite(confidence_level) or not 0.0 < confidence_level < 1.0:
        raise ValueError("confidence_level must lie in (0, 1)")

    base = result.projection_result
    roots = np.asarray(base.studentized_roots, dtype=float)
    expected = (result.n_bootstrap, result.n_targets)
    if roots.shape != expected:
        raise ValueError("studentized_roots shape is inconsistent with the family test")
    if not np.all(np.isfinite(roots)):
        raise ValueError("studentized_roots must contain only finite values")

    observed = np.asarray(result.observed_statistics, dtype=float)
    if observed.shape != (result.n_targets,) or not np.all(np.isfinite(observed)):
        raise ValueError("observed_statistics are inconsistent with the family test")

    maximum = np.asarray(result.max_statistics, dtype=float)
    if maximum.shape != (result.n_bootstrap,) or not np.all(np.isfinite(maximum)):
        raise ValueError("max_statistics are inconsistent with the family test")

    global_statistic = float(result.global_statistic)
    if not np.isfinite(global_statistic):
        raise ValueError("global_statistic must be finite")

    targetwise_reject = np.asarray(result.reject_targetwise, dtype=bool)
    adjusted_reject = np.asarray(result.reject_familywise, dtype=bool)
    if targetwise_reject.shape != (result.n_targets,):
        raise ValueError("reject_targetwise shape is inconsistent with the family test")
    if adjusted_reject.shape != (result.n_targets,):
        raise ValueError("reject_familywise shape is inconsistent with the family test")

    absolute_roots = np.abs(roots)
    absolute_observed = np.abs(observed)
    targetwise_exceedances = np.sum(
        absolute_roots >= absolute_observed[None, :],
        axis=0,
    ).astype(int)
    adjusted_exceedances = np.sum(
        maximum[:, None] >= absolute_observed[None, :],
        axis=0,
    ).astype(int)
    global_exceedances = int(np.sum(maximum >= global_statistic))

    n_bootstrap = result.n_bootstrap
    targetwise_tail = targetwise_exceedances.astype(float) / float(n_bootstrap)
    adjusted_tail = adjusted_exceedances.astype(float) / float(n_bootstrap)
    global_tail = global_exceedances / float(n_bootstrap)

    targetwise_mcse = np.sqrt(
        targetwise_tail * (1.0 - targetwise_tail) / float(n_bootstrap)
    )
    adjusted_mcse = np.sqrt(
        adjusted_tail * (1.0 - adjusted_tail) / float(n_bootstrap)
    )
    global_mcse = float(np.sqrt(global_tail * (1.0 - global_tail) / float(n_bootstrap)))

    targetwise_lower, targetwise_upper = _exact_binomial_interval(
        targetwise_exceedances,
        n_bootstrap=n_bootstrap,
        confidence_level=confidence_level,
    )
    adjusted_lower, adjusted_upper = _exact_binomial_interval(
        adjusted_exceedances,
        n_bootstrap=n_bootstrap,
        confidence_level=confidence_level,
    )
    global_lower_array, global_upper_array = _exact_binomial_interval(
        np.asarray([global_exceedances], dtype=int),
        n_bootstrap=n_bootstrap,
        confidence_level=confidence_level,
    )
    global_lower = float(global_lower_array[0])
    global_upper = float(global_upper_array[0])

    targetwise_stable = _decision_stability(
        targetwise_lower,
        targetwise_upper,
        rejected=targetwise_reject,
        significance_level=result.significance_level,
    )
    adjusted_stable = _decision_stability(
        adjusted_lower,
        adjusted_upper,
        rejected=adjusted_reject,
        significance_level=result.significance_level,
    )
    global_stable = bool(
        _decision_stability(
            np.asarray([global_lower]),
            np.asarray([global_upper]),
            rejected=np.asarray([result.reject_global]),
            significance_level=result.significance_level,
        )[0]
    )

    return FPCAWildBootstrapMonteCarloDiagnosticResult(
        family_test_result=result,
        confidence_level=confidence_level,
        targetwise_exceedances=targetwise_exceedances,
        adjusted_exceedances=adjusted_exceedances,
        global_exceedances=global_exceedances,
        targetwise_tail_probabilities=targetwise_tail,
        adjusted_tail_probabilities=adjusted_tail,
        global_tail_probability=global_tail,
        targetwise_mcse=targetwise_mcse,
        adjusted_mcse=adjusted_mcse,
        global_mcse=global_mcse,
        targetwise_interval_lower=targetwise_lower,
        targetwise_interval_upper=targetwise_upper,
        adjusted_interval_lower=adjusted_lower,
        adjusted_interval_upper=adjusted_upper,
        global_interval_lower=global_lower,
        global_interval_upper=global_upper,
        targetwise_decision_stable=np.asarray(targetwise_stable, dtype=bool),
        adjusted_decision_stable=np.asarray(adjusted_stable, dtype=bool),
        global_decision_stable=global_stable,
        provenance={
            **dict(result.provenance),
            "fpca_wild_bootstrap_monte_carlo_diagnostics": {
                "method": "binomial_monte_carlo_precision_diagnostic",
                "interval_method": "clopper_pearson_exact_binomial",
                "confidence_level": confidence_level,
                "n_bootstrap": n_bootstrap,
                "exceedance_model": (
                    "binomial_conditional_on_observed_statistic_and_bootstrap_design"
                ),
                "tail_probability_estimator": "exceedances_over_B",
                "monte_carlo_standard_error": "sqrt(qhat*(1-qhat)/B)",
                "reported_test_pvalue_correction": result.pvalue_correction,
                "reported_test_minimum_attainable_p": result.minimum_attainable_p,
                "decision_stability_rule": (
                    "complete_monte_carlo_interval_on_reported_decision_side_of_alpha"
                ),
                "changes_reported_test_decisions": False,
                "additional_bootstrap_draws": False,
                "bootstrap_roots_reused": True,
                "scientific_sampling_uncertainty_quantified": False,
                "monte_carlo_sampling_uncertainty_quantified": True,
                "strong_fwer_claim_added": False,
                "clustered_wild_bootstrap": False,
                "component_selection_uncertainty_included": False,
            },
        },
    )


def fpca_wild_bootstrap_monte_carlo_diagnostic_frame(
    result: FPCAWildBootstrapMonteCarloDiagnosticResult,
) -> pd.DataFrame:
    """Return target-level Monte Carlo precision diagnostics."""

    if not isinstance(result, FPCAWildBootstrapMonteCarloDiagnosticResult):
        raise TypeError("result must be an FPCAWildBootstrapMonteCarloDiagnosticResult")
    family = result.family_test_result
    base = family.projection_result

    targetwise_status = np.where(
        result.targetwise_decision_stable,
        np.where(family.reject_targetwise, "stable_reject", "stable_non_reject"),
        "monte_carlo_sensitive",
    )
    adjusted_status = np.where(
        result.adjusted_decision_stable,
        np.where(family.reject_familywise, "stable_reject", "stable_non_reject"),
        "monte_carlo_sensitive",
    )

    return pd.DataFrame(
        {
            "curve_id": base.target_curve_ids,
            "targetwise_exceedances": result.targetwise_exceedances,
            "targetwise_tail_probability": result.targetwise_tail_probabilities,
            "targetwise_mcse": result.targetwise_mcse,
            "targetwise_mc_lower": result.targetwise_interval_lower,
            "targetwise_mc_upper": result.targetwise_interval_upper,
            "targetwise_precision_status": targetwise_status,
            "adjusted_exceedances": result.adjusted_exceedances,
            "adjusted_tail_probability": result.adjusted_tail_probabilities,
            "adjusted_mcse": result.adjusted_mcse,
            "adjusted_mc_lower": result.adjusted_interval_lower,
            "adjusted_mc_upper": result.adjusted_interval_upper,
            "adjusted_precision_status": adjusted_status,
            "reported_targetwise_p_value": family.targetwise_p_values,
            "reported_adjusted_p_value": family.adjusted_p_values,
            "alpha": np.repeat(family.significance_level, result.n_targets),
        }
    )
