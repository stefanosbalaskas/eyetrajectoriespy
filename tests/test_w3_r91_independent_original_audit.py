"""R91-A independent source regeneration and observable-HT tamper contracts."""
from itertools import product
from pathlib import Path

import numpy as np
import pytest

from scripts import audit_w3_r91_original_completed_recovery_independent as audit
from scripts import run_w3_r91_guaranteed_random_recovery as original


def test_independent_source_and_mask_regeneration():
    assert audit.EXPECTED_ROWS==6144
    assert audit.ORIGINAL_CHECKOUT=="eb65592307e1c7bc70d5cd31794bae46996bc656"
    assert audit.SOURCE_SEEDS==original.SEEDS
    for config in audit.CONFIGS:
        x,y,mu=audit.source(0,config)
        X,Y,p=original.generate(0,config)
        np.testing.assert_array_equal(x,X)
        np.testing.assert_allclose(y,Y,rtol=1e-12,atol=1e-12)
        np.testing.assert_allclose(mu,p,rtol=1e-12,atol=1e-12)
        assert audit.sha_float(y)==original.digest(Y)
        missing_u=audit.uniform(0,config,"mask",y.shape)
        for law in audit.MECHANISMS:
            m=audit.stage_one(x,y,mu,missing_u,law)
            n=original.first_stage_missing(X,Y,p,missing_u,law)
            np.testing.assert_array_equal(m,n)
            assert audit.sha_bool(m)==original.mask_digest(n)


def test_independent_analytic_design_variance_exact_enumeration():
    values=np.array([-.5,0.,-.5,.5])
    mask=np.ones(4,bool)
    secondary=np.array([1,1,0,0],bool)
    outcomes=[]
    variances=[]
    for left,right in product([False,True],repeat=2):
        recovered=np.array([0,0,left,right],bool)
        visible=np.where(secondary|recovered,values,np.nan)
        v=audit.design_based_ht(visible,mask,secondary,recovered,.5)
        outcomes.append(v["ht"])
        variances.append(v["vhat"])
    truth=float(np.mean(audit.bounded(values)))
    z=audit.bounded(values[~secondary])
    oracle=float(np.dot(z,z))/(4*4)
    assert np.mean(outcomes)==pytest.approx(truth)
    assert np.var(outcomes)==pytest.approx(oracle)
    assert np.mean(variances)==pytest.approx(oracle)


def test_rejects_unreturned_hidden_y_and_incorrect_source():
    m=np.ones(4,bool)
    s=np.array([1,1,0,0],bool)
    a=np.array([0,0,1,0],bool)
    y=np.array([.2,.4,.5,np.nan])
    assert audit.design_based_ht(y,m,s,a,.25)["completed_n"]==1
    with pytest.raises(ValueError,match="hidden outcome"):
        audit.design_based_ht(np.array([.2,.4,.5,.9]),m,s,a,.25)
    with pytest.raises(ValueError,match="provenance"):
        audit.design_based_ht(y,m,s,s,.25)
    with pytest.raises(ValueError,match="inclusion probability"):
        audit.design_based_ht(y,m,s,a,0.)
    with pytest.raises(ValueError,match="archive incomplete"):
        audit.verify_original(Path("/path/that/does/not/exist"))


def test_original_recovery_subset_matches_independent_frozen_replicates():
    config="independent_curves"
    x,Y,mu=audit.source(0,config)
    missing=audit.stage_one(x,Y,mu,audit.uniform(0,config,"mask",Y.shape),"MNAR")
    sec=audit.secondary_success(Y,mu,missing,audit.uniform(0,config,"secondary",Y.shape))
    first=original.evaluate(0,config)
    for rep in (0,1,15):
        u=audit.random_recovery(0,config,rep,Y.shape)
        for g in audit.GUARANTEE_FRACTIONS:
            recovered=missing&~sec&(u<g)
            actual=next(r for r in first if r["mechanism"]=="MNAR"
                        and r["assignment_rep"]==rep and r["guarantee_fraction"]==g)
            val=audit.verify_row(actual,0,config,"MNAR",rep,g,x,Y,mu,missing,sec,recovered)
            assert np.isfinite(val["ht_error"])
            assert val["oracle_var"]>=0.
