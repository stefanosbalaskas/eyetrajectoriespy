"""R35 exact-boundary profile restricted Gaussian likelihood contracts."""
import numpy as np
import pytest
from scripts import run_w3_r35_slope_boundary_profiles as r35
from scripts.w3_r25_gaussian_reml_components import (
    estimate_reml_components,prepare_reml_design,restricted_loglik_and_gradient)


def prepared():
    X,y,w,g,t,tr,x=r35.prepare_source(0,"ordinary_dependent")
    model=prepare_reml_design(X,y,w,g,t,tr,x,slope=r35.WORKING_FAMILY)
    fitted=estimate_reml_components(X,y,w,g,t,tr,x,slope=r35.WORKING_FAMILY)
    assert fitted["status"]=="ok"
    return model,fitted


def test_original_new_seed_and_exact_native_source():
    assert r35.MASTER_SEED!=202610163434
    assert r35.BLOCKS==4 and r35.PARTICIPANTS==24
    assert r35.PLANNED==8 and r35.EXPECTED_POINTS==56
    for support in r35.SUPPORT:
        X,y,w,g,t,tr,x=r35.prepare_source(0,support)
        assert len(np.unique(g))==24
        assert np.isfinite([X.min(),X.max(),y.min(),y.max()]).all()
        if support.startswith("extreme"):
            assert x[np.flatnonzero(g==0)[0]]==3.
            assert x[np.flatnonzero(g==1)[0]]==-2.5
    with pytest.raises(ValueError,match="unregistered"):
        r35.prepare_source(0,"wrong_source")


def test_positive_fixed_slope_objective_matches_independent_R25_reml():
    model,fit=prepared()
    ref=fit["reference_variance_scale_from_observed_residuals"]
    theta=fit["variance_components"]
    logfree=np.log([theta[r35.COMPONENTS[k]]/ref for k in r35.FREE_INDICES])
    slope_ratio=theta["participant_slope"]/ref
    a,g=r35.fixed_slope_reml_objective(logfree,model,ref,slope_ratio)
    full=np.empty(len(r35.COMPONENTS))
    full[list(r35.FREE_INDICES)]=logfree
    full[r35.SLOPE_INDEX]=np.log(slope_ratio)
    b,fullgradient=restricted_loglik_and_gradient(full,model,ref)
    np.testing.assert_allclose(a,b,rtol=2e-9,atol=2e-9)
    np.testing.assert_allclose(g,fullgradient[list(r35.FREE_INDICES)],
                               rtol=4e-7,atol=4e-7)


def test_exact_zero_slope_is_finite_and_analytic_free_gradient():
    model,fit=prepared()
    ref=fit["reference_variance_scale_from_observed_residuals"]
    theta=fit["variance_components"]
    logfree=np.log([theta[r35.COMPONENTS[k]]/ref for k in r35.FREE_INDICES])
    value,gradient=r35.fixed_slope_reml_objective(logfree,model,ref,0.)
    assert np.isfinite(value) and np.isfinite(gradient).all()
    eps=1e-4
    reference_grad=[]
    for k in range(3):
        d=np.zeros(3);d[k]=eps
        ap=r35.fixed_slope_reml_objective(logfree+d,model,ref,0.)[0]
        am=r35.fixed_slope_reml_objective(logfree-d,model,ref,0.)[0]
        reference_grad.append((ap-am)/(2*eps))
    np.testing.assert_allclose(gradient,reference_grad,rtol=2e-4,atol=2e-5)
    tiny=r35.fixed_slope_reml_objective(logfree,model,ref,1e-12)[0]
    np.testing.assert_allclose(value,tiny,atol=1e-5,rtol=1e-9)
    with pytest.raises(ValueError,match="nonnegative"):
        r35.fixed_slope_reml_objective(logfree,model,ref,-1.)


def test_fixed_slope_boundary_optimization_keeps_three_components_free():
    model,fit=prepared()
    r=r35.profile_one(model,
          fit["reference_variance_scale_from_observed_residuals"],
          fit["variance_components"],0.)
    assert r["fixed_slope_variance_is_exact_zero"]
    assert r["status"] in ("ok","nonconverged","failed")
    if r["status"]=="ok":
        assert len(r["free_component_estimates"])==3
        assert "participant_slope" not in r["free_component_estimates"]


def test_original_profiles_preserve_all_failure_outcomes():
    a=r35.evaluate(0,"ordinary_dependent")
    assert a["source_generated"],a["source_failure"]
    assert a["simulator_true_components_passed_to_nuisance"] is False
    assert a["standard_chi_square_boundary_cutoffs_authorized"] is False
    assert a["pointwise_coverage_evaluated"] is False
    assert len(a["points"]) in (0,7)
    if len(a["points"])==7:
        assert a["points"][0]["fixed_slope_variance_is_exact_zero"]
    result=r35.summarize([a])
    assert result["recorded_source_cases"]==1
    assert result["missing_source_cases"]==7
    assert result["profiles_include_exact_zero_variance"]
    assert result["no_boundary_lrt_chi_square_cutoff_applied"]
    assert result["no_functional_coefficient_CI_or_coverage"]
    assert not result["release_authorized"]
