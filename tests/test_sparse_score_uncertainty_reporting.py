import numpy as np
import pandas as pd

from eyetrajectoriespy.sparse_score_uncertainty import (
    SparseFPCAScoreUncertaintyResult,
)
from eyetrajectoriespy.sparse_score_uncertainty_reporting import (
    sparse_fpca_score_uncertainty_reporting_text,
)


def _result(*, ridge: float, status_codes=("ok", "ok")):
    return SparseFPCAScoreUncertaintyResult(
        reference=None,
        curve_ids=("c1", "c2"),
        covariance=np.repeat(np.eye(2)[None, :, :], 2, axis=0),
        standard_errors=np.ones((2, 2)),
        diagnostics=pd.DataFrame(
            {
                "curve_id": ["c1", "c2"],
                "status_code": list(status_codes),
            }
        ),
        n_components=2,
        provenance={"score_ridge": ridge},
    )


def test_reporting_text_states_conditional_scope_and_exclusions():
    text = sparse_fpca_score_uncertainty_reporting_text(_result(ridge=0.0))

    assert "conditional on the fitted mean, covariance surface, eigensystem" in text
    assert "excludes population-estimation uncertainty" in text
    assert "smoothing bandwidths" in text
    assert "noise variance" in text
    assert "No score ridge" in text


def test_reporting_text_explains_ridge_and_retained_failures():
    text = sparse_fpca_score_uncertainty_reporting_text(
        _result(ridge=0.25, status_codes=("ok", "score_covariance_ill_conditioned"))
    )

    assert "score ridge (0.25)" in text
    assert "numerical regularization" in text
    assert "not interpreted as additional measurement-error variance" in text
    assert "1 of 2" in text
    assert "rather than silently dropped" in text
