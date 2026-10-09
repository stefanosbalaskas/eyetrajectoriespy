"""Model-independent source contracts for posterior cross-backend check."""
from __future__ import annotations

import numpy as np
import pytest

from scripts.run_b6_b7_independent_pymc_nuts import (
    _planar_data,_summarize_posterior
)


@pytest.mark.parametrize("asynchronous",[False,True])
def test_new_PyMC_reference_uses_real_irregular_clock_and_shared_cross_covariance(asynchronous):
    gaze,grid,noise,true_mean,true_cov=_planar_data(202688,asynchronous)
    assert gaze.n_curves==18
    assert len(grid)==23
    assert gaze.dimension_names==("x","y")
    assert true_mean.shape==(len(grid),2)
    assert true_cov.shape==(2*len(grid),2*len(grid))
    assert np.linalg.norm(true_cov[:len(grid),len(grid):])>0
    assert np.linalg.eigvalsh(true_cov).min()>-1e-9
    assert np.max(np.abs(true_cov-true_cov.T))<1e-10
    assert noise==(.04,.06)
    assert len(gaze.metadata.participant_id.unique())==18
    if asynchronous:
        assert any(np.isnan(v).any() for v in gaze.values)
    else:
        assert all(np.isfinite(v).all() for v in gaze.values)


def test_independent_reference_midpoint_targets_exact_channel_major_xy_block():
    _,grid,_,_,cov=_planar_data(771231,True)
    g=len(grid);mid=g//2
    target=cov[mid,g+mid]
    assert np.isfinite(target)
    assert target==cov[g+mid,mid]
    # x/y same-time cross covariance *not* adjacent x-grid point.
    assert not np.isclose(target,cov[mid,mid+1],atol=1e-6)


def test_posterior_comparison_is_descriptive_and_failure_aware():
    native=np.linspace(-.5,1.,100)
    independent=np.linspace(-.2,.8,120)
    result=_summarize_posterior(native,independent,.2,"x_mid_population_mean")
    assert result["quantity"]=="x_mid_population_mean"
    assert result["intervals_overlap"]
    assert result["native_90_covers_truth"]
    assert not result["scientifically_qualified"]
    assert len(result["reference_q05_q95"])==2
    with pytest.raises(ValueError,match="invalid"):
        _summarize_posterior(native,np.r_[independent,np.nan],.2,"invalid")
