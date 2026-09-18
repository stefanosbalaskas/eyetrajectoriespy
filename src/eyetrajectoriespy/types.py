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

    Unlike :class:\`TrajectorySet\`, each curve retains its own sampling times.
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
