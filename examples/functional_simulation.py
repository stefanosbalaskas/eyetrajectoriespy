"""Executable native functional-simulation example."""

import numpy as np

from eyetrajectoriespy import (
    functional_simulation_reporting_text,
    functional_simulation_truth_frame,
    simulate_functional_process,
)


def mean(time):
    time = np.asarray(time, dtype=float)
    return 0.25 + 0.30 * time


def phi1(time):
    time = np.asarray(time, dtype=float)
    return np.sqrt(2.0) * np.sin(np.pi * time)


def phi2(time):
    time = np.asarray(time, dtype=float)
    return np.sqrt(2.0) * np.sin(2.0 * np.pi * time)


simulation = simulate_functional_process(
    mean=mean,
    eigenfunctions=(phi1, phi2),
    eigenvalues=(1.0, 0.35),
    truth_grid=np.linspace(0.0, 1.0, 81),
    n_participants=12,
    trials_per_participant=2,
    observation_design="irregular",
    samples_per_curve=(7, 12),
    irregular_time_design="center_clustered",
    participant_eigenvalues=(0.20, 0.05),
    trial_eigenvalues=(0.10, 0.02),
    measurement_noise_sd=0.05,
    missingness={"kind": "mcar", "probability": 0.08},
    phase_variation={"kind": "power", "sd": 0.12},
    random_state=1101,
)

audit = functional_simulation_truth_frame(simulation)
assert len(audit) == simulation.observations.n_curves
assert (
    audit["n_pre_missing_samples"]
    - audit["n_missing_by_design"]
    == audit["n_observed_samples"]
).all()
assert simulation.truth.provenance[
    "raw_dense_to_irregular_interpolation_performed"
] is False

print(functional_simulation_reporting_text(simulation))
print(
    audit[
        [
            "curve_id",
            "participant_id",
            "trial_id",
            "n_observed_samples",
            "n_missing_by_design",
            "max_phase_displacement",
        ]
    ].head()
)
