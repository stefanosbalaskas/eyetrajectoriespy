"""R20 research-only estimated covariance component and CR2 contracts."""
import numpy as np
import pytest
from scripts import run_w3_r17_fresh_feasibility as source
from scripts import run_w3_r16_leverage_covariance_factorial as r16
from scripts.w3_r20_estimated_working_target import (
    COMPONENTS,MODELS,_kernels,observed_weighted_rows,estimate_feasible_working_target)
from scripts.w3_r17_cr2_blockwise import cr2_blockwise_wls


@pytest.mark.parametrize("support,slope",[
 ("ordinary_independent","shared_slope"),
 ("extreme_independent","shared_slope"),
 ("ordinary_dependent","predictor_scaled_slope"),
 ("extreme_dependent","predictor_scaled_slope"),
])
def test_observable_only_estimation_and_known_source_kernel_check(support,slope):
    data=source.fresh_source(0,support,n=24)
    X,y,w,g,t,trial,x=observed_weighted_rows(
        (None,data[1],data[2],data[3],data[4],None),"legendre5")
    original_X,original_y,original_w,original_g,known=source.prepare(data,"legendre5")
    np.testing.assert_allclose(X,original_X,rtol=0,atol=1e-12)
    np.testing.assert_allclose(y,original_y,rtol=0,atol=1e-12)
    np.testing.assert_allclose(w,original_w,rtol=0,atol=1e-12)
    np.testing.assert_array_equal(g,original_g)
    truth_coeffs=np.array([
        r16.SIGMA_INTERCEPT**2,r16.SIGMA_RANDOM_SLOPE**2,
        r16.SIGMA_TRIAL**2,r16.SIGMA_SENSOR**2
    ])
    for i,who in enumerate(np.unique(g)):
        ix=np.flatnonzero(g==who)
        components=_kernels(t[ix],trial[ix],x[ix],w[ix],slope)
        predicted=sum(coeff*K for coeff,K in zip(truth_coeffs,components))
        np.testing.assert_allclose(predicted,known[i],rtol=1e-9,atol=1e-11)
    output=estimate_feasible_working_target(
        X,y,w,g,t,trial,x,slope=slope)
    assert output["estimated_from_outcomes"] is True
    assert output["uses_generating_truth_oracle"] is False
    assert output["df_accounts_for_covariance_estimation"] is False
    assert not output["pointwise_inference_qualified"]
    assert len(output["working_blocks"])==24
    assert all(v>=0 for v in output["variance_components"].values())
    for block in output["working_blocks"]:
        assert np.linalg.eigvalsh(block).min()>0
    c=np.r_[np.zeros(r16.basis(np.asarray([.5]),"legendre5").shape[1]),
            r16.basis(np.asarray([r16.TIME[r16.FOCAL]]),"legendre5")[0]]
    result=cr2_blockwise_wls(X,y,w,g,c,output["working_blocks"])
    assert result["cr2_se"]>0 and result["satterthwaite_df"]>0
    assert result["max_adjustment_covariance_error"]<1e-7


def test_nuisance_family_is_prespecified_and_not_selected_from_truth():
    assert MODELS==("shared_slope","predictor_scaled_slope")
    assert len(COMPONENTS)==4
    d=source.fresh_source(0,"ordinary_independent",n=24)
    X,y,w,g,t,trial,x=observed_weighted_rows(
        (None,d[1],d[2],d[3],d[4],None),"legendre5")
    estimates=[estimate_feasible_working_target(X,y,w,g,t,trial,x,slope=s)
               for s in MODELS]
    assert all(e["working_model_correctness_assumed"] is False for e in estimates)
    assert all(e["public_api_authorized"] is False for e in estimates)


def test_reject_singular_and_invalid_observable_source():
    d=source.fresh_source(0,"ordinary_independent",n=24)
    X,y,w,g,t,trial,x=observed_weighted_rows(
        (None,d[1],d[2],d[3],d[4],None),"legendre5")
    with pytest.raises(ValueError):
        estimate_feasible_working_target(X,y,np.zeros_like(w),g,t,trial,x,slope="shared_slope")
    with pytest.raises(ValueError):
        estimate_feasible_working_target(X,y,w,g,t,trial,x,slope="oracle_true")
    altered=x.copy()
    altered[1]=altered[1]+1
    with pytest.raises(ValueError,match="constant"):
        estimate_feasible_working_target(X,y,w,g,t,trial,altered,slope="shared_slope")
