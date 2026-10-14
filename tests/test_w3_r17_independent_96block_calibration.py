"""R17 larger pointwise calibration preflight and failure-inclusive accounting."""
import numpy as np
import pytest
from scripts import run_w3_r17_fresh_feasibility as prior
from scripts import run_w3_r17_independent_96block_calibration as study
from scripts import run_w3_r16_leverage_covariance_factorial as r16


def test_new_independent_master_seed_and_nested_source():
    assert study.MASTER_SEED!=prior.R17_SEED!=r16.SEED
    a=prior.fresh_source(0,"extreme_dependent",n=24,master_seed=study.MASTER_SEED,
                         n_blocks=study.BLOCKS,max_n=96)
    b=prior.fresh_source(0,"extreme_dependent",n=48,master_seed=study.MASTER_SEED,
                         n_blocks=study.BLOCKS,max_n=96)
    for (a_time,a_value),(b_time,b_value) in zip(zip(a[1].time,a[1].values),
                                                  zip(b[1].time,b[1].values)):
        np.testing.assert_array_equal(a_time,b_time)
        np.testing.assert_array_equal(a_value,b_value)
    assert len(np.unique(b[3]))==48
    assert a[1].provenance["interpolation_performed"] is False
    assert a[1].provenance["fresh_master_seed"]==study.MASTER_SEED


@pytest.mark.parametrize("n,support,model,target",[
    (24,"ordinary_independent","legendre5","correct"),
    (48,"extreme_independent","cubic_spline13","correct"),
    (96,"extreme_dependent","legendre5","diagonal_misspecified"),
])
def test_original_source_multi_sample_size_and_mathematical_contract(n,support,model,target):
    r=study.run_case(0,n,support,model,target)
    assert r["status"]=="ok",r["error"]
    assert r["n_participants"]==n
    assert all(isinstance(x,bool) for x in r["coverage"].values())
    assert r["satterthwaite_df"]>0
    assert not r["release_authorized"]
    assert not r["pointwise_inference_qualified"]


def test_wilson_and_paired_bootstrap_do_not_relabel_cases_as_independent():
    assert study.wilson_interval(0,0) is None
    for successes in (0,9,86,96):
        lo,hi=study.wilson_interval(successes,96)
        assert 0<=lo<=hi<=1
        assert lo<=successes/96<=hi
    rows=[dict(block=b,coverage={"cr2_satterthwaite":(b%3!=0),
                                "cr1_tGminus1":(b%2==0)})
          for b in range(96)]
    x=study.paired_bootstrap_delta(rows,"cr2_satterthwaite","cr1_tGminus1",135)
    y=study.paired_bootstrap_delta(list(reversed(rows)),"cr2_satterthwaite","cr1_tGminus1",135)
    assert x==y
    assert x["n_independent_paired_blocks"]==96
    assert x["bootstrap_95_interval"][0]<=x["bootstrap_95_interval"][1]


def test_planned_design_and_missing_failure_accounting():
    assert study.BLOCKS==96
    assert study.SIZES==(24,48,96)
    assert study.PLANNED==4608
    good=study.run_case(0,24,"ordinary_independent","legendre5","correct")
    bad=dict(good,target="diagonal_misspecified",status="failed",error={"type":"Fixture","message":"preserve"})
    report=study.summarize([good,bad])
    assert report["recorded_evaluations"]==2
    assert report["successful_evaluations"]==1
    assert report["failed_evaluations"]==1
    assert report["missing_evaluations"]==study.PLANNED-2
    assert not report["production_release_ready"]
    assert not report["method_selected"]
