"""Stabilized-volatility truncation selection for Gaussian FPCR wild bootstrap."""

from __future__ import annotations

import warnings

import numpy as np
import pandas as pd

from .fpca import transform_fpca
from .regression_inference import _validate_complete_finite, _validate_targets
from .stability import _fit_for_trajectories
from .types import (
    FPCAWildBootstrapTruncationScanResult,
    FPCAWildBootstrapTruncationSelectionResult,
    TrajectorySet,
)
from .wild_regression import (
    _draw_wild_multipliers,
    _fixed_score_fit,
    _heteroscedastic_projection_se,
    _validate_component_count,
    _validate_independent_curve_rows,
)


def _validate_candidate_components(
    values,
    *,
    residual_components: int,
    maximum: int,
) -> tuple[int, ...]:
    try:
        raw = tuple(values)
    except TypeError as exc:
        raise TypeError("candidate_components must be an iterable of integers") from exc
    if len(raw) < 2:
        raise ValueError("candidate_components must contain at least two values")

    parsed: list[int] = []
    for value in raw:
        parsed.append(
            _validate_component_count(
                value,
                name="each candidate component count",
                maximum=maximum,
            )
        )
    candidates = tuple(parsed)
    if tuple(sorted(set(candidates))) != candidates:
        raise ValueError(
            "candidate_components must be unique and strictly increasing"
        )
    if any(b != a + 1 for a, b in zip(candidates[:-1], candidates[1:])):
        raise ValueError(
            "candidate_components must be consecutive integers for stabilized-volatility selection"
        )
    if candidates[0] < residual_components:
        raise ValueError(
            "every candidate inference component count must be greater than or equal "
            "to residual_components"
        )
    return candidates


