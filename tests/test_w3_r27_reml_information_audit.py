"""R27 independent analytic restricted-likelihood information contracts."""
import numpy as np
import pytest

from scripts import run_w3_r27_reml_information_audit as r27
from scripts.w3_r25_gaussian_reml_components import restricted_loglik_and_gradient


@pytest.mark.parametrize("support",[
    "ordinary_independent","ordinary_dependent"
])
def test_conditional_reml_score_matches_independently_tested_likelihood_gradient(support):
    model=r27.information_for_original_design(0,24,support)
    assert np.linalg.eigvalsh(model["info_log"]).min()>0
    assert np.isfinite(model["relative_local_component_SE"]).all()
    rng=np.random.default_rng(202610153728)
    parts=[]
    noise=[]
    for ix,Zi,Ki,fac,U,V,Vinv,VK in model["design"]:
        value=np.linalg.cholesky(V)@rng.standard_normal(len(V))
        parts.append((Zi,value,Ki))
        noise.append(value)
    score=r27.score_for_gaussian_innovations(model,np.concatenate(noise))
    _,negative_gradient=restricted_loglik_and_gradient(
        np.log(r27.THETA),parts,1.0)
    np.testing.assert_allclose(score,-negative_gradient,atol=2e-8,rtol=5e-8)
    assert len(score)==4


def test_fisher_information_scale_sensitivity_and_mean_covariance_reference():
    m=r27.information_for_original_design(15,24,"ordinary_independent")
    info=m["info_log"]
    np.testing.assert_allclose(info,info.T,atol=2e-10)
    np.testing.assert_allclose(np.diag(info),m["expected_score_variance"],rtol=0,atol=1e-10)
    assert np.linalg.eigvalsh(info).min()>0
    inv=np.linalg.inv(info)
    np.testing.assert_allclose(
        np.sqrt(np.diag(inv)),m["relative_local_component_SE"],rtol=1e-9)
    assert m["information_eigen_condition"]>=1
    assert np.max(np.abs(m["information_correlation"]))<=1.00000001


def test_conditional_innovation_draws_not_new_independent_source_blocks():
    m=r27.information_for_original_design(0,24,"ordinary_dependent")
    x=r27.simulate(m)
    assert x["conditional_gaussian_innovations"]==128
    assert x["sampled_score_covariance_is_not_new_source_blocks"]
    assert x["no_nuisance_reml_fit_coverage_calculated"]
    assert all(np.isfinite(list(x["score_variance_over_expected_information"].values())))
    assert x["information_eigen_condition"]>0
    assert not x["release_authorized"]


def test_fixed_original_source_isolated_from_inference_publication():
    assert r27.EXPECTED==8
    assert r27.ORIGINAL_BLOCKS==(0,15)
    assert r27.ORIGINAL_N==(24,96)
    assert r27.CONDITIONAL_DRAWS==128
    summary=r27.summarize([r27.simulate(
        r27.information_for_original_design(0,24,"ordinary_independent"))])
    assert summary["new_independent_source_designs"]==0
    assert summary["conditional_innovation_vectors"]==128
    assert not summary["no_interval_coverage_computed"] is False
    assert not summary["estimated_working_covariance_inference_qualified"]
    assert not summary["release_authorized"]
