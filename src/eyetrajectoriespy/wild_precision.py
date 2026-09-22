"""Finite-resample Monte Carlo precision diagnostics for wild-bootstrap tests."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import beta

from .types import (
    FPCAWildBootstrapFamilyTestResult,
    FPCAWildBootstrapMonteCarloPrecisionResult,
)


def _validate_confidence_level(confidence_level: float) -> float:
    if isinstance(confidence_level, bool) or not isinstance(
        confidence_level, (int, float, np.integer, np.floating)
    ):
        raise TypeError("confidence_level must be numeric")
    value = float(confidence_level)
    if not np.isfinite(value) or not 0.0 < value < 1.0:
        raise ValueError("confidence_level must lie in (0, 1)")
    return value


def _exact_binomial_interval(
    counts: np.ndarray,
    *,
    n: int,
    confidence_level: float,
) -> tuple[np.ndarray, np.ndarray]:
    counts = np.asarray(counts, dtype=int)
    alpha = 1.0 - confidence_level
    lower = np.zeros(counts.shape, dtype=float)
    upper = np.ones(counts.shape, dtype=float)

    positive = counts > 0
    below_n = counts < n
    lower[positive] = beta.ppf(
        alpha / 2.0,
        counts[positive],
        n - counts[positive] + 1,
    )
    upper[below_n] = beta.ppf(
        1.0 - alpha / 2.0,
        counts[below_n] + 1,
        n - counts[below_n],
    )
    return lower, upper


def _alpha_relation(
    lower: np.ndarray,
    upper: np.ndarray,
    *,
    alpha: float,
) -> tuple[str, ...]:
    relation: list[str] = []
    for lo, hi in zip(lower, upper, strict=True):
        if hi < alpha:
            relation.append("below_alpha")
        elif lo > alpha:
            relation.append("above_alpha")
        else:
            relation.append("overlaps_alpha")
    return tuple(relation)


def fpca_wild_bootstrap_family_test_monte_carlo_precision(
    result: FPCAWildBootstrapFamilyTestResult,
    *,
    confidence_level: float = 0.95,
) -> FPCAWildBootstrapMonteCarloPrecisionResult:
    """Quantify finite-B Monte Carlo precision for a fixed-family bootstrap test.

    The diagnostic reuses the exact studentized roots and observed statistics in
    the supplied result. It does not rerun FPCA, regression, residual estimation,
    multiplier generation, or the bootstrap. Exceedance counts are treated as
    Bernoulli outcomes conditional on the retained bootstrap comparison distribution.

    Exact Clopper-Pearson intervals describe uncertainty in the underlying
    resampling tail probability. They are Monte Carlo diagnostics, not confidence
    intervals for a scientific effect and not an additional family-wise error
    guarantee. Existing target-wise, adjusted, and global p-values are unchanged.
    """

    if not isinstance(result, FPCAWildBootstrapFamilyTestResult):
        raise TypeError("result must be an FPCAWildBootstrapFamilyTestResult")
    confidence_level = _validate_confidence_level(confidence_level)

    base = result.projection_result
    roots = np.asarray(base.studentized_roots, dtype=float)
    expected = (result.n_bootstrap, result.n_targets)
    if roots.shape != expected:
        raise ValueError("studentized_roots shape is inconsistent with the test result")
    if not np.all(np.isfinite(roots)):
        raise ValueError("studentized_roots must contain only finite values")

    observed = np.asarray(result.observed_statistics, dtype=float)
    if observed.shape != (result.n_targets,):
        raise ValueError("observed_statistics shape is inconsistent with the test result")
    if not np.all(np.isfinite(observed)):
        raise ValueError("observed_statistics must contain only finite values")

    absolute_roots = np.abs(roots)
    absolute_observed = np.abs(observed)
    max_statistics = np.max(absolute_roots, axis=1)
    targetwise_counts = np.sum(
        absolute_roots >= absolute_observed[None, :],
        axis=0,
    ).astype(int)
    adjusted_counts = np.sum(
        max_statistics[:, None] >= absolute_observed[None, :],
        axis=0,
    ).astype(int)
    global_statistic = float(np.max(absolute_observed))
    global_count = int(np.sum(max_statistics >= global_statistic))

    n_bootstrap = result.n_bootstrap
    targetwise_probability = targetwise_counts.astype(float) / n_bootstrap
    adjusted_probability = adjusted_counts.astype(float) / n_bootstrap
    global_probability = global_count / n_bootstrap

    targetwise_mcse = np.sqrt(
        targetwise_probability * (1.0 - targetwise_probability) / n_bootstrap
    )
    adjusted_mcse = np.sqrt(
        adjusted_probability * (1.0 - adjusted_probability) / n_bootstrap
    )
    global_mcse = float(
        np.sqrt(global_probability * (1.0 - global_probability) / n_bootstrap)
    )

    targetwise_lower, targetwise_upper = _exact_binomial_interval(
        targetwise_counts,
        n=n_bootstrap,
        confidence_level=confidence_level,
    )
    adjusted_lower, adjusted_upper = _exact_binomial_interval(
        adjusted_counts,
        n=n_bootstrap,
        confidence_level=confidence_level,
    )
    global_lower_arr, global_upper_arr = _exact_binomial_interval(
        np.asarray([global_count]),
        n=n_bootstrap,
        confidence_level=confidence_level,
    )
    global_lower = float(global_lower_arr[0])
    global_upper = float(global_upper_arr[0])

    alpha = result.significance_level
    targetwise_relation = _alpha_relation(
        targetwise_lower,
        targetwise_upper,
        alpha=alpha,
    )
    adjusted_relation = _alpha_relation(
        adjusted_lower,
        adjusted_upper,
        alpha=alpha,
    )
    global_relation = _alpha_relation(
        np.asarray([global_lower]),
        np.asarray([global_upper]),
        alpha=alpha,
    )[0]

    return FPCAWildBootstrapMonteCarloPrecisionResult(
        family_test_result=result,
        targetwise_exceedances=targetwise_counts,
        adjusted_exceedances=adjusted_counts,
        global_exceedances=global_count,
        targetwise_tail_probabilities=targetwise_probability,
        adjusted_tail_probabilities=adjusted_probability,
        global_tail_probability=global_probability,
        targetwise_mcse=np.asarray(targetwise_mcse, dtype=float),
        adjusted_mcse=np.asarray(adjusted_mcse, dtype=float),
        global_mcse=global_mcse,
        targetwise_ci_lower=np.asarray(targetwise_lower, dtype=float),
        targetwise_ci_upper=np.asarray(targetwise_upper, dtype=float),
        adjusted_ci_lower=np.asarray(adjusted_lower, dtype=float),
        adjusted_ci_upper=np.asarray(adjusted_upper, dtype=float),
        global_ci_lower=global_lower,
        global_ci_upper=global_upper,
        confidence_level=confidence_level,
        targetwise_alpha_relation=targetwise_relation,
        adjusted_alpha_relation=adjusted_relation,
        global_alpha_relation=global_relation,
        provenance={
            **dict(result.provenance),
            "fpca_wild_bootstrap_monte_carlo_precision": {
                "method": "finite_bootstrap_tail_count_precision",
                "n_bootstrap": n_bootstrap,
                "confidence_level": confidence_level,
                "interval_method": "clopper_pearson_exact_binomial",
                "mcse_method": "sqrt_p_one_minus_p_over_B",
                "tail_probability_estimator": "exceedances_over_B",
                "reported_p_values_changed": False,
                "bootstrap_roots_reused": True,
                "bootstrap_rerun": False,
                "alpha_relation_is_diagnostic_only": True,
                "scientific_effect_confidence_interval": False,
                "additional_familywise_error_guarantee": False,
                "strong_fwer_for_arbitrary_subset_nulls_claimed": False,
                "clustered_wild_bootstrap": False,
                "component_selection_uncertainty_included": False,
            },
        },
    )


def fpca_wild_bootstrap_monte_carlo_precision_frame(
    result: FPCAWildBootstrapMonteCarloPrecisionResult,
) -> pd.DataFrame:
    """Return target-level finite-resample precision diagnostics."""

    if not isinstance(result, FPCAWildBootstrapMonteCarloPrecisionResult):
        raise TypeError(
            "result must be an FPCAWildBootstrapMonteCarloPrecisionResult"
        )
    test = result.family_test_result
    base = test.projection_result
    return pd.DataFrame(
        {
            "curve_id": base.target_curve_ids,
            "targetwise_p_value": test.targetwise_p_values,
            "targetwise_exceedances": result.targetwise_exceedances,
            "targetwise_tail_probability": result.targetwise_tail_probabilities,
            "targetwise_mcse": result.targetwise_mcse,
            "targetwise_ci_lower": result.targetwise_ci_lower,
            "targetwise_ci_upper": result.targetwise_ci_upper,
            "targetwise_alpha_relation": result.targetwise_alpha_relation,
            "adjusted_p_value": test.adjusted_p_values,
            "adjusted_exceedances": result.adjusted_exceedances,
            "adjusted_tail_probability": result.adjusted_tail_probabilities,
            "adjusted_mcse": result.adjusted_mcse,
            "adjusted_ci_lower": result.adjusted_ci_lower,
            "adjusted_ci_upper": result.adjusted_ci_upper,
            "adjusted_alpha_relation": result.adjusted_alpha_relation,
            "global_p_value": np.repeat(test.global_p_value, result.n_targets),
            "global_exceedances": np.repeat(
                result.global_exceedances,
                result.n_targets,
            ),
            "global_tail_probability": np.repeat(
                result.global_tail_probability,
                result.n_targets,
            ),
            "global_mcse": np.repeat(result.global_mcse, result.n_targets),
            "global_ci_lower": np.repeat(result.global_ci_lower, result.n_targets),
            "global_ci_upper": np.repeat(result.global_ci_upper, result.n_targets),
            "global_alpha_relation": np.repeat(
                result.global_alpha_relation,
                result.n_targets,
            ),
        }
    )