def scan_wild_bootstrap_fpca_truncations(
    trajectories: TrajectorySet,
    outcome: np.ndarray | pd.Series,
    *,
    candidate_components,
    targets: TrajectorySet | None = None,
    n_bootstrap: int = 1000,
    residual_components: int = 2,
    scaling: str = "none",
    multiplier: str = "normal",
    confidence_level: float = 0.95,
    independent_unit_column: str | None = None,
    random_state: int | None = 0,
) -> FPCAWildBootstrapTruncationScanResult:
    """Scan target-wise wild-bootstrap intervals over consecutive h values.

    One FPCA/MFPCA basis is fitted at the maximum candidate truncation. The same
    wild multiplier draw is then reused across every candidate h for a given
    bootstrap replicate so adjacent interval changes are not contaminated by
    independent Monte Carlo draws.

    Residual estimation and the bootstrap pseudo-truth use k=g equal to
    residual_components. Every candidate h must satisfy h greater than or equal
    to g.
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
    candidates = _validate_candidate_components(
        candidate_components,
        residual_components=residual_components,
        maximum=maximum,
    )
    if scaling not in {"none", "dimension_sd"}:
        raise ValueError("scaling must be 'none' or 'dimension_sd'")
    if multiplier not in {"normal", "mammen"}:
        raise ValueError("multiplier must be 'normal' or 'mammen'")
    if not 0 < confidence_level < 1:
        raise ValueError("confidence_level must lie in (0, 1)")

    _validate_independent_curve_rows(
        trajectories,
        independent_unit_column=independent_unit_column,
    )

    max_components = candidates[-1]
    reference_fpca = _fit_for_trajectories(
        trajectories,
        n_components=max_components,
        scaling=scaling,
    )
    scores = np.asarray(
        reference_fpca.scores[:, :max_components],
        dtype=float,
    )
    target_scores = np.asarray(
        transform_fpca(reference_fpca, target_set)[:, :max_components],
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
    pseudo_truth_projection = (
        target_scores[:, :residual_components] @ params_k[1:]
    )

    rng = np.random.default_rng(random_state)
    multiplier_draws = np.empty(
        (n_bootstrap, trajectories.n_curves),
        dtype=float,
    )
    pseudo_outcomes = np.empty_like(multiplier_draws)
    bootstrap_residuals_k = np.empty_like(multiplier_draws)
    for bootstrap_index in range(n_bootstrap):
        multiplier_draws[bootstrap_index] = _draw_wild_multipliers(
            rng,
            n=trajectories.n_curves,
            multiplier=multiplier,
        )
        pseudo_outcomes[bootstrap_index] = (
            fitted_k + residuals_k * multiplier_draws[bootstrap_index]
        )
        _, _, bootstrap_residuals_k[bootstrap_index] = _fixed_score_fit(
            scores,
            pseudo_outcomes[bootstrap_index],
            n_components=residual_components,
            context=(
                f"wild truncation scan replicate {bootstrap_index} "
                "residual-truncation"
            ),
        )

    n_candidates = len(candidates)
    n_targets = target_set.n_curves
    reference_projections = np.empty((n_candidates, n_targets), dtype=float)
    reference_se = np.empty_like(reference_projections)
    critical_values = np.empty_like(reference_projections)
    lower = np.empty_like(reference_projections)
    upper = np.empty_like(reference_projections)
    studentized_roots = np.empty(
        (n_candidates, n_bootstrap, n_targets),
        dtype=float,
    )

    for candidate_index, h in enumerate(candidates):
        target_h = target_scores[:, :h]
        score_h = scores[:, :h]
        params_h, _, _ = _fixed_score_fit(
            scores,
            y,
            n_components=h,
            context=f"reference inference-truncation h={h}",
        )
        projection_h = target_h @ params_h[1:]
        se_h = _heteroscedastic_projection_se(
            score_h,
            residuals_k,
            target_h,
            context=f"reference h={h}",
        )
        reference_projections[candidate_index] = projection_h
        reference_se[candidate_index] = se_h

        root_scale = max(
            1.0,
            float(np.max(np.abs(projection_h))) if projection_h.size else 1.0,
        )
        root_tolerance = 100.0 * np.finfo(float).eps * root_scale

        for bootstrap_index in range(n_bootstrap):
            params_star_h, _, _ = _fixed_score_fit(
                scores,
                pseudo_outcomes[bootstrap_index],
                n_components=h,
                context=(
                    f"wild truncation scan replicate {bootstrap_index} "
                    f"inference-truncation h={h}"
                ),
            )
            projection_star = target_h @ params_star_h[1:]
            se_star = _heteroscedastic_projection_se(
                score_h,
                bootstrap_residuals_k[bootstrap_index],
                target_h,
                context=(
                    f"wild truncation scan replicate {bootstrap_index} h={h}"
                ),
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
                    f"wild truncation scan replicate {bootstrap_index}, h={h} "
                    "has zero bootstrap standard error with non-zero projection "
                    f"root for target index/indices {bad[:8]}"
                )
            studentized_roots[
                candidate_index,
                bootstrap_index,
            ] = statistic

        critical_h = np.quantile(
            np.abs(studentized_roots[candidate_index]),
            confidence_level,
            axis=0,
            method="higher",
        )
        critical_values[candidate_index] = critical_h
        lower[candidate_index] = projection_h - critical_h * se_h
        upper[candidate_index] = projection_h + critical_h * se_h

    centers = (lower + upper) / 2.0
    widths = upper - lower

    return FPCAWildBootstrapTruncationScanResult(
        reference_fpca=reference_fpca,
        target_curve_ids=target_set.curve_ids,
        candidate_components=candidates,
        residual_components=residual_components,
        pseudo_truth_projection=np.asarray(
            pseudo_truth_projection,
            dtype=float,
        ),
        reference_projections=reference_projections,
        reference_se=reference_se,
        critical_values=critical_values,
        lower=lower,
        upper=upper,
        centers=centers,
        widths=widths,
        studentized_roots=studentized_roots,
        confidence_level=float(confidence_level),
        scaling=scaling,
        multiplier=multiplier,
        target_source=target_source,
        independent_unit_column=independent_unit_column,
        random_state=random_state,
        provenance={
            **dict(trajectories.provenance),
            "fpca_wild_bootstrap_truncation_scan": {
                "method": "shared_multiplier_wild_bootstrap_truncation_scan",
                "family": "gaussian",
                "residual_components_k": residual_components,
                "pseudo_truth_components_g": residual_components,
                "candidate_inference_components_h": list(candidates),
                "g_equals_k": True,
                "all_h_at_least_g": True,
                "shared_multiplier_draws_across_h": True,
                "n_bootstrap": n_bootstrap,
                "confidence_level": float(confidence_level),
                "scaling": scaling,
                "multiplier": multiplier,
                "interval": "symmetrized_studentized_targetwise",
                "functional_regressors_fixed": True,
                "fpca_basis_refit_in_bootstrap": False,
                "target_curves_fixed": True,
                "independence_assumption": "independent_curve_rows",
                "independent_unit_column": independent_unit_column,
                "simultaneous_across_targets": False,
                "random_state": random_state,
            },
        },
    )


def fpca_wild_bootstrap_truncation_scan_frame(
    result: FPCAWildBootstrapTruncationScanResult,
) -> pd.DataFrame:
    """Return one row per candidate h and fixed target trajectory."""

    rows: list[dict[str, object]] = []
    for i, h in enumerate(result.candidate_components):
        for j, curve_id in enumerate(result.target_curve_ids):
            rows.append(
                {
                    "curve_id": curve_id,
                    "inference_components": h,
                    "reference_projection": result.reference_projections[i, j],
                    "heteroscedastic_se": result.reference_se[i, j],
                    "critical_value": result.critical_values[i, j],
                    "lower": result.lower[i, j],
                    "upper": result.upper[i, j],
                    "center": result.centers[i, j],
                    "width": result.widths[i, j],
                }
            )
    return pd.DataFrame(rows)


def select_fpca_wild_bootstrap_truncation(
    scan: FPCAWildBootstrapTruncationScanResult,
    *,
    width_threshold: float,
    center_threshold: float,
    stability_run: int,
    on_failure: str = "error",
) -> FPCAWildBootstrapTruncationSelectionResult:
    """Select target-specific h values by the stabilized-volatility rule.

    For consecutive candidate h values, a transition at h is width-stable when
    abs(width[h+1] - width[h]) <= width_threshold and center-stable under
    the analogous center threshold. A stable transition satisfies both.

    stability_run is the paper's integer r. Selection therefore requires
    r+1 consecutive stable transitions beginning at h and chooses the earliest
    such h for each target.
    """

    if not isinstance(scan, FPCAWildBootstrapTruncationScanResult):
        raise TypeError(
            "scan must be an FPCAWildBootstrapTruncationScanResult"
        )
    for value, name in [
        (width_threshold, "width_threshold"),
        (center_threshold, "center_threshold"),
    ]:
        if not np.isscalar(value) or isinstance(value, (bool, np.bool_)):
            raise TypeError(f"{name} must be a finite positive scalar")
        value_float = float(value)
        if not np.isfinite(value_float) or value_float <= 0:
            raise ValueError(f"{name} must be finite and strictly positive")

    width_threshold = float(width_threshold)
    center_threshold = float(center_threshold)

    if isinstance(stability_run, bool) or not isinstance(
        stability_run,
        (int, np.integer),
    ):
        raise TypeError("stability_run must be an integer")
    stability_run = int(stability_run)
    if stability_run < 0:
        raise ValueError("stability_run must be non-negative")
    required_transitions = stability_run + 1
    if required_transitions > scan.n_candidates - 1:
        raise ValueError(
            "stability_run requires more consecutive stable transitions than "
            "the candidate grid can provide"
        )
    if on_failure not in {"error", "warn", "ignore"}:
        raise ValueError("on_failure must be 'error', 'warn', or 'ignore'")

    width_changes = np.abs(np.diff(scan.widths, axis=0))
    center_changes = np.abs(np.diff(scan.centers, axis=0))
    stable_width = width_changes <= width_threshold
    stable_center = center_changes <= center_threshold
    stable_both = stable_width & stable_center

    selected_indices = np.full(scan.n_targets, -1, dtype=int)
    selected_components = np.full(scan.n_targets, np.nan, dtype=float)
    selected_centers = np.full(scan.n_targets, np.nan, dtype=float)
    selected_widths = np.full(scan.n_targets, np.nan, dtype=float)
    selected_lower = np.full(scan.n_targets, np.nan, dtype=float)
    selected_upper = np.full(scan.n_targets, np.nan, dtype=float)

    last_start = stable_both.shape[0] - required_transitions
    for target_index in range(scan.n_targets):
        for start in range(last_start + 1):
            stop = start + required_transitions
            if np.all(stable_both[start:stop, target_index]):
                selected_indices[target_index] = start
                selected_components[target_index] = float(
                    scan.candidate_components[start]
                )
                selected_centers[target_index] = scan.centers[
                    start,
                    target_index,
                ]
                selected_widths[target_index] = scan.widths[
                    start,
                    target_index,
                ]
                selected_lower[target_index] = scan.lower[
                    start,
                    target_index,
                ]
                selected_upper[target_index] = scan.upper[
                    start,
                    target_index,
                ]
                break

    failed = np.flatnonzero(selected_indices < 0)
    if failed.size:
        failed_ids = [scan.target_curve_ids[i] for i in failed]
        message = (
            "stabilized-volatility selection found no qualifying run for "
            f"{failed.size} target(s): {failed_ids[:8]}. Expand the pre-specified "
            "candidate grid or reconsider the pre-specified thresholds; the "
            "package will not silently choose the largest h."
        )
        if on_failure == "error":
            raise RuntimeError(message)
        if on_failure == "warn":
            warnings.warn(message, RuntimeWarning, stacklevel=2)

    return FPCAWildBootstrapTruncationSelectionResult(
        scan=scan,
        width_changes=width_changes,
        center_changes=center_changes,
        stable_width=stable_width,
        stable_center=stable_center,
        stable_both=stable_both,
        selected_candidate_indices=selected_indices,
        selected_components=selected_components,
        selected_centers=selected_centers,
        selected_widths=selected_widths,
        selected_lower=selected_lower,
        selected_upper=selected_upper,
        width_threshold=width_threshold,
        center_threshold=center_threshold,
        stability_run=stability_run,
        on_failure=on_failure,
        provenance={
            **dict(scan.provenance),
            "fpca_wild_bootstrap_truncation_selection": {
                "method": "stabilized_volatility",
                "width_threshold_rho_w": width_threshold,
                "center_threshold_rho_c": center_threshold,
                "stability_run_r": stability_run,
                "required_consecutive_stable_transitions": required_transitions,
                "selection": (
                    "earliest_candidate_h_starting_qualifying_stable_run"
                ),
                "threshold_units": "scalar_outcome_units",
                "thresholds_package_defaulted": False,
                "on_failure": on_failure,
                "silent_largest_h_fallback": False,
                "target_specific_selection": True,
            },
        },
    )


def fpca_wild_bootstrap_truncation_selection_frame(
    result: FPCAWildBootstrapTruncationSelectionResult,
) -> pd.DataFrame:
    """Return one row per target with stabilized-volatility selection."""

    if not isinstance(result, FPCAWildBootstrapTruncationSelectionResult):
        raise TypeError(
            "result must be an FPCAWildBootstrapTruncationSelectionResult"
        )
    selected = result.selected_components
    return pd.DataFrame(
        {
            "curve_id": result.scan.target_curve_ids,
            "selected_inference_components": pd.array(
                [
                    pd.NA if np.isnan(value) else int(value)
                    for value in selected
                ],
                dtype="Int64",
            ),
            "selected_center": result.selected_centers,
            "selected_width": result.selected_widths,
            "selected_lower": result.selected_lower,
            "selected_upper": result.selected_upper,
        }
    )
