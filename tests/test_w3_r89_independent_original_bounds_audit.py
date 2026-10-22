"""Independent R89-A source and sharp-bound audit contracts."""
import numpy as np
import pytest
from scripts import audit_w3_r89_original_finite_bounds_independent as a
from scripts import run_w3_r89_bounded_missing_gaze as s


def test_source_and_mask_independent_implementation():
    assert a.EXPECTED_ROWS==512
    assert a.ORIGINAL_CHECKOUT=="656df21a042e0e823147e37002580aeba41ac17d"
    assert a.SOURCE_SEEDS==s.SEEDS
    for c in a.CONFIGS:
        X,Y,mu=a.source(0,c)
        orig_x,orig_y,orig_mu=s.generate(0,c)
        np.testing.assert_array_equal(X,orig_x)
        np.testing.assert_allclose(Y,orig_y,rtol=1e-12,atol=1e-12)
        np.testing.assert_allclose(mu,orig_mu,rtol=1e-12,atol=1e-12)
        assert a.sha_float(Y)==s.digest(orig_y)
        U=a.uniform(0,c,"mask",Y.shape)
        for law in a.MECHANISMS:
            ma=a.stage_one(X,Y,mu,U,law)
            mb=s.first_stage_missing(orig_x,orig_y,orig_mu,U,law)
            np.testing.assert_array_equal(ma,mb)
            assert a.sha_bool(ma)==s.mask_digest(mb)


def test_bound_independence_and_tamper_failures():
    mask=np.array([True,True,True,False])
    recovered=np.array([True,False,True,False])
    vis=np.array([-.5,np.nan,.5,42.])
    r=a.compute_interval(vis,mask,recovered)
    assert r["total_n"]==3
    assert r["returned_n"]==2
    assert r["width"]==pytest.approx(1/3)
    assert r["lower"]==pytest.approx((.25+.75)/3)
    with pytest.raises(ValueError,match="leaked"):
        a.compute_interval(np.array([-.5,.2,.5,42.]),mask,recovered)
    with pytest.raises(ValueError,match="original numerical"):
        a.numeric_equal(.1,.6,"tampered-result")
    with pytest.raises(ValueError,match="original field"):
        a.numeric_equal("good","corrupt","tampered-identity")
    with pytest.raises(ValueError,match="archive incomplete"):
        a.audit(__import__("pathlib").Path("/not/a/r89/archive"))
