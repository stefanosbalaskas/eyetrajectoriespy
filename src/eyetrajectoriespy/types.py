"""Core scientific data structures for :mod:`eyetrajectoriespy`.

The package deliberately separates *data representation* from *estimation*.
A :class:`TrajectorySet` is the canonical object passed between preprocessing,
registration, FPCA, clustering, regression, and reporting helpers.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class TrajectorySet:
    """Collection of functional trajectories observed on a common grid.

    Parameters
    ----------
    time:
        One-dimensional, strictly increasing common time grid with shape
        ``(n_time,)``.
    values:
        Numeric array with shape ``(n_curves, n_time, n_dimensions)``.
        Missing observations are represented with ``np.nan`` and are never
        interpreted as zeros.
    curve_ids:
        Unique labels, one per trajectory.
    dimension_names:
        Names for the functional dimensions, e.g. ``("x", "y")``.
    metadata:
        One row per curve. It may contain participant, trial, condition,
        stimulus, or other design variables.
    coordinate_system:
        Explicit coordinate semantics such as ``"pixels"``, ``"normalized"``,
        ``"degrees"``, or ``"landmark_relative"``.
    time_unit:
        Explicit time unit such as ``"ms"``, ``"s"``, or ``"normalized"``.
    provenance:
        JSON-like dictionary describing source/preprocessing decisions.
    """

    time: np.ndarray
    values: np.ndarray
    curve_ids: tuple[str, ...]
    dimension_names: tuple[str, ...]
    metadata: pd.DataFrame = field(default_factory=pd.DataFrame)
    coordinate_system: str = "unknown"
    time_unit: str = "unknown"
    provenance: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        time = np.asarray(self.time, dtype=float)
        values = np.asarray(self.values, dtype=float)
        if time.ndim != 1:
            raise ValueError("time must be one-dimensional")
        if time.size < 2:
            raise ValueError("time must contain at least two samples")
        if not np.all(np.isfinite(time)):
            raise ValueError("time must contain only finite values")
        if not np.all(np.diff(time) > 0):
            raise ValueError("time must be strictly increasing")
        if values.ndim != 3:
            raise ValueError("values must have shape (n_curves, n_time, n_dimensions)")
        if values.shape[1] != time.size:
            raise ValueError("values.shape[1] must equal len(time)")
        if values.shape[0] != len(self.curve_ids):
            raise ValueError("curve_ids length must equal number of curves")
        if values.shape[2] != len(self.dimension_names):
            raise ValueError("dimension_names length must equal number of dimensions")
        if len(set(self.curve_ids)) != len(self.curve_ids):
            raise ValueError("curve_ids must be unique")
        if len(set(self.dimension_names)) != len(self.dimension_names):
            raise ValueError("dimension_names must be unique")

        md = self.metadata.copy()
        if md.empty:
            md = pd.DataFrame(index=pd.Index(self.curve_ids, name="curve_id"))
        elif len(md) != values.shape[0]:
            raise ValueError("metadata must have exactly one row per curve")
        else:
            md = md.reset_index(drop=True)
            md.index = pd.Index(self.curve_ids, name="curve_id")

        object.__setattr__(self, "time", time)
        object.__setattr__(self, "values", values)
        object.__setattr__(self, "metadata", md)
        object.__setattr__(self, "curve_ids", tuple(map(str, self.curve_ids)))
        object.__setattr__(self, "dimension_names", tuple(map(str, self.dimension_names)))
        object.__setattr__(self, "provenance", dict(self.provenance))

    @property
    def n_curves(self) -> int:
        """Number of trajectories."""

        return self.values.shape[0]

    @property
    def n_time(self) -> int:
        """Number of samples on the common grid."""

        return self.values.shape[1]

    @property
    def n_dimensions(self) -> int:
        """Number of functional dimensions."""

        return self.values.shape[2]

    def dimension(self, name: str) -> np.ndarray:
        """Return one named dimension as ``(n_curves, n_time)``."""

        try:
            index = self.dimension_names.index(name)
        except ValueError as exc:
            raise KeyError(f"Unknown dimension {name!r}") from exc
        return self.values[:, :, index]

    def subset(self, indices: Sequence[int]) -> "TrajectorySet":
        """Return a curve subset while preserving metadata and provenance."""

        idx = np.asarray(indices, dtype=int)
        ids = tuple(self.curve_ids[i] for i in idx)
        md = self.metadata.iloc[idx].reset_index(drop=True)
        return replace(self, values=self.values[idx], curve_ids=ids, metadata=md)

    def with_values(
        self,
        values: np.ndarray,
        *,
        time: np.ndarray | None = None,
        provenance_update: Mapping[str, Any] | None = None,
        time_unit: str | None = None,
        coordinate_system: str | None = None,
    ) -> "TrajectorySet":
        """Create a transformed copy with appended provenance."""

        provenance = dict(self.provenance)
        if provenance_update:
            provenance.update(dict(provenance_update))
        return replace(
            self,
            values=np.asarray(values, dtype=float),
            time=self.time if time is None else np.asarray(time, dtype=float),
            provenance=provenance,
            time_unit=self.time_unit if time_unit is None else time_unit,
            coordinate_system=(
                self.coordinate_system if coordinate_system is None else coordinate_system
            ),
        )


@dataclass(frozen=True)
class DiscreteFrechetResult:
    """Discrete Fréchet distance plus one deterministic optimal coupling."""

    distance: float
    coupling: np.ndarray
    local_distances: np.ndarray
    n_points_a: int
    n_points_b: int
    n_dimensions: int
    provenance: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DynamicTimeWarpingResult:
    """DTW cost plus one deterministic optimal monotone alignment path."""

    distance: float
    path: np.ndarray
    local_distances: np.ndarray
    path_length: int
    mean_local_distance: float
    n_points_a: int
    n_points_b: int
    n_dimensions: int
    window_radius: int | None
    provenance: Mapping[str, Any] = field(default_factory=dict)
    raw_distance: float | None = None
    normalized_distance: float | None = None
    step_pattern: str = "symmetric1"
    normalization_denominator: float | None = None
    step_weights: np.ndarray | None = None
    weighted_local_costs: np.ndarray | None = None


@dataclass(frozen=True)
class FPCAResult:
    """Result from grid-based functional principal component analysis."""

    mean: np.ndarray
    components: np.ndarray
    scores: np.ndarray
    explained_variance: np.ndarray
    explained_variance_ratio: np.ndarray
    time: np.ndarray
    dimension_names: tuple[str, ...]
    coordinate_system: str
    time_unit: str
    curve_ids: tuple[str, ...]
    weights: np.ndarray
    scale: np.ndarray
    provenance: Mapping[str, Any] = field(default_factory=dict)
    model: Any | None = None

    @property
    def n_components(self) -> int:
        return self.components.shape[0]

    def cumulative_explained_variance(self) -> np.ndarray:
        """Cumulative proportion of functional variance explained."""

        return np.cumsum(self.explained_variance_ratio)


@dataclass(frozen=True)
class RegistrationResult:
    """Registered trajectories and explicit phase information."""

    registered: TrajectorySet
    original: TrajectorySet
    warping_functions: np.ndarray
    reference_landmarks: np.ndarray
    observed_landmarks: np.ndarray
    method: str
    provenance: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CompositionalFPCAResult:
    """FPCA result for simplex-valued AOI probability functions."""

    fpca: FPCAResult
    reference_dimension: int
    original_dimension_names: tuple[str, ...]
    epsilon: float
    provenance: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class MultilevelFPCAResult:
    """Participant- and trial-level functional variation decomposition."""

    grand_mean: np.ndarray
    participant_fpca: FPCAResult
    trial_fpca: FPCAResult
    participant_scores: pd.DataFrame
    trial_scores: pd.DataFrame
    participant_column: str
    provenance: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ElasticFPCAResult:
    """Thin result wrapper for optional SRVF-based elastic trajectory analysis."""

    aligned: TrajectorySet
    warping_functions: np.ndarray
    scores: np.ndarray | None
    principal_directions: np.ndarray | None
    mean_curve: np.ndarray | None
    backend: str
    provenance: Mapping[str, Any] = field(default_factory=dict)
    backend_object: Any | None = None


@dataclass(frozen=True)
class FunctionalRegressionResult:
    """Scalar-on-function model fitted to FPCA scores."""

    model: Any
    component_indices: tuple[int, ...]
    coefficients: pd.Series
    predictions: np.ndarray
    family: str
    provenance: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ClusterResult:
    """Clustering result using functional scores or distances."""

    labels: np.ndarray
    centers: np.ndarray | None
    method: str
    model: Any | None
    provenance: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class IrregularTrajectorySet:
    """Collection of trajectories sampled on curve-specific time grids.

    Unlike :class:`TrajectorySet`, each curve retains its own sampling times.
    No interpolation or common-grid projection is implied by this object.
    """

    time: tuple[np.ndarray, ...]
    values: tuple[np.ndarray, ...]
    curve_ids: tuple[str, ...]
    dimension_names: tuple[str, ...]
    metadata: pd.DataFrame = field(default_factory=pd.DataFrame)
    coordinate_system: str = "unknown"
    time_unit: str = "unknown"
    provenance: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        times = tuple(np.asarray(t, dtype=float) for t in self.time)
        values = tuple(np.asarray(v, dtype=float) for v in self.values)
        if not times:
            raise ValueError("At least one irregular trajectory is required")
        if len(times) != len(values) or len(times) != len(self.curve_ids):
            raise ValueError("time, values, and curve_ids must have the same length")
        if len(set(self.curve_ids)) != len(self.curve_ids):
            raise ValueError("curve_ids must be unique")
        if not self.dimension_names or len(set(self.dimension_names)) != len(self.dimension_names):
            raise ValueError("dimension_names must be non-empty and unique")
        n_dim = len(self.dimension_names)
        for i, (time, value) in enumerate(zip(times, values, strict=True)):
            if time.ndim != 1 or time.size < 2:
                raise ValueError(f"time[{i}] must be one-dimensional with at least two samples")
            if not np.all(np.isfinite(time)) or not np.all(np.diff(time) > 0):
                raise ValueError(f"time[{i}] must be finite and strictly increasing")
            if value.ndim != 2 or value.shape != (time.size, n_dim):
                raise ValueError(
                    f"values[{i}] must have shape ({time.size}, {n_dim}); got {value.shape}"
                )

        md = self.metadata.copy()
        if md.empty:
            md = pd.DataFrame(index=pd.Index(self.curve_ids, name="curve_id"))
        elif len(md) != len(times):
            raise ValueError("metadata must have exactly one row per curve")
        else:
            md = md.reset_index(drop=True)
            md.index = pd.Index(self.curve_ids, name="curve_id")

        object.__setattr__(self, "time", times)
        object.__setattr__(self, "values", values)
        object.__setattr__(self, "curve_ids", tuple(map(str, self.curve_ids)))
        object.__setattr__(self, "dimension_names", tuple(map(str, self.dimension_names)))
        object.__setattr__(self, "metadata", md)
        object.__setattr__(self, "provenance", dict(self.provenance))

    @property
    def n_curves(self) -> int:
        return len(self.time)

    @property
    def n_dimensions(self) -> int:
        return len(self.dimension_names)

    @property
    def sample_counts(self) -> np.ndarray:
        """Number of observed samples for each curve."""
        return np.asarray([len(t) for t in self.time], dtype=int)

    def dimension(self, name: str) -> tuple[np.ndarray, ...]:
        """Return one named functional dimension without resampling."""
        try:
            index = self.dimension_names.index(name)
        except ValueError as exc:
            raise KeyError(f"Unknown dimension {name!r}") from exc
        return tuple(value[:, index] for value in self.values)

    def subset(self, indices: Sequence[int]) -> "IrregularTrajectorySet":
        """Return a curve subset while preserving native grids and provenance."""
        idx = np.asarray(indices, dtype=int)
        ids = tuple(self.curve_ids[i] for i in idx)
        return replace(
            self,
            time=tuple(self.time[i] for i in idx),
            values=tuple(self.values[i] for i in idx),
            curve_ids=ids,
            metadata=self.metadata.iloc[idx].reset_index(drop=True),
        )


@dataclass(frozen=True)
class FPCAStabilityResult:
    """Bootstrap stability diagnostics for matched functional principal components."""

    reference: FPCAResult
    similarities: np.ndarray
    signed_similarities: np.ndarray
    assignments: np.ndarray
    explained_variance_ratio: np.ndarray
    bootstrap_curve_counts: np.ndarray
    resampling_unit: str
    random_state: int | None
    provenance: Mapping[str, Any] = field(default_factory=dict)

    @property
    def n_bootstrap(self) -> int:
        return self.similarities.shape[0]


@dataclass(frozen=True)
class RegistrationSensitivityResult:
    """Comparison of FPCA before and after an explicit registration step."""

    unregistered_fpca: FPCAResult
    registered_fpca: FPCAResult
    component_assignments: np.ndarray
    signed_component_similarity: np.ndarray
    score_correlations: np.ndarray
    provenance: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class BasisProjectionResult:
    """Provenance-preserving wrapper around an optional functional basis object."""

    backend_object: Any
    dimension: str
    basis_type: str
    n_basis: int
    time_domain: tuple[float, float]
    provenance: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ConformalFunctionalAnomalyResult:
    """Split-conformal anomaly p-values for new functional trajectories."""

    reference: FPCAResult
    calibration_curve_ids: tuple[str, ...]
    target_curve_ids: tuple[str, ...]
    calibration_scores: np.ndarray
    target_scores: np.ndarray
    p_values: np.ndarray
    review_flags: np.ndarray
    alpha: float
    nonconformity: str
    mahalanobis_covariance: str | None
    n_components: int
    scaling: str
    provenance: Mapping[str, Any] = field(default_factory=dict)

    @property
    def n_calibration(self) -> int:
        return self.calibration_scores.shape[0]

    @property
    def n_targets(self) -> int:
        return self.target_scores.shape[0]

    @property
    def minimum_attainable_p(self) -> float:
        return 1.0 / (self.n_calibration + 1.0)


@dataclass(frozen=True)
class FunctionalOutlierResult:
    """Functional outlier/review diagnostics without automatic exclusion."""

    diagnostics: pd.DataFrame
    method: str
    reference: FPCAResult | None = None
    provenance: Mapping[str, Any] = field(default_factory=dict)
    backend_object: Any | None = None


@dataclass(frozen=True)
class FPCAInfluenceResult:
    """Leave-one-group-out sensitivity of functional principal components."""

    reference: FPCAResult
    summary: pd.DataFrame
    components: pd.DataFrame
    group_column: str | None
    n_components: int
    provenance: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class FPCACrossValidationResult:
    """Held-out reconstruction diagnostics across candidate FPC counts."""

    fold_errors: pd.DataFrame
    assignments: pd.DataFrame
    component_counts: tuple[int, ...]
    cv_unit: str
    n_splits: int
    group_column: str | None
    scaling: str
    random_state: int | None
    provenance: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class FPCAComponentEnvelopeResult:
    """Pointwise descriptive bootstrap envelopes for matched FPC functions."""

    reference: FPCAResult
    lower: np.ndarray
    median: np.ndarray
    upper: np.ndarray
    similarities: np.ndarray
    level: float
    resampling_unit: str
    random_state: int | None
    provenance: Mapping[str, Any] = field(default_factory=dict)

    @property
    def n_bootstrap(self) -> int:
        return self.similarities.shape[0]


@dataclass(frozen=True)
class FPCAComponentBandResult:
    """Bootstrap-calibrated simultaneous uncertainty bands for FPC functions."""

    reference: FPCAResult
    lower: np.ndarray
    upper: np.ndarray
    pointwise_se: np.ndarray
    critical_values: np.ndarray
    max_statistics: np.ndarray
    similarities: np.ndarray
    confidence_level: float
    simultaneous_scope: str
    resampling_unit: str
    participant_column: str | None
    relative_gap_threshold: float | None
    minimum_relative_gaps: np.ndarray
    random_state: int | None
    provenance: Mapping[str, Any] = field(default_factory=dict)

    @property
    def n_bootstrap(self) -> int:
        return self.similarities.shape[0]

    @property
    def n_components(self) -> int:
        return self.lower.shape[0]


@dataclass(frozen=True)
class FPCASpectrumUncertaintyResult:
    """Bootstrap uncertainty for matched FPCA eigenvalues and variance spectra."""

    reference: FPCAResult
    bootstrap_eigenvalues: np.ndarray
    bootstrap_explained_variance_ratio: np.ndarray
    bootstrap_cumulative_variance_ratio: np.ndarray
    eigenvalue_se: np.ndarray
    eigenvalue_critical_values: np.ndarray
    eigenvalue_lower: np.ndarray
    eigenvalue_upper: np.ndarray
    eigenvalue_max_statistics: np.ndarray
    explained_variance_ratio_se: np.ndarray
    explained_variance_ratio_critical_values: np.ndarray
    explained_variance_ratio_lower: np.ndarray
    explained_variance_ratio_upper: np.ndarray
    explained_variance_ratio_max_statistics: np.ndarray
    cumulative_variance_ratio_se: np.ndarray
    cumulative_variance_ratio_critical_values: np.ndarray
    cumulative_variance_ratio_lower: np.ndarray
    cumulative_variance_ratio_upper: np.ndarray
    cumulative_variance_ratio_max_statistics: np.ndarray
    assignments: np.ndarray
    similarities: np.ndarray
    confidence_level: float
    simultaneous_scope: str
    resampling_unit: str
    participant_column: str | None
    random_state: int | None
    provenance: Mapping[str, Any] = field(default_factory=dict)

    @property
    def n_bootstrap(self) -> int:
        return self.bootstrap_eigenvalues.shape[0]

    @property
    def n_components(self) -> int:
        return self.bootstrap_eigenvalues.shape[1]


@dataclass(frozen=True)
class FPCAScoreUncertaintyResult:
    """Basis-resampling uncertainty for FPCA scores of fixed target curves."""

    reference: FPCAResult
    target_curve_ids: tuple[str, ...]
    reference_scores: np.ndarray
    bootstrap_scores: np.ndarray
    lower: np.ndarray
    median: np.ndarray
    upper: np.ndarray
    score_se: np.ndarray
    assignments: np.ndarray
    similarities: np.ndarray
    level: float
    resampling_unit: str
    participant_column: str | None
    target_source: str
    random_state: int | None
    provenance: Mapping[str, Any] = field(default_factory=dict)

    @property
    def n_bootstrap(self) -> int:
        return self.bootstrap_scores.shape[0]

    @property
    def n_targets(self) -> int:
        return self.bootstrap_scores.shape[1]

    @property
    def n_components(self) -> int:
        return self.bootstrap_scores.shape[2]


@dataclass(frozen=True)
class FPCASubspaceComparisonResult:
    """Principal-angle comparison of corresponding FPCA component subspaces."""

    reference: FPCAResult
    candidate: FPCAResult
    component_indices: tuple[int, ...]
    principal_cosines: np.ndarray
    principal_angles_degrees: np.ndarray
    projector_distance_frobenius: float
    normalized_projector_distance: float
    provenance: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class FPCASubspaceStabilityResult:
    """Bootstrap stability diagnostics for an FPCA component subspace."""

    reference: FPCAResult
    component_indices: tuple[int, ...]
    principal_cosines: np.ndarray
    principal_angles_degrees: np.ndarray
    projector_distance_frobenius: np.ndarray
    normalized_projector_distance: np.ndarray
    resampling_unit: str
    random_state: int | None
    provenance: Mapping[str, Any] = field(default_factory=dict)

    @property
    def n_bootstrap(self) -> int:
        return self.principal_cosines.shape[0]


@dataclass(frozen=True)
class SparseFPCAResult:
    """Sparse univariate FPCA fitted to native irregular observations."""

    scores: np.ndarray
    eigenvalues: np.ndarray
    dimension: str
    curve_ids: tuple[str, ...]
    metadata: pd.DataFrame
    coordinate_system: str
    time_unit: str
    n_components: int
    fit_method: str
    fit_smoothing: str | None
    score_method: str
    score_smoothing: str | None
    tolerance: float
    normalize: bool
    provenance: Mapping[str, Any] = field(default_factory=dict)
    backend_object: Any | None = None
    backend_data: Any | None = None
    reconstructed_backend: Any | None = None


@dataclass(frozen=True)
class FunctionalMeanBandResult:
    """Simultaneous multiplier-bootstrap band for a functional mean."""

    mean: np.ndarray
    lower: np.ndarray
    upper: np.ndarray
    pointwise_se: np.ndarray
    critical_value: float
    max_statistics: np.ndarray
    confidence_level: float
    unit: str
    unit_ids: tuple[str, ...]
    participant_column: str | None
    time: np.ndarray
    dimension_names: tuple[str, ...]
    coordinate_system: str
    time_unit: str
    provenance: Mapping[str, Any] = field(default_factory=dict)

    @property
    def n_units(self) -> int:
        return len(self.unit_ids)



@dataclass(frozen=True)
class TrajectoryDistanceSensitivityResult:
    """Descriptive robustness diagnostics across trajectory-distance contracts."""

    specification_names: tuple[str, ...]
    distance_matrices: np.ndarray
    specification_table: pd.DataFrame
    pairwise_distance_table: pd.DataFrame
    comparison_table: pd.DataFrame
    neighbor_overlap_table: pd.DataFrame
    neighbor_orders: np.ndarray
    neighbor_cutoff_ties: np.ndarray
    curve_ids: tuple[str, ...]
    dimensions: tuple[str, ...]
    dimension_weights: np.ndarray
    neighbor_k: int
    provenance: Mapping[str, Any] = field(default_factory=dict)

    @property
    def n_specifications(self) -> int:
        return len(self.specification_names)

    @property
    def n_curves(self) -> int:
        return len(self.curve_ids)


@dataclass(frozen=True)
class FunctionalMixedEffectsResult:
    """Joint Gaussian functional mixed-effects regression fit."""

    coefficient_functions: np.ndarray
    coefficient_standard_errors: np.ndarray
    fixed_basis_coefficients: np.ndarray
    fixed_parameter_covariance: np.ndarray
    fixed_basis: np.ndarray
    fixed_basis_knots: np.ndarray
    random_basis: np.ndarray
    random_basis_knots: np.ndarray
    random_effect_coefficients: np.ndarray
    random_effect_functions: np.ndarray
    random_effect_covariance: np.ndarray
    residual_variance: float
    fitted_functions: np.ndarray
    residual_functions: np.ndarray
    observed_functions: np.ndarray
    scalar_design_matrix: np.ndarray
    coefficient_names: tuple[str, ...]
    predictor_names: tuple[str, ...]
    scalar_design_rank: int
    expanded_design_rank: int
    participant_column: str
    participant_ids: tuple[str, ...]
    curve_participant_ids: tuple[str, ...]
    curves_per_participant: tuple[int, ...]
    source_curve_ids: tuple[str, ...]
    time: np.ndarray
    dimension_name: str
    coordinate_system: str
    time_unit: str
    fixed_basis_size: int
    random_basis_size: int
    spline_degree: int
    reml: bool
    method: str
    maxiter: int
    converged: bool
    boundary_fit: bool
    backend_warnings: tuple[str, ...]
    log_likelihood: float
    provenance: Mapping[str, Any] = field(default_factory=dict)
    model: Any | None = None

    @property
    def n_coefficients(self) -> int:
        return len(self.coefficient_names)

    @property
    def n_participants(self) -> int:
        return len(self.participant_ids)

    @property
    def n_curves(self) -> int:
        return len(self.source_curve_ids)


@dataclass(frozen=True)
class FunctionalMixedEffectsBootstrapResult:
    """Participant-cluster bootstrap for functional mixed-effects coefficients."""

    reference: FunctionalMixedEffectsResult
    bootstrap_fixed_basis_coefficients: np.ndarray
    bootstrap_coefficient_functions: np.ndarray
    sampled_participant_indices: np.ndarray
    bootstrap_mean: np.ndarray
    bootstrap_standard_errors: np.ndarray
    random_state: int | None
    covariance_conditioning: str
    provenance: Mapping[str, Any] = field(default_factory=dict)

    @property
    def n_bootstrap(self) -> int:
        return self.bootstrap_coefficient_functions.shape[0]

    @property
    def n_participants(self) -> int:
        return self.sampled_participant_indices.shape[1]


@dataclass(frozen=True)
class FunctionalMixedEffectsBandResult:
    """Observed-grid simultaneous bands for mixed-effects coefficient functions."""

    reference: FunctionalMixedEffectsResult
    lower: np.ndarray
    upper: np.ndarray
    pointwise_standard_errors: np.ndarray
    critical_values: np.ndarray
    max_statistics: np.ndarray
    confidence_level: float
    simultaneous_scope: str
    bootstrap: FunctionalMixedEffectsBootstrapResult
    provenance: Mapping[str, Any] = field(default_factory=dict)

    @property
    def n_coefficients(self) -> int:
        return self.lower.shape[0]

    @property
    def n_time(self) -> int:
        return self.lower.shape[1]


@dataclass(frozen=True)
class FunctionOnScalarResult:
    """Observed-grid function-on-scalar regression fit."""

    coefficients: np.ndarray
    standard_errors: np.ndarray
    fitted_functions: np.ndarray
    residual_functions: np.ndarray
    observed_functions: np.ndarray
    design_matrix: np.ndarray
    coefficient_names: tuple[str, ...]
    predictor_names: tuple[str, ...]
    design_rank: int
    residual_degrees_of_freedom: int
    unit: str
    unit_ids: tuple[str, ...]
    curves_per_unit: tuple[int, ...]
    participant_column: str | None
    time: np.ndarray
    dimension_names: tuple[str, ...]
    coordinate_system: str
    time_unit: str
    source_curve_ids: tuple[str, ...]
    provenance: Mapping[str, Any] = field(default_factory=dict)

    @property
    def n_coefficients(self) -> int:
        return len(self.coefficient_names)

    @property
    def n_units(self) -> int:
        return len(self.unit_ids)


@dataclass(frozen=True)
class FunctionOnScalarBootstrapResult:
    """Wild-bootstrap coefficient replicates for function-on-scalar regression."""

    reference: FunctionOnScalarResult
    bootstrap_coefficients: np.ndarray
    multipliers: np.ndarray
    multiplier: str
    random_state: int | None
    provenance: Mapping[str, Any] = field(default_factory=dict)

    @property
    def n_bootstrap(self) -> int:
        return self.bootstrap_coefficients.shape[0]


@dataclass(frozen=True)
class FunctionOnScalarBandResult:
    """Observed-grid simultaneous bands for function-on-scalar coefficients."""

    reference: FunctionOnScalarResult
    lower: np.ndarray
    upper: np.ndarray
    critical_values: np.ndarray
    max_statistics: np.ndarray
    confidence_level: float
    simultaneous_scope: str
    bootstrap: FunctionOnScalarBootstrapResult
    provenance: Mapping[str, Any] = field(default_factory=dict)

    @property
    def n_coefficients(self) -> int:
        return self.lower.shape[0]


@dataclass(frozen=True)
class FPCARegressionUncertaintyResult:
    """Paired-bootstrap uncertainty for Gaussian FPCA scalar regression."""

    reference_fpca: FPCAResult
    reference_regression: FunctionalRegressionResult
    reference_slope: np.ndarray
    bootstrap_slopes: np.ndarray
    slope_lower: np.ndarray
    slope_median: np.ndarray
    slope_upper: np.ndarray
    slope_se: np.ndarray
    reference_intercept: float
    bootstrap_intercepts: np.ndarray
    target_curve_ids: tuple[str, ...]
    reference_mean_predictions: np.ndarray
    bootstrap_mean_predictions: np.ndarray
    prediction_lower: np.ndarray
    prediction_median: np.ndarray
    prediction_upper: np.ndarray
    prediction_se: np.ndarray
    level: float
    n_components: int
    scaling: str
    resampling_unit: str
    participant_column: str | None
    target_source: str
    random_state: int | None
    provenance: Mapping[str, Any] = field(default_factory=dict)

    @property
    def n_bootstrap(self) -> int:
        return self.bootstrap_slopes.shape[0]

    @property
    def n_targets(self) -> int:
        return self.bootstrap_mean_predictions.shape[1]


@dataclass(frozen=True)
class FPCARegressionSlopeBandResult:
    """Observed-grid simultaneous bootstrap band for a Gaussian FPCR slope."""

    regression_uncertainty: FPCARegressionUncertaintyResult
    lower: np.ndarray
    upper: np.ndarray
    pointwise_se: np.ndarray
    critical_values: np.ndarray
    max_statistics: np.ndarray
    confidence_level: float
    simultaneous_scope: str
    provenance: Mapping[str, Any] = field(default_factory=dict)

    @property
    def n_bootstrap(self) -> int:
        return self.regression_uncertainty.n_bootstrap

    @property
    def n_time(self) -> int:
        return self.lower.shape[0]

    @property
    def n_dimensions(self) -> int:
        return self.lower.shape[1]


@dataclass(frozen=True)
class FPCARegressionPredictionIntervalResult:
    """Future-outcome predictive distribution for Gaussian FPCR fixed targets."""

    regression_uncertainty: FPCARegressionUncertaintyResult
    centered_residuals: np.ndarray
    sampled_residuals: np.ndarray
    predictive_draws: np.ndarray
    lower: np.ndarray
    median: np.ndarray
    upper: np.ndarray
    predictive_se: np.ndarray
    confidence_level: float
    residual_method: str
    random_state: int | None
    provenance: Mapping[str, Any] = field(default_factory=dict)

    @property
    def n_bootstrap(self) -> int:
        return self.predictive_draws.shape[0]

    @property
    def n_targets(self) -> int:
        return self.predictive_draws.shape[1]


@dataclass(frozen=True)
class FPCAWildBootstrapProjectionResult:
    """Studentized wild-bootstrap inference for centered Gaussian FPCR projections."""

    reference_fpca: FPCAResult
    target_curve_ids: tuple[str, ...]
    reference_projection: np.ndarray
    pseudo_truth_projection: np.ndarray
    reference_se: np.ndarray
    bootstrap_projections: np.ndarray
    bootstrap_se: np.ndarray
    studentized_roots: np.ndarray
    critical_values: np.ndarray
    lower: np.ndarray
    upper: np.ndarray
    residuals: np.ndarray
    confidence_level: float
    residual_components: int
    inference_components: int
    scaling: str
    multiplier: str
    target_source: str
    independent_unit_column: str | None
    random_state: int | None
    provenance: Mapping[str, Any] = field(default_factory=dict)

    @property
    def n_bootstrap(self) -> int:
        return self.bootstrap_projections.shape[0]

    @property
    def n_targets(self) -> int:
        return self.bootstrap_projections.shape[1]


@dataclass(frozen=True)
class FPCAWildBootstrapSimultaneousResult:
    """Familywise simultaneous inference across fixed FPCR target projections."""

    projection_result: FPCAWildBootstrapProjectionResult
    targetwise_critical_values: np.ndarray
    critical_value: float
    max_statistics: np.ndarray
    lower: np.ndarray
    upper: np.ndarray
    confidence_level: float
    provenance: Mapping[str, Any] = field(default_factory=dict)

    @property
    def n_bootstrap(self) -> int:
        return self.projection_result.n_bootstrap

    @property
    def n_targets(self) -> int:
        return self.projection_result.n_targets

@dataclass(frozen=True)
class FPCAWildBootstrapFamilyTestResult:
    """Bootstrap maxT tests for a fixed family of Gaussian FPCR projections."""

    projection_result: FPCAWildBootstrapProjectionResult
    null_values: np.ndarray
    observed_statistics: np.ndarray
    targetwise_p_values: np.ndarray
    adjusted_p_values: np.ndarray
    max_statistics: np.ndarray
    global_statistic: float
    global_p_value: float
    reject_targetwise: np.ndarray
    reject_familywise: np.ndarray
    reject_global: bool
    significance_level: float
    pvalue_correction: str
    provenance: Mapping[str, Any] = field(default_factory=dict)

    @property
    def n_bootstrap(self) -> int:
        return self.projection_result.n_bootstrap

    @property
    def n_targets(self) -> int:
        return self.projection_result.n_targets

    @property
    def minimum_attainable_p(self) -> float:
        if self.pvalue_correction == "plus_one":
            return 1.0 / (self.n_bootstrap + 1.0)
        return 0.0

@dataclass(frozen=True)
class FPCAWildBootstrapMonteCarloDiagnosticResult:
    """Monte Carlo precision diagnostics for a fixed-family wild-bootstrap test."""

    family_test_result: FPCAWildBootstrapFamilyTestResult
    confidence_level: float
    targetwise_exceedances: np.ndarray
    adjusted_exceedances: np.ndarray
    global_exceedances: int
    targetwise_tail_probabilities: np.ndarray
    adjusted_tail_probabilities: np.ndarray
    global_tail_probability: float
    targetwise_mcse: np.ndarray
    adjusted_mcse: np.ndarray
    global_mcse: float
    targetwise_interval_lower: np.ndarray
    targetwise_interval_upper: np.ndarray
    adjusted_interval_lower: np.ndarray
    adjusted_interval_upper: np.ndarray
    global_interval_lower: float
    global_interval_upper: float
    targetwise_decision_stable: np.ndarray
    adjusted_decision_stable: np.ndarray
    global_decision_stable: bool
    provenance: Mapping[str, Any] = field(default_factory=dict)

    @property
    def n_bootstrap(self) -> int:
        return self.family_test_result.n_bootstrap

    @property
    def n_targets(self) -> int:
        return self.family_test_result.n_targets

    @property
    def significance_level(self) -> float:
        return self.family_test_result.significance_level


@dataclass(frozen=True)
class FPCAWildBootstrapTruncationScanResult:
    """Shared-multiplier wild-bootstrap interval scan over inference truncations."""

    reference_fpca: FPCAResult
    target_curve_ids: tuple[str, ...]
    candidate_components: tuple[int, ...]
    residual_components: int
    pseudo_truth_projection: np.ndarray
    reference_projections: np.ndarray
    reference_se: np.ndarray
    critical_values: np.ndarray
    lower: np.ndarray
    upper: np.ndarray
    centers: np.ndarray
    widths: np.ndarray
    studentized_roots: np.ndarray
    confidence_level: float
    scaling: str
    multiplier: str
    target_source: str
    independent_unit_column: str | None
    random_state: int | None
    provenance: Mapping[str, Any] = field(default_factory=dict)

    @property
    def n_bootstrap(self) -> int:
        return self.studentized_roots.shape[1]

    @property
    def n_targets(self) -> int:
        return self.studentized_roots.shape[2]

    @property
    def n_candidates(self) -> int:
        return len(self.candidate_components)


@dataclass(frozen=True)
class FPCAWildBootstrapTruncationSelectionResult:
    """Stabilized-volatility selection from a wild-bootstrap truncation scan."""

    scan: FPCAWildBootstrapTruncationScanResult
    width_changes: np.ndarray
    center_changes: np.ndarray
    stable_width: np.ndarray
    stable_center: np.ndarray
    stable_both: np.ndarray
    selected_candidate_indices: np.ndarray
    selected_components: np.ndarray
    selected_centers: np.ndarray
    selected_widths: np.ndarray
    selected_lower: np.ndarray
    selected_upper: np.ndarray
    width_threshold: float
    center_threshold: float
    stability_run: int
    on_failure: str
    provenance: Mapping[str, Any] = field(default_factory=dict)

    @property
    def n_targets(self) -> int:
        return self.scan.n_targets


@dataclass(frozen=True)
class FPCARegressionCVResult:
    """Outcome-tuned FPCA regression cross-validation diagnostics."""

    fold_losses: pd.DataFrame
    assignments: pd.DataFrame
    predictions: pd.DataFrame
    component_counts: tuple[int, ...]
    family: str
    loss: str
    cv_unit: str
    n_splits: int
    group_column: str | None
    scaling: str
    random_state: int | None
    provenance: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class FPCANestedRegressionCVResult:
    """Nested CV evaluation of outcome-tuned FPCA regression selection."""

    outer_folds: pd.DataFrame
    inner_summaries: pd.DataFrame
    predictions: pd.DataFrame
    family: str
    loss: str
    selection_rule: str
    component_counts: tuple[int, ...]
    outer_splits: int
    inner_splits: int
    cv_unit: str
    group_column: str | None
    scaling: str
    random_state: int | None
    provenance: Mapping[str, Any] = field(default_factory=dict)
