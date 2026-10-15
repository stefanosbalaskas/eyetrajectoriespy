"""R20 estimated-covariance pilot source, outcome and accounting contracts."""
import numpy as np
import pytest
from scripts import run_w3_r20_estimated_target_pilot as pilot
from scripts import run_w3_r17_fresh_feasibility as source
from scripts import run_w3_r16_leverage_covariance_factorial as r16


def test_new_seed_not_recycled_and_nesting_preserved():
    assert pilot.MASTER_SEED not in (source.R17_SEED,r16.SEED)
    assert pilot.BLOCKS==8 and pilot.PLANNED==256
    a=source.fresh_source(0,"ordinary_independent",n=24,
         master_seed=pilot.MASTER_SEED,n_blocks=pilot.BLOCKS,max_n=48)
    b=source.fresh_source(0,"ordinary_independent",n=48,
         master_seed=pilot.MASTER_SEED,n_blocks=pilot.BLOCKS,max_n=48)
    for (t,v),(tt,vv) in zip(zip(a[1].time,a[1].values),zip(b[1].time,b[1].values)):
        np.testing.assert_array_equal(t,tt)
        np.testing.assert_array_equal(v,vv)
    assert a[1].provenance["interpolation_performed"] is False


@pytest.mark.parametrize("support,family,expected_status",[
    ("ordinary_independent","shared_slope","failed"),
    ("ordinary_dependent","predictor_scaled_slope","ok"),
    ("extreme_independent","shared_slope","failed"),
])
def test_observable_estimated_target_smoke(support,family,expected_status):
    """Reproduce original R20 outcomes, including rejected CR2 adjustments."""
    x=pilot.evaluate(0,24,support,"legendre5",family)
    assert x["status"]==expected_status,x["error"]
    assert x["working_covariance_estimated_from_responses"]
    assert not x["nominal_coverage_qualified"]
    assert not x["release_authorized"]
    if expected_status=="failed":
        assert x["error"]=={
            "type":"ValueError",
            "message":"nonpositive or ill-conditioned working covariance",
        }
        assert "inclusion" not in x
    else:
        assert x["source_uses_known_covariance_in_estimator"] is False
        assert x["conditional_satterthwaite_df"]>0
        assert x["conditional_df_ignores_estimated_covariance_uncertainty"]


def test_failure_retention_and_independent_blocks():
    ok=pilot.evaluate(0,24,"ordinary_dependent","legendre5","predictor_scaled_slope")
    assert ok["status"]=="ok",ok["error"]
    fail=dict(ok,working_family="shared_slope",status="failed",
              error={"type":"Fixture","message":"not removed"})
    s=pilot.summarize([ok,fail])
    assert s["recorded_evaluations"]==2
    assert s["completed_evaluations"]==1
    assert s["failed_evaluations"]==1
    assert s["missing_evaluations"]==pilot.PLANNED-2
    assert s["independent_generating_blocks"]==8
    assert not s["estimated_target_df_qualified"]
    assert not s["release_authorized"]
