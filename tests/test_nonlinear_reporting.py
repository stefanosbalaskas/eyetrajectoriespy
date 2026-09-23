import numpy as np

from eyetrajectoriespy import (
    KantzDivergenceResult,
    LargestLyapunovResult,
    LocalDivergenceResult,
    LocalReturnMapResult,
    RecurrenceResult,
    RQAResult,
    ReturnMapStabilityResult,
    SurrogateNonlinearityResult,
    WindowedRQAResult,
    largest_lyapunov_reporting_text,
    return_map_stability_reporting_text,
    rqa_reporting_text,
    surrogate_nonlinearity_reporting_text,
    windowed_rqa_reporting_text,
)
from scipy.sparse import csr_matrix
import pandas as pd


def test_reporting_helpers_preserve_scope_language():
    recurrence = RecurrenceResult(
        matrix=csr_matrix((5, 5), dtype=bool),
        time_a=np.arange(5.0),
        time_b=np.arange(5.0),
        source_curve_ids=("c",),
        radius=0.25,
        target_recurrence_rate=None,
        achieved_recurrence_rate=0.1,
        metric="euclidean",
        theiler_window_samples=2,
        kind="auto",
        state_dimension=2,
        provenance={"radius_policy": "fixed"},
    )
    metrics = RQAResult(
        recurrence_rate=0.1,
        determinism=0.5,
        mean_diagonal_length=2.0,
        max_diagonal_length=3,
        diagonal_entropy=0.2,
        laminarity=0.4,
        trapping_time=2.5,
        max_vertical_length=4,
        center_of_recurrence_mass=30.0,
        n_recurrence_points=10,
        n_diagonal_lines=2,
        n_vertical_lines=2,
        min_diagonal_length=2,
        min_vertical_length=2,
    )
    text = rqa_reporting_text(recurrence, metrics)
    assert "fixed radius" in text
    assert "Theiler window" in text
    assert "DET" in text

    dynamic = WindowedRQAResult(
        table=pd.DataFrame({"center_time": [1.0, 2.0]}),
        window_samples=100,
        step_samples=50,
        dropped_tail_samples=7,
        time_unit="s",
    )
    assert "7 samples" in windowed_rqa_reporting_text(dynamic)

    divergence = LocalDivergenceResult(
        horizons=np.arange(5),
        time_lags=np.arange(5, dtype=float) * 0.01,
        mean_log_divergence=np.linspace(-2, 0, 5),
        pair_counts=np.full(5, 20),
        zero_distance_counts=np.zeros(5, dtype=int),
        nearest_neighbor_indices=np.arange(20),
        theiler_window_samples=4,
        max_horizon_samples=4,
        curve_id="c",
        time_unit="s",
    )
    lle = LargestLyapunovResult(
        exponent=2.0,
        exponent_unit="1/s",
        intercept=-2.0,
        r_squared=0.95,
        standard_error=0.1,
        fit_start=0.01,
        fit_end=0.04,
        n_fit_points=4,
        divergence=divergence,
    )
    lle_text = largest_lyapunov_reporting_text(lle)
    assert "not as standalone evidence of deterministic chaos" in lle_text

    kantz_divergence = KantzDivergenceResult(
        horizons=np.arange(5),
        time_lags=np.arange(5, dtype=float) * 0.01,
        mean_log_divergence=np.linspace(-2, 0, 5),
        reference_counts=np.full(5, 10),
        pair_counts=np.full(5, 40),
        zero_mean_neighborhood_counts=np.zeros(5, dtype=int),
        initial_neighbor_counts=np.full(20, 4),
        radius=0.08,
        min_neighbors=2,
        theiler_window_samples=4,
        max_horizon_samples=4,
        curve_id="c",
        time_unit="s",
    )
    kantz_lle = LargestLyapunovResult(
        exponent=2.2,
        exponent_unit="1/s",
        intercept=-2.1,
        r_squared=0.94,
        standard_error=0.12,
        fit_start=0.01,
        fit_end=0.04,
        n_fit_points=4,
        divergence=kantz_divergence,
    )
    kantz_text = largest_lyapunov_reporting_text(kantz_lle)
    assert "Kantz fixed-radius neighborhood divergence" in kantz_text
    assert "radius=0.08" in kantz_text
    assert "not as standalone evidence of deterministic chaos" in kantz_text

    surrogate = SurrogateNonlinearityResult(
        observed_statistic=2.0,
        surrogate_statistics=np.array([0.5, 1.0, 1.5]),
        p_value=0.25,
        alternative="greater",
        statistic="largest_lyapunov",
        method="iaaft",
        n_surrogates=3,
        random_state=42,
        convergence_iterations=np.array([10, 11, 12]),
        spectral_errors=np.array([0.01, 0.02, 0.015]),
    )
    surrogate_text = surrogate_nonlinearity_reporting_text(surrogate)
    assert "plus-one Monte Carlo" in surrogate_text
    assert "not as proof" in surrogate_text

    fit = LocalReturnMapResult(
        reference_state=np.array([0.0]),
        selected_transition_indices=np.array([0, 1, 2]),
        jacobian=np.array([[0.8]]),
        intercept=np.array([0.0]),
        residuals=np.zeros((3, 1)),
        r_squared=np.array([0.9]),
        design_condition_number=2.0,
        neighborhood_policy="n_neighbors",
        neighborhood_value=3,
        provenance={
            "crossing_provenance": {
                "section_dimension": "x",
                "section_value": 0.0,
                "direction": "positive",
            }
        },
    )
    stability = ReturnMapStabilityResult(
        eigenvalues=np.array([0.8 + 0j]),
        spectral_radius=0.8,
        classification="contracting",
        tolerance=1e-6,
    )
    return_text = return_map_stability_reporting_text(fit, stability)
    assert "condition number" in return_text
    assert "not interpreted as classical Floquet multipliers" in return_text
