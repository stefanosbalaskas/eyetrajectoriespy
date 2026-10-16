"""R53 original Gaussian REML score/Hessian/CR2 response influence contracts."""
import numpy as np
import pytest

from scripts import run_w3_r52_gaussian_cr2_joint_law as r52
from scripts import run_w3_r53_local_reml_influence as r53
from scripts import run_w3_r49_nuisance_refit_bootstrap_t as r49
from scripts.w3_r25_gaussian_reml_components import prepare_reml_design


def test_new_primitive_independence_and_frozen_refusal_denominators():
    assert r53.SOURCE_SEED != r52.MASTER_SEED
    assert r53.BLOCKS==4 and r53.PARTICIPANTS==24
    assert r53.N_SOURCE==8
    assert r53.N_DIRECTION==24
    assert r53.N_PERTURBED_FITS==48
    assert r53.N_TOTAL_FITS==56
    assert r53.N_SOLVER_STARTS==112
    assert r53.KKT_LIMIT==.001
    a=r53.source(0,r53.SUPPORT[0])
    paired=r53.source(0,r53.SUPPORT[1])
    independent=r53.source(1,r53.SUPPORT[0])
    older=r52.source(0,r52.SUPPORT[0])
    np.testing.assert_array_equal(
        a[0]["participant_intercept"],paired[0]["participant_intercept"])
    assert not np.array_equal(
        a[0]["participant_intercept"],independent[0]["participant_intercept"])
    assert not np.array_equal(
        a[0]["participant_intercept"],older[0]["participant_intercept"])
    with pytest.raises(ValueError,match="outside"):
        r53.source(4,r53.SUPPORT[0])


def _known_theta():
    # Far inside the inherited positive physical variance box.
    return np.array([.08,.06,.03,.2])


def test_original_REML_physical_gradient_Hessian_matches_independent_finite_differences():
    data=r53.problem(0,r53.SUPPORT[0])
    theta=_known_theta()
    m,g,H,B=r53.score_hessian(data,theta)
    prepared=prepare_reml_design(
        data["X"],data["y"],data["w"],data["group"],
        data["time"],data["trial"],data["x"],
        slope=r49.SLOPE_FAMILY)
    _,from_original=r49._objective(theta,prepared,1.)
    np.testing.assert_allclose(g,from_original,rtol=1e-6,atol=1e-6)
    assert H.shape==(4,4) and B.shape==(4,len(data["y"]))
    np.testing.assert_allclose(H,H.T,rtol=1e-10,atol=1e-8)
    assert np.linalg.norm(m["P"]@m["Z"])<1e-5*np.linalg.norm(m["Z"])
    for k in range(4):
        h=theta[k]*.0002
        a=theta.copy();b=theta.copy()
        a[k]+=h;b[k]-=h
        ga=r53.score_hessian(data,a)[1]
        gb=r53.score_hessian(data,b)[1]
        np.testing.assert_allclose(
            H[:,k],(ga-gb)/(2*h),rtol=5e-3,atol=2e-3)
    rng=np.random.default_rng(312)
    d=rng.standard_normal(len(data["y"]))
    eps=1e-5
    plus={**data,"y":data["y"]+eps*d/np.sqrt(data["w"])}
    minus={**data,"y":data["y"]-eps*d/np.sqrt(data["w"])}
    dg=(r53.score_hessian(plus,theta)[1]-
        r53.score_hessian(minus,theta)[1])/(2*eps)
    np.testing.assert_allclose(dg,-B@d,rtol=1e-5,atol=2e-4)


def test_CR2_variance_explicit_response_partial_and_nuisance_partial():
    data=r53.problem(0,r53.SUPPORT[0])
    theta=_known_theta()
    original=r53.cr2(data,theta)
    q=original["cr2_se"]**2
    p,steps=r53.gradient_of_CR2_variance(data,theta,q)
    assert p.shape==(4,) and len(steps)==4
    rng=np.random.default_rng(14)
    d=rng.standard_normal(len(data["y"]))
    e=1e-5
    xp={**data,"y":data["y"]+e*d/np.sqrt(data["w"])}
    xm={**data,"y":data["y"]-e*d/np.sqrt(data["w"])}
    qdiff=(r53.cr2(xp,theta)["cr2_se"]**2-
           r53.cr2(xm,theta)["cr2_se"]**2)/(2*e)
    _,_,a=r52.joint_geometry(
        data["X"],data["w"],data["group"],data["contrast"],
        r53.covariance_blocks(data,theta),
        r53.covariance_blocks(data,theta))
    h=a["score_rows"]
    grad=2*h.T@(h@(data["y"]*np.sqrt(data["w"])))
    assert qdiff==pytest.approx(float(grad@d),rel=2e-5,abs=1e-6)
    j=0
    e2=theta[j]*.0001
    up=theta.copy();dn=theta.copy()
    up[j]+=e2;dn[j]-=e2
    gd=(r53.cr2(data,up)["cr2_se"]**2-
        r53.cr2(data,dn)["cr2_se"]**2)/(2*e2)
    assert p[0]==pytest.approx(float(gd),rel=1e-4,abs=1e-3)


def test_bad_Hessian_boundary_implicitly_refused_not_regularized():
    bad={"status":"refused"}
    assert r53.local_influence(None,bad)["status"]=="refused"
    x=r53.perturb_record(0)
    assert x["status"]=="not_attempted"
    assert x["numerical_plus"] is None and x["numerical_minus"] is None


def test_all_planned_denominators_and_perturbation_refusals_preserved():
    fake={
        "block":0,"support":r53.SUPPORT[0],
        "original_nuisance":{
            "status":"not_attempted",
            "numerical_starts":[{"label":k,"status":"not_attempted"}
                                for k,_ in r49.START_RATIOS]},
        "influence_status":"refused",
        "perturbations":[r53.perturb_record(i) for i in range(r53.DIRECTIONS)],
    }
    report=r53.summary([fake])
    assert report["planned_response_perturbation_records"]==24
    assert report["recorded_response_perturbation_records"]==3
    assert report["recorded_plus_minus_fit_attempts"]==0
    assert report["planned_total_REML_fit_attempt_slots"]==56
    assert report["planned_two_start_optimizer_outcome_slots"]==112
    assert not report["complete_structural_source_and_perturbation_denominator"]
    assert not report["release_authorized"]
    with pytest.raises(ValueError,match="duplicate"):
        r53.summary([fake,fake])


def test_json_evidence_retains_numpy_derivative_vectors_without_nan(tmp_path):
    import json
    record={
        "partial_theta_gradient":np.array([1.,-2.,.0001]),
        "nested":{"matrix":np.eye(2),"scalar":np.float64(.25)},
    }
    destination=tmp_path/"evidence.json"
    r53._write(destination,record)
    recovered=json.loads(destination.read_text())
    assert recovered["partial_theta_gradient"]==[1.,-2.,.0001]
    assert recovered["nested"]["matrix"]==[[1.,0.],[0.,1.]]
    assert recovered["nested"]["scalar"]==.25
    with pytest.raises(ValueError):
        r53._write(destination,{"invalid":np.array([np.nan])})
