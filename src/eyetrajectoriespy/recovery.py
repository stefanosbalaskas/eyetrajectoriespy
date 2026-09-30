"""Known-truth recovery metrics for functional estimators.

Recovery is evaluated only after an estimator has been fitted. The estimator
does not receive latent truth through this module.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Literal

import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment

from ._functional_simulation import FunctionalSimulationTruth
from .fpca import functional_trapezoid_weights
from .types import (
    FPCAResult,
    FunctionalMixedEffectsResult,
    RegistrationResult,
    SparseFPCAResult,
    SparseMFPCAResult,
)


RecoveryDirection = Literal["higher_is_better", "lower_is_better"]


@dataclass(frozen=True)
class FunctionalRecoveryMetric:
    """Semantic definition of one recovery quantity."""

    name: str
    quantity: str
    direction: RecoveryDirection
    units: str
    scope: str
    description: str

    def __post_init__(self) -> None:
        for attribute in ("name", "quantity", "units", "scope", "description"):
            value = str(getattr(self, attribute)).strip()
            if not value:
                raise ValueError(f"{attribute} must be non-empty")
            object.__setattr__(self, attribute, value)
        if self.direction not in {"higher_is_better", "lower_is_better"}:
            raise ValueError(
                "direction must be 'higher_is_better' or 'lower_is_better'"
            )


@dataclass(frozen=True)
class FunctionalRecoveryValue:
    """One scalar recovery value with optional component/source labels."""

    metric: FunctionalRecoveryMetric
    value: float
    component: int | None = None
    source: str | None = None

    def __post_init__(self) -> None:
        scalar = float(self.value)
        if not np.isfinite(scalar):
            raise ValueError("recovery values must be finite")
        if self.component is not None and int(self.component) < 0:
            raise ValueError("component must be non-negative")
        source = None if self.source is None else str(self.source).strip()
        if self.source is not None and not source:
            raise ValueError("source must be non-empty when supplied")
        object.__setattr__(self, "value", scalar)
        object.__setattr__(
            self,
            "component",
            None if self.component is None else int(self.component),
        )
        object.__setattr__(self, "source", source)


@dataclass(frozen=True)
class FunctionalRecoveryAssessment:
    """Structured recovery evidence for one fitted replicate."""

    values: tuple[FunctionalRecoveryValue, ...]
    provenance: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.values:
            raise ValueError("recovery assessment must contain at least one value")
        keys = [
            (value.metric.name, value.component, value.source)
            for value in self.values
        ]
        if len(set(keys)) != len(keys):
            raise ValueError("recovery assessment contains duplicate metric labels")
        object.__setattr__(
            self, "provenance", MappingProxyType(dict(self.provenance))
        )

    def as_mapping(self) -> Mapping[str, float]:
        """Flatten values into deterministic scalar keys."""

        return MappingProxyType(
            {
                functional_recovery_value_key(value): value.value
                for value in self.values
            }
        )


def _metric(
    name: str,
    quantity: str,
    direction: RecoveryDirection,
    units: str,
    scope: str,
    description: str,
) -> FunctionalRecoveryMetric:
    return FunctionalRecoveryMetric(
        name=name,
        quantity=quantity,
        direction=direction,
        units=units,
        scope=scope,
        description=description,
    )


_METRICS = {
    metric.name: metric
    for metric in (
        _metric(
            "mean_ise",
            "population mean function",
            "lower_is_better",
            "squared signal × time",
            "population",
            "Integrated squared error of the fitted mean function.",
        ),
        _metric(
            "covariance_ise",
            "population covariance operator",
            "lower_is_better",
            "squared covariance × time²",
            "population",
            "Quadrature-weighted integrated squared covariance error.",
        ),
        _metric(
            "covariance_block_ise",
            "planar covariance block",
            "lower_is_better",
            "squared covariance × time²",
            "covariance_block",
            "Quadrature-weighted integrated squared error of one named planar covariance block.",
        ),
        _metric(
            "score_subspace_procrustes_rmse",
            "latent score coordinates within a tied eigenspace",
            "lower_is_better",
            "score units",
            "tied_eigenspace",
            "Root-mean-square score error after optimal orthogonal Procrustes alignment within an identified tied truth eigenspace.",
        ),
        _metric(
            "eigenvalue_relative_error",
            "functional eigenvalue",
            "lower_is_better",
            "relative",
            "component",
            "Absolute eigenvalue error divided by the matched true eigenvalue.",
        ),
        _metric(
            "component_absolute_similarity",
            "functional eigenfunction",
            "higher_is_better",
            "absolute weighted inner product",
            "component",
            "Sign-invariant similarity after optimal component matching.",
        ),
        _metric(
            "subspace_principal_cosine",
            "retained functional subspace",
            "higher_is_better",
            "cosine",
            "subspace",
            "Principal cosine between retained fitted and true subspaces.",
        ),
        _metric(
            "subspace_principal_angle_degrees",
            "retained functional subspace",
            "lower_is_better",
            "degrees",
            "subspace",
            "Principal angle between retained fitted and true subspaces.",
        ),
        _metric(
            "score_correlation",
            "latent functional score",
            "higher_is_better",
            "correlation",
            "component",
            "Correlation after matched-component sign alignment.",
        ),
        _metric(
            "score_rmse",
            "latent functional score",
            "lower_is_better",
            "score units",
            "component",
            "Root-mean-square score error after sign alignment.",
        ),
        _metric(
            "reconstruction_ise",
            "latent trajectory reconstruction",
            "lower_is_better",
            "squared signal × time",
            "curve",
            "Mean curve-level integrated squared reconstruction error.",
        ),
        _metric(
            "score_failure_rate",
            "conditional score solve",
            "lower_is_better",
            "proportion",
            "numerical",
            "Proportion of curves whose score system did not return status 'ok'.",
        ),
        _metric(
            "score_condition_number_median",
            "conditional score covariance system",
            "lower_is_better",
            "condition number",
            "numerical",
            "Median finite score-system condition number across curves.",
        ),
        _metric(
            "score_condition_number_q95",
            "conditional score covariance system",
            "lower_is_better",
            "condition number",
            "numerical",
            "95th percentile finite score-system condition number across curves.",
        ),
        _metric(
            "score_condition_number_max",
            "conditional score covariance system",
            "lower_is_better",
            "condition number",
            "numerical",
            "Maximum finite score-system condition number across curves.",
        ),
        _metric(
            "psd_repair_applied",
            "fitted covariance PSD repair",
            "lower_is_better",
            "indicator",
            "numerical",
            "Indicator that covariance projection was actually applied.",
        ),
        _metric(
            "psd_relative_operator_correction",
            "fitted covariance PSD repair",
            "lower_is_better",
            "relative Frobenius norm",
            "numerical",
            "Relative weighted-operator correction introduced by PSD repair.",
        ),
        _metric(
            "noise_variance_absolute_error",
            "measurement-noise variance",
            "lower_is_better",
            "variance units",
            "measurement_error",
            "Absolute fitted-versus-generating measurement-noise variance error.",
        ),
        _metric(
            "noise_variance_relative_error",
            "measurement-noise variance",
            "lower_is_better",
            "relative",
            "measurement_error",
            "Absolute measurement-noise variance error divided by true variance.",
        ),
        _metric(
            "coefficient_function_ise",
            "functional mixed-effects coefficient function",
            "lower_is_better",
            "squared signal × time",
            "mixed_effects",
            "Integrated squared error of a matched coefficient function.",
        ),
        _metric(
            "source_variance_function_ise",
            "functional random-effect variance function",
            "lower_is_better",
            "variance² × time",
            "mixed_effects",
            "Integrated squared error of participant/trial variance functions.",
        ),
        _metric(
            "source_integrated_variance_absolute_error",
            "integrated functional random-effect variance",
            "lower_is_better",
            "signal variance × time",
            "mixed_effects",
            "Absolute integrated participant/trial variance error.",
        ),
        _metric(
            "source_integrated_variance_relative_error",
            "integrated functional random-effect variance",
            "lower_is_better",
            "relative",
            "mixed_effects",
            "Relative integrated participant/trial variance error.",
        ),
        _metric(
            "phase_warp_ise",
            "registration inverse phase warp",
            "lower_is_better",
            "time² × time",
            "registration",
            "Mean integrated squared error of recovered inverse phase warps.",
        ),
        _metric(
            "phase_warp_max_absolute_error",
            "registration inverse phase warp",
            "lower_is_better",
            "time",
            "registration",
            "Maximum absolute recovered inverse-warp error across curves/time.",
        ),
        _metric(
            "source_variance_absolute_error",
            "hierarchical score-source variance",
            "lower_is_better",
            "score variance",
            "hierarchy",
            "Absolute realized-versus-declared score-source variance error.",
        ),
        _metric(
            "source_variance_relative_error",
            "hierarchical score-source variance",
            "lower_is_better",
            "relative",
            "hierarchy",
            "Absolute score-source variance error divided by declared variance.",
        ),
    )
}
METRIC_CATALOG: Mapping[str, FunctionalRecoveryMetric] = MappingProxyType(
    _METRICS
)


def functional_recovery_metric_catalog() -> tuple[FunctionalRecoveryMetric, ...]:
    """Return the stable built-in recovery-metric definitions."""

    return tuple(METRIC_CATALOG.values())


def functional_recovery_metric_catalog_frame() -> pd.DataFrame:
    """Return the recovery catalog as an auditable table."""

    return pd.DataFrame(
        [
            {
                "metric": metric.name,
                "quantity": metric.quantity,
                "direction": metric.direction,
                "units": metric.units,
                "scope": metric.scope,
                "description": metric.description,
            }
            for metric in functional_recovery_metric_catalog()
        ]
    )


def functional_recovery_value_key(value: FunctionalRecoveryValue) -> str:
    """Return a deterministic flat key for compatibility tables/JSON."""

    key = value.metric.name
    if value.source is not None:
        key += f".source_{value.source}"
    if value.component is not None:
        key += f".component_{value.component + 1}"
    return key


def functional_recovery_assessment_frame(
    assessment: FunctionalRecoveryAssessment,
) -> pd.DataFrame:
    """Return one row per semantic recovery value."""

    if not isinstance(assessment, FunctionalRecoveryAssessment):
        raise TypeError("assessment must be a FunctionalRecoveryAssessment")
    return pd.DataFrame(
        [
            {
                "metric": value.metric.name,
                "value": value.value,
                "component": (
                    None if value.component is None else value.component + 1
                ),
                "source": value.source,
                "quantity": value.metric.quantity,
                "direction": value.metric.direction,
                "units": value.metric.units,
                "scope": value.metric.scope,
                "description": value.metric.description,
            }
            for value in assessment.values
        ]
    )


def _value(
    name: str,
    value: float,
    *,
    component: int | None = None,
    source: str | None = None,
) -> FunctionalRecoveryValue:
    return FunctionalRecoveryValue(
        metric=METRIC_CATALOG[name],
        value=float(value),
        component=component,
        source=source,
    )


def _require_truth_grid(
    grid: np.ndarray,
    truth: FunctionalSimulationTruth,
) -> None:
    candidate = np.asarray(grid, dtype=float)
    reference = np.asarray(truth.truth_grid, dtype=float)
    if candidate.shape != reference.shape or not np.array_equal(
        candidate, reference
    ):
        raise ValueError(
            "recovery evaluation requires the fitted grid to equal "
            "truth.truth_grid exactly; truth is not silently interpolated"
        )


def _functional_weights(
    time_weights: np.ndarray,
    n_dimensions: int,
) -> np.ndarray:
    weights = np.asarray(time_weights, dtype=float)
    if (
        weights.ndim != 1
        or np.any(~np.isfinite(weights))
        or np.any(weights <= 0)
    ):
        raise ValueError(
            "functional quadrature weights must be finite and positive"
        )
    return np.repeat(weights, n_dimensions)


def _normalized_rows(
    functions: np.ndarray,
    flat_weights: np.ndarray,
) -> np.ndarray:
    functions = np.asarray(functions, dtype=float)
    if functions.ndim != 3:
        raise ValueError(
            "functional components must have shape "
            "(n_components, n_time, n_dimensions)"
        )
    flat = functions.reshape(functions.shape[0], -1)
    if flat.shape[1] != flat_weights.size:
        raise ValueError(
            "component geometry does not match quadrature weights"
        )
    norms = np.sqrt(np.sum(flat**2 * flat_weights[None, :], axis=1))
    if np.any(~np.isfinite(norms)) or np.any(norms <= 0):
        raise ValueError("functional components contain an invalid norm")
    return flat / norms[:, None]


@dataclass(frozen=True)
class _Alignment:
    truth_indices: np.ndarray
    signs: np.ndarray
    component_similarity: np.ndarray
    principal_cosines: np.ndarray


def _align_components(
    estimated: np.ndarray,
    truth: np.ndarray,
    flat_weights: np.ndarray,
) -> _Alignment:
    estimated_normalized = _normalized_rows(estimated, flat_weights)
    truth_normalized = _normalized_rows(truth, flat_weights)
    if estimated_normalized.shape[0] > truth_normalized.shape[0]:
        raise ValueError(
            "truth contains fewer components than the fitted result"
        )
    signed_similarity = (
        estimated_normalized * flat_weights[None, :]
    ) @ truth_normalized.T
    similarity = np.abs(signed_similarity)
    rows, truth_indices = linear_sum_assignment(-similarity)
    order = np.argsort(rows)
    truth_indices = truth_indices[order]
    matched_signed = signed_similarity[
        np.arange(estimated_normalized.shape[0]), truth_indices
    ]
    signs = np.where(matched_signed >= 0, 1.0, -1.0)
    matched_similarity = np.abs(matched_signed)

    sqrt_weights = np.sqrt(flat_weights)
    estimated_weighted = estimated_normalized.T * sqrt_weights[:, None]
    truth_weighted = (
        truth_normalized[truth_indices].T * sqrt_weights[:, None]
    )
    q_estimated, _ = np.linalg.qr(estimated_weighted)
    q_truth, _ = np.linalg.qr(truth_weighted)
    principal_cosines = np.clip(
        np.linalg.svd(q_estimated.T @ q_truth, compute_uv=False),
        0.0,
        1.0,
    )
    return _Alignment(
        truth_indices=truth_indices.astype(int),
        signs=signs,
        component_similarity=matched_similarity,
        principal_cosines=principal_cosines,
    )


def _covariance_from_modes(
    eigenvalues: np.ndarray,
    components: np.ndarray,
) -> np.ndarray:
    flat = np.asarray(components, dtype=float).reshape(
        len(eigenvalues), -1
    )
    covariance = np.zeros((flat.shape[1], flat.shape[1]), dtype=float)
    for eigenvalue, component in zip(
        np.asarray(eigenvalues, dtype=float), flat, strict=True
    ):
        covariance += float(eigenvalue) * np.outer(component, component)
    return covariance


def _ise(
    difference: np.ndarray,
    flat_weights: np.ndarray,
) -> float:
    flat = np.asarray(difference, dtype=float).reshape(-1)
    if flat.shape != flat_weights.shape:
        raise ValueError(
            "functional difference does not match quadrature weights"
        )
    return float(np.sum(flat**2 * flat_weights))


def _planar_truth_covariance_blocks(
    truth: FunctionalSimulationTruth,
) -> dict[str, np.ndarray]:
    """Construct named planar truth covariance blocks on truth.truth_grid."""

    components = np.asarray(truth.eigenfunctions, dtype=float)
    eigenvalues = np.asarray(truth.eigenvalues, dtype=float)
    if components.ndim != 3 or components.shape[2] != 2:
        raise ValueError(
            "sparse MFPCA recovery requires exactly two truth dimensions"
        )
    x = components[:, :, 0]
    y = components[:, :, 1]
    return {
        "cxx": np.einsum(
            "k,ks,kt->st", eigenvalues, x, x, optimize=True
        ),
        "cxy": np.einsum(
            "k,ks,kt->st", eigenvalues, x, y, optimize=True
        ),
        "cyx": np.einsum(
            "k,ks,kt->st", eigenvalues, y, x, optimize=True
        ),
        "cyy": np.einsum(
            "k,ks,kt->st", eigenvalues, y, y, optimize=True
        ),
    }


def _covariance_block_ise(
    estimated: np.ndarray,
    target: np.ndarray,
    time_weights: np.ndarray,
) -> float:
    """Quadrature-weighted ISE for one G x G covariance block."""

    estimate = np.asarray(estimated, dtype=float)
    truth = np.asarray(target, dtype=float)
    weights = np.asarray(time_weights, dtype=float)
    expected = (weights.size, weights.size)
    if estimate.shape != expected or truth.shape != expected:
        raise ValueError(
            "planar covariance blocks must match the truth-grid geometry"
        )
    if not np.all(np.isfinite(estimate)) or not np.all(np.isfinite(truth)):
        raise ValueError("planar covariance blocks must be finite")
    return float(
        np.sum(
            (estimate - truth) ** 2
            * np.outer(weights, weights)
        )
    )


def _truth_tie_groups(
    eigenvalues: np.ndarray,
    *,
    relative_tolerance: float,
) -> tuple[tuple[int, ...], ...]:
    """Return contiguous truth-eigenvalue groups that are not identifiable singly."""

    values = np.asarray(eigenvalues, dtype=float)
    tolerance = float(relative_tolerance)
    if values.ndim != 1 or values.size < 1:
        raise ValueError("truth eigenvalues must be a non-empty vector")
    if not np.all(np.isfinite(values)) or np.any(values <= 0):
        raise ValueError("truth eigenvalues must be finite and positive")
    if not np.isfinite(tolerance) or tolerance < 0:
        raise ValueError(
            "relative_tolerance must be finite and non-negative"
        )

    groups: list[tuple[int, ...]] = []
    start = 0
    for index in range(1, values.size):
        scale = max(
            abs(float(values[index - 1])),
            abs(float(values[index])),
            np.finfo(float).tiny,
        )
        tied = (
            abs(float(values[index - 1] - values[index]))
            <= tolerance * scale
        )
        if not tied:
            if index - start > 1:
                groups.append(tuple(range(start, index)))
            start = index
    if values.size - start > 1:
        groups.append(tuple(range(start, values.size)))
    return tuple(groups)


def _weighted_subspace_principal_cosines(
    estimated: np.ndarray,
    truth: np.ndarray,
    flat_weights: np.ndarray,
) -> np.ndarray:
    """Principal cosines between two equally sized functional subspaces."""

    estimated_normalized = _normalized_rows(estimated, flat_weights)
    truth_normalized = _normalized_rows(truth, flat_weights)
    if estimated_normalized.shape != truth_normalized.shape:
        raise ValueError(
            "subspace comparison requires equal component counts/geometries"
        )
    sqrt_weights = np.sqrt(np.asarray(flat_weights, dtype=float))
    q_estimated, _ = np.linalg.qr(
        estimated_normalized.T * sqrt_weights[:, None]
    )
    q_truth, _ = np.linalg.qr(
        truth_normalized.T * sqrt_weights[:, None]
    )
    return np.clip(
        np.linalg.svd(q_estimated.T @ q_truth, compute_uv=False),
        0.0,
        1.0,
    )


def _score_procrustes_rmse(
    estimated_scores: np.ndarray,
    truth_scores: np.ndarray,
) -> float | None:
    """Orthogonally align tied score coordinates and return elementwise RMSE."""

    estimated = np.asarray(estimated_scores, dtype=float)
    target = np.asarray(truth_scores, dtype=float)
    if estimated.shape != target.shape or estimated.ndim != 2:
        raise ValueError(
            "score Procrustes comparison requires equal two-dimensional arrays"
        )
    finite_rows = np.all(np.isfinite(estimated), axis=1) & np.all(
        np.isfinite(target), axis=1
    )
    if np.count_nonzero(finite_rows) < max(2, estimated.shape[1]):
        return None
    estimate = estimated[finite_rows]
    truth_finite = target[finite_rows]
    u, _, vt = np.linalg.svd(
        estimate.T @ truth_finite,
        full_matrices=False,
    )
    rotation = u @ vt
    aligned = estimate @ rotation
    return float(np.sqrt(np.mean((aligned - truth_finite) ** 2)))


def _population_values(
    *,
    estimated_mean: np.ndarray,
    estimated_components: np.ndarray,
    estimated_eigenvalues: np.ndarray,
    estimated_scores: np.ndarray,
    weights: np.ndarray,
    truth: FunctionalSimulationTruth,
    reconstructed: np.ndarray,
    estimated_covariance: np.ndarray | None = None,
) -> tuple[tuple[FunctionalRecoveryValue, ...], _Alignment]:
    estimated_mean = np.asarray(estimated_mean, dtype=float)
    estimated_components = np.asarray(estimated_components, dtype=float)
    estimated_eigenvalues = np.asarray(
        estimated_eigenvalues, dtype=float
    )
    estimated_scores = np.asarray(estimated_scores, dtype=float)
    truth_mean = np.asarray(truth.mean, dtype=float)
    truth_components = np.asarray(truth.eigenfunctions, dtype=float)

    if estimated_mean.shape != truth_mean.shape:
        raise ValueError(
            "fitted mean and generating mean must have identical shape"
        )
    if (
        estimated_components.ndim != 3
        or estimated_components.shape[1:] != truth_mean.shape
    ):
        raise ValueError(
            "fitted component grid/dimensions do not match truth"
        )
    if estimated_eigenvalues.shape != (estimated_components.shape[0],):
        raise ValueError(
            "fitted eigenvalues do not match fitted component count"
        )
    if (
        estimated_scores.ndim != 2
        or estimated_scores.shape[1] != estimated_components.shape[0]
    ):
        raise ValueError(
            "fitted scores do not match fitted component count"
        )
    if estimated_scores.shape[0] != truth.scores.shape[0]:
        raise ValueError(
            "fitted and generating scores must contain the same curves"
        )

    flat_weights = _functional_weights(weights, truth_mean.shape[1])
    alignment = _align_components(
        estimated_components, truth_components, flat_weights
    )

    values: list[FunctionalRecoveryValue] = [
        _value(
            "mean_ise",
            _ise(estimated_mean - truth_mean, flat_weights),
        )
    ]

    if estimated_covariance is None:
        covariance_estimate = _covariance_from_modes(
            estimated_eigenvalues,
            estimated_components,
        )
    else:
        covariance_estimate = np.asarray(
            estimated_covariance,
            dtype=float,
        )
    true_covariance = _covariance_from_modes(
        truth.eigenvalues,
        truth_components,
    )
    if covariance_estimate.shape != true_covariance.shape:
        raise ValueError(
            "fitted covariance and generating covariance must have "
            "identical flattened geometry"
        )
    covariance_weights = np.outer(flat_weights, flat_weights)
    values.append(
        _value(
            "covariance_ise",
            np.sum(
                (covariance_estimate - true_covariance) ** 2
                * covariance_weights
            ),
        )
    )

    for component, truth_component in enumerate(
        alignment.truth_indices
    ):
        target_eigenvalue = float(truth.eigenvalues[truth_component])
        values.extend(
            [
                _value(
                    "eigenvalue_relative_error",
                    abs(
                        float(estimated_eigenvalues[component])
                        - target_eigenvalue
                    )
                    / abs(target_eigenvalue),
                    component=component,
                ),
                _value(
                    "component_absolute_similarity",
                    alignment.component_similarity[component],
                    component=component,
                ),
            ]
        )
        estimate = (
            alignment.signs[component]
            * estimated_scores[:, component]
        )
        target = np.asarray(
            truth.scores[:, truth_component], dtype=float
        )
        finite = np.isfinite(estimate) & np.isfinite(target)
        if np.count_nonzero(finite) >= 2:
            values.extend(
                [
                    _value(
                        "score_correlation",
                        np.corrcoef(
                            estimate[finite], target[finite]
                        )[0, 1],
                        component=component,
                    ),
                    _value(
                        "score_rmse",
                        np.sqrt(
                            np.mean(
                                (
                                    estimate[finite]
                                    - target[finite]
                                )
                                ** 2
                            )
                        ),
                        component=component,
                    ),
                ]
            )

    for index, cosine in enumerate(alignment.principal_cosines):
        values.extend(
            [
                _value(
                    "subspace_principal_cosine",
                    cosine,
                    component=index,
                ),
                _value(
                    "subspace_principal_angle_degrees",
                    np.degrees(np.arccos(cosine)),
                    component=index,
                ),
            ]
        )

    reconstructed = np.asarray(reconstructed, dtype=float)
    latent = np.asarray(truth.latent_on_truth_grid, dtype=float)
    if reconstructed.shape != latent.shape:
        raise ValueError(
            "reconstructed curves and latent truth must have identical shape"
        )
    curve_ise = np.sum(
        (reconstructed - latent) ** 2
        * np.asarray(weights, dtype=float)[None, :, None],
        axis=(1, 2),
    )
    finite_curve = np.isfinite(curve_ise)
    if np.any(finite_curve):
        values.append(
            _value(
                "reconstruction_ise",
                float(np.mean(curve_ise[finite_curve])),
            )
        )

    return tuple(values), alignment


def evaluate_fpca_recovery(
    result: FPCAResult,
    truth: FunctionalSimulationTruth,
) -> FunctionalRecoveryAssessment:
    """Evaluate grid FPCA/MFPCA against exact generating truth.

    The fitted grid must equal the simulation truth grid and the fit must use
    scaling="none". The evaluator never interpolates or silently rescales truth.
    """

    if not isinstance(result, FPCAResult):
        raise TypeError("result must be an FPCAResult")
    if not isinstance(truth, FunctionalSimulationTruth):
        raise TypeError("truth must be a FunctionalSimulationTruth")
    _require_truth_grid(result.time, truth)
    scaling = dict(result.provenance).get("fpca", {}).get("scaling")
    if scaling not in {None, "none"}:
        raise ValueError(
            "known-truth FPCA recovery requires scaling='none'"
        )
    if result.dimension_names != truth.dimension_names:
        raise ValueError(
            "fitted dimension names/order do not match generating truth"
        )
    if not np.allclose(
        result.scale,
        np.ones_like(result.scale),
        rtol=0.0,
        atol=1e-12,
    ):
        raise ValueError(
            "known-truth FPCA recovery requires unit dimension scales"
        )

    reconstruction = result.mean[None, :, :] + np.einsum(
        "nk,ktd->ntd",
        result.scores,
        result.components,
        optimize=True,
    )
    values, alignment = _population_values(
        estimated_mean=result.mean,
        estimated_components=result.components,
        estimated_eigenvalues=result.explained_variance,
        estimated_scores=result.scores,
        weights=result.weights,
        truth=truth,
        reconstructed=reconstruction,
    )
    return FunctionalRecoveryAssessment(
        values=values,
        provenance={
            "estimator": "FPCA",
            "multivariate": len(result.dimension_names) > 1,
            "truth_grid_match": "exact",
            "scaling": "none",
            "matched_truth_components": (
                alignment.truth_indices.tolist()
            ),
            "alignment_signs": alignment.signs.tolist(),
        },
    )


def _univariate_truth(
    truth: FunctionalSimulationTruth,
    dimension_index: int,
    dimension_name: str,
) -> FunctionalSimulationTruth:
    return FunctionalSimulationTruth(
        **{
            **truth.__dict__,
            "mean": truth.mean[:, [dimension_index]],
            "eigenfunctions": truth.eigenfunctions[
                :, :, [dimension_index]
            ],
            "latent_on_truth_grid": truth.latent_on_truth_grid[
                :, :, [dimension_index]
            ],
            "measurement_noise_covariance": np.asarray(
                [[
                    truth.measurement_noise_covariance[
                        dimension_index, dimension_index
                    ]
                ]],
                dtype=float,
            ),
            "dimension_names": (dimension_name,),
        }
    )


def evaluate_sparse_fpca_recovery(
    result: SparseFPCAResult,
    truth: FunctionalSimulationTruth,
) -> FunctionalRecoveryAssessment:
    """Evaluate native univariate sparse FPCA/PACE against simulation truth."""

    if not isinstance(result, SparseFPCAResult):
        raise TypeError("result must be a SparseFPCAResult")
    if not isinstance(truth, FunctionalSimulationTruth):
        raise TypeError("truth must be a FunctionalSimulationTruth")
    if result.evaluation_grid is None:
        raise ValueError(
            "sparse result does not contain an evaluation grid"
        )
    if result.mean is None or result.covariance is None:
        raise ValueError(
            "sparse result does not contain native mean/covariance"
        )
    if result.eigenfunctions is None:
        raise ValueError(
            "sparse result does not contain native eigenfunctions"
        )
    _require_truth_grid(result.evaluation_grid, truth)

    try:
        dimension_index = truth.dimension_names.index(result.dimension)
    except ValueError as exc:
        raise ValueError(
            "sparse result dimension is absent from generating truth"
        ) from exc
    truth_one = _univariate_truth(
        truth, dimension_index, result.dimension
    )
    weights = (
        functional_trapezoid_weights(result.evaluation_grid)
        if result.quadrature_weights is None
        else np.asarray(result.quadrature_weights, dtype=float)
    )
    components = np.asarray(
        result.eigenfunctions, dtype=float
    )[:, :, None]
    mean = np.asarray(result.mean, dtype=float)[:, None]
    scores = np.asarray(result.scores, dtype=float)
    reconstruction = mean[None, :, :] + np.einsum(
        "nk,ktd->ntd",
        scores,
        components,
        optimize=True,
    )

    values, alignment = _population_values(
        estimated_mean=mean,
        estimated_components=components,
        estimated_eigenvalues=np.asarray(
            result.eigenvalues, dtype=float
        ),
        estimated_scores=scores,
        weights=weights,
        truth=truth_one,
        reconstructed=reconstruction,
        estimated_covariance=np.asarray(
            result.covariance,
            dtype=float,
        ),
    )
    values = list(values)

    diagnostics = result.score_diagnostics
    if len(diagnostics):
        if "status_code" in diagnostics.columns:
            values.append(
                _value(
                    "score_failure_rate",
                    np.mean(
                        diagnostics["status_code"].to_numpy()
                        != "ok"
                    ),
                )
            )
        if "condition_number" in diagnostics.columns:
            condition = pd.to_numeric(
                diagnostics["condition_number"], errors="coerce"
            ).to_numpy(dtype=float)
            condition = condition[np.isfinite(condition)]
            if condition.size:
                values.extend(
                    [
                        _value(
                            "score_condition_number_median",
                            np.median(condition),
                        ),
                        _value(
                            "score_condition_number_q95",
                            np.quantile(condition, 0.95),
                        ),
                        _value(
                            "score_condition_number_max",
                            np.max(condition),
                        ),
                    ]
                )
    else:
        values.append(
            _value(
                "score_failure_rate",
                np.mean(
                    ~np.all(np.isfinite(scores), axis=1)
                ),
            )
        )

    covariance_diagnostics = dict(result.covariance_diagnostics)
    applied_action = str(
        covariance_diagnostics.get("applied_action", "unknown")
    )
    correction = covariance_diagnostics.get(
        "relative_operator_correction_frobenius_norm"
    )
    if correction is not None and np.isfinite(float(correction)):
        values.extend(
            [
                _value(
                    "psd_repair_applied",
                    1.0 if applied_action == "project" else 0.0,
                ),
                _value(
                    "psd_relative_operator_correction",
                    float(correction),
                ),
            ]
        )

    true_noise = float(
        truth.measurement_noise_covariance[
            dimension_index, dimension_index
        ]
    )
    if result.noise_variance is not None:
        noise_error = abs(
            float(result.noise_variance) - true_noise
        )
        values.append(
            _value("noise_variance_absolute_error", noise_error)
        )
        if true_noise > 0:
            values.append(
                _value(
                    "noise_variance_relative_error",
                    noise_error / true_noise,
                )
            )

    sparse_provenance = dict(result.provenance).get(
        "sparse_fpca", {}
    )
    return FunctionalRecoveryAssessment(
        values=tuple(values),
        provenance={
            "estimator": "native_sparse_fpca_pace",
            "truth_grid_match": "exact",
            "dimension": result.dimension,
            "noise_variance_method": sparse_provenance.get(
                "noise_variance_method"
            ),
            "measurement_error_variance_supplied": (
                sparse_provenance.get(
                    "measurement_error_variance_supplied"
                )
            ),
            "matched_truth_components": (
                alignment.truth_indices.tolist()
            ),
            "alignment_signs": alignment.signs.tolist(),
        },
    )


def evaluate_sparse_mfpca_recovery(
    result: SparseMFPCAResult,
    truth: FunctionalSimulationTruth,
) -> FunctionalRecoveryAssessment:
    """Evaluate native sparse multivariate FPCA/joint PACE against truth.

    Covariance recovery is block-aware so public time-major functional arrays
    are never confused with the internal channel-major block operator. Exact
    or near-tied truth eigenspaces are treated as subspaces: component-specific
    eigenfunction and score metrics are omitted inside those groups and
    replaced by principal-angle geometry plus Procrustes-aligned score RMSE.
    """

    if not isinstance(result, SparseMFPCAResult):
        raise TypeError("result must be a SparseMFPCAResult")
    if not isinstance(truth, FunctionalSimulationTruth):
        raise TypeError("truth must be a FunctionalSimulationTruth")
    _require_truth_grid(result.evaluation_grid, truth)
    if tuple(result.dimensions) != tuple(truth.dimension_names):
        raise ValueError(
            "fitted dimension names/order do not match generating truth"
        )
    if len(result.dimensions) != 2:
        raise ValueError(
            "sparse MFPCA recovery requires exactly two dimensions"
        )

    mean = np.asarray(result.mean, dtype=float)
    components = np.asarray(result.eigenfunctions, dtype=float)
    eigenvalues = np.asarray(result.eigenvalues, dtype=float)
    scores = np.asarray(result.scores, dtype=float)
    truth_mean = np.asarray(truth.mean, dtype=float)
    truth_components = np.asarray(truth.eigenfunctions, dtype=float)
    truth_scores = np.asarray(truth.scores, dtype=float)
    if mean.shape != truth_mean.shape:
        raise ValueError(
            "fitted mean and generating mean must have identical shape"
        )
    if (
        components.ndim != 3
        or components.shape[1:] != truth_mean.shape
        or components.shape[2] != 2
    ):
        raise ValueError(
            "fitted joint eigenfunctions do not match truth geometry"
        )
    if eigenvalues.shape != (components.shape[0],):
        raise ValueError(
            "fitted eigenvalues do not match fitted component count"
        )
    if scores.shape != (truth_scores.shape[0], components.shape[0]):
        raise ValueError(
            "fitted scores do not match truth curve/component geometry"
        )

    weights = np.asarray(result.quadrature_weights, dtype=float)
    expected_weights = functional_trapezoid_weights(
        result.evaluation_grid
    )
    if weights.shape != expected_weights.shape or not np.allclose(
        weights,
        expected_weights,
        rtol=0.0,
        atol=1e-14,
    ):
        raise ValueError(
            "sparse MFPCA recovery requires the declared functional quadrature weights"
        )
    flat_weights = _functional_weights(weights, 2)
    alignment = _align_components(
        components,
        truth_components,
        flat_weights,
    )

    tie_tolerance = 1e-8
    tie_groups = _truth_tie_groups(
        truth.eigenvalues,
        relative_tolerance=tie_tolerance,
    )
    tie_lookup = {
        component: group
        for group in tie_groups
        for component in group
    }
    selected_truth = set(int(value) for value in alignment.truth_indices)
    for group in tie_groups:
        overlap = selected_truth.intersection(group)
        if overlap and len(overlap) != len(group):
            raise ValueError(
                "retained components split a tied truth eigenspace; "
                "component-level recovery is not identifiable"
            )

    values: list[FunctionalRecoveryValue] = [
        _value(
            "mean_ise",
            _ise(mean - truth_mean, flat_weights),
        )
    ]

    truth_blocks = _planar_truth_covariance_blocks(truth)
    estimated_blocks = {
        "cxx": np.asarray(result.covariance_cxx, dtype=float),
        "cxy": np.asarray(result.covariance_cxy, dtype=float),
        "cyx": np.asarray(result.covariance_cyx, dtype=float),
        "cyy": np.asarray(result.covariance_cyy, dtype=float),
    }
    block_errors: dict[str, float] = {}
    for block_name in ("cxx", "cxy", "cyx", "cyy"):
        error = _covariance_block_ise(
            estimated_blocks[block_name],
            truth_blocks[block_name],
            weights,
        )
        block_errors[block_name] = error
        values.append(
            _value(
                "covariance_block_ise",
                error,
                source=block_name,
            )
        )
    values.append(
        _value(
            "covariance_ise",
            sum(block_errors.values()),
        )
    )

    for component, truth_component_raw in enumerate(
        alignment.truth_indices
    ):
        truth_component = int(truth_component_raw)
        target_eigenvalue = float(truth.eigenvalues[truth_component])
        values.append(
            _value(
                "eigenvalue_relative_error",
                abs(float(eigenvalues[component]) - target_eigenvalue)
                / abs(target_eigenvalue),
                component=component,
            )
        )
        if truth_component in tie_lookup:
            continue
        values.append(
            _value(
                "component_absolute_similarity",
                alignment.component_similarity[component],
                component=component,
            )
        )
        estimate = alignment.signs[component] * scores[:, component]
        target = truth_scores[:, truth_component]
        finite = np.isfinite(estimate) & np.isfinite(target)
        if np.count_nonzero(finite) >= 2:
            correlation = float(
                np.corrcoef(estimate[finite], target[finite])[0, 1]
            )
            if np.isfinite(correlation):
                values.append(
                    _value(
                        "score_correlation",
                        correlation,
                        component=component,
                    )
                )
            values.append(
                _value(
                    "score_rmse",
                    np.sqrt(
                        np.mean((estimate[finite] - target[finite]) ** 2)
                    ),
                    component=component,
                )
            )

    for index, cosine in enumerate(alignment.principal_cosines):
        values.extend(
            [
                _value(
                    "subspace_principal_cosine",
                    cosine,
                    component=index,
                ),
                _value(
                    "subspace_principal_angle_degrees",
                    np.degrees(np.arccos(cosine)),
                    component=index,
                ),
            ]
        )

    tied_sources: list[str] = []
    for group in tie_groups:
        if not set(group).issubset(selected_truth):
            continue
        estimated_indices = [
            index
            for index, truth_index in enumerate(alignment.truth_indices)
            if int(truth_index) in group
        ]
        source = "truth_components_" + "_".join(
            str(index + 1) for index in group
        )
        tied_sources.append(source)
        group_cosines = _weighted_subspace_principal_cosines(
            components[estimated_indices],
            truth_components[list(group)],
            flat_weights,
        )
        for local_index, cosine in enumerate(group_cosines):
            values.extend(
                [
                    _value(
                        "subspace_principal_cosine",
                        cosine,
                        component=local_index,
                        source=source,
                    ),
                    _value(
                        "subspace_principal_angle_degrees",
                        np.degrees(np.arccos(cosine)),
                        component=local_index,
                        source=source,
                    ),
                ]
            )
        procrustes = _score_procrustes_rmse(
            scores[:, estimated_indices],
            truth_scores[:, list(group)],
        )
        if procrustes is not None:
            values.append(
                _value(
                    "score_subspace_procrustes_rmse",
                    procrustes,
                    source=source,
                )
            )

    reconstruction = mean[None, :, :] + np.einsum(
        "nk,ktd->ntd",
        scores,
        components,
        optimize=True,
    )
    latent = np.asarray(truth.latent_on_truth_grid, dtype=float)
    if reconstruction.shape != latent.shape:
        raise ValueError(
            "reconstructed curves and latent truth must have identical shape"
        )
    curve_ise = np.sum(
        (reconstruction - latent) ** 2
        * weights[None, :, None],
        axis=(1, 2),
    )
    finite_curve = np.isfinite(curve_ise)
    if np.any(finite_curve):
        values.append(
            _value(
                "reconstruction_ise",
                float(np.mean(curve_ise[finite_curve])),
            )
        )

    diagnostics = result.score_diagnostics
    if len(diagnostics):
        if "status_code" in diagnostics.columns:
            values.append(
                _value(
                    "score_failure_rate",
                    np.mean(
                        diagnostics["status_code"].to_numpy()
                        != "ok"
                    ),
                )
            )
        if "condition_number" in diagnostics.columns:
            condition = pd.to_numeric(
                diagnostics["condition_number"],
                errors="coerce",
            ).to_numpy(dtype=float)
            condition = condition[np.isfinite(condition)]
            if condition.size:
                values.extend(
                    [
                        _value(
                            "score_condition_number_median",
                            np.median(condition),
                        ),
                        _value(
                            "score_condition_number_q95",
                            np.quantile(condition, 0.95),
                        ),
                        _value(
                            "score_condition_number_max",
                            np.max(condition),
                        ),
                    ]
                )
    else:
        values.append(
            _value(
                "score_failure_rate",
                np.mean(~np.all(np.isfinite(scores), axis=1)),
            )
        )

    covariance_diagnostics = dict(result.covariance_diagnostics)
    applied_action = str(
        covariance_diagnostics.get("applied_action", "unknown")
    )
    correction = covariance_diagnostics.get(
        "relative_operator_correction_frobenius_norm"
    )
    if correction is not None and np.isfinite(float(correction)):
        values.extend(
            [
                _value(
                    "psd_repair_applied",
                    1.0 if applied_action == "project" else 0.0,
                ),
                _value(
                    "psd_relative_operator_correction",
                    float(correction),
                ),
            ]
        )

    supplied_error = np.asarray(
        result.measurement_error_covariance,
        dtype=float,
    )
    truth_error = np.asarray(
        truth.measurement_noise_covariance,
        dtype=float,
    )
    measurement_error_truth_supplied = (
        supplied_error.shape == truth_error.shape
        and np.allclose(
            supplied_error,
            truth_error,
            rtol=0.0,
            atol=1e-12,
        )
    )
    sparse_provenance = dict(result.provenance).get(
        "sparse_mfpca", {}
    )
    return FunctionalRecoveryAssessment(
        values=tuple(values),
        provenance={
            "estimator": "native_sparse_mfpca_joint_pace",
            "truth_grid_match": "exact",
            "dimensions": list(result.dimensions),
            "covariance_recovery": "named_block_quadrature_ise",
            "joint_covariance_ise_definition": (
                "cxx + cxy + cyx + cyy"
            ),
            "matched_truth_components": (
                alignment.truth_indices.tolist()
            ),
            "alignment_signs": alignment.signs.tolist(),
            "truth_eigenvalue_tie_relative_tolerance": tie_tolerance,
            "tied_truth_component_groups": [
                [index + 1 for index in group]
                for group in tie_groups
            ],
            "tied_score_subspace_sources": tied_sources,
            "component_metrics_omitted_for_tied_eigenspaces": bool(
                tie_groups
            ),
            "measurement_error_mode": sparse_provenance.get(
                "measurement_error_mode"
            ),
            "measurement_error_truth_supplied": bool(
                measurement_error_truth_supplied
            ),
            "measurement_error_recovery_metric_reported": False,
        },
    )


def evaluate_hierarchy_truth_recovery(
    truth: FunctionalSimulationTruth,
) -> FunctionalRecoveryAssessment:
    """Audit realized curve/participant/trial score-source variances."""

    if not isinstance(truth, FunctionalSimulationTruth):
        raise TypeError("truth must be a FunctionalSimulationTruth")
    sources = {
        "curve": (
            np.asarray(truth.curve_scores, dtype=float),
            np.asarray(truth.eigenvalues, dtype=float),
        ),
        "participant": (
            np.asarray(truth.participant_scores, dtype=float),
            np.asarray(truth.participant_eigenvalues, dtype=float),
        ),
        "trial": (
            np.asarray(truth.trial_scores, dtype=float),
            np.asarray(truth.trial_eigenvalues, dtype=float),
        ),
    }
    values: list[FunctionalRecoveryValue] = []
    for source, (draws, target) in sources.items():
        empirical = np.var(draws, axis=0, ddof=0)
        for component, (estimate, declared) in enumerate(
            zip(empirical, target, strict=True)
        ):
            absolute = abs(float(estimate) - float(declared))
            values.append(
                _value(
                    "source_variance_absolute_error",
                    absolute,
                    component=component,
                    source=source,
                )
            )
            if declared > 0:
                values.append(
                    _value(
                        "source_variance_relative_error",
                        absolute / float(declared),
                        component=component,
                        source=source,
                    )
                )
    return FunctionalRecoveryAssessment(
        values=tuple(values),
        provenance={
            "estimator": "none",
            "purpose": "simulation_source_variance_audit",
            "ddof": 0,
        },
    )


def evaluate_registration_recovery(
    result: RegistrationResult,
    truth: FunctionalSimulationTruth,
) -> FunctionalRecoveryAssessment:
    """Evaluate registered phase warps against exact inverse simulator warps.

    Simulation evaluates latent functions at w_i(t). Landmark registration
    stores h_i(t), the reference-to-observed mapping used in G_i(h_i(t)).
    Therefore the known-truth registration target is h_i = w_i^{-1}.
    """

    if not isinstance(result, RegistrationResult):
        raise TypeError("result must be a RegistrationResult")
    if not isinstance(truth, FunctionalSimulationTruth):
        raise TypeError("truth must be a FunctionalSimulationTruth")
    _require_truth_grid(result.original.time, truth)
    estimated = np.asarray(result.warping_functions, dtype=float)
    generated = np.asarray(
        truth.phase_warps_on_truth_grid,
        dtype=float,
    )
    if estimated.shape != generated.shape:
        raise ValueError(
            "registration warps and generating phase warps must have "
            "identical curve/time geometry"
        )

    grid = np.asarray(truth.truth_grid, dtype=float)
    true_inverse = np.stack(
        [
            np.interp(grid, generated[curve], grid)
            for curve in range(generated.shape[0])
        ],
        axis=0,
    )
    difference = estimated - true_inverse
    weights = functional_trapezoid_weights(grid)
    curve_ise = np.sum(
        difference**2 * weights[None, :],
        axis=1,
    )
    return FunctionalRecoveryAssessment(
        values=(
            _value(
                "phase_warp_ise",
                float(np.mean(curve_ise)),
            ),
            _value(
                "phase_warp_max_absolute_error",
                float(np.max(np.abs(difference))),
            ),
        ),
        provenance={
            "estimator": "landmark_registration",
            "truth_grid_match": "exact",
            "truth_target": "inverse_phase_warp",
            "simulator_phase_relation": "observed(t)=latent(w(t))",
        },
    )


def evaluate_functional_mixed_effects_recovery(
    result: FunctionalMixedEffectsResult,
    truth: FunctionalSimulationTruth,
    *,
    intercept_name: str = "Intercept",
) -> FunctionalRecoveryAssessment:
    """Evaluate intercept and participant/trial variance functions.

    The comparison is performed in the observed time domain. Spline-basis
    covariance parameters are not compared directly with simulator KL
    eigenvalues because those parameterizations are basis-dependent.
    Curve-level KL variation and scalar residual variance are deliberately not
    equated: the current simulator's curve-level functional process is not the
    same estimand as an iid scalar residual variance.
    """

    if not isinstance(result, FunctionalMixedEffectsResult):
        raise TypeError(
            "result must be a FunctionalMixedEffectsResult"
        )
    if not isinstance(truth, FunctionalSimulationTruth):
        raise TypeError(
            "truth must be a FunctionalSimulationTruth"
        )
    _require_truth_grid(result.time, truth)
    if result.random_slope_predictor is not None:
        raise ValueError(
            "mixed-effects recovery currently supports participant/trial "
            "functional intercepts only; random-slope truth is not declared "
            "by FunctionalSimulationScenario"
        )
    try:
        dimension_index = truth.dimension_names.index(
            result.dimension_name
        )
    except ValueError as exc:
        raise ValueError(
            "mixed-effects response dimension is absent from generating truth"
        ) from exc
    try:
        coefficient_index = result.coefficient_names.index(
            intercept_name
        )
    except ValueError as exc:
        raise ValueError(
            f"coefficient {intercept_name!r} is absent from the fitted model"
        ) from exc

    grid = np.asarray(truth.truth_grid, dtype=float)
    weights = functional_trapezoid_weights(grid)
    true_mean = np.asarray(
        truth.mean[:, dimension_index],
        dtype=float,
    )
    fitted_intercept = np.asarray(
        result.coefficient_functions[coefficient_index],
        dtype=float,
    )
    if fitted_intercept.shape != true_mean.shape:
        raise ValueError(
            "mixed-effects coefficient and truth mean grids do not match"
        )

    values: list[FunctionalRecoveryValue] = [
        _value(
            "coefficient_function_ise",
            np.sum(
                (fitted_intercept - true_mean) ** 2
                * weights
            ),
            source="intercept",
        )
    ]

    truth_modes = np.asarray(
        truth.eigenfunctions[:, :, dimension_index],
        dtype=float,
    )

    def score_source(
        source: str,
        fitted_variance: np.ndarray,
        declared_eigenvalues: np.ndarray,
    ) -> None:
        declared = np.asarray(
            declared_eigenvalues,
            dtype=float,
        )
        true_variance = np.sum(
            declared[:, None] * truth_modes**2,
            axis=0,
        )
        fitted_variance = np.asarray(
            fitted_variance,
            dtype=float,
        )
        if fitted_variance.shape != true_variance.shape:
            raise ValueError(
                f"{source} fitted and truth variance functions do not match"
            )
        values.append(
            _value(
                "source_variance_function_ise",
                np.sum(
                    (fitted_variance - true_variance) ** 2
                    * weights
                ),
                source=source,
            )
        )
        fitted_integrated = float(
            np.sum(fitted_variance * weights)
        )
        true_integrated = float(
            np.sum(true_variance * weights)
        )
        absolute = abs(
            fitted_integrated - true_integrated
        )
        values.append(
            _value(
                "source_integrated_variance_absolute_error",
                absolute,
                source=source,
            )
        )
        if true_integrated > 0:
            values.append(
                _value(
                    "source_integrated_variance_relative_error",
                    absolute / true_integrated,
                    source=source,
                )
            )

    participant_basis = np.asarray(
        result.random_basis,
        dtype=float,
    )
    participant_variance = np.einsum(
        "ti,ij,tj->t",
        participant_basis,
        np.asarray(
            result.random_intercept_covariance,
            dtype=float,
        ),
        participant_basis,
        optimize=True,
    )
    score_source(
        "participant",
        participant_variance,
        truth.participant_eigenvalues,
    )

    has_declared_trial_variance = bool(
        np.any(
            np.asarray(
                truth.trial_eigenvalues,
                dtype=float,
            )
            > 0
        )
    )
    if result.trial_random_effect == "functional_intercept":
        if (
            result.trial_random_basis is None
            or result.trial_random_effect_covariance is None
        ):
            raise ValueError(
                "trial random-effect fit is missing its basis/covariance"
            )
        trial_basis = np.asarray(
            result.trial_random_basis,
            dtype=float,
        )
        trial_variance = np.einsum(
            "ti,ij,tj->t",
            trial_basis,
            np.asarray(
                result.trial_random_effect_covariance,
                dtype=float,
            ),
            trial_basis,
            optimize=True,
        )
        score_source(
            "trial",
            trial_variance,
            truth.trial_eigenvalues,
        )
    elif has_declared_trial_variance:
        raise ValueError(
            "generating truth contains trial functional variance but the "
            "fitted model does not contain a trial functional random intercept"
        )

    return FunctionalRecoveryAssessment(
        values=tuple(values),
        provenance={
            "estimator": "functional_mixed_effects",
            "truth_grid_match": "exact",
            "dimension": result.dimension_name,
            "intercept_name": intercept_name,
            "participant_variance_target": "time_domain_variance_function",
            "trial_variance_target": "time_domain_variance_function",
            "basis_covariance_compared_directly_to_kl_eigenvalues": False,
            "curve_level_kl_variance_scored_as_scalar_residual": False,
        },
    )


def functional_recovery_reporting_text(
    assessment: FunctionalRecoveryAssessment,
) -> str:
    """Return compact reporting text for one semantic recovery assessment."""

    if not isinstance(assessment, FunctionalRecoveryAssessment):
        raise TypeError(
            "assessment must be a FunctionalRecoveryAssessment"
        )
    frame = functional_recovery_assessment_frame(assessment)
    metric_names = ", ".join(sorted(frame["metric"].unique()))
    estimator = dict(assessment.provenance).get(
        "estimator",
        "unspecified",
    )
    return (
        f"Known-truth recovery was evaluated after fitting for estimator "
        f"{estimator!r}. Recorded metric families: {metric_names}. "
        "Metric direction, units, scope, and component/source labels are "
        "retained explicitly. Recovery truth is an evaluation input only "
        "and is not an estimator-tuning input."
    )


def plot_functional_recovery_summary(
    summary: pd.DataFrame,
    *,
    metric: str,
    statistic: str = "median",
):
    """Plot one recovery metric across declared scenarios.

    Interquartile ranges are shown when statistic="median"; otherwise the
    requested scalar summary column is plotted without an invented interval.
    This is descriptive and performs no pass/fail interpretation.
    """

    import matplotlib.pyplot as plt

    if not isinstance(summary, pd.DataFrame):
        raise TypeError("summary must be a pandas DataFrame")
    required = {"scenario", "metric", statistic}
    missing = required - set(summary.columns)
    if missing:
        raise ValueError(
            f"summary is missing required columns: {sorted(missing)}"
        )
    selected = summary.loc[
        summary["metric"] == metric
    ].copy()
    if selected.empty:
        raise ValueError(
            f"metric {metric!r} is absent from the recovery summary"
        )
    labels = []
    for row in selected.itertuples(index=False):
        label = str(row.scenario)
        component = getattr(row, "component", None)
        source = getattr(row, "source", None)
        if pd.notna(source):
            label += f" / {source}"
        if pd.notna(component):
            label += f" / C{int(component)}"
        labels.append(label)

    x = np.arange(len(selected))
    y = selected[statistic].to_numpy(dtype=float)
    fig, ax = plt.subplots()
    if statistic == "median" and {"q25", "q75"} <= set(selected.columns):
        lower = y - selected["q25"].to_numpy(dtype=float)
        upper = selected["q75"].to_numpy(dtype=float) - y
        ax.errorbar(
            x,
            y,
            yerr=np.vstack([lower, upper]),
            fmt="o",
            capsize=3,
        )
    else:
        ax.plot(x, y, "o")
    ax.set_xticks(x, labels, rotation=45, ha="right")
    ax.set_ylabel(statistic.replace("_", " "))
    ax.set_title(metric.replace("_", " "))
    fig.tight_layout()
    return ax
