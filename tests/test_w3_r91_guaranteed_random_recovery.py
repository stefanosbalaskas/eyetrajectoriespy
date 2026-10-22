"""R91 observed-only design unbiasedness, provenance and new-source contracts."""
from itertools import product

import numpy as np
import pytest

from scripts import run_w3_r91_guaranteed_random_recovery as r91


def test_frozen_new_source_denominators_and_seeds():
    assert r91.N_SOURCES==64
    assert r91.N_RECORDS==6144
    assert r91.GUARANTEE_FRACTIONS==(.10,.25,.50)
    assert r91.ASSIGNMENT_REPLICATES==16
    assert len(r91.SHARDS)==8
    assert len(set(r91.SEEDS.values()))==4
    with pytest.raises(ValueError,match="primitive block"):
        r91.generate(32,"independent_curves")
    with pytest.raises(ValueError,match="randomization replicate"):
        r91.randomized_guarantee_uniform(0,"independent_curves",16,(4,))


def test_exact_enumerated_design_unbiasedness_and_variance_identity():
    """Exhaustively enumerate 2 independent Bernoulli retrieval decisions."""
    target=np.array([1,1,1,1],bool)
    secondary=np.array([1,1,0,0],bool)
    y=np.array([-.5,.0, -.5,.5])
    z=r91.bounded_value(y)
    truth=float(np.mean(z))
    g=.5
    possible=[]
    variance_hats=[]
    for a,b in product([False,True],repeat=2):
        returned=np.array([0,0,a,b],bool)
        visible=np.where(secondary|returned,y,np.nan)
        fit=r91.design_ht(visible,target,secondary,returned,g)
        possible.append(fit["ht_estimate"])
        variance_hats.append(fit["unbiased_design_variance_estimate"])
    assert float(np.mean(possible))==pytest.approx(truth,abs=1e-15)
    theoretical=(1.-g)/g*float(np.dot(z[~secondary],z[~secondary]))/(4*4)
    assert float(np.var(possible))==pytest.approx(theoretical,abs=1e-15)
    assert float(np.mean(variance_hats))==pytest.approx(theoretical,abs=1e-15)


def test_observed_only_rejects_hidden_response_or_unmeasured_guarantee():
    target=np.array([1,1,1,1],bool)
    secondary=np.array([1,0,0,0],bool)
    guaranteed=np.array([0,1,0,0],bool)
    observed=np.array([0.,.4,np.nan,np.nan])
    fit=r91.design_ht(observed,target,secondary,guaranteed,.25)
    assert fit["initially_missing_n"]==4
    assert fit["guaranteed_n"]==1
    assert fit["retrieval_is_actual_measurement_not_assignment_only"]
    with pytest.raises(ValueError,match="unobserved record leaked"):
        r91.design_ht(np.array([0.,.4,.7,np.nan]),target,secondary,guaranteed,.25)
    with pytest.raises(ValueError,match="unobserved record leaked"):
        r91.design_ht(np.array([0.,np.nan,np.nan,np.nan]),target,secondary,guaranteed,.25)
    with pytest.raises(ValueError,match="provenance"):
        r91.design_ht(observed,target,secondary,secondary,.25)
    with pytest.raises(ValueError,match="probability"):
        r91.design_ht(observed,target,secondary,guaranteed,0.)


def test_original_case_masks_nesting_source_invariance_and_finite_variance():
    for config in r91.CONFIGS:
        cases=r91.evaluate(0,config)
        assert len(cases)==2*16*3
        assert len({r["original_Y_digest"] for r in cases})==1
        for law in r91.MECHANISMS:
            cell=[r for r in cases if r["mechanism"]==law]
            assert len(cell)==48
            true={r["oracle_source_true_mean_only"] for r in cell}
            assert len(true)==1
            for rep in range(16):
                matching=sorted((r for r in cell if r["assignment_rep"]==rep),
                                key=lambda r:r["guarantee_fraction"])
                assert len(matching)==3
                assert all(a["actual_guaranteed_returned_n"]<=b["actual_guaranteed_returned_n"]
                           for a,b in zip(matching[:-1],matching[1:]))
                assert all(a["sharp_bound_width"]+1e-12>=b["sharp_bound_width"]
                           for a,b in zip(matching[:-1],matching[1:]))
            assert all(r["estimated_design_variance"]>=0. for r in cell)
            assert all(r["oracle_conditional_design_variance_only"]>=0. for r in cell)
            assert all(r["release_authorized"] is False for r in cell)
            assert all(r["finite_replicate_mean_exact_unbiased_claim"] is False for r in cell)


def test_full_archive_required_and_bad_shards_fail_closed(tmp_path):
    with pytest.raises(ValueError,match="four-block"):
        r91.shard(tmp_path/"invalid",2,6)
    with pytest.raises(ValueError,match="all eight"):
        r91.aggregate(tmp_path/"out",tmp_path/"noarchive")
    with pytest.raises(ValueError,match="ledger incomplete"):
        r91.summarize([])
