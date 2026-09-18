import numpy as np
import pytest

from eyetrajectoriespy import (
    alr_transform, fit_compositional_fpca, inverse_alr, phase_summary,
    reconstruct_compositional_fpca, register_to_landmarks,
    simulate_aoi_probability_trajectories, simulate_planar_trajectories,
    warping_displacement,
)

def test_landmark_registration_identity_when_landmarks_match():
    x=simulate_planar_trajectories(n_participants=4,trials_per_participant=2,n_time=51,duration=2)
    obs=np.full((x.n_curves,1),1.0)
    r=register_to_landmarks(x,obs,reference_landmarks=np.array([1.0]))
    assert np.allclose(r.registered.values,x.values,equal_nan=True)
    assert np.allclose(warping_displacement(r),0)
    assert np.allclose(phase_summary(r)["max_absolute_displacement"],0)

def test_registration_warping_hits_observed_landmark():
    x=simulate_planar_trajectories(n_participants=3,trials_per_participant=2,n_time=101,duration=2)
    obs=np.linspace(.7,1.2,x.n_curves)[:,None]
    r=register_to_landmarks(x,obs,reference_landmarks=np.array([1.0]))
    idx=np.argmin(abs(x.time-1.0))
    assert np.allclose(r.warping_functions[:,idx],obs[:,0],atol=.03)

def test_registration_rejects_invalid_landmarks():
    x=simulate_planar_trajectories(n_participants=3,trials_per_participant=1,n_time=31,duration=2)
    with pytest.raises(ValueError):
        register_to_landmarks(x,np.zeros((x.n_curves,1)),reference_landmarks=np.array([1.]))
    with pytest.raises(ValueError):
        register_to_landmarks(x,np.ones((x.n_curves,2)),reference_landmarks=np.array([1.]))

def test_alr_roundtrip_and_simplex_reconstruction():
    x=simulate_aoi_probability_trajectories(n_curves=25,n_time=41,n_aoi=4)
    z=alr_transform(x.values,reference_dimension=3)
    assert np.allclose(inverse_alr(z,reference_dimension=3,n_dimensions=4),x.values)
    fit=fit_compositional_fpca(x,reference_dimension=3,n_components=0.95)
    recon=reconstruct_compositional_fpca(fit)
    assert np.allclose(recon.sum(axis=2),1.0)
    assert np.all(recon>0)

def test_alr_zero_replacement_is_finite():
    values=np.array([[[0.,.5,.5],[.2,.3,.5]],[[.1,.4,.5],[.2,.2,.6]]])
    assert np.isfinite(alr_transform(values,epsilon=1e-5)).all()
    with pytest.raises(ValueError):
        alr_transform(values,epsilon=0)
