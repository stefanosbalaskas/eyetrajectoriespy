"""R49 original covariance-refit bootstrap-t numerical and source contracts."""
import numpy as np
import pytest

from scripts import run_w3_r48_independent_fitted_cr2 as r48
from scripts import run_w3_r49_nuisance_refit_bootstrap_t as r49
from scripts.w3_r25_gaussian_reml_components import prepare_reml_design


def test_frozen_new_independent_source_and_all_refusal_denominators():
    assert r49.SOURCE_SEED!=r48.MASTER_SEED
    assert r49.BLOCKS==8 and r49.PARTICIPANTS==24
    assert r49.N_SOURCES==16
    assert r49.N_INTERVALS==48
    assert r49.N_BOOT==31
    assert r49.N_BOOT_ATTEMPTS==496
    assert r49.N_NUMERICAL_STARTS==1024
    assert r49.KKT_TOL==1e-3
    assert r49.NOMINAL==.90
    assert r49.TARGETS==(
        "known_oracle_conditional_Satterthwaite",
        "fitted_REML_conditional_Satterthwaite",
        "fitted_REML_parametric_refit_bootstrap_t",
    )


def test_source_independence_and_genuine_leverage_pairing():
    ordinary=r49.source(0,r49.SUPPORT[0])
    extreme=r49.source(0,r49.SUPPORT[1])
    independent=r49.source(1,r49.SUPPORT[0])
    prior=r48.original_source(0,r48.SUPPORT[0])
    np.testing.assert_array_equal(
        ordinary[0]["participant_intercept"],
        extreme[0]["participant_intercept"])
    assert not np.array_equal(
        ordinary[0]["participant_intercept"],
        independent[0]["participant_intercept"])
    assert not np.array_equal(
        ordinary[0]["participant_intercept"],
        prior[0]["participant_intercept"])
    assert extreme[2][np.flatnonzero(extreme[3]==0)[0]]==pytest.approx(3.)
    assert extreme[2][np.flatnonzero(extreme[3]==1)[0]]==pytest.approx(-2.5)
    with pytest.raises(ValueError,match="outside"):
        r49.source(8,r49.SUPPORT[0])


def test_four_component_physical_objective_and_analytic_gradient_consistent():
    data=r49.original_problem(0,r49.SUPPORT[0])
    X,y,w,g,t,tr,x=(data[k] for k in (
        "X","y","w","group","time","trial","x"))
    prep=prepare_reml_design(
        X,y,w,g,t,tr,x,slope=r49.SLOPE_FAMILY)
    Z=X*np.sqrt(w)[:,None]
    beta=np.linalg.lstsq(Z,y*np.sqrt(w),rcond=None)[0]
    ref=max(float(np.mean((y-X@beta)**2)),1e-8)
    ratios=np.array([.1,.2,.4,1.1])
    value,gradient=r49._objective(ratios,prep,ref)
    assert np.isfinite(value)
    assert gradient.shape==(4,)
    for j in range(4):
        dx=np.zeros(4);dx[j]=1e-5
        right=r49._objective(ratios+dx,prep,ref)[0]
        left=r49._objective(ratios-dx,prep,ref)[0]
        assert gradient[j]==pytest.approx(
            (right-left)/(2e-5),rel=2e-4,abs=1e-4)
    assert r49._physical_kkt(gradient,ratios).shape==(4,)
    with pytest.raises(ValueError):
        r49._objective([1.,2.,3.],prep,ref)


def test_parametric_resample_depends_on_observed_fitted_target_not_true_oracle():
    data=r49.original_problem(0,r49.SUPPORT[0])
    fitted=r49.fit_nuisance(data)
    assert len(fitted["numerical_starts"])==2
    assert fitted["global_optimum_proven"] is False if fitted["status"]=="accepted" else True
    if fitted["status"]!="accepted":
        pytest.skip("valid original numerical refusal preserved in independent science")
    simulated,seed=r49.parametric_draw(
        data,fitted["working_blocks"],0,r49.SUPPORT[0],0)
    repeated,seed2=r49.parametric_draw(
        data,fitted["working_blocks"],0,r49.SUPPORT[0],0)
    assert seed==seed2
    np.testing.assert_array_equal(simulated,repeated)
    assert np.isfinite(simulated).all()
    assert not np.array_equal(simulated,data["y"])
    without_oracle={k:v for k,v in data.items() if k!="oracle_covariance"}
    copied,_=r49.parametric_draw(
        without_oracle,fitted["working_blocks"],0,r49.SUPPORT[0],0)
    np.testing.assert_array_equal(simulated,copied)


def test_explicit_numerical_refusal_and_incomplete_bootstrap_never_covered():
    miss=r49.refused_interval(r49.TARGETS[2],"one refused refit")
    assert miss["truth_included"] is False
    assert miss["status"]=="refused"
    original={
        "block":0,"support":r49.SUPPORT[0],
        "source_status":"failed",
        "original_numerical_fit":{
            "status":"not_attempted",
            "numerical_starts":[
                {"label":a,"status":"not_attempted"}
                for a,_ in r49.START_RATIOS]},
        "intervals":[
            r49.refused_interval(target,"source_failed")
            for target in r49.TARGETS],
        "bootstrap_attempts":[
            {"replicate":rep,"status":"not_attempted",
             "numerical_starts":[
                 {"label":a,"status":"not_attempted"}
                 for a,_ in r49.START_RATIOS]}
            for rep in range(r49.N_BOOT)],
    }
    report=r49.summarize([original])
    assert report["recorded_interval_records"]==3
    assert report["recorded_nuisance_solver_start_slots"]==64
    assert report["planned_nuisance_solver_start_slots"]==1024
    assert report["pointwise_90_nominal_NOT_qualified"]
    assert not report["complete_failure_inclusive_ledger"]
    assert not report["release_authorized"]
    with pytest.raises(ValueError,match="duplicate"):
        r49.summarize([original,original])
