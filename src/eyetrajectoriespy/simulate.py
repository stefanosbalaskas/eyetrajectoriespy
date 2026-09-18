"""Deterministic synthetic trajectory generators for examples and tests."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .types import TrajectorySet


def simulate_planar_trajectories(
    *,
    n_participants: int = 20,
    trials_per_participant: int = 6,
    n_time: int = 121,
    duration: float = 2.0,
    random_state: int = 42,
) -> TrajectorySet:
    """Simulate repeated 2-D gaze paths with known participant/trial variation."""
    if n_participants < 2 or trials_per_participant < 1 or n_time < 5 or duration <= 0:
        raise ValueError("Use at least 2 participants, 1 trial each, 5 time points, and positive duration")
    rng = np.random.default_rng(random_state)
    time = np.linspace(0.0, duration, n_time)
    u = time / duration
    n = n_participants * trials_per_participant
    values = np.empty((n, n_time, 2), dtype=float)
    rows = []
    ids = []
    index = 0
    for participant in range(n_participants):
        p_shift = rng.normal(0.0, 0.025, size=2)
        p_phase = rng.normal(0.0, 0.035)
        p_amp = rng.normal(1.0, 0.07)
        for trial in range(trials_per_participant):
            condition = "evidence_prompt" if trial % 2 else "control"
            prompt = 1.0 if condition == "evidence_prompt" else 0.0
            phase = np.clip(u + p_phase + rng.normal(0, 0.018), 0, 1)
            evidence_gate = 1 / (1 + np.exp(-(phase - (0.38 - 0.04 * prompt)) / 0.055))
            decision_gate = 1 / (1 + np.exp(-(phase - 0.73) / 0.07))
            x = 0.50 + (0.26 + 0.05 * prompt) * p_amp * evidence_gate - 0.17 * decision_gate
            y = 0.50 - 0.17 * p_amp * evidence_gate + 0.27 * decision_gate
            x += p_shift[0] + 0.012 * np.sin(2 * np.pi * phase) + rng.normal(0, 0.008, n_time)
            y += p_shift[1] + 0.010 * np.cos(2 * np.pi * phase) + rng.normal(0, 0.008, n_time)
            values[index, :, 0] = np.clip(x, 0.0, 1.0)
            values[index, :, 1] = np.clip(y, 0.0, 1.0)
            ids.append(f"P{participant + 1:03d}|T{trial + 1:02d}")
            rows.append({
                "participant_id": f"P{participant + 1:03d}",
                "trial_id": trial + 1,
                "condition": condition,
                "latent_participant_amplitude": p_amp,
            })
            index += 1
    return TrajectorySet(
        time=time,
        values=values,
        curve_ids=tuple(ids),
        dimension_names=("x", "y"),
        metadata=pd.DataFrame(rows),
        coordinate_system="normalized",
        time_unit="s",
        provenance={"source": "simulate_planar_trajectories", "random_state": random_state, "synthetic": True},
    )


def simulate_aoi_probability_trajectories(
    *,
    n_curves: int = 80,
    n_time: int = 101,
    n_aoi: int = 4,
    duration: float = 2.0,
    random_state: int = 17,
) -> TrajectorySet:
    """Simulate smooth AOI probability functions that lie on the simplex."""
    if n_curves < 2 or n_time < 5 or n_aoi < 2 or duration <= 0:
        raise ValueError("Use at least 2 curves, 5 time points, 2 AOIs, and positive duration")
    rng = np.random.default_rng(random_state)
    time = np.linspace(0.0, duration, n_time)
    u = time / duration
    centers = np.linspace(0.12, 0.88, n_aoi)
    logits = np.empty((n_curves, n_time, n_aoi), dtype=float)
    for i in range(n_curves):
        shift = rng.normal(0, 0.035)
        participant_bias = rng.normal(0, 0.25, n_aoi)
        for k, center in enumerate(centers):
            logits[i, :, k] = -((u - center - shift) ** 2) / 0.025 + participant_bias[k]
        logits[i] += rng.normal(0, 0.08, size=(n_time, n_aoi))
    logits -= logits.max(axis=2, keepdims=True)
    exp = np.exp(logits)
    probs = exp / exp.sum(axis=2, keepdims=True)
    return TrajectorySet(
        time=time,
        values=probs,
        curve_ids=tuple(f"curve_{i + 1:03d}" for i in range(n_curves)),
        dimension_names=tuple(f"AOI_{i + 1}" for i in range(n_aoi)),
        metadata=pd.DataFrame({"curve_index": np.arange(n_curves)}),
        coordinate_system="probability_simplex",
        time_unit="s",
        provenance={"source": "simulate_aoi_probability_trajectories", "random_state": random_state, "synthetic": True},
    )
