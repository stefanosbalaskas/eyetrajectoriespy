"""E3: explicit sensitivity runs; descriptive metrics, retained failures, no model selection."""

from __future__ import annotations

from dataclasses import dataclass, is_dataclass
import json
from typing import Any, Callable, Mapping, Sequence

import numpy as np
import pandas as pd

from ._core import workflow_config_to_dict


@dataclass(frozen=True)
class WorkflowSpecification:
    """One analyst-declared specification for a single named estimand."""
    name: str
    config: Any
    estimand_id: str
    scientific_rationale: str

    def __post_init__(self) -> None:
        if not all(x.strip() for x in (self.name, self.estimand_id, self.scientific_rationale)):
            raise ValueError("name, estimand_id and scientific_rationale must be nonempty")
        if not is_dataclass(self.config) or isinstance(self.config, type):
            raise TypeError("config must be a dataclass instance")
        workflow_config_to_dict(self.config)


@dataclass(frozen=True)
class WorkflowSensitivityResult:
    estimand_id: str
    baseline_name: str
    specifications: pd.DataFrame
    metric_frame: pd.DataFrame
    outcomes: Mapping[str, Any]
    errors: Mapping[str, str]
    warnings: tuple[str, ...]
    provenance: Mapping[str, Any]


def run_workflow_sensitivity(
    data: Any,
    *,
    runner: Callable[..., Any],
    specifications: Sequence[WorkflowSpecification],
    baseline_name: str,
    metrics: Mapping[str, Callable[[Any], float]],
    runner_kwargs: Mapping[str, Any] | None = None,
    conclusions: Mapping[str, Callable[[Any], str | bool]] | None = None,
) -> WorkflowSensitivityResult:
    """Run all declared configs through runner(data, config=..., **kwargs).

    Every specification must target the same analyst-declared estimand and the
    same workflow contract. The caller supplies scientifically comparable
    scalar metrics. No p-values, confidence intervals or winners are inferred.
    """
    specs = tuple(specifications)
    if not specs or any(not isinstance(x, WorkflowSpecification) for x in specs):
        raise ValueError("specifications must contain WorkflowSpecification records")
    names = [x.name for x in specs]
    if len(set(names)) != len(names) or baseline_name not in names:
        raise ValueError("specification names must be unique and include baseline_name")
    if len({x.estimand_id for x in specs}) != 1:
        raise ValueError("Cannot compare different declared estimands")
    if not metrics or any(not k or not callable(fn) for k, fn in metrics.items()):
        raise ValueError("Supply nonempty named scalar metric extractors")
    if not callable(runner):
        raise TypeError("runner must be callable")
    conclusion_rules = dict(conclusions or {})
    if any(not name or not callable(fn) for name, fn in conclusion_rules.items()):
        raise ValueError("Conclusion labels require explicitly declared extraction functions")
    kw = dict(runner_kwargs or {})
    if "config" in kw:
        raise ValueError("config must come only from a declared specification")
    ledger: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []
    outcomes: dict[str, Any] = {}
    errors: dict[str, str] = {}
    first_contract: str | None = None
    for spec in specs:
        record = {
            "specification": spec.name, "estimand_id": spec.estimand_id,
            "scientific_rationale": spec.scientific_rationale,
            "config_json": json.dumps(workflow_config_to_dict(spec.config), sort_keys=True),
            "status": "completed", "workflow_contract": None, "error_type": None, "error": None,
        }
        metrics_row: dict[str, Any] = {"specification": spec.name}
        try:
            result = runner(data, config=spec.config, **kw)
            contract = getattr(result, "workflow_contract", None)
            if not isinstance(contract, str) or not contract:
                raise TypeError("runner must return a typed workflow result")
            if first_contract is not None and contract != first_contract:
                raise ValueError("Incompatible workflow contracts: estimands cannot be compared")
            extracted = {name: float(fn(result)) for name, fn in metrics.items()}
            if not all(np.isfinite(v) for v in extracted.values()):
                raise ValueError("All metric extractors must return finite scalar results")
            first_contract = contract
            record["workflow_contract"] = contract
            outcomes[spec.name] = result
            metrics_row.update(extracted)
            for label, rule in conclusion_rules.items():
                outcome = rule(result)
                if not isinstance(outcome, (str, bool)) or not str(outcome).strip():
                    raise TypeError("Analyst-declared conclusions must be nonempty strings or booleans")
                metrics_row[f"conclusion_{label}"] = str(outcome)
        except Exception as exc:
            errors[spec.name] = f"{type(exc).__name__}: {exc}"
            record.update(status="failed", error_type=type(exc).__name__, error=str(exc))
            metrics_row.update({name: np.nan for name in metrics})
            metrics_row.update({f"conclusion_{name}": None for name in conclusion_rules})
        ledger.append(record)
        rows.append(metrics_row)
    frame = pd.DataFrame(rows)
    warnings = []
    if baseline_name in outcomes:
        baseline = frame.loc[frame["specification"] == baseline_name].iloc[0]
        for name in metrics:
            frame[f"{name}_delta_from_baseline"] = frame[name] - float(baseline[name])
        for name in conclusion_rules:
            column = f"conclusion_{name}"
            frame[f"conclusion_{name}_changed"] = [
                pd.NA if pd.isna(value) else bool(value != baseline[column])
                for value in frame[column]
            ]
    else:
        warnings.append("Baseline failed; no differences from baseline can be computed.")
        for name in metrics:
            frame[f"{name}_delta_from_baseline"] = np.nan
        for name in conclusion_rules:
            frame[f"conclusion_{name}_changed"] = pd.NA
    if errors:
        warnings.append(f"{len(errors)} of {len(specs)} specifications failed; failures retained.")
    warnings.append("Metrics and analyst-extracted conclusion labels are descriptive; no inference or automatic ranking is generated.")
    return WorkflowSensitivityResult(
        estimand_id=specs[0].estimand_id, baseline_name=baseline_name,
        specifications=pd.DataFrame(ledger), metric_frame=frame,
        outcomes=outcomes, errors=errors, warnings=tuple(warnings),
        provenance={"run_count": len(specs), "completed_count": len(outcomes),
                    "automatic_model_selection": False, "inferential_tests_generated": False,
                    "estimand_comparability": "analyst_declared"},
    )


def plot_workflow_sensitivity(
    result: WorkflowSensitivityResult, *, metric: str, ax: Any = None
) -> Any:
    """Visualize descriptive metric stability; crosses denote failed fits."""
    import matplotlib.pyplot as plt

    if metric not in result.metric_frame or metric == "specification":
        raise ValueError("Choose a recorded scalar metric")
    if ax is None:
        _, ax = plt.subplots(figsize=(8, 4))
    data = result.metric_frame
    x = np.arange(len(data))
    y = data[metric].to_numpy(dtype=float)
    good = np.isfinite(y)
    ax.plot(x[good], y[good], "o-", label="Descriptive metric")
    if (~good).any():
        ax.scatter(x[~good], np.zeros((~good).sum()), marker="x", label="Failed — no estimate")
        ax.legend()
    ax.set_xticks(x)
    ax.set_xticklabels(data["specification"], rotation=30, ha="right")
    ax.set_xlabel("Declared analytical specification")
    ax.set_ylabel(metric + " (analyst-declared units)")
    ax.set_title("Descriptive sensitivity; no automatic statistical inference")
    return ax
