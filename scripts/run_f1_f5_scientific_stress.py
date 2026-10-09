"""Research-only F1 full-fit and F5 dependent-null stress programme.

F1 refits the ACTUAL sparse PACE group test; conditional estimates exclude failed
fits and must always be read alongside failure counts.
F5 tests ordered whole-curves under stationary AR dependence, block sensitivity
and two-break alternatives. No nominal significance calibration is claimed.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
import pandas as pd

from eyetrajectoriespy.research import (
    detect_ordered_functional_changepoint,
    simulate_functional_study_power,
)
from eyetrajectoriespy.types import TrajectorySet
from eyetrajectoriespy.research.calibration_seed import (calibration_replicate_seed, calibration_manifest)


F1_DESIGNS = {
    "balanced_equal_covariance": dict(units_per_group=8, other_group_size=8,
                                      group_noise_multiplier=1., samples_per_trial=17,
                                      trials_per_participant=1),
    "unequal_heteroscedastic_null": dict(units_per_group=8, other_group_size=16,
                                        group_noise_multiplier=2., samples_per_trial=17,
                                        trials_per_participant=1),
    "clustered_two_trials": dict(units_per_group=8, other_group_size=8,
                                 group_noise_multiplier=1., samples_per_trial=17,
                                 trials_per_participant=2),
    "very_sparse": dict(units_per_group=8, other_group_size=8,
                         group_noise_multiplier=1., samples_per_trial=9,
                         trials_per_participant=1),
}
F5_SCENARIOS = {
    "iid_gaussian": dict(phi=0., heavy_tail=False),
    "weak_AR1": dict(phi=.35, heavy_tail=False),
    "strong_AR1": dict(phi=.8, heavy_tail=False),
    "iid_heavy_tail": dict(phi=0., heavy_tail=True),
}


def _wilson(p: pd.Series, alpha: float) -> dict:
    good = p.dropna().to_numpy(dtype=float)
    n = len(good)
    if not n:
        return {"n_success": 0, "rejections": 0, "rate": None, "mc_se": None,
                "wilson_95_interval": None}
    k = int(np.count_nonzero(good <= alpha))
    rate = k/n
    z = 1.959963984540054
    denom = 1 + z*z/n
    center = (rate + z*z/(2*n))/denom
    radius = (z/denom)*np.sqrt(rate*(1-rate)/n + z*z/(4*n*n))
    return {"n_success": n, "rejections": k, "rate": rate,
            "mc_se": float(np.sqrt(rate*(1-rate)/n)),
            "wilson_95_interval": [float(max(0., center-radius)),
                                   float(min(1., center+radius))]}


def _ordered_fixture(seed: int, scenario: str, change: str) -> TrajectorySet:
    """Fixed marginal innovation variance; dependence varies separately."""
    spec = F5_SCENARIOS[scenario]
    rng = np.random.default_rng(seed)
    n, grid_size = 36, 17
    t = np.linspace(0, 1, grid_size)
    shape = (n, grid_size, 2)
    if spec["heavy_tail"]:
        innovation = rng.standard_t(5, size=shape)*(.07/np.sqrt(5/3))
    else:
        innovation = rng.normal(0, .07, shape)
    phi = spec["phi"]
    curves = np.empty_like(innovation)
    curves[0] = innovation[0]
    for i in range(1, n):
        curves[i] = phi*curves[i-1]+np.sqrt(1-phi**2)*innovation[i]
    signal = .17*np.sin(np.pi*t)
    if change == "one_break":
        curves[18:, :, 0] += signal
    elif change == "two_breaks":
        curves[12:24, :, 0] += signal
    elif change != "null":
        raise ValueError("change must be null, one_break or two_breaks")
    return TrajectorySet(
        time=t, values=curves, curve_ids=tuple(f"c{i}" for i in range(n)),
        dimension_names=("x","y"), coordinate_system="normalized",
        time_unit="s", provenance={"synthetic":True,
        "ordered_curve_AR_parameter":phi, "change":change},
    )


def f1_study(replicates: int, permutations: int, seed: int, *, shard_id: int = 0) -> tuple[pd.DataFrame, list[dict]]:
    frames = []
    results = []
    for name, kwargs in F1_DESIGNS.items():
        design_seed=calibration_replicate_seed("F1",master_seed=seed,
            shard_id=shard_id,scenario=name,replicate=0)
        result = simulate_functional_study_power(
            n_replicates=replicates, effect_amplitude=.11, noise_sd=.015,
            n_permutations=permutations, random_state=design_seed, **kwargs)
        one = result.cases.copy()
        one["design"] = name
        one["shard_id"] = shard_id
        frames.append(one)
        for case in ("null", "alternative"):
            rows = one.loc[one.scenario == case]
            good = rows.loc[rows.status=="ok"]
            results.append({
                "design": name, "scenario": case, "attempts": len(rows),
                "failed_fits": len(rows)-len(good),
                "p_value_summary": _wilson(good.p_value, .05),
                "type_one_qualified":False, "power_qualified":False,
            })
    return pd.concat(frames, ignore_index=True), results


def f5_study(replicates: int, draws: int, seed: int, *, shard_id: int = 0) -> tuple[pd.DataFrame, list[dict]]:
    rows = []
    for scenario, spec in F5_SCENARIOS.items():
        dependence = "independent" if spec["phi"] == 0 else "weak_block"
        blocks = [None] if dependence == "independent" else [2, 4, 8]
        for block in blocks:
            for case in ("null", "one_break", "two_breaks"):
                for rep in range(replicates):
                    simulation_seed = calibration_replicate_seed(
                        "F5",master_seed=seed,shard_id=shard_id,
                        scenario=f"{scenario}|block{block}|{case}",replicate=rep)
                    item = dict(scenario=scenario, phi=spec["phi"],
                                block_length=block, change=case,
                                replicate=rep, seed=simulation_seed,
                                shard_id=shard_id,
                                status="failed", p_value=np.nan,
                                detected_split=np.nan, exception_type=None,
                                exception=None)
                    try:
                        trial = _ordered_fixture(simulation_seed, scenario, case)
                        fit = detect_ordered_functional_changepoint(
                            trial, dependence=dependence, block_length=block,
                            min_segment=6, n_bootstrap=draws,
                            random_state=simulation_seed+1001)
                        item.update(status="ok", p_value=fit.p_value_experimental,
                                    detected_split=fit.split_index)
                    except Exception as exc:
                        item["exception_type"] = type(exc).__name__
                        item["exception"] = str(exc)[:500]
                    rows.append(item)
    frame = pd.DataFrame(rows)
    summary = []
    for (scenario, block, case), group in frame.groupby(
        ["scenario", "block_length", "change"], dropna=False
    ):
        good = group.loc[group.status=="ok"]
        summary.append({
            "scenario":scenario,
            "block_length": None if pd.isna(block) else int(block),
            "change":case, "attempts":len(group),
            "failed_fits":len(group)-len(good),
            "p_value_summary":_wilson(good.p_value,.05),
            "scientific_size_or_power_qualified":False,
            "multiple_break_identification_qualified":False,
        })
    return frame, summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--f1-replicates", type=int, default=8)
    parser.add_argument("--master-seed",type=int,default=622014)
    parser.add_argument("--shard-id",type=int,default=0)
    parser.add_argument("--f1-permutations", type=int, default=199)
    parser.add_argument("--f5-replicates", type=int, default=25)
    parser.add_argument("--f5-bootstrap", type=int, default=199)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    if (args.f1_replicates < 2 or args.f5_replicates < 2 or
        args.f1_permutations < 99 or args.f5_bootstrap < 99):
        raise ValueError("at least 2 refits and 99 randomization draws are required")
    f1_cases, f1_summary = f1_study(args.f1_replicates, args.f1_permutations,
        args.master_seed,shard_id=args.shard_id)
    f5_cases, f5_summary = f5_study(args.f5_replicates, args.f5_bootstrap,
        args.master_seed,shard_id=args.shard_id)
    args.out.mkdir(parents=True, exist_ok=True)
    f1_cases.to_csv(args.out/"f1-cases.csv", index=False)
    f5_cases.to_csv(args.out/"f5-cases.csv", index=False)
    (args.out/"manifest.json").write_text(json.dumps(calibration_manifest(
        "F1_F5",master_seed=args.master_seed,shard_id=args.shard_id,
        records_per_scenario=args.f1_replicates,
        case_files=("f1-cases.csv","f5-cases.csv")),
        sort_keys=True,indent=2)+"\n")
    evidence = {
        "schema_version":1, "programme":"F1_full_fit_F5_ordered_functional_stress",
        "master_seed":args.master_seed,"shard_id":args.shard_id,
        "F1_test_is_real_native_PACE_pipeline":True,
        "F1_null_conditions_include_nonexchangeable_heteroscedastic_design":True,
        "F5_depends_on_declared_block_length":True,
        "F5_multiple_break_data_does_not_imply_multiple_break_estimator":True,
        "conditional_rejection_excludes_failure_and_is_not_unconditional_size":True,
        "f1":f1_summary, "f5":f5_summary,
        "f1_n_fit_attempts":len(f1_cases),
        "f1_fit_failures":int((f1_cases.status=="failed").sum()),
        "f5_n_fit_attempts":len(f5_cases),
        "f5_fit_failures":int((f5_cases.status=="failed").sum()),
        "null_size_scientifically_qualified":False,
        "power_scientifically_qualified":False,
        "release_authorized":False,
    }
    target=args.out/"evidence.json"
    target.write_text(json.dumps(evidence, indent=2, sort_keys=True)+"\n")
    (args.out/"sha256.txt").write_text("".join(
        sha256(file.read_bytes()).hexdigest()+"  "+file.name+"\n"
        for file in sorted(args.out.iterdir()) if file.name!="sha256.txt"))
    print(json.dumps({
        "f1_attempts":len(f1_cases),
        "f1_failures":evidence["f1_fit_failures"],
        "f5_attempts":len(f5_cases),
        "f5_failures":evidence["f5_fit_failures"],
        "scientifically_qualified":False}, sort_keys=True))


if __name__=="__main__":
    main()
