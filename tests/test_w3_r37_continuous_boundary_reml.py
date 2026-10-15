"""R37 exact-zero continuous Gaussian REML score and multistart contracts."""
import numpy as np
import pytest
from scripts import run_w3_r37_continuous_boundary_reml as r37
from scripts.w3_r25_gaussian_reml_components import (
    estimate_reml_components,prepare_reml_design,restricted_loglik_and_gradient)


def model(support="ordinary_dependent",state="positive_slope"):
    case=r37.source(0,support,state)
    from scripts.w3_r20_estimated_working_target import observed_weighted_rows
    X,y,w,g,t,tr,x=observed_weighted_rows(
        (None,case[1],case[2],case[3],case[4],None),"legendre5")
    prep=prepare_reml_design(X,y,w,g,t,tr,x,slope="predictor_scaled_slope")
    fit=estimate_reml_components(X,y,w,g,t,tr,x,slope="predictor_scaled_slope")
    assert fit["status"]=="ok"
    ref=fit["reference_variance_scale_from_observed_residuals"]
    return prep,fit,ref


def test_source_coupling_and_strict_exact_zero():
    a=r37.source(0,"extreme_dependent","positive_slope")
    b=r37.source(0,"extreme_dependent","zero_slope")
    assert r37.BLOCKS==4 and r37.PLANNED==16
    assert r37.MASTER_SEED!=202610163636
    for x,y in zip(a[1].time,b[1].time):
        np.testing.assert_array_equal(x,y)
    for y_pos,y_null in zip(a[1].values,b[1].values):
        assert y_pos.shape==y_null.shape
    assert np.any(np.concatenate(a[1].values)!=np.concatenate(b[1].values))
    assert b[0] is None
    with pytest.raises(ValueError,match="unregistered"):
        r37.source(0,"wrong_support","zero_slope")


def test_analytic_continuous_objective_matches_R25_and_slope_score():
    prep,fit,reference=model()
    pars=np.array([np.log(fit["variance_components"][r37.COMPONENTS[k]]/reference)
                    for k in r37.FREE]+[
        fit["variance_components"]["participant_slope"]/reference])
    x,grad=r37.continuous_reml_objective(pars,prep,reference)
    logratios=np.empty(len(r37.COMPONENTS))
    logratios[list(r37.FREE)]=pars[:3]
    logratios[r37.SLOPE]=np.log(pars[3])
    y,g=restricted_loglik_and_gradient(logratios,prep,reference)
    np.testing.assert_allclose(x,y,atol=5e-9,rtol=1e-9)
    np.testing.assert_allclose(grad[:3],g[list(r37.FREE)],atol=2e-7,rtol=2e-6)
    np.testing.assert_allclose(grad[3],g[r37.SLOPE]/pars[3],atol=2e-7,rtol=2e-6)


def test_exact_zero_slope_derivative_is_one_sided_valid():
    prep,fit,reference=model(state="zero_slope")
    z=np.array([np.log(fit["variance_components"][r37.COMPONENTS[k]]/reference)
                 for k in r37.FREE]+[0.])
    value,grad=r37.continuous_reml_objective(z,prep,reference)
    assert np.isfinite(value) and np.isfinite(grad).all()
    h=1e-5
    plus=z.copy();plus[3]=h
    slope_gradient=(r37.continuous_reml_objective(plus,prep,reference)[0]-value)/h
    np.testing.assert_allclose(grad[3],slope_gradient,atol=3e-3,rtol=8e-3)
    with pytest.raises(ValueError,match="nonnegative"):
        r37.continuous_reml_objective(np.array([0,0,0,-1.]),prep,reference)


def test_continuous_multistart_and_grid_numerical_contract():
    row=r37.evaluate(0,"ordinary_dependent","zero_slope")
    assert row["source_ok"],row["source_error"]
    assert row["original_reml_status"]=="ok"
    assert len(row["optimizations"])==4
    assert len(row["grid_points"])==7
    assert row["continuous_reference_status"] in ("computed","incomplete")
    assert not row["release_authorized"]
    if row["continuous_reference_status"]=="computed":
        assert row["best_multistart_slope_ratio"]>=0
        assert row["best_multistart_slope_ratio"]<=r37.MAX_RATIO
        if not row["no_evidence_continuous_worse_than_grid"]:
            assert row["two_times_grid_to_continuous_nll_gain"] < -2e-4
    summary=r37.summarize([row])
    assert summary["recorded_source_cases"]==1
    assert summary["missing_source_cases"]==15
    assert summary["no_global_optimizer_certificate"]
    assert summary["no_chisquare_mixture_or_test_calibration"]
    assert summary["no_coefficient_CI_or_coverage"]
    assert not summary["release_authorized"]
