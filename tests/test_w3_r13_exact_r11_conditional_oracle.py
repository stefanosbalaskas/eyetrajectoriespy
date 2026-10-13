"""Exact R11 complete-source identity and R13 Gaussian oracle contracts."""
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
import pytest
from scipy.stats import norm

from scripts.run_w3_r11_paired_observation_process import (
    original_full_source,recorded_case,
)
from scripts.run_w3_r13_exact_r11_conditional_oracle import (
    BLOCKS, COHORTS, MODELS, HISTORICAL_SEED, FRESH_SEED, N_PARTICIPANTS,
    METHODS, CONFIDENCE, TOL, replay_r11_generator, source,
    wls_and_conditional_oracle, case, audit, wilson, bootstrap_ci,
)


@pytest.mark.parametrize("block",[0,1,17,95])
def test_historical_source_replay_exactly_matches_original_r11(block):
    old=original_full_source(block,"baseline")
    replay=replay_r11_generator(block,HISTORICAL_SEED)
    for key in ("time","values","conditional_mean","x","n_trials",
                "dropout_uniforms","true_slope"):
        np.testing.assert_array_equal(replay[key],old[key],
                                      err_msg=f"{key} mismatch in source {block}")


def test_fresh_r11_dgp_is_independent_seed_but_same_source_structure():
    legacy=source(0,"historical_R11")
    fresh=source(0,"fresh_R11_DGP")
    assert HISTORICAL_SEED!=FRESH_SEED
    assert not np.array_equal(legacy["values"],fresh["values"])
    assert not np.array_equal(legacy["x"],fresh["x"])
    assert legacy["time"].shape==fresh["time"].shape
    assert len(np.unique(fresh["x"]))==N_PARTICIPANTS
    assert np.all(np.diff(fresh["time"],axis=2)>0)
    for co in COHORTS:
        assert 1<=source(0,co)["n_trials"].min()
        assert source(0,co)["n_trials"].max()<=3


@pytest.mark.parametrize("model",MODELS)
@pytest.mark.parametrize("cohort",COHORTS)
def test_historical_and_fresh_conditional_gaussian_oracle_numerics(model,cohort):
    src=source(0,cohort)
    recorded=recorded_case(src,"complete")
    d=wls_and_conditional_oracle(recorded,model)
    assert d["n_points"]==int(sum(map(len,recorded["gaze"].time)))
    assert d["n_trials"]==int(src["n_trials"].sum())
    assert d["source_qr_max_diff"]<=TOL
    assert d["participant_score_max_diff"]<=TOL
    assert d["original_cr1_max_diff"]<=TOL
    assert d["oracle_se"]>0
    assert d["cr1_se"]>0
    assert np.isfinite(d["projection"])
    assert np.isfinite(d["estimate"])
    assert d["r11_width"]>0
    src_case=case(0,cohort,model)
    assert src_case["status"]=="ok",src_case["exception"]
    assert src_case["native_W3_rejected"]
    assert src_case["source_immutable"]
    assert src_case["n_independent_participants"]==N_PARTICIPANTS
    assert set(src_case["methods"])==set(METHODS)
    assert json.loads(json.dumps(src_case))["status"]=="ok"
    assert not src_case["release_authorized"]


def test_oracle_variance_is_not_identical_to_cr1_and_has_distinct_inference():
    src=source(1,"historical_R11")
    r=recorded_case(src,"complete")
    d=wls_and_conditional_oracle(r,"legendre5")
    assert not np.isclose(d["oracle_se"],d["cr1_se"],atol=1e-10,rtol=1e-10)
    assert np.isclose(d["r11_width"],
                      2*d["cr1_se"]*__import__("scipy").stats.t.ppf(
                          (1+CONFIDENCE)/2,N_PARTICIPANTS-1),atol=TOL)


def test_known_conditional_gaussian_covariance_by_independent_point_simulation():
    # The source code's analytical oracle is also checked against an
    # independent conditional Monte Carlo computation with same ORIGINAL
    # observed design but new independent latent participant/trial/sensor
    # innovations. This tests the variance model, not empirical coverage.
    src=source(0,"historical_R11")
    r=recorded_case(src,"complete")
    x=r["x"];ids=r["units"];n=N_PARTICIPANTS
    trial_counts=np.bincount(ids,minlength=n)
    all_X=[];all_weights=[];all_variance_components=[]
    from scripts.run_w3_r9_mean_basis_selection_stress import basis,TIME
    from scripts.run_w3_r12_complete_cluster_variance_oracle import (
        SIGMA_INTERCEPT,SIGMA_RANDOM_SLOPE,SIGMA_TRIAL,SIGMA_SENSOR,
    )
    for c,(t,v) in enumerate(zip(r["gaze"].time,r["gaze"].values)):
        B=basis(t,"legendre5")
        Xi=np.column_stack((B,B*float(x[c])))
        w=1/(len(t)*trial_counts[ids[c]])
        all_X.append(Xi);all_weights.append(w)
    Q=sum(w*Xi.T@Xi for Xi,w in zip(all_X,all_weights))
    contrast=np.r_[np.zeros(6),basis(np.array([TIME[15]]),"legendre5")[0]]
    G=np.linalg.solve(Q,contrast)
    # Each latent component's influence on midpoint estimate is linear.
    coeff_per_person=np.zeros((n,2))
    trial_coeffs=[]
    sensor_var=0.
    for c,(t,Xi,w) in enumerate(zip(r["gaze"].time,all_X,all_weights)):
        pid=ids[c];xi=x[c]
        coeff_per_person[pid,0]+=SIGMA_INTERCEPT*w*G@Xi.T@(1+.30*t)
        coeff_per_person[pid,1]+=SIGMA_RANDOM_SLOPE*w*G@Xi.T@(xi*(1+.25*t))
        trial_coeffs.append(SIGMA_TRIAL*w*G@Xi.T@np.ones(len(t)))
        sensor_var+=sum((SIGMA_SENSOR*w*(Xi@G))**2)
    independent_se=np.sqrt(float(np.sum(coeff_per_person**2)+
                                 np.sum(np.square(trial_coeffs))+sensor_var))
    fit=wls_and_conditional_oracle(r,"legendre5")
    np.testing.assert_allclose(independent_se,fit["oracle_se"],atol=3e-10)


def test_failure_ledger_and_monte_carlo_units_never_drop_cases():
    a=case(0,"historical_R11","legendre5")
    b=dict(a,model="cubic_spline13",status="failed",
           exception={"type":"ForcedFailure"})
    report=audit([a,b])
    assert report["n_original_source_cases_expected"]==2*BLOCKS*len(MODELS)
    assert report["recorded_cases"]==2
    assert report["completed_cases"]==1
    assert report["failed_cases"]==1
    assert len(report["missing_cases"])==report["n_original_source_cases_expected"]-2
    assert not report["release_authorized"]
    assert wilson(0,0) is None
    assert abs(wilson(0,96)[0])<1e-12
    assert wilson(96,96)[1]==1
    assert bootstrap_ci([1,-2,.2],112)==bootstrap_ci([1,-2,.2],112)
    with pytest.raises(ValueError,match="duplicate"):
        audit([a,a])


def test_guardrails_and_source_seed_identity():
    with pytest.raises(ValueError,match="outside"):
        replay_r11_generator(BLOCKS,HISTORICAL_SEED)
    with pytest.raises(ValueError,match="undeclared"):
        source(0,"post_hoc_selected")
    assert source(0,"fresh_R11_DGP")["block"]==0
