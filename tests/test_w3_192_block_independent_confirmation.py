"""W3 R3 independent-seed confirmation: no hidden model/replication promotion."""
from pathlib import Path
import sys
import numpy as np
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

from scripts.run_w3_192_block_independent_confirmation import (
    MASTER_SEED, BLOCKS, DESIGNS, REGIMES, INDEPENDENT_UNITS,
    BOOTSTRAP_DRAWS, fresh_source, shared_weights, evaluate,
    paired_block_bootstrap_interval, audit,
)
from scripts.run_w3_heteroskedastic_ar1_stress import source as prior_source


@pytest.mark.parametrize("design",DESIGNS)
def test_source_traces_are_fresh_and_regimes_share_innovations(design):
    iid, frame_a, truth_a, Xa, Ya=fresh_source(0,design,"iid")
    joint, frame_b, truth_b, Xb, Yb=fresh_source(0,design,"heteroskedastic_ar1")
    assert iid.n_curves == (108 if design=="participant" else 36)
    np.testing.assert_array_equal(Xa,Xb)
    np.testing.assert_array_equal(truth_a,truth_b)
    assert not np.array_equal(iid.values,joint.values)
    np.testing.assert_array_equal(frame_a.condition,frame_b.condition)
    old,*_=prior_source(0,design,36,"iid")
    assert not np.array_equal(old.values,iid.values)
    if design=="participant":
        assert frame_a.condition.iloc[:3].nunique()==1
        assert iid.metadata.participant_id.nunique()==INDEPENDENT_UNITS


def test_source_independence_across_blocks_and_false_inputs():
    a,*_=fresh_source(0,"curve","iid")
    b,*_=fresh_source(1,"curve","iid")
    assert not np.array_equal(a.values,b.values)
    assert MASTER_SEED != 2026101263
    with pytest.raises(ValueError,match="prespecified"):
        fresh_source(BLOCKS,"curve","iid")
    with pytest.raises(ValueError,match="unplanned"):
        fresh_source(0,"curve","not-a-regime")


def test_wild_weights_per_independent_unit_matched_across_regimes():
    a=shared_weights(0,"participant")
    b=shared_weights(0,"participant")
    assert a.shape==(BOOTSTRAP_DRAWS,INDEPENDENT_UNITS)
    np.testing.assert_array_equal(a,b)
    assert set(np.unique(a))=={-1.,1.}
    assert not np.array_equal(a,shared_weights(0,"curve"))


@pytest.mark.parametrize("design,regime",[
    ("curve","iid"),
    ("curve","heteroskedastic_ar1"),
    ("participant","heteroskedastic_ar1"),
])
def test_real_workflow_matches_independent_package_and_bootstrap_oracles(design,regime):
    r=evaluate(0,design,regime)
    assert r["status"]=="ok",r["exception"]
    assert r["beta_oracle_max_abs"] <= 2e-10
    assert r["hc1_oracle_max_abs"] <= 2e-10
    assert r["package_fixed_band_checked"]
    assert isinstance(r["fixed_truth_included"],bool)
    assert isinstance(r["restudentized_truth_included"],bool)
    assert not r["calibration_qualified"]
    assert not r["release_authorized"]


def test_paired_mc_interval_resamples_blocks_not_source_cells():
    assert paired_block_bootstrap_interval([],seed=11) is None
    sample=[1,0,-1,1,0,0,1,-1]
    x=paired_block_bootstrap_interval(sample,seed=123,draws=1000)
    assert len(x)==2 and -1<=x[0]<=x[1]<=1
    assert x==paired_block_bootstrap_interval(sample,seed=123,draws=1000)


def test_source_audit_keeps_missing_failure_and_paired_denominator():
    good=evaluate(0,"curve","iid")
    bad=dict(good,regime="heteroskedastic_ar1",
             status="failed",exception={"type":"ControlledFailure"})
    out=audit([good,bad])
    assert out["planned_cases"]==BLOCKS*len(DESIGNS)*len(REGIMES)
    assert out["present_cases"]==2
    assert out["fitting_or_contract_failures"]==1
    assert len(out["missing_cases"])==out["planned_cases"]-2
    cell=out["groups"]["curve"]["iid"]
    assert cell["completed"]==1
    assert cell["attempted"]==BLOCKS
    assert not cell["no_failed_dataset_deleted_from_attempted_denominator"]
    assert out["interval_coverage_qualified"] is False
    with pytest.raises(ValueError,match="duplicate"):
        audit([good,good])
