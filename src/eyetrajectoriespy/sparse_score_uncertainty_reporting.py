"""Reporting helpers for conditional native sparse-PACE score uncertainty."""

from __future__ import annotations

import numpy as np

from .sparse_score_uncertainty import SparseFPCAScoreUncertaintyResult


def sparse_fpca_score_uncertainty_reporting_text(
    result: SparseFPCAScoreUncertaintyResult,
) -> str:
    """Return manuscript-ready scope wording for conditional score uncertainty."""

    if not isinstance(result, SparseFPCAScoreUncertaintyResult):
        raise TypeError("result must be a SparseFPCAScoreUncertaintyResult")

    diagnostics = result.diagnostics
    if "status_code" not in diagnostics.columns:
        raise ValueError("result diagnostics must contain status_code")
    failed = int(np.count_nonzero(diagnostics["status_code"].to_numpy() != "ok"))
    n_curves = len(result.curve_ids)
    score_ridge = float(result.provenance.get("score_ridge", 0.0))

    text = (
        f"Conditional PACE score uncertainty was computed for {n_curves} curves "
        f"and {result.n_components} retained component(s) using the full fitted "
        "covariance evaluated at native observation times. The covariance is "
        "conditional on the fitted mean, covariance surface, eigensystem, and "
        "measurement-error variance and therefore excludes population-estimation "
        "uncertainty, including uncertainty from estimating smoothing bandwidths "
        "and the noise variance."
    )
    if score_ridge > 0:
        text += (
            f" The fitted PACE score ridge ({score_ridge:g}) was inherited as "
            "numerical regularization of the score system and was not interpreted "
            "as additional measurement-error variance."
        )
    else:
        text += " No score ridge was added to the conditional system."

    if failed:
        text += (
            f" {failed} of {n_curves} curve-level uncertainty systems failed the "
            "declared numerical diagnostics and were retained explicitly rather "
            "than silently dropped."
        )
    else:
        text += " All curve-level conditional uncertainty systems passed the declared numerical diagnostics."
    return text
