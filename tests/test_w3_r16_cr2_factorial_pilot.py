import numpy as np
from scripts.run_w3_r16_cr2_factorial_pilot import one,summarize,BLOCKS,SUPPORT,MODELS

def test_source_contract_and_no_promotion():
    r=one(0,24,"ordinary_independent","legendre5")
    assert r["status"]=="ok",r["exception"]
    assert r["dense_oracle_delta"]<2e-7
    assert r["cr2_se"]>0 and r["oracle_se"]>0
    assert r["df_qualified"] is False
    assert r["production_release_ready"] is False

def test_factorial_is_recorded_failure_inclusive():
    good=one(0,24,"ordinary_independent","legendre5")
    bad=dict(good,status="failed",support="extreme_independent")
    report=summarize([good,bad])
    assert report["planned_cases"]==BLOCKS*len(SUPPORT)*len(MODELS)
    assert report["successful_cases"]==1 and report["failed_cases"]==1
    assert report["recorded_cases"]==2
    assert not report["cr2_df_qualified"]
    assert not report["production_release_ready"]
