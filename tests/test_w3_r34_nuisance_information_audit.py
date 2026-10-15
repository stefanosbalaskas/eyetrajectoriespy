"""R34 local nuisance information is diagnostic, not interval calibration."""
import numpy as np
import pytest
from scripts import run_w3_r34_nuisance_information_audit as r34
from scripts import run_w3_r17_fresh_feasibility as fresh
from scripts import run_w3_r16_leverage_covariance_factorial as r16
from scripts.w3_r25_gaussian_reml_components import estimate_reml_components


def test_fresh_source_and_extreme_leverage_contract():
    assert r34.MASTER_SEED not in (202610153232,202610153333)
    assert r34.BLOCKS==4
    assert r34.PLANNED==16
    a=r34.observed_native_problem(0,"extreme_dependent")
    b=fresh.fresh_source(0,"extreme_dependent",n=24,master_seed=r34.MASTER_SEED,
                         n_blocks=4,max_n=24)
    X,y,w,g,t,tr,x,c=a
    assert len(np.unique(g))==24
    np.testing.assert_array_equal(y,np.concatenate([v[:,0] for v in b[1].values]))
    assert c.shape==(X.shape[1],)
    assert c.shape[0]==2*r16.basis(np.array([.5]),"legendre5").shape[1]
    assert x[np.flatnonzero(g==0)[0]]==3
    assert x[np.flatnonzero(g==1)[0]]==-2.5


def test_covariance_perturbations_are_positive_and_native_only():
    data=r34.observed_native_problem(0,"ordinary_dependent")
    X,y,w,g,t,tr,x,c=data
    fit=estimate_reml_components(X,y,w,g,t,tr,x,slope="predictor_scaled_slope")
    assert fit["status"]=="ok"
    theta=np.array([fit["variance_components"][key] for key in r34.COMPONENTS])
    base=r34.covariance_from_components(g,t,tr,x,w,"predictor_scaled_slope",theta)
    metric=r34.cr2_local_metric(data,"predictor_scaled_slope",np.log(theta))
    np.testing.assert_allclose(metric["cr2_se"],r34.cr2_local_metric(
        data,"predictor_scaled_slope",np.log(theta))["cr2_se"],rtol=0,atol=0)
    change=r34.covariance_from_components(g,t,tr,x,w,"predictor_scaled_slope",
                     theta*np.array([1.0,1.02,1.0,1.0]))
    assert np.linalg.norm(change[0]-base[0])>0
    assert np.linalg.eigvalsh(change[0])[0]>0
    assert metric["halfwidth_90"]>0 and metric["conditional_df"]>0


def test_unregistered_covariance_or_nonpositive_variance_refused():
    d=r34.observed_native_problem(0,"ordinary_dependent")
    X,y,w,g,t,tr,x,c=d
    with pytest.raises(ValueError,match="undeclared"):
        r34.covariance_from_components(g,t,tr,x,w,"invented_model",np.ones(4))
    with pytest.raises(ValueError,match="strictly positive"):
        r34.covariance_from_components(g,t,tr,x,w,"shared_slope",np.array([1.,0.,1.,1.]))


def test_failure_inclusive_local_diagnostic_not_coverage():
    x=r34.evaluate(0,"ordinary_dependent","predictor_scaled_slope")
    assert x["generated"],x["source_error"]
    assert x["reml_status"] in ("ok","failed","nonconverged")
    assert x["true_generating_covariance_not_supplied_to_nuisance_fit"]
    assert x["observed_information_status"] in (
        "usable_for_local_diagnostic","refused","not_attempted")
    assert x["local_metric_status"] in ("ok","refused","not_attempted")
    if x["local_metric_status"]=="ok":
        assert x["gradient_step_relative_deviation"]<=.1
        assert x["max_abs_df_derivative"]>=0
    report=r34.summarize([x])
    assert report["recorded_cases"]==1
    assert report["missing_cases"]==15
    assert report["observed_curvature_delta_sd_not_coefficient_ci_correction"]
    assert not report["pointwise_coverage_qualified"]
    assert not report["release_authorized"]


def test_refusal_bookkeeping_does_not_exclude_original_denominator():
    x=r34.evaluate(0,"ordinary_dependent","predictor_scaled_slope")
    y=dict(x,source_support="extreme_dependent",
           local_metric_status="refused",
           observed_information_status="not_attempted",
           local_metric_error={"type":"OriginalNumericalRefusal"})
    report=r34.summarize([x,y])
    assert report["recorded_cases"]==2
    assert report["missing_cases"]==14
    assert report["cr2_derivative_refusals"]>=1
    assert report["pointwise_coverage_qualified"] is False
