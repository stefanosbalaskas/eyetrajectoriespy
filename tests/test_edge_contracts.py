import numpy as np
import pandas as pd
import pytest

from eyetrajectoriespy import (
    TrajectorySet, center_on_landmark, cluster_fpca_scores, component_trajectories,
    fit_mfpca, fit_scalar_on_function_regression, from_irregular_long_dataframe,
    from_long_dataframe, functional_l2_distance, interpolate_short_gaps,
    nearest_trajectory_indices, normalize_coordinates, normalize_time,
    reconstruct_fpca, register_to_landmarks, resample_to_grid,
    score_distance_matrix, select_n_components, simulate_planar_trajectories,
    smooth_trajectories, transform_fpca, validate_common_grid,
    validate_simplex, validate_trajectory_set,
)

def sample():
    return simulate_planar_trajectories(n_participants=4,trials_per_participant=2,n_time=21,duration=2)

def test_validation_error_contracts():
    with pytest.raises(TypeError):
        validate_trajectory_set("bad")
    x=sample()
    with pytest.raises(ValueError,match="Missing required dimensions"):
        validate_trajectory_set(x,require_dimensions=["z"])
    validate_common_grid(x)
    with pytest.raises(ValueError):
        validate_simplex(np.array([[[np.nan,.5]]]))
    with pytest.raises(ValueError):
        validate_simplex(np.array([[[-.1,1.1]]]))

def test_types_more_constructor_contracts():
    with pytest.raises(ValueError):
        TrajectorySet(np.array([0.]),np.zeros((1,1,1)),("a",),("x",))
    with pytest.raises(ValueError):
        TrajectorySet(np.array([0.,np.nan]),np.zeros((1,2,1)),("a",),("x",))
    with pytest.raises(ValueError):
        TrajectorySet(np.array([0.,1.]),np.zeros((1,2,2)),("a",),("x",))
    with pytest.raises(ValueError):
        TrajectorySet(np.array([0.,1.]),np.zeros((2,2,1)),("a","a"),("x",))
    with pytest.raises(ValueError):
        TrajectorySet(np.array([0.,1.]),np.zeros((1,2,2)),("a",),("x","x"))
    with pytest.raises(ValueError):
        TrajectorySet(np.array([0.,1.]),np.zeros((1,2,1)),("a",),("x",),pd.DataFrame({"q":[1,2]}))

def test_io_input_errors():
    with pytest.raises(TypeError):
        from_long_dataframe([],curve_columns=["p"],time_column="t")
    df=pd.DataFrame({"p":[1,1],"t":[0.,1.],"x":[0.,1.],"y":[0.,1.]})
    with pytest.raises(ValueError):
        from_long_dataframe(df,curve_columns=["p"],time_column="missing")
    with pytest.raises(ValueError):
        from_long_dataframe(df,curve_columns=[],time_column="t")
    with pytest.raises(ValueError):
        from_long_dataframe(df,curve_columns=["p"],time_column="t",value_columns=[])
    irregular=pd.DataFrame({"p":[1,1,2,2],"t":[0.,1.,0.,.8],"x":[0,1,0,1],"y":[0,1,0,1]})
    with pytest.raises(ValueError):
        from_long_dataframe(irregular,curve_columns=["p"],time_column="t")
    with pytest.raises(ValueError):
        from_irregular_long_dataframe(df,curve_columns=["p"],time_column="t",grid=np.array([0.,0.]))
    with pytest.raises(ValueError):
        from_irregular_long_dataframe(df,curve_columns=["p"],time_column="t",grid=np.array([0.,1.]),value_columns=["z"])

