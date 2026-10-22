"""R90-A independent source-equation, observed-only and provenance contracts."""
import numpy as np
import pytest
from pathlib import Path
from scripts import audit_w3_r90_original_saturation_independent as independent
from scripts import run_w3_r90_audit_saturation as original


def test_independent_generation_is_frozen_and_distinct_from_r89():
    assert independent.EXPECTED_ROWS==1280
    assert independent.ORIGINAL_CHECKOUT=="2f713c36cdb9977e8277e5a0412e4b162f2aedf2"
    assert independent.AUDITS==(0.,.25,.5,.75,1.)
    assert independent.SOURCE_SEEDS==original.SEEDS
    for config in independent.CONFIGS:
        X,Y,mu=independent.source(0,config)
        x,y,p=original.generate(0,config)
        np.testing.assert_array_equal(X,x)
        np.testing.assert_allclose(Y,y,rtol=1e-12,atol=1e-12)
        np.testing.assert_allclose(mu,p,rtol=1e-12,atol=1e-12)
        assert independent.sha_float(Y)==original.digest(y)
        mask_u=independent.uniform(0,config,"mask",Y.shape)
        for mechanism in independent.MECHANISMS:
            a=independent.stage_one(X,Y,mu,mask_u,mechanism)
            b=original.first_stage_missing(X,Y,mu,mask_u,mechanism)
            np.testing.assert_array_equal(a,b)
            assert independent.sha_bool(a)==original.mask_digest(b)


def test_independent_observed_only_bounds_and_tamper():
    eligible=np.array([1,1,1,0],dtype=bool)
    seen=np.array([1,0,1,0],dtype=bool)
    y=np.array([-.5,np.nan,.5,100000.])
    r=independent.compute_interval(y,eligible,seen)
    assert r["total_n"]==3 and r["returned_n"]==2
    assert r["lower"]==pytest.approx(1./3.)
    assert r["width"]==pytest.approx(1./3.)
    y[3]=-100000.
    assert independent.compute_interval(y,eligible,seen)==r
    with pytest.raises(ValueError,match="leaked"):
        y[1]=.2
        independent.compute_interval(y,eligible,seen)
    with pytest.raises(ValueError,match="original numerical disagreement"):
        independent.numeric_equal(.1,.5,"damaged")
    with pytest.raises(ValueError,match="archive incomplete"):
        independent.audit(Path("/nonexistent/r90/source"))


def test_original_one_block_saturation_matches_independent_score_algebra():
    c="independent_curves"
    X,Y,mu=independent.source(0,c)
    U={name:independent.uniform(0,c,name,Y.shape) for name in
       ("mask","secondary","assignment","return")}
    missing=independent.stage_one(X,Y,mu,U["mask"],"MNAR")
    secondary=independent.secondary_success(Y,mu,missing,U["secondary"])
    rows=original.evaluate(0,c)
    for law in independent.RETURN_LAWS:
        complete=independent.audit_completion(X,Y,mu,law)
        for q in independent.AUDITS:
            assigned=missing&~secondary&(U["assignment"]<q)
            returned=assigned&(U["return"]<complete)
            row=next(r for r in rows if r["mechanism"]=="MNAR"
                     and r["return_law"]==law and r["audit_fraction"]==q)
            measured=np.where(secondary|returned,Y,np.nan)
            measured_mask=secondary|returned
            z=independent.compute_interval(measured,missing,measured_mask)
            for field in ("lower","upper","width","total_n","returned_n"):
                independent.numeric_equal(row["mean_bounds"][field],z[field],
                                          "independent-original/"+field)
            assert row["audit_assigned_digest"]==independent.sha_bool(assigned)
            assert row["audit_returned_digest"]==independent.sha_bool(returned)
