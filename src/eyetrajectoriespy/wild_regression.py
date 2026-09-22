"""Heteroscedastic wild-bootstrap inference for Gaussian FPCR projections."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .fpca import transform_fpca
from .regression_inference import _validate_complete_finite, _validate_targets
from .stability import _fit_for_trajectories
from .types import FPCAWildBootstrapProjectionResult, TrajectorySet


def _validate_component_count(
    value: int,
    *,
    name: str,
    maximum: int,
) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, np.integer)):
        raise TypeError(f"{name} must be an integer")
    value = int(value)
    if value < 1 or value > maximum:
        raise ValueError(f"{name} must lie in [1, {maximum}]")
    return value


def _fixed_score_fit(
    scores: np.ndarray,
    outcome: np.ndarray,
    *,
    n_components: int,
    context: str,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    design = np.column_stack(
        [
            np.ones(scores.shape[0], dtype=float),
            scores[:, :n_components],
        ]
    )
    required_rank = n_components + 1
    rank = int(np.linalg.matrix_rank(design))
    if rank < required_rank:
        raise RuntimeError(
            f"{context} score-regression design is rank deficient "
            f"(rank={rank}, required={required_rank})"
        )
    parameters, *_ = np.linalg.lstsq(design, outcome, rcond=None)
    fitted = design @ parameters
    residuals = outcome - fitted
    if not (
        np.all(np.isfinite(parameters))
        and np.all(np.isfinite(fitted))
        and np.all(np.isfinite(residuals))
    ):
        raise RuntimeError(f"{context} score regression produced non-finite values")
    return parameters, fitted, residuals


def _heteroscedastic_projection_se(
    scores: np.ndarray,
    residuals: np.ndarray,
    target_scores: np.ndarray,
    *,
    context: str,
) -> np.ndarray:
    """Score-space form of the FPCR heteroscedastic projection scaling."""

    n, h = scores.shape
    if residuals.shape != (n,):
        raise ValueError("residual vector is incompatible with score rows")
    if target_scores.ndim != 2 or target_scores.shape[1] != h:
        raise ValueError("target scores are incompatible with inference scores")
    if n < 2:
        raise ValueError("at least two independent curves are required")

    gamma = scores.T @ scores / float(n)
    rank = int(np.linalg.matrix_rank(gamma))
    if rank < h:
        raise RuntimeError(
            f"{context} score covariance is rank deficient "
            f"(rank={rank}, required={h})"
        )
    gamma_inv = np.linalg.inv(gamma)

    products = scores * residuals[:, None]
    centered = products - products.mean(axis=0, keepdims=True)
    lambda_hat = centered.T @ centered / float(n - 1)

    directions = target_scores @ gamma_inv.T
    scale = np.einsum("ti,ij,tj->t", directions, lambda_hat, directions)
    numerical_scale = max(
        1.0,
        float(np.max(np.abs(scale))) if scale.size else 1.0,
    )
    tolerance = 100.0 * np.finfo(float).eps * numerical_scale
    if np.any(scale < -tolerance):
        raise RuntimeError(
            f"{context} heteroscedastic projection variance is materially negative"
        )
    scale = np.maximum(scale, 0.0)
    se = np.sqrt(scale / float(n))
    if not np.all(np.isfinite(se)):
        raise RuntimeError(
            f"{context} heteroscedastic projection standard errors are non-finite"
        )
    return se


def _draw_wild_multipliers(
    rng: np.random.Generator,
    *,
    n: int,
    multiplier: str,
) -> np.ndarray:
    if multiplier == "normal":
        return rng.normal(0.0, 1.0, size=n)
    if multiplier == "mammen":
        sqrt5 = np.sqrt(5.0)
        negative = -(sqrt5 - 1.0) / 2.0
        positive = (sqrt5 + 1.0) / 2.0
        p_negative = (sqrt5 + 1.0) / (2.0 * sqrt5)
        use_negative = rng.random(n) < p_negative
        return np.where(use_negative, negative, positive)
    raise ValueError("multiplier must be 'normal' or 'mammen'")


def wild_bootstrap_fpca_projection(
    trajectories: TrajectorySet,
    outcome: np.ndarray | pd.Series,
    *,
    targets: TrajectorySet | None = None,
    n_bootstrap: int = 1000,
    residual_components: int = 2,
    inference_components: int = 3,
    scaling: str = "none",
    multiplier: str = "normal",
    confidence_level: float = 0.95,
    independent_unit_column: str | None = None,
    random_state: int | None = 0,
) -> FPCAWildBootstrapProjectionResult:
    """Studentized wild-bootstrap intervals for centered Gaussian FPCR projections.

    The functional regressors and their FPCA basis stay fixed. Residuals are
    estimated with residual_components=k. The bootstrap pseudo-truth uses the
    same truncation g=k. Inference uses inference_components=h and requires
    h greater than or equal to k.

    Each pseudo-response is the k-component fitted response plus a mean-zero,
    variance-one wild multiplier times the k-component residual. Bootstrap
    projection roots are studentized with a heteroscedastic scale recomputed
    from the pseudo-fit residuals.

    The estimand is the centered functional projection for each fixed target,
    relative to the training functional mean. It is not a future-outcome
    prediction interval and is not a clustered or repeated-participant bootstrap.
    """

    _validate_complete_finite(trajectories, name="training trajectories")
    y = np.asarray(outcome, dtype=float)
    if y.shape != (trajectories.n_curves,):
        raise ValueError(
            "outcome must contain exactly one value per training trajectory"
        )
    if not np.all(np.isfinite(y)):
        raise ValueError("outcome must contain only finite values")

    if targets is None:
        target_set = trajectories
        target_source = "training"
    else:
        target_set = targets
        target_source = "external"
        _validate_targets(trajectories, target_set)

    if isinstance(n_bootstrap, bool) or not isinstance(
        n_bootstrap,
        (int, np.integer),
    ):
        raise TypeError("n_bootstrap must be an integer")
    n_bootstrap = int(n_bootstrap)
    if n_bootstrap < 20:
        raise ValueError("n_bootstrap must be at least 20")

    maximum = min(
        trajectories.n_curves - 1,
        trajectories.n_time * trajectories.n_dimensions,
    )
    residual_components = _validate_component_count(
        residual_components,
        name="residual_components",
        maximum=maximum,
    )
    inference_components = _validate_component_count(
        inference_components,
        name="inference_components",
        maximum=maximum,
    )
    if inference_components < residual_components:
        raise ValueError(
            "inference_components must be greater than or equal to "
            "residual_components"
        )
    if scaling not in {"none", "dimension_sd"}:
        raise ValueError("scaling must be 'none' or 'dimension_sd'")
    if multiplier not in {"normal", "mammen"}:
        raise ValueError("multiplier must be 'normal' or 'mammen'")
    if not 0 < confidence_level < 1:
        raise ValueError("confidence_level must lie in (0, 1)")

    if independent_unit_column is not None:
        if independent_unit_column not in trajectories.metadata.columns:
            raise ValueError(
                f"metadata does not contain independent-unit column "
                f"{independent_unit_column!r}"
            )
        unit = trajectories.metadata[independent_unit_column]
        if unit.isna().any():
            raise ValueError("independent_unit_column contains missing values")
        if unit.astype(str).duplicated().any():
            raise ValueError(
                "wild bootstrap currently requires independent curve rows; "
                "repeated/clustered unit IDs are not supported. Aggregate to "
                "independent-unit trajectories or use the participant-level "
                "paired FPCR bootstrap instead."
            )

    reference_fpca = _fit_for_trajectories(
        trajectories,
        n_components=inference_components,
        scaling=scaling,
    )
    scores = np.asarray(
        reference_fpca.scores[:, :inference_components],
        dtype=float,
    )
    target_scores = np.asarray(
        transform_fpca(reference_fpca, target_set)[:, :inference_components],
        dtype=float,
    )
    if not np.all(np.isfinite(scores)) or not np.all(np.isfinite(target_scores)):
        raise RuntimeError("FPCA score geometry contains non-finite values")

    params_k, fitted_k, residuals_k = _fixed_score_fit(
        scores,
        y,
        n_components=residual_components,
        context="reference residual-truncation",
    )
    params_h, _, _ = _fixed_score_fit(
        scores,
        y,
        n_components=inference_components,
        context="reference inference-truncation",
    )

    target_k = target_scores[:, :residual_components]
    target_h = target_scores[:, :inference_components]
    pseudo_truth_projection = target_k @ params_k[1:]
    reference_projection = target_h @ params_h[1:]
    reference_se = _heteroscedastic_projection_se(
        scores[:, :inference_components],
        residuals_k,
        target_h,
        context="reference",
    )

    rng = np.random.default_rng(random_state)
    bootstrap_projections = np.empty(
        (n_bootstrap, target_set.n_curves),
        dtype=float,
    )
    bootstrap_se = np.empty_like(bootstrap_projections)
    studentized_roots = np.empty_like(bootstrap_projections)

    root_scale = max(
        1.0,
        float(np.max(np.abs(reference_projection)))
        if reference_projection.size
        else 1.0,
    )
    root_tolerance = 100.0 * np.finfo(float).eps * root_scale

    for bootstrap_index in range(n_bootstrap):
        wild = _draw_wild_multipliers(
            rng,
            n=trajectories.n_curves,
            multiplier=multiplier,
        )
        pseudo_outcome = fitted_k + residuals_k * wild

        params_star_h, _, _ = _fixed_score_fit(
            scores,
            pseudo_outcome,
            n_components=inference_components,
            context=f"wild bootstrap replicate {bootstrap_index} inference-truncation",
        )
        _, _, residuals_star_k = _fixed_score_fit(
            scores,
            pseudo_outcome,
            n_components=residual_components,
            context=f"wild bootstrap replicate {bootstrap_index} residual-truncation",
        )

        projection_star = target_h @ params_star_h[1:]
        se_star = _heteroscedastic_projection_se(
            scores[:, :inference_components],
            residuals_star_k,
            target_h,
            context=f"wild bootstrap replicate {bootstrap_index}",
        )
        root = projection_star - pseudo_truth_projection

        statistic = np.zeros_like(root)
        se_scale = max(
            1.0,
            float(np.max(se_star)) if se_star.size else 1.0,
        )
        positive = se_star > np.finfo(float).eps * se_scale
        np.divide(root, se_star, out=statistic, where=positive)
        degenerate = (~positive) & (np.abs(root) > root_tolerance)
        if np.any(degenerate):
            bad = np.flatnonzero(degenerate).tolist()
            raise RuntimeError(
                f"wild bootstrap replicate {bootstrap_index} has zero "
                "bootstrap standard error with non-zero projection root for "
                f"target index/indices {bad[:8]}"
            )

        bootstrap_projections[bootstrap_index] = projection_star
        bootstrap_se[bootstrap_index] = se_star
        studentized_roots[bootstrap_index] = statistic

    critical_values = np.quantile(
        np.abs(studentized_roots),
        confidence_level,
        axis=0,
        method="higher",
    )
    lower = reference_projection - critical_values * reference_se
    upper = reference_projection + critical_values * reference_se

    sqrt5 = np.sqrt(5.0)
    multiplier_contract = (
        {"mean": 0.0, "variance": 1.0}
        if multiplier == "normal"
        else {
            "mean": 0.0,
            "variance": 1.0,
            "negative_support": -(sqrt5 - 1.0) / 2.0,
            "positive_support": (sqrt5 + 1.0) / 2.0,
            "negative_probability": (sqrt5 + 1.0) / (2.0 * sqrt5),
        }
    )

    return FPCAWildBootstrapProjectionResult(
        reference_fpca=reference_fpca,
        target_curve_ids=target_set.curve_ids,
        reference_projection=np.asarray(reference_projection, dtype=float),
        pseudo_truth_projection=np.asarray(
            pseudo_truth_projection,
            dtype=float,
        ),
        reference_se=np.asarray(reference_se, dtype=float),
        bootstrap_projections=bootstrap_projections,
        bootstrap_se=bootstrap_se,
        studentized_roots=studentized_roots,
        critical_values=np.asarray(critical_values, dtype=float),
        lower=np.asarray(lower, dtype=float),
        upper=np.asarray(upper, dtype=float),
        residuals=np.asarray(residuals_k, dtype=float),
        confidence_level=float(confidence_level),
        residual_components=residual_components,
        inference_components=inference_components,
        scaling=scaling,
        multiplier=multiplier,
        target_source=target_source,
        independent_unit_column=independent_unit_column,
        random_state=random_state,
        provenance={
            **dict(trajectories.provenance),
            "fpca_wild_bootstrap_projection": {
                "method": (
                    "fixed_regressor_studentized_multiplier_wild_bootstrap"
                ),
                "family": "gaussian",
                "estimand": (
                    "centered_projection_relative_to_training_functional_mean"
                ),
                "n_bootstrap": n_bootstrap,
                "residual_components_k": residual_components,
                "pseudo_truth_components_g": residual_components,
                "inference_components_h": inference_components,
                "g_equals_k": True,
                "h_at_least_g": True,
                "scaling": scaling,
                "multiplier": multiplier,
                "multiplier_contract": multiplier_contract,
                "studentization": (
                    "bootstrap_level_heteroscedastic_score_covariance"
                ),
                "interval": "symmetrized_studentized_targetwise",
                "confidence_level": float(confidence_level),
                "fpca_basis_refit_in_bootstrap": False,
                "functional_regressors_fixed": True,
                "target_curves_fixed": True,
                "independence_assumption": "independent_curve_rows",
                "independent_unit_column": independent_unit_column,
                "clustered_wild_bootstrap": False,
                "future_outcome_prediction_interval": False,
                "simultaneous_across_targets": False,
                "component_selection_uncertainty_included": False,
                "random_state": random_state,
            },
        },
    )


def fpca_wild_bootstrap_projection_frame(
    result: FPCAWildBootstrapProjectionResult,
) -> pd.DataFrame:
    """Return fixed-target centered-projection wild-bootstrap summaries."""

    return pd.DataFrame(
        {
            "curve_id": result.target_curve_ids,
            "reference_projection": result.reference_projection,
            "pseudo_truth_projection": result.pseudo_truth_projection,
            "heteroscedastic_se": result.reference_se,
            "critical_value": result.critical_values,
            "lower": result.lower,
            "upper": result.upper,
        }
    )
