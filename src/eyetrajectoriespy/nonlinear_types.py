"""Result objects for nonlinear trajectory dynamics."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Mapping

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix

if TYPE_CHECKING:
    from .types import FunctionalMeanBandResult, TrajectorySet


@dataclass(frozen=True)
class DelayEmbeddingResult:
    """Delay-coordinate state-space reconstruction for common-grid trajectories."""

    values: np.ndarray
    time: np.ndarray
    curve_ids: tuple[str, ...]
    source_dimension_names: tuple[str, ...]
    state_names: tuple[str, ...]
    embedding_dimension: int
    delay_samples: int
    delay_time: float
    time_unit: str
    coordinate_system: str
    provenance: Mapping[str, Any] = field(default_factory=dict)

    @property
    def n_curves(self) -> int:
        return self.values.shape[0]

    @property
    def n_states(self) -> int:
        return self.values.shape[1]

    @property
    def state_dimension(self) -> int:
        return self.values.shape[2]


@dataclass(frozen=True)
class EmbeddingDelayDiagnosticResult:
    """Average-mutual-information and autocorrelation delay diagnostics."""

    table: pd.DataFrame
    curve_id: str
    dimension: str
    bins: int
    max_lag_samples: int
    time_unit: str
    provenance: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EmbeddingDimensionDiagnosticResult:
    """False-nearest-neighbor embedding-dimension diagnostics."""

    table: pd.DataFrame
    curve_id: str
    dimension: str
    delay_samples: int
    theiler_window_samples: int
    rtol: float
    atol: float
    provenance: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RecurrenceResult:
    """Sparse recurrence or cross-recurrence matrix plus explicit construction metadata."""

    matrix: csr_matrix
    time_a: np.ndarray
    time_b: np.ndarray
    source_curve_ids: tuple[str, ...]
    radius: float
    target_recurrence_rate: float | None
    achieved_recurrence_rate: float
    metric: str
    theiler_window_samples: int
    kind: str
    state_dimension: int
    provenance: Mapping[str, Any] = field(default_factory=dict)
    time_unit: str | None = None

    @property
    def shape(self) -> tuple[int, int]:
        return self.matrix.shape


@dataclass(frozen=True)
class JointRecurrenceResult:
    """Sparse intersection of synchronized auto-recurrence matrices."""

    matrix: csr_matrix
    time: np.ndarray
    component_recurrences: tuple["RecurrenceResult", ...]
    component_labels: tuple[str, ...]
    joint_recurrence_rate: float
    n_joint_recurrent_pairs: int
    eligible_pair_count: int
    theiler_window_samples: int
    provenance: Mapping[str, Any] = field(default_factory=dict)

    @property
    def shape(self) -> tuple[int, int]:
        return self.matrix.shape

    @property
    def n_components(self) -> int:
        return len(self.component_recurrences)


@dataclass(frozen=True)
class RecurrenceNetworkResult:
    """Sparse recurrence-network topology with explicit graph conventions."""

    adjacency: csr_matrix
    degree: np.ndarray
    normalized_degree: np.ndarray
    local_clustering: np.ndarray
    component_labels: np.ndarray
    component_sizes: np.ndarray
    edge_count: int
    graph_density: float
    transitivity: float
    mean_local_clustering: float
    n_connected_components: int
    largest_component_fraction: float
    isolated_node_fraction: float
    source_recurrence: "RecurrenceResult"
    provenance: Mapping[str, Any] = field(default_factory=dict)

    @property
    def n_nodes(self) -> int:
        return self.adjacency.shape[0]


@dataclass(frozen=True)
class RecurrenceRadiusProfileResult:
    """Exact recurrence-rate profile over an analyst-declared radius grid."""

    table: pd.DataFrame
    curve_id: str
    metric: str
    theiler_window_samples: int
    state_dimension: int
    eligible_pair_count: int
    provenance: Mapping[str, Any] = field(default_factory=dict)

    @property
    def n_radii(self) -> int:
        return len(self.table)


@dataclass(frozen=True)
class RQAResult:
    """Recurrence-quantification metrics with line-threshold provenance."""

    recurrence_rate: float
    determinism: float
    mean_diagonal_length: float
    max_diagonal_length: int
    diagonal_entropy: float
    laminarity: float
    trapping_time: float
    max_vertical_length: int
    center_of_recurrence_mass: float
    n_recurrence_points: int
    n_diagonal_lines: int
    n_vertical_lines: int
    min_diagonal_length: int
    min_vertical_length: int
    provenance: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class WindowedRQAResult:
    """Time-resolved RQA metrics from explicitly sized sliding windows."""

    table: pd.DataFrame
    window_samples: int
    step_samples: int
    dropped_tail_samples: int
    time_unit: str
    provenance: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class WindowedRQAFunctionalResult:
    """Functional trajectory representation of windowed RQA across curves."""

    trajectories: "TrajectorySet"
    window_results: tuple[WindowedRQAResult, ...]
    metrics: tuple[str, ...]
    window_samples: int
    step_samples: int
    overlap_samples: int
    overlap_fraction: float
    dropped_tail_samples: int
    time_unit: str
    undefined_policy: str
    provenance: Mapping[str, Any] = field(default_factory=dict)

    @property
    def n_curves(self) -> int:
        return self.trajectories.n_curves

    @property
    def n_windows(self) -> int:
        return self.trajectories.n_time


@dataclass(frozen=True)
class WindowedRQASensitivityResult:
    """Declared window/step sensitivity analyses for functional RQA."""

    analyses: tuple[WindowedRQAFunctionalResult, ...]
    design_table: pd.DataFrame
    summary_table: pd.DataFrame
    pairwise_table: pd.DataFrame
    metrics: tuple[str, ...]
    provenance: Mapping[str, Any] = field(default_factory=dict)

    @property
    def n_specifications(self) -> int:
        return len(self.analyses)


@dataclass(frozen=True)
class WindowedRQAMeanBandResult:
    """Unit-level simultaneous mean band for functional RQA trajectories."""

    functional_rqa: WindowedRQAFunctionalResult
    band: "FunctionalMeanBandResult"
    unit: str
    participant_column: str | None
    provenance: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RQAParameterSensitivityResult:
    """Declared multiverse of reconstructed-state RQA specifications."""

    table: pd.DataFrame
    summary_table: pd.DataFrame
    parameter_columns: tuple[str, ...]
    metric_columns: tuple[str, ...]
    curve_id: str
    provenance: Mapping[str, Any] = field(default_factory=dict)

    @property
    def n_specifications(self) -> int:
        return len(self.table)


@dataclass(frozen=True)
class LyapunovParameterSensitivityResult:
    """Declared multiverse of Rosenstein LLE specifications."""

    table: pd.DataFrame
    summary_table: pd.DataFrame
    parameter_columns: tuple[str, ...]
    curve_id: str
    exponent_unit: str
    provenance: Mapping[str, Any] = field(default_factory=dict)

    @property
    def n_specifications(self) -> int:
        return len(self.table)


@dataclass(frozen=True)
class KantzParameterSensitivityResult:
    """Declared multiverse of Kantz LLE neighborhood specifications."""

    table: pd.DataFrame
    summary_table: pd.DataFrame
    parameter_columns: tuple[str, ...]
    curve_id: str
    exponent_unit: str
    provenance: Mapping[str, Any] = field(default_factory=dict)

    @property
    def n_specifications(self) -> int:
        return len(self.table)


@dataclass(frozen=True)
class RQAMeanBootstrapResult:
    """Bootstrap uncertainty for population-average per-curve RQA metrics."""

    observed_table: pd.DataFrame
    unit_table: pd.DataFrame
    bootstrap_table: pd.DataFrame
    summary_table: pd.DataFrame
    metrics: tuple[str, ...]
    unit: str
    unit_ids: tuple[str, ...]
    participant_column: str | None
    confidence_level: float
    n_bootstrap: int
    provenance: Mapping[str, Any] = field(default_factory=dict)

    @property
    def n_units(self) -> int:
        return len(self.unit_ids)


@dataclass(frozen=True)
class LocalDivergenceResult:
    """Rosenstein-style mean log-divergence curve before linear fitting."""

    horizons: np.ndarray
    time_lags: np.ndarray
    mean_log_divergence: np.ndarray
    pair_counts: np.ndarray
    zero_distance_counts: np.ndarray
    nearest_neighbor_indices: np.ndarray
    theiler_window_samples: int
    max_horizon_samples: int
    curve_id: str
    time_unit: str
    provenance: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class KantzDivergenceResult:
    """Kantz neighborhood-averaged mean log-divergence curve."""

    horizons: np.ndarray
    time_lags: np.ndarray
    mean_log_divergence: np.ndarray
    reference_counts: np.ndarray
    pair_counts: np.ndarray
    zero_mean_neighborhood_counts: np.ndarray
    initial_neighbor_counts: np.ndarray
    radius: float
    min_neighbors: int
    theiler_window_samples: int
    max_horizon_samples: int
    curve_id: str
    time_unit: str
    provenance: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class LargestLyapunovResult:
    """Largest-Lyapunov estimate from an explicitly selected divergence interval."""

    exponent: float
    exponent_unit: str
    intercept: float
    r_squared: float
    standard_error: float
    fit_start: float
    fit_end: float
    n_fit_points: int
    divergence: LocalDivergenceResult | KantzDivergenceResult
    provenance: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class MultivariateIAAFTResult:
    """Cross-spectrum-aware multivariate IAAFT surrogate ensemble."""

    surrogates: np.ndarray
    source_values: np.ndarray
    curve_id: str
    dimension_names: tuple[str, ...]
    reference_dimension: str
    dimension_pairs: tuple[tuple[str, str], ...]
    convergence_iterations: np.ndarray
    spectral_errors: np.ndarray
    cross_spectral_errors: np.ndarray
    n_surrogates: int
    max_iterations: int
    tolerance: float
    random_state: int | None
    provenance: Mapping[str, Any] = field(default_factory=dict)

    @property
    def n_time(self) -> int:
        return self.surrogates.shape[1]

    @property
    def n_dimensions(self) -> int:
        return self.surrogates.shape[2]


@dataclass(frozen=True)
class MultivariateSurrogateNonlinearityResult:
    """Monte Carlo nonlinear-statistic test using multivariate IAAFT surrogates."""

    observed_statistic: float
    surrogate_statistics: np.ndarray
    p_value: float
    alternative: str
    statistic: str
    surrogate_result: MultivariateIAAFTResult
    provenance: Mapping[str, Any] = field(default_factory=dict)

    @property
    def n_surrogates(self) -> int:
        return self.surrogate_result.n_surrogates


@dataclass(frozen=True)
class SurrogateNonlinearityResult:
    """Monte Carlo surrogate-data test for a declared nonlinear statistic."""

    observed_statistic: float
    surrogate_statistics: np.ndarray
    p_value: float
    alternative: str
    statistic: str
    method: str
    n_surrogates: int
    random_state: int | None
    convergence_iterations: np.ndarray
    spectral_errors: np.ndarray
    provenance: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PoincareCrossingResult:
    """Interpolated crossings of an explicitly declared Poincare section."""

    states: np.ndarray
    times: np.ndarray
    left_indices: np.ndarray
    fractions: np.ndarray
    curve_id: str
    section_dimension: str
    section_value: float
    direction: str
    state_dimensions: tuple[str, ...]
    provenance: Mapping[str, Any] = field(default_factory=dict)

    @property
    def n_crossings(self) -> int:
        return self.states.shape[0]


@dataclass(frozen=True)
class LocalReturnMapResult:
    """Local affine return-map fit around an explicitly declared reference state."""

    reference_state: np.ndarray
    selected_transition_indices: np.ndarray
    jacobian: np.ndarray
    intercept: np.ndarray
    residuals: np.ndarray
    r_squared: np.ndarray
    design_condition_number: float
    neighborhood_policy: str
    neighborhood_value: float | int
    provenance: Mapping[str, Any] = field(default_factory=dict)

    @property
    def n_transitions(self) -> int:
        return self.selected_transition_indices.size


@dataclass(frozen=True)
class ReturnMapStabilityResult:
    """Eigenvalue-based local return-map contraction/expansion diagnostic."""

    eigenvalues: np.ndarray
    spectral_radius: float
    classification: str
    tolerance: float
    provenance: Mapping[str, Any] = field(default_factory=dict)
