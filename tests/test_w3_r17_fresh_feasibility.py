"""Independent R17 source/ledger guards; substantive coverage not asserted."""
import numpy as np
from scripts.run_w3_r17_fresh_feasibility import (
    BLOCKS,N,R17_SEED,TARGETS,evaluate,fresh_source,prepare,summarize
)
from scripts import run_w3_r16_leverage_covariance_factorial as r16

def test_fresh_source_reproducibility_and_separate_seed():
    a=fresh_source(0,"ordinary_independent")
    b=fresh_source(0,"ordinary_independent")
    assert len(a[1].time)==len(b[1].time)
    for one,two in zip(a[1].values,b[1].values):
        np.testing.assert_array_equal(one,two)
    old=r16.source(0,N,"ordinary_independent")
    assert not np.array_equal(a[0]["participant_intercept"],old[0]["participant_intercept"])
    assert R17_SEED!=r16.SEED
    assert a[1].provenance["interpolation_performed"] is False

def test_true_within_person_covariance_positive_definite():
    src=fresh_source(0,"extreme_dependent")
    X,y,w,g,phi=prepare(src,"legendre5")
    assert len(phi)==N
    assert len(y)==len(g)==X.shape[0]
    for v in phi:
        assert np.linalg.eigvalsh(v).min()>0

def test_original_source_smoke_with_correct_target():
    row=evaluate(0,"ordinary_independent","legendre5","correct")
    assert row["status"]=="ok",row["error"]
    assert row["oracle_agreement_error"]<2e-7
    assert row["satterthwaite_df"]>0
    assert not row["pointwise_inference_qualified"]
    assert not row["release_authorized"]

def test_ledger_is_failure_inclusive():
    row=evaluate(0,"ordinary_independent","legendre5","correct")
    failed=dict(row,status="failed",target="diagonal_misspecified")
    s=summarize([row,failed])
    assert s["independent_generating_blocks"]==BLOCKS
    assert s["planned_cases"]==BLOCKS*len(r16.SUPPORT)*len(r16.MODELS)*len(TARGETS)
    assert s["completed_cases"]==1 and s["failed_cases"]==1
    assert not s["calibrated_pointwise_inference"]