def test_preprocessing_error_contracts():
    x=sample()
    with pytest.raises(ValueError):
        resample_to_grid(x,np.array([0.,0.]))
    with pytest.raises(ValueError):
        resample_to_grid(x,np.linspace(0,2,10),max_gap=0)
    with pytest.raises(ValueError):
        interpolate_short_gaps(x,max_gap=0)
    v=x.values.copy(); v[0,1,:]=np.nan
    with pytest.raises(ValueError):
        interpolate_short_gaps(x.with_values(v),max_gap=1,method="cubic")
    with pytest.warns(UserWarning):
        with pytest.raises(ValueError):
            smooth_trajectories(x,method="savgol",window=None)
    with pytest.warns(UserWarning):
        with pytest.raises(ValueError):
            smooth_trajectories(x,method="savgol",window=4)
    with pytest.warns(UserWarning):
        with pytest.raises(ValueError):
            smooth_trajectories(x,method="gaussian",sigma=0)
    with pytest.raises(ValueError):
        normalize_time(x,start=1,end=1)
    with pytest.raises(ValueError):
        normalize_coordinates(x,width=0,height=1)
    one=TrajectorySet(x.time,x.values[:,:,:1],x.curve_ids,("x",),x.metadata.reset_index(drop=True),x.coordinate_system,x.time_unit,x.provenance)
    with pytest.raises(ValueError):
        normalize_coordinates(one,width=1,height=1)
    with pytest.raises(ValueError):
        center_on_landmark(x,landmark_x=np.arange(3),landmark_y=.5)

def test_fpca_error_contracts():
    x=sample()
    with pytest.raises(TypeError):
        fit_mfpca(x,n_components=True)
    with pytest.raises(ValueError):
        fit_mfpca(x,n_components=0)
    with pytest.raises(ValueError):
        fit_mfpca(x,n_components=1.0)
    fit=fit_mfpca(x,n_components=3)
    with pytest.raises(ValueError):
        transform_fpca(fit,x.with_values(x.values.copy(),time=np.linspace(0,3,x.n_time)))
    swapped=TrajectorySet(x.time,x.values[:,:,::-1],x.curve_ids,("y","x"),x.metadata.reset_index(drop=True),x.coordinate_system,x.time_unit,x.provenance)
    with pytest.raises(ValueError):
        transform_fpca(fit,swapped)
    with pytest.raises(ValueError):
        reconstruct_fpca(fit,scores=np.zeros((1,1,1)))
    with pytest.raises(ValueError):
        reconstruct_fpca(fit,n_components=4)
    with pytest.raises(IndexError):
        component_trajectories(fit,99)
    with pytest.raises(ValueError):
        select_n_components(fit,threshold=0)

def test_analysis_error_contracts():
    x=sample(); fit=fit_mfpca(x,n_components=3)
    with pytest.raises(ValueError):
        functional_l2_distance(np.zeros((2,2)),np.zeros((3,2)),time=np.arange(2))
    a=x.values[0].copy(); a[0,0]=np.nan
    with pytest.raises(ValueError):
        functional_l2_distance(a,x.values[1],time=x.time)
    with pytest.raises(ValueError):
        functional_l2_distance(x.values[0],x.values[1],time=x.time,dimension_weights=np.array([-1,1]))
    with pytest.raises(ValueError):
        cluster_fpca_scores(fit,n_clusters=1)
    with pytest.raises(ValueError):
        cluster_fpca_scores(fit,n_clusters=2,n_components=9)
    with pytest.raises(IndexError):
        nearest_trajectory_indices(x,index=999)
    with pytest.raises(ValueError):
        nearest_trajectory_indices(x,index=0,n_neighbors=0)
    with pytest.raises(ValueError):
        score_distance_matrix(fit,n_components=9)
    y=np.arange(x.n_curves,dtype=float)
    with pytest.raises(ValueError):
        fit_scalar_on_function_regression(fit,y,n_components=9)
    with pytest.raises(ValueError):
        fit_scalar_on_function_regression(fit,y,covariates=pd.DataFrame({"a":[1.]}))

def test_registration_error_contracts_more():
    x=sample()
    with pytest.raises(ValueError):
        register_to_landmarks(x,np.ones((x.n_curves,1)),reference_landmarks=np.array([0.]))
    with pytest.raises(ValueError):
        register_to_landmarks(x,np.ones((x.n_curves,2)),reference_landmarks=np.array([.8,1.2]))
