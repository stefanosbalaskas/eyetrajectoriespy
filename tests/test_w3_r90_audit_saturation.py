"""R90 prospectively frozen saturation, nested selection and refusal gates."""
import numpy as np
import pytest
from scripts import run_w3_r90_audit_saturation as r90


def test_new_source_and_frozen_prospective_grid():
    assert r90.BLOCKS==32
    assert r90.N_SOURCES==64
    assert r90.N_RECORDS==1280
    assert r90.AUDIT_FRACTIONS==(0.,.25,.50,.75,1.)
    assert set(r90.SEEDS.values())==set(range(202610229000,202610229005))
    assert len(r90.SHARDS)==8
    with pytest.raises(ValueError,match="original primitive block"):
        r90.generate(32,"independent_curves")
    with pytest.raises(ValueError,match="original stream identity"):
        r90.stream_seed(0,"independent_curves","nonsense")


def test_sharp_bounds_cannot_see_an_unreturned_target():
    y=np.array([-.6,np.nan,.1,np.nan,1200.])
    eligible=np.array([1,1,1,1,0],dtype=bool)
    measured=np.array([1,0,1,0,0],dtype=bool)
    expected=r90.sharp_bounds(y,eligible,measured)
    assert expected["width"]==.5
    y[-1]=-5000.
    assert r90.sharp_bounds(y,eligible,measured)==expected
    with pytest.raises(ValueError,match="unreturned outcome leaked"):
        y[1]=.1
        r90.sharp_bounds(y,eligible,measured)


def test_q_zero_q_full_complete_and_full_selective_floor_per_source():
    for config in r90.CONFIGS:
        cases=r90.evaluate(0,config)
        assert len(cases)==20
        assert len({r["original_Y_digest"] for r in cases})==1
        for mechanism in r90.MECHANISMS:
            def lookup(law,q):
                return next(r for r in cases if
                    r["mechanism"]==mechanism and
                    r["return_law"]==law and r["audit_fraction"]==q)
            baseline=lookup("complete",0.)
            assert baseline["audit_assigned_n"]==0
            assert baseline["observed_digest"]==lookup("outcome_selective",0.)["observed_digest"]
            assert lookup("complete",1.)["mean_bounds"]["unreturned_n"]==0
            assert lookup("complete",1.)["mean_bounds"]["width"]==0.
            assert lookup("complete",1.)["contrast_width"]<1e-12
            for law in r90.RETURN_LAWS:
                path=[lookup(law,q) for q in r90.AUDIT_FRACTIONS]
                assert all(a["mean_bounds"]["width"]+1e-12>=b["mean_bounds"]["width"]
                           for a,b in zip(path[:-1],path[1:]))
                assert all(a["contrast_width"]+1e-12>=b["contrast_width"]
                           for a,b in zip(path[:-1],path[1:]))
                assert all(r["response_mechanism_identified"] is False for r in path)
                assert all(r["release_authorized"] is False for r in path)
            assert lookup("outcome_selective",1.)["mean_bounds"]["width"]>=0.
            assert lookup("outcome_selective",1.)["audit_returned_n"]<=lookup("complete",1.)["audit_returned_n"]


def test_fail_closed_missing_complete_original_evidence(tmp_path):
    with pytest.raises(ValueError,match="four-block"):
        r90.shard(tmp_path/"impossible",1,5)
    with pytest.raises(ValueError,match="all eight"):
        r90.aggregate(tmp_path/"out",tmp_path/"unavailable")
    with pytest.raises(ValueError,match="ledger incomplete"):
        r90.summarize([])
