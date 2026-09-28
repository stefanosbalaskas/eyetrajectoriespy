"""Declared qualification and stress scenarios for 0.11 recovery studies."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import numpy as np
import pandas as pd

from .simulate import (
    FunctionalSimulationScenario,
    functional_simulation_scenario_frame,
)


def _labels(
    *,
    role: str,
    target: str,
    description: str,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    labels = {
        "matrix_role": role,
        "scientific_target": target,
        "description": description,
        "automatic_thresholds": role == "qualification",
    }
    if extra:
        labels.update(dict(extra))
    return labels


def functional_recovery_qualification_scenarios(
    *,
    replicates: int = 3,
    seed_start: int = 202800,
) -> tuple[FunctionalSimulationScenario, ...]:
    """Return the small deterministic recovery suite intended for CI gates.

    The scenarios declare data generation only. Estimator settings and
    qualification thresholds remain separate validation contracts.
    """

    if replicates < 1:
        raise ValueError("replicates must be positive")
    if not isinstance(seed_start, (int, np.integer)):
        raise TypeError("seed_start must be an integer")

    return (
        FunctionalSimulationScenario(
            name="dense_gaussian",
            truth_grid=np.linspace(0.0, 1.0, 81),
            eigenvalues=(1.0, 0.35),
            n_participants=200,
            measurement_noise_sd=0.05,
            replicates=replicates,
            seed_start=seed_start,
            labels=_labels(
                role="qualification",
                target="fpca",
                description=(
                    "Dense Gaussian FPCA population/subspace/score recovery."
                ),
            ),
        ),
        FunctionalSimulationScenario(
            name="dense_student_t",
            truth_grid=np.linspace(0.0, 1.0, 81),
            eigenvalues=(1.0, 0.35),
            n_participants=200,
            measurement_noise_sd=0.05,
            score_distribution="student_t",
            score_df=6.0,
            replicates=replicates,
            seed_start=seed_start + 100,
            labels=_labels(
                role="qualification",
                target="fpca",
                description=(
                    "Dense variance-matched Student-t FPCA recovery."
                ),
            ),
        ),
        FunctionalSimulationScenario(
            name="native_sparse",
            truth_grid=np.linspace(0.0, 1.0, 31),
            eigenvalues=(1.0, 0.35),
            n_participants=64,
            observation_design="irregular",
            samples_per_curve=(8, 12),
            irregular_time_design="uniform",
            measurement_noise_sd=0.08,
            replicates=replicates,
            seed_start=seed_start + 200,
            labels=_labels(
                role="qualification",
                target="sparse_fpca_pace",
                description=(
                    "Native irregular sparse FPCA/PACE recovery. "
                    "Fixed-noise and estimated-noise fits are distinct "
                    "estimator contracts over the same generating regime."
                ),
            ),
        ),
        FunctionalSimulationScenario(
            name="hierarchy_sources",
            truth_grid=np.linspace(0.0, 1.0, 31),
            eigenvalues=(1.0, 0.35),
            n_participants=300,
            trials_per_participant=2,
            participant_eigenvalues=(0.20, 0.08),
            trial_eigenvalues=(0.10, 0.04),
            measurement_noise_sd=0.0,
            replicates=replicates,
            seed_start=seed_start + 300,
            labels=_labels(
                role="qualification",
                target="hierarchy_truth",
                description=(
                    "Finite-sample audit of separately declared curve, "
                    "participant, and trial score-source variances."
                ),
            ),
        ),
    )


def functional_recovery_stress_scenarios(
    *,
    replicates: int = 10,
    seed_start: int = 204000,
) -> tuple[FunctionalSimulationScenario, ...]:
    """Return named descriptive stress regimes with no automatic thresholds."""

    if replicates < 1:
        raise ValueError("replicates must be positive")
    if not isinstance(seed_start, (int, np.integer)):
        raise TypeError("seed_start must be an integer")

    grid = np.linspace(0.0, 1.0, 41)
    cases = (
        FunctionalSimulationScenario(
            name="stress_very_sparse",
            truth_grid=grid,
            eigenvalues=(1.0, 0.35),
            n_participants=100,
            observation_design="irregular",
            samples_per_curve=(3, 5),
            measurement_noise_sd=0.08,
            replicates=replicates,
            seed_start=seed_start,
            labels=_labels(
                role="stress",
                target="sparse_fpca_pace",
                description="Very sparse native curves with only 3-5 samples.",
            ),
        ),
        FunctionalSimulationScenario(
            name="stress_unequal_sample_counts",
            truth_grid=grid,
            eigenvalues=(1.0, 0.35),
            n_participants=100,
            observation_design="irregular",
            samples_per_curve=(3, 20),
            measurement_noise_sd=0.08,
            replicates=replicates,
            seed_start=seed_start + 100,
            labels=_labels(
                role="stress",
                target="sparse_fpca_pace",
                description="Strongly unequal per-curve sample counts.",
            ),
        ),
        FunctionalSimulationScenario(
            name="stress_center_clustered_times",
            truth_grid=grid,
            eigenvalues=(1.0, 0.35),
            n_participants=100,
            observation_design="irregular",
            samples_per_curve=(8, 12),
            irregular_time_design="center_clustered",
            measurement_noise_sd=0.08,
            replicates=replicates,
            seed_start=seed_start + 200,
            labels=_labels(
                role="stress",
                target="sparse_fpca_pace",
                description="Nonuniform observation times concentrated centrally.",
            ),
        ),
        FunctionalSimulationScenario(
            name="stress_boundary_poor_times",
            truth_grid=grid,
            eigenvalues=(1.0, 0.35),
            n_participants=100,
            observation_design="irregular",
            samples_per_curve=(8, 12),
            irregular_time_design="boundary_poor",
            measurement_noise_sd=0.08,
            replicates=replicates,
            seed_start=seed_start + 300,
            labels=_labels(
                role="stress",
                target="sparse_fpca_pace",
                description="Observation schedules with weak boundary coverage.",
            ),
        ),
        FunctionalSimulationScenario(
            name="stress_estimated_noise_diagonal_difference",
            truth_grid=grid,
            eigenvalues=(1.0, 0.35),
            n_participants=120,
            observation_design="irregular",
            samples_per_curve=(10, 14),
            irregular_time_design="uniform",
            measurement_noise_sd=0.10,
            replicates=replicates,
            seed_start=seed_start + 350,
            labels=_labels(
                role="stress",
                target="sparse_fpca_pace_estimated_noise",
                description=(
                    "Diagonal-difference measurement-noise estimation. "
                    "The initial seeded qualification probe retained strong "
                    "subspace/score recovery but showed very large noise-"
                    "variance error, so this regime is descriptive rather "
                    "than CI-qualified."
                ),
            ),
        ),
        FunctionalSimulationScenario(
            name="stress_high_measurement_noise",
            truth_grid=grid,
            eigenvalues=(1.0, 0.35),
            n_participants=120,
            observation_design="irregular",
            samples_per_curve=(8, 12),
            measurement_noise_sd=0.20,
            replicates=replicates,
            seed_start=seed_start + 400,
            labels=_labels(
                role="stress",
                target="sparse_fpca_pace",
                description="High measurement noise relative to latent variation.",
            ),
        ),
        FunctionalSimulationScenario(
            name="stress_nearly_tied_eigenvalues",
            truth_grid=grid,
            eigenvalues=(1.0, 0.90),
            n_participants=160,
            measurement_noise_sd=0.05,
            replicates=replicates,
            seed_start=seed_start + 500,
            labels=_labels(
                role="stress",
                target="fpca_subspace",
                description=(
                    "Nearly tied leading eigenvalues; subspace metrics are "
                    "primary and individual eigenfunctions are unstable."
                ),
            ),
        ),
        FunctionalSimulationScenario(
            name="stress_heavy_tailed_scores",
            truth_grid=grid,
            eigenvalues=(1.0, 0.35),
            n_participants=160,
            measurement_noise_sd=0.05,
            score_distribution="student_t",
            score_df=4.0,
            replicates=replicates,
            seed_start=seed_start + 600,
            labels=_labels(
                role="stress",
                target="fpca",
                description="Variance-matched heavy-tailed functional scores.",
            ),
        ),
        FunctionalSimulationScenario(
            name="stress_participant_heavy_hierarchy",
            truth_grid=grid,
            eigenvalues=(1.0, 0.35),
            n_participants=120,
            trials_per_participant=4,
            participant_eigenvalues=(0.60, 0.20),
            trial_eigenvalues=(0.05, 0.02),
            measurement_noise_sd=0.03,
            replicates=replicates,
            seed_start=seed_start + 700,
            labels=_labels(
                role="stress",
                target="functional_mixed_effects",
                description="Participant-dominant hierarchical variation.",
            ),
        ),
        FunctionalSimulationScenario(
            name="stress_trial_heavy_hierarchy",
            truth_grid=grid,
            eigenvalues=(1.0, 0.35),
            n_participants=120,
            trials_per_participant=4,
            participant_eigenvalues=(0.05, 0.02),
            trial_eigenvalues=(0.60, 0.20),
            measurement_noise_sd=0.03,
            replicates=replicates,
            seed_start=seed_start + 800,
            labels=_labels(
                role="stress",
                target="functional_mixed_effects",
                description="Trial-dominant hierarchical variation.",
            ),
        ),
        FunctionalSimulationScenario(
            name="stress_phase_variation",
            truth_grid=grid,
            eigenvalues=(1.0, 0.35),
            n_participants=120,
            measurement_noise_sd=0.03,
            phase_variation={"kind": "power", "sd": 0.20},
            replicates=replicates,
            seed_start=seed_start + 900,
            labels=_labels(
                role="stress",
                target="registration_phase",
                description="Substantial endpoint-preserving phase variation.",
            ),
        ),
        FunctionalSimulationScenario(
            name="stress_mcar_missingness",
            truth_grid=grid,
            eigenvalues=(1.0, 0.35),
            n_participants=120,
            measurement_noise_sd=0.05,
            missingness={"kind": "mcar", "probability": 0.20},
            replicates=replicates,
            seed_start=seed_start + 1000,
            labels=_labels(
                role="stress",
                target="missing_data_workflow",
                description="MCAR sample missingness.",
            ),
        ),
        FunctionalSimulationScenario(
            name="stress_block_missingness",
            truth_grid=grid,
            eigenvalues=(1.0, 0.35),
            n_participants=120,
            measurement_noise_sd=0.05,
            missingness={"kind": "block", "fraction": 0.20},
            replicates=replicates,
            seed_start=seed_start + 1100,
            labels=_labels(
                role="stress",
                target="missing_data_workflow",
                description="Structured contiguous-block missingness.",
            ),
        ),
        FunctionalSimulationScenario(
            name="stress_correlated_multichannel_noise",
            truth_grid=grid,
            eigenvalues=(1.0, 0.35),
            n_participants=160,
            dimension_names=("x", "y"),
            measurement_noise_sd=None,
            measurement_noise_covariance=np.array(
                [[0.04, 0.018], [0.018, 0.09]],
                dtype=float,
            ),
            replicates=replicates,
            seed_start=seed_start + 1200,
            labels=_labels(
                role="stress",
                target="mfpca",
                description="Correlated two-channel measurement noise.",
            ),
        ),
    )
    return cases


def functional_recovery_scenario_catalog_frame(
    *,
    qualification_replicates: int = 3,
    stress_replicates: int = 10,
) -> pd.DataFrame:
    """Return qualification and stress designs in one descriptive table."""

    scenarios = (
        functional_recovery_qualification_scenarios(
            replicates=qualification_replicates,
        )
        + functional_recovery_stress_scenarios(
            replicates=stress_replicates,
        )
    )
    frame = functional_simulation_scenario_frame(scenarios)
    roles = [
        dict(scenario.labels).get("matrix_role")
        for scenario in scenarios
    ]
    targets = [
        dict(scenario.labels).get("scientific_target")
        for scenario in scenarios
    ]
    descriptions = [
        dict(scenario.labels).get("description")
        for scenario in scenarios
    ]
    frame.insert(1, "matrix_role", roles)
    frame.insert(2, "scientific_target", targets)
    frame.insert(3, "description", descriptions)
    return frame
