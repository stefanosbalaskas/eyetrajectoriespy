import numpy as np
import pytest
import matplotlib.pyplot as plt

from eyetrajectoriespy import (
    acceleration_magnitude_function, cumulative_path_length,
    differentiate_trajectories, distance_to_landmark_function,
    fit_mfpca, fpca_reporting_text, multilevel_fpca_reporting_text,
    plot_fpca_component, plot_fpca_variance, plot_planar_trajectories,
    plot_registration, plot_trajectory_overlay, plot_warping_functions,
    register_to_landmarks, simulate_planar_trajectories, speed_function,
    summarise_fpca, summarise_trajectory_set, fit_multilevel_fpca,
)

def test_kinematic_shapes_and_path_monotonicity():
    x=simulate_planar_trajectories(n_participants=3,trials_per_participant=2,n_time=51)
    v=differentiate_trajectories(x)
    a=differentiate_trajectories(x,order=2)
    s=speed_function(x)
    am=acceleration_magnitude_function(x)
    p=cumulative_path_length(x)
    assert v.values.shape==x.values.shape and a.values.shape==x.values.shape
    assert s.values.shape==(x.n_curves,x.n_time,1)
    assert am.values.shape==s.values.shape
    assert np.all(np.diff(p.values[:,:,0],axis=1)>=-1e-12)
    with pytest.raises(ValueError):
        differentiate_trajectories(x,order=3)

def test_distance_to_landmark():
    x=simulate_planar_trajectories(n_participants=2,trials_per_participant=1,n_time=21)
    assert distance_to_landmark_function(x,landmark_x=.5,landmark_y=.5).values.min() >= 0

def test_reporting_helpers():
    x=simulate_planar_trajectories(n_participants=4,trials_per_participant=2,n_time=31)
    fit=fit_mfpca(x,n_components=3,scaling="dimension_sd")
    assert summarise_trajectory_set(x).iloc[0]["n_curves"]==8
    assert len(summarise_fpca(fit))==3
    assert "Functional PCA retained" in fpca_reporting_text(fit)
    ml=fit_multilevel_fpca(x,participant_column="participant_id",participant_components=2,trial_components=2)
    assert "Two-level functional decomposition" in multilevel_fpca_reporting_text(ml)

def test_plotting_helpers_return_axes_and_figures():
    x=simulate_planar_trajectories(n_participants=3,trials_per_participant=2,n_time=31)
    fit=fit_mfpca(x,n_components=3,scaling="dimension_sd")
    assert plot_trajectory_overlay(x,dimension="x") is not None
    assert plot_planar_trajectories(x) is not None
    assert plot_fpca_variance(fit) is not None
    assert plot_fpca_component(fit,component=0,dimension="x") is not None
    reg=register_to_landmarks(x,np.full((x.n_curves,1),1.0),reference_landmarks=np.array([1.0]))
    fig,axes=plot_registration(reg)
    assert len(axes)==2 and fig is not None
    assert plot_warping_functions(reg) is not None
    plt.close("all")
