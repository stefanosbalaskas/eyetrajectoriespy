"""Experimental simulation of observed operating characteristics for native F1.

This deliberately invokes the *actual* experimental sparse pooled-PACE group
test at every replicate. It does not import fPASS theoretical power, choose
a recommended sample size, or certify F1's type-I error.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Mapping
import numpy as np
import pandas as pd
from eyetrajectoriespy.types import IrregularTrajectorySet
from .sparse_group_inference import test_sparse_functional_groups

@dataclass(frozen=True)
class FunctionalPowerSimulation:
    cases: pd.DataFrame
    summary: pd.DataFrame
    plan: Mapping[str, Any]
    scientifically_qualified: bool = False
    recommended_sample_size: int | None = None


def _generate_sparse_two_group(
    rng: np.random.Generator,
    *,
    units_per_group: int,
    trials_per_participant: int,
    samples_per_trial: int,
    noise_sd: float,
    effect_amplitude: float,
) -> tuple[IrregularTrajectorySet, list[str], list[str]]:
    time, values, names, participants, labels = [], [], [], [], []
    total = 2 * units_per_group
    for unit in range(total):
        member = f"participant_{unit:04d}"
        condition = "A" if unit < units_per_group else "B"
        latent = rng.normal(size=2)
        for trial in range(trials_per_participant):
            grid = np.r_[0.0, np.sort(rng.uniform(.02, .98, samples_per_trial-2)), 1.0]
            base = np.column_stack((
                .45 + .06*latent[0]*np.sin(np.pi*grid)
                  + .04*latent[1]*np.cos(2*np.pi*grid),
                .5 + .05*latent[0]*np.cos(np.pi*grid)
                  + .045*latent[1]*np.sin(2*np.pi*grid),
            ))
            if condition == "B":
                base += effect_amplitude * np.column_stack((
                    np.sin(np.pi * grid),
                    -.5 * np.cos(np.pi*grid)
                ))
            base += rng.normal(scale=noise_sd, size=base.shape)
            time.append(grid)
            values.append(base)
            names.append(f"{member}_trial_{trial:02d}")
            participants.append(member)
            labels.append(condition)
    data = IrregularTrajectorySet(
        time=tuple(time), values=tuple(values), curve_ids=tuple(names),
        dimension_names=("x", "y"), coordinate_system="normalized",
        time_unit="s",
        metadata=pd.DataFrame({"participant_id": participants,
                               "group": labels}),
        provenance={"source": "simulated_known_truth",
                    "effect_amplitude": effect_amplitude,
                    "noise_sd": noise_sd},
    )
    return data, labels, participants


def simulate_functional_study_power(
    *,
    units_per_group: int,
    n_replicates: int,
    samples_per_trial: int = 19,
    trials_per_participant: int = 1,
    noise_sd: float = .012,
    effect_amplitude: float = .08,
    n_permutations: int = 99,
    fit_kwargs: Mapping[str, Any] | None = None,
    random_state: int = 2026,
) -> FunctionalPowerSimulation:
    """Known-truth null and alternative with fresh native sparse fit per draw.

    Retains *all* fit exceptions in cases; rejection fractions among successful
    fits are conditional results and cannot establish valid power when fitting
    is selective. No sample-size recommendation is issued.
    """
    if isinstance(units_per_group, bool) or not isinstance(units_per_group, int) or units_per_group < 4:
        raise ValueError("at least four independent units per group")
    if isinstance(n_replicates, bool) or not isinstance(n_replicates, int) or n_replicates < 2:
        raise ValueError("at least two simulation replicates per scenario")
    if not isinstance(samples_per_trial, int) or samples_per_trial < 7:
        raise ValueError("at least seven observation times per trial")
    if not isinstance(trials_per_participant, int) or trials_per_participant < 1:
        raise ValueError("positive trials_per_participant required")
    if not isinstance(n_permutations, int) or n_permutations < 99:
        raise ValueError("at least 99 permutations required")
    if not np.isfinite(effect_amplitude) or effect_amplitude <= 0:
        raise ValueError("positive effect_amplitude required")
    if not np.isfinite(noise_sd) or noise_sd <= 0:
        raise ValueError("positive noise_sd required")
    settings = dict(fit_kwargs) if fit_kwargs is not None else {
        "n_components": 2,
        "evaluation_grid": np.linspace(0.0, 1.0, 21),
        "mean_bandwidth": .3,
        "covariance_bandwidth": .45,
        "measurement_error": "diagonal",
        "measurement_error_variance": (noise_sd**2, noise_sd**2),
        "psd_action": "project",
        "score_failure_action": "retain_nan",
    }
    rng = np.random.default_rng(random_state)
    rows = []
    for scenario, magnitude in (("null", 0.0), ("alternative", effect_amplitude)):
        for iteration in range(n_replicates):
            fixture_seed = int(rng.integers(0, 2**31 - 1))
            data_rng = np.random.default_rng(fixture_seed)
            gaze, labels, unit_ids = _generate_sparse_two_group(
                data_rng, units_per_group=units_per_group,
                trials_per_participant=trials_per_participant,
                samples_per_trial=samples_per_trial, noise_sd=noise_sd,
                effect_amplitude=magnitude,
            )
            row = {"scenario": scenario, "iteration": iteration,
                   "seed": fixture_seed, "effect": magnitude, "status": "failed",
                   "p_value": np.nan, "statistic": np.nan,
                   "exception_type": None, "reason": None}
            try:
                test = test_sparse_functional_groups(
                    gaze, labels, unit_ids=unit_ids, fit_kwargs=settings,
                    n_permutations=n_permutations, random_state=fixture_seed,
                )
                row.update(status="ok", p_value=test.p_value,
                           statistic=test.statistic)
            except Exception as err:
                row["exception_type"] = type(err).__name__
                row["reason"] = str(err)[:500]
            rows.append(row)
    frame = pd.DataFrame(rows)
    summary = []
    for name in ("null", "alternative"):
        sub = frame.loc[frame.scenario == name]
        ok = sub.loc[sub.status == "ok"]
        rejection_rate = (
            float((ok.p_value <= .05).mean()) if len(ok) else np.nan
        )
        summary.append({
            "scenario": name, "n_attempted": len(sub), "n_fit_success": len(ok),
            "n_fit_failed": len(sub)-len(ok),
            "fraction_reject_005_given_fit": rejection_rate,
            "mc_se_conditional": (
                float(np.sqrt(rejection_rate*(1-rejection_rate)/len(ok)))
                if len(ok) else np.nan
            ),
            "null_size_qualified": False,
            "power_qualified": False,
        })
    return FunctionalPowerSimulation(
        cases=frame, summary=pd.DataFrame(summary),
        plan={
            "actual_test": "pooled_PACE_conditional_unit_permutation_F1_experimental",
            "units_per_group": units_per_group,
            "trials_per_participant": trials_per_participant,
            "sampling_density": samples_per_trial,
            "effect_amplitude": effect_amplitude, "noise_sd": noise_sd,
            "n_replicates": n_replicates, "n_permutations": n_permutations,
            "simulation_seed": random_state,
            "fit_failures_retained": True,
            "not_fPASS_theoretical_power": True,
            "power_is_descriptive_conditional_on_fit": True,
            "reference_population_qualified": False,
        },
    )
