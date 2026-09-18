import numpy as np
import pytest

from eyetrajectoriespy import (
    component_trajectories, fit_fpca, fit_mfpca, fpca_score_frame,
    functional_trapezoid_weights, reconstruct_fpca, select_n_components,
    simulate_planar_trajectories, transform_fpca,
)
from eyetrajectoriespy.types import TrajectorySet

def test_trapezoid_weights_integrate_domain():
    t=np.array([0.,.2,.7,1.])
    w=functional_trapezoid_weights(t)
    assert np.isclose(w.sum(),1.0)
    assert np.isclose(functional_trapezoid_weights(t,normalize=True).sum(),1.0)
    with pytest.raises(ValueError):
        functional_trapezoid_weights(np.array([0.,0.]))

def test_mfpca_shapes_variance_and_transform_roundtrip_scores():
    x=simulate_planar_trajectories(n_participants=8,trials_per_participant=3,n_time=61,random_state=2)
    fit=fit_mfpca(x,n_components=4,scaling="dimension_sd")
    assert fit.components.shape==(4,61,2)
    assert fit.scores.shape==(24,4)
    assert np.isclose(fit.explained_variance_ratio.sum(), fit.model.explained_variance_ratio_.sum())
    assert np.allclose(transform_fpca(fit,x),fit.scores)

def test_reconstruction_improves_with_components():
    x=simulate_planar_trajectories(n_participants=10,trials_per_participant=2,n_time=51,random_state=3)
    fit=fit_mfpca(x,n_components=8,scaling="dimension_sd")
    e1=np.mean((reconstruct_fpca(fit,n_components=1)-x.values)**2)
    e8=np.mean((reconstruct_fpca(fit,n_components=8)-x.values)**2)
    assert e8 <= e1

def test_fpca_rejects_missing_and_bad_scaling():
    x=simulate_planar_trajectories(n_participants=3,trials_per_participant=2,n_time=21)
    v=x.values.copy(); v[0,1,0]=np.nan
    with pytest.raises(ValueError):
        fit_fpca(x.with_values(v))
    with pytest.raises(ValueError):
        fit_fpca(x,scaling="mystery")

def test_univariate_fpca_and_component_helpers():
    x=simulate_planar_trajectories(n_participants=5,trials_per_participant=2,n_time=41)
    one=TrajectorySet(x.time,x.values[:,:,:1],x.curve_ids,("x",),x.metadata.reset_index(drop=True),x.coordinate_system,x.time_unit,x.provenance)
    fit=fit_fpca(one,n_components=3)
    assert component_trajectories(fit,0).shape==(5,41,1)
    assert list(fpca_score_frame(fit).columns)==["curve_id","FPC1","FPC2","FPC3"]
    with pytest.raises(ValueError):
        fit_mfpca(one)

def test_select_components():
    x=simulate_planar_trajectories(n_participants=6,trials_per_participant=2,n_time=31)
    fit=fit_mfpca(x,n_components=0.95)
    n=select_n_components(fit,threshold=.9)
    assert 1 <= n <= fit.n_components
