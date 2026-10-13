"""W3 R15 finite-person source/leverage and actual delete-person cluster contracts."""
from pathlib import Path
import sys
import numpy as np
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.run_w3_r15_fresh_cluster_leverage import (
    BLOCKS,SIZES,SUPPORT,MODELS,METHODS,MAX_N,NUMERICAL_TOL,
    generating_block,source,fit,evaluate,audit,wilson,mc_interval,
)


def test_new_independent_source_and_nested_participants_without_fake_trials():
    a=generating_block(0)
    b=generating_block(1)
    assert a["x"].shape==(MAX_N,)
    assert not np.array_equal(a["sensor_noise"],b["sensor_noise"])
    for n in SIZES:
        regular=source(0,n,"ordinary")
        extreme=source(0,n,"two_extreme_predictors")
        src1,g1,x1,u1,tr1,mu1=regular
        src2,g2,x2,u2,tr2,mu2=extreme
        assert len(np.unique(u1))==n
        assert len(g1.curve_ids)==int(src1["n_trials"][:n].sum())
        assert len(g2.curve_ids)==len(g1.curve_ids)
        np.testing.assert_array_equal(src1["time"],src2["time"])
        np.testing.assert_array_equal(src1["sensor_noise"],src2["sensor_noise"])
        np.testing.assert_array_equal(u1,u2)
        np.testing.assert_array_equal(tr1,tr2)
        assert x2[0]==3.0
        assert x2[int(src1["n_trials"][0])]==-2.5
        assert np.array_equal(x1[int(sum(src1["n_trials"][:2])):],
                              x2[int(sum(src1["n_trials"][:2])):])
        for ta,tb in zip(g1.time,g2.time):
            np.testing.assert_array_equal(ta,tb)


@pytest.mark.parametrize("model",MODELS)
@pytest.mark.parametrize("support",SUPPORT)
@pytest.mark.parametrize("n",SIZES)
def test_new_original_source_numerical_and_cluster_jackknife_contracts(model,support,n):
    generated=source(0,n,support)
    d=fit(generated,model)
    assert d["qr_delta"]<=NUMERICAL_TOL
    assert d["score_delta"]<=NUMERICAL_TOL
    assert d["native_trials"]>=n
    assert d["native_points"]>=n*31
    assert 0<d["max_block_leverage"]<1
    assert d["mean_block_leverage"]<d["max_block_leverage"]
    assert abs(d["project"]-d["known_mid_slope"])<1e-5
    assert d["jack_se"]>0 and d["cr1_se"]>0 and d["oracle_se"]>0
    r=evaluate(0,n,support,model)
    assert r["status"]=="ok",r["exception"]
    assert r["complete_native_source"] and r["public_dense_W3_rejects_async"]
    assert set(r["methods"])==set(METHODS)
    assert r["methods"]["cr1_t"]["width"]>r["methods"]["cr1_normal"]["width"]
    assert r["methods"]["oracle_t"]["width"]>r["methods"]["oracle_normal"]["width"]
    assert not r["release_authorized"] and not r["method_winner_selected"]


@pytest.mark.parametrize("n",SIZES)
@pytest.mark.parametrize("model",MODELS)
def test_predictor_extreme_is_actual_source_leverage_stressor(n,model):
    normal=fit(source(0,n,"ordinary"),model)
    outlier=fit(source(0,n,"two_extreme_predictors"),model)
    assert outlier["first_two_mean_block_leverage"]>normal["first_two_mean_block_leverage"]
    assert outlier["max_block_leverage"]>normal["max_block_leverage"]


def test_conditional_oracle_against_independent_dense_same_person_covariance():
    # Reconstruct the known Gaussian covariance from the original n=24
    # repeated time series without using the implementation's sufficient
    # statistic. This specifically checks participant-shared covariance.
    from scripts.run_w3_r9_mean_basis_selection_stress import basis
    from scripts.run_w3_r12_complete_cluster_variance_oracle import (
        SIGMA_INTERCEPT,SIGMA_RANDOM_SLOPE,SIGMA_TRIAL,SIGMA_SENSOR)
    original=source(0,24,"ordinary")
    src,gaze,x,person,trials,means=original
    z=fit(original,"legendre5")
    k=6;p=12
    fullQ=np.zeros((p,p))
    components=[]
    n_trials=np.bincount(person,minlength=24)
    for c,(t,y) in enumerate(zip(gaze.time,gaze.values)):
        b=basis(t,"legendre5")
        X=np.column_stack((b,b*x[c]))
        w=1/(n_trials[person[c]]*len(t))
        fullQ+=w*X.T@X
        components.append((X,t,x[c],int(person[c]),int(trials[c]),w))
    h=np.r_[np.zeros(k),basis(np.array([.5]),"legendre5")[0]]
    direction=np.linalg.solve(fullQ,h)
    per_person=np.zeros((24,2));per_trial=[];sensor=0.
    for X,t,xi,pid,tid,w in components:
        per_person[pid,0]+=SIGMA_INTERCEPT*w*direction@X.T@(1+.30*t)
        per_person[pid,1]+=SIGMA_RANDOM_SLOPE*w*direction@X.T@(xi*(1+.25*t))
        per_trial.append(SIGMA_TRIAL*w*direction@X.T@np.ones(len(t)))
        sensor+=np.sum(np.square(SIGMA_SENSOR*w*(X@direction)))
    independent=np.sqrt(np.sum(np.square(per_person))+
                        np.sum(np.square(per_trial))+sensor)
    np.testing.assert_allclose(z["oracle_se"],independent,atol=1e-10,rtol=1e-9)


def test_source_failures_not_disappeared_from_audit():
    ok=evaluate(0,24,"ordinary","legendre5")
    bad=dict(ok,support="two_extreme_predictors",status="failed",
             exception={"type":"ReferenceFailure"})
    report=audit([ok,bad])
    assert report["planned_cases"]==BLOCKS*len(SIZES)*len(SUPPORT)*len(MODELS)
    assert report["completed_cases"]==1 and report["failed_cases"]==1
    assert report["recorded_cases"]==2
    assert len(report["missing_cases"])==report["planned_cases"]-2
    assert report["no_method_winner"] and not report["release_authorized"]
    with pytest.raises(ValueError,match="duplicate"):
        audit([ok,ok])


def test_predeclared_source_seed_failure_guards_and_mc_denominator():
    with pytest.raises(ValueError,match="not predeclared"):
        generating_block(BLOCKS)
    with pytest.raises(ValueError,match="undeclared"):
        source(0,15,"ordinary")
    with pytest.raises(ValueError,match="undeclared"):
        source(0,24,"posthoc")
    with pytest.raises(ValueError,match="undeclared"):
        fit(source(0,24,"ordinary"),"selected_after_results")
    assert wilson(0,0) is None
    assert abs(wilson(0,96)[0])<1e-12
    assert wilson(96,96)[1]==1
    assert mc_interval([-.1,.2,.3],31)==mc_interval([-.1,.2,.3],31)
