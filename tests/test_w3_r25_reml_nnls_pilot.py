"""R25 REML mathematical score and paired failure-inclusive experiment guards."""
import numpy as np
import pytest

from scripts import run_w3_r17_fresh_feasibility as original
from scripts import run_w3_r16_leverage_covariance_factorial as r16
from scripts import run_w3_r25_reml_nnls_pilot as pilot
from scripts.w3_r20_estimated_working_target import (
    COMPONENTS,observed_weighted_rows)
from scripts.w3_r25_gaussian_reml_components import (
    estimate_reml_components,prepare_reml_design,
    restricted_loglik_and_gradient)


def observed_rows(block=0,support="ordinary_independent"):
    d=original.fresh_source(block,support,n=24,master_seed=pilot.MASTER_SEED,
        n_blocks=pilot.BLOCKS,max_n=max(pilot.SIZES))
    return observed_weighted_rows((None,d[1],d[2],d[3],d[4],None),"legendre5")


def test_analytic_reml_log_variance_score_matches_finite_differences():
    X,y,w,g,t,tr,x=observed_rows()
    parts=prepare_reml_design(X,y,w,g,t,tr,x,slope="shared_slope")
    theta_ref=max(float(np.var(y)),1e-3)
    u=np.log(np.array([.09,.04,.02,.015])/theta_ref)
    f,grad=restricted_loglik_and_gradient(u,parts,theta_ref)
    numeric=[]
    eps=1e-5
    for k in range(len(COMPONENTS)):
        dx=np.zeros(len(COMPONENTS));dx[k]=eps
        plus=restricted_loglik_and_gradient(u+dx,parts,theta_ref)[0]
        minus=restricted_loglik_and_gradient(u-dx,parts,theta_ref)[0]
        numeric.append((plus-minus)/(2*eps))
    np.testing.assert_allclose(grad,numeric,rtol=7e-5,atol=1e-5)
    assert np.isfinite(f)


def test_reml_restricted_objective_ignores_shifts_in_fixed_mean_space():
    X,y,w,g,t,tr,x=observed_rows()
    prepared=prepare_reml_design(X,y,w,g,t,tr,x,slope="shared_slope")
    p=X.shape[1]
    shifted=prepare_reml_design(
        X,y+X@np.linspace(-.8,.7,p),w,g,t,tr,x,slope="shared_slope")
    theta_ref=.08
    u=np.log(np.array([.08,.03,.02,.04])/theta_ref)
    f0,g0=restricted_loglik_and_gradient(u,prepared,theta_ref)
    f1,g1=restricted_loglik_and_gradient(u,shifted,theta_ref)
    np.testing.assert_allclose(f0,f1,rtol=1e-9,atol=1e-7)
    np.testing.assert_allclose(g0,g1,rtol=1e-8,atol=1e-6)


@pytest.mark.parametrize("support,family",[
    ("ordinary_independent","shared_slope"),
    ("ordinary_dependent","predictor_scaled_slope"),
])
def test_observable_only_optimizer_reports_convergence_or_refusal(support,family):
    X,y,w,g,t,tr,x=observed_rows(support=support)
    result=estimate_reml_components(X,y,w,g,t,tr,x,slope=family,maxiter=110)
    assert result["status"] in ("ok","nonconverged")
    assert result["estimated_from_observed_responses"]
    assert not result["uses_source_gaussian_oracle"]
    assert not result["estimated_nuisance_uncertainty_accounted_for"]
    assert not result["component_covariance_qualified"]
    assert not result["public_api_authorized"]
    assert len(result["working_blocks"])==24
    assert all(v>0 for v in result["variance_components"].values())
    assert np.isfinite(result["restricted_negative_loglik"])


def test_paired_original_source_accounting_and_truth_boundary():
    assert pilot.BLOCKS==4
    assert pilot.EXPECTED==64
    assert pilot.MASTER_SEED not in (
        original.R17_SEED,r16.SEED,202610153301)
    case=pilot.evaluate(0,24,"ordinary_independent","shared_slope")
    assert case["source_generated"]
    assert case["truth_passed_to_estimator"] is False
    assert case["no_inferential_coverage_evaluated"] is True
    assert not case["release_authorized"]
    for name in pilot.METHODS:
        assert name in case["methods"]
        method=case["methods"][name]
        if method["status"]=="ok":
            assert len(method["absolute_relative_component_errors_matched_only"])==4
    a=pilot.summarize([case])
    assert a["missing_cases"]==63
    assert a["no_coverage_computed"]
    assert not a["release_authorized"]


def test_invalid_observed_design_and_undeclared_covariance_family():
    X,y,w,g,t,tr,x=observed_rows()
    with pytest.raises(ValueError,match="predeclared"):
        prepare_reml_design(X,y,w,g,t,tr,x,slope="oracle_correct")
    with pytest.raises(ValueError):
        prepare_reml_design(X,y,np.zeros_like(w),g,t,tr,x,slope="shared_slope")
