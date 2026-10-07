#!/usr/bin/env python3
"""Evaluate B2 replicated recovery and predeclared tuning sensitivity."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd


def _load_b1():
    path = Path(__file__).with_name(
        "evaluate_bayesian_fpca_comparator.py"
    )
    spec = importlib.util.spec_from_file_location(
        "_b1_bayesian_fpca_evaluator",
        path,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(
            "cannot load B1 comparator evaluator"
        )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


B1 = _load_b1()


def _truthy(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() == "true"


def _status(path: Path) -> dict[str, object]:
    if path.suffix == ".json":
        return json.loads(
            path.read_text(encoding="utf-8")
        )
    frame = pd.read_csv(path)
    if len(frame) != 1:
        raise ValueError(
            f"{path.name} must contain exactly one status row"
        )
    return frame.iloc[0].to_dict()


def _metrics(
    root: Path,
    prefix: str,
    truth: dict[str, object],
) -> dict[str, object]:
    grid = np.asarray(
        truth["truth_grid"],
        dtype=float,
    )
    weights = B1._trap_weights(grid)
    dimensions = tuple(
        str(value)
        for value in truth["dimension_names"]
    )
    curve_ids = tuple(
        str(value)
        for value in truth["curve_ids"]
    )
    truth_functions = np.asarray(
        truth["eigenfunctions"],
        dtype=float,
    )
    truth_scores = np.asarray(
        truth["scores"],
        dtype=float,
    )
    truth_eigenvalues = np.asarray(
        truth["eigenvalues"],
        dtype=float,
    )
    truth_mean = np.asarray(
        truth["mean"],
        dtype=float,
    )
    truth_latent = np.asarray(
        truth["latent_on_truth_grid"],
        dtype=float,
    )
    n_components = truth_eigenvalues.size

    mean = B1._read_mean(
        root / f"{prefix}_mean.csv",
        grid,
        dimensions,
    )
    functions = B1._read_functions(
        root / f"{prefix}_eigenfunctions.csv",
        grid,
        dimensions,
        n_components,
    )
    scores = B1._read_scores(
        root / f"{prefix}_scores.csv",
        curve_ids,
        n_components,
    )
    eigenvalues = B1._read_eigenvalues(
        root / f"{prefix}_eigenvalues.csv",
        n_components,
    )

    functional_cosines = (
        B1.functional_subspace_cosines(
            functions,
            truth_functions,
            weights,
        )
    )
    score_cosines = B1.score_subspace_cosines(
        scores,
        truth_scores,
    )

    return {
        "mean_ise": B1._mean_ise(
            mean,
            truth_mean,
            weights,
        ),
        "reconstruction_ise": (
            B1._reconstruction_ise(
                mean,
                functions,
                scores,
                truth_latent,
                weights,
            )
        ),
        "functional_subspace_min_cosine": float(
            np.min(functional_cosines)
        ),
        "score_subspace_min_cosine": (
            float(np.nanmin(score_cosines))
            if np.any(
                np.isfinite(score_cosines)
            )
            else float("nan")
        ),
        "spectrum_pve_l1_error": B1._pve_l1(
            eigenvalues,
            truth_eigenvalues,
        ),
        "score_failure_rate": float(
            np.mean(
                ~np.all(
                    np.isfinite(scores),
                    axis=1,
                )
            )
        ),
    }


def _method_record(
    root: Path,
    prefix: str,
    truth: dict[str, object],
    status_path: Path,
) -> dict[str, object]:
    if not status_path.exists():
        return {
            "status": "failed",
            "error": (
                f"missing {status_path.name}"
            ),
        }
    status = _status(status_path)
    if str(status.get("status")) != "ok":
        return {
            "status": "failed",
            "error": str(
                status.get("error", "")
            ),
        }
    return {
        "status": "ok",
        **_metrics(
            root,
            prefix,
            truth,
        ),
    }


def _summary(
    values: list[float],
) -> dict[str, float | int]:
    array = np.asarray(
        [
            value
            for value in values
            if np.isfinite(value)
        ],
        dtype=float,
    )
    if not array.size:
        return {
            "n": 0,
            "mean": float("nan"),
            "sd": float("nan"),
            "median": float("nan"),
            "q25": float("nan"),
            "q75": float("nan"),
        }
    return {
        "n": int(array.size),
        "mean": float(np.mean(array)),
        "sd": (
            float(np.std(array, ddof=1))
            if array.size > 1
            else 0.0
        ),
        "median": float(np.median(array)),
        "q25": float(
            np.quantile(array, 0.25)
        ),
        "q75": float(
            np.quantile(array, 0.75)
        ),
    }


def _aggregate(
    records: list[dict[str, object]],
    method: str,
) -> dict[str, object]:
    successful = [
        record[method]
        for record in records
        if record[method]["status"] == "ok"
    ]
    fields = (
        "mean_ise",
        "reconstruction_ise",
        "functional_subspace_min_cosine",
        "score_subspace_min_cosine",
        "spectrum_pve_l1_error",
        "score_failure_rate",
    )
    return {
        "n_replicates": len(records),
        "n_success": len(successful),
        "fit_failure_rate": float(
            (
                len(records)
                - len(successful)
            )
            / len(records)
        ),
        "metrics": {
            field: _summary(
                [
                    float(item[field])
                    for item in successful
                ]
            )
            for field in fields
        },
    }


def _paired(
    records: list[dict[str, object]],
    left: str,
    right: str,
) -> dict[str, object]:
    paired = [
        record
        for record in records
        if (
            record[left]["status"] == "ok"
            and record[right]["status"] == "ok"
        )
    ]
    result: dict[str, object] = {
        "n_paired": len(paired),
        "descriptive_only": True,
    }
    specifications = {
        "reconstruction_ise": "lower",
        "mean_ise": "lower",
        "functional_subspace_min_cosine": "higher",
        "score_subspace_min_cosine": "higher",
        "spectrum_pve_l1_error": "lower",
    }

    for field, favorable in specifications.items():
        differences = [
            float(record[right][field])
            - float(record[left][field])
            for record in paired
        ]
        array = np.asarray(
            differences,
            dtype=float,
        )
        if not array.size:
            fraction = float("nan")
        elif favorable == "lower":
            fraction = float(
                np.mean(array < 0)
            )
        else:
            fraction = float(
                np.mean(array > 0)
            )
        result[field] = {
            "right_minus_left": _summary(
                differences
            ),
            "fraction_right_in_favorable_direction": (
                fraction
            ),
        }
    return result


def evaluate(
    root: Path,
) -> dict[str, object]:
    manifest = json.loads(
        (
            root / "manifest.json"
        ).read_text(encoding="utf-8")
    )
    if manifest.get("b4_decision") != "deferred":
        raise ValueError(
            "B4 must remain deferred"
        )
    if (
        manifest.get(
            "qualification_thresholds_introduced"
        )
        is not False
    ):
        raise ValueError(
            "B2 must not introduce qualification thresholds"
        )
    if (
        manifest.get(
            "architecture_winner_selected"
        )
        is not False
    ):
        raise ValueError(
            "B2 must not select an architecture winner"
        )

    rows = pd.read_csv(
        root / "manifest.csv"
    )
    scenario_results = []
    fairness_results = []

    for scenario, group in rows.groupby(
        "scenario",
        sort=False,
    ):
        records = []
        fairness_records = []

        for row in group.itertuples(
            index=False
        ):
            replicate = int(row.replicate)
            directory = (
                root
                / "scenarios"
                / str(row.scenario)
                / f"replicate_{replicate:03d}"
            )
            truth = json.loads(
                (
                    directory / "truth.json"
                ).read_text(
                    encoding="utf-8"
                )
            )
            record = {
                "replicate": replicate,
                "seed": int(row.seed),
                "native_fixed": _method_record(
                    directory,
                    "native_fixed",
                    truth,
                    directory
                    / "native_fixed_status.json",
                ),
                "bayesfpca_fixed": (
                    _method_record(
                        directory,
                        "bayesfpca_fixed",
                        truth,
                        directory
                        / "bayesfpca_fixed_status.csv",
                    )
                ),
            }
            records.append(record)

            if _truthy(row.fairness):
                fairness_record = {
                    "replicate": replicate,
                    "native_selected": (
                        _method_record(
                            directory,
                            "native_selected",
                            truth,
                            directory
                            / "native_selected_status.json",
                        )
                    ),
                    "bayesfpca_selected": (
                        _method_record(
                            directory,
                            "bayesfpca_selected",
                            truth,
                            directory
                            / "bayesfpca_selected_status.csv",
                        )
                    ),
                }
                selection_path = (
                    directory
                    / "native_selection.json"
                )
                if selection_path.exists():
                    fairness_record[
                        "native_selection"
                    ] = json.loads(
                        selection_path.read_text(
                            encoding="utf-8"
                        )
                    )

                sensitivity_path = (
                    directory
                    / "bayesfpca_k_sensitivity.csv"
                )
                if sensitivity_path.exists():
                    fairness_record[
                        "bayesfpca_k_sensitivity"
                    ] = pd.read_csv(
                        sensitivity_path
                    ).to_dict(
                        orient="records"
                    )

                fairness_records.append(
                    fairness_record
                )

        first_truth = json.loads(
            (
                root
                / "scenarios"
                / str(scenario)
                / "replicate_000"
                / "truth.json"
            ).read_text(encoding="utf-8")
        )
        scenario_results.append(
            {
                "scenario": scenario,
                "truth_family": (
                    first_truth["truth_family"]
                ),
                "observation_mechanism": (
                    first_truth[
                        "observation_mechanism"
                    ]
                ),
                "informative_observation_is_sensitivity_only": bool(
                    first_truth[
                        "contract"
                    ].get(
                        "informative_observation_is_sensitivity_only",
                        False,
                    )
                ),
                "native_fixed": _aggregate(
                    records,
                    "native_fixed",
                ),
                "bayesfpca_fixed": _aggregate(
                    records,
                    "bayesfpca_fixed",
                ),
                "paired_fixed": _paired(
                    records,
                    "native_fixed",
                    "bayesfpca_fixed",
                ),
                "replicates": records,
            }
        )

        if fairness_records:
            fairness_results.append(
                {
                    "scenario": scenario,
                    "native_selected": _aggregate(
                        fairness_records,
                        "native_selected",
                    ),
                    "bayesfpca_selected": (
                        _aggregate(
                            fairness_records,
                            "bayesfpca_selected",
                        )
                    ),
                    "paired_selected": _paired(
                        fairness_records,
                        "native_selected",
                        "bayesfpca_selected",
                    ),
                    "replicates": (
                        fairness_records
                    ),
                }
            )

    payload = {
        "schema_version": 1,
        "programme": (
            "post-1.1-bayesian-fpca-b2-replication"
        ),
        "evidence_type": (
            "replicated_recovery_and_predeclared_tuning_sensitivity"
        ),
        "primary_replicates": int(
            manifest["primary_replicates"]
        ),
        "fairness_replicates": int(
            manifest["fairness_replicates"]
        ),
        "qualification_thresholds_introduced": False,
        "architecture_winner_selected": False,
        "automatic_promotion_decision": False,
        "p_values_computed": False,
        "b4_decision": "deferred",
        "scenario_results": scenario_results,
        "fairness_results": fairness_results,
        "interpretation": (
            "B2 is descriptive replicated recovery and "
            "predeclared tuning sensitivity. It does not "
            "establish intrinsic architectural superiority "
            "and does not authorize a native Bayesian API."
        ),
    }
    (
        root / "b2_replication_summary.json"
    ).write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
            default=str,
        )
        + "\n",
        encoding="utf-8",
    )
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "evidence_dir",
        type=Path,
    )
    args = parser.parse_args()
    payload = evaluate(
        args.evidence_dir
    )
    print(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
            default=str,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
