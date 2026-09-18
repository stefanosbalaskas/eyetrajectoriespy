import numpy as np
import pandas as pd
import pytest

from eyetrajectoriespy import (
    center_on_landmark, from_irregular_long_dataframe, from_long_dataframe,
    interpolate_short_gaps, normalize_coordinates, normalize_time,
    resample_to_grid, smooth_trajectories,
)

def long_df():
    rows=[]
    for p in ["p1", "p2"]:
        for t in [0.0, 0.5, 1.0]:
            rows.append({"p":p,"trial":1,"t":t,"x":t + (p=="p2"),"y":2*t,"condition":"A"})
    return pd.DataFrame(rows)

def test_from_long_dataframe_common_grid_and_metadata():
    x = from_long_dataframe(long_df(), curve_columns=["p","trial"], time_column="t", metadata_columns=["condition"])
    assert x.values.shape == (2,3,2)
    assert list(x.metadata["condition"]) == ["A","A"]

def test_from_long_dataframe_rejects_duplicate_and_variable_metadata():
    df=long_df(); df=pd.concat([df,df.iloc[[0]]],ignore_index=True)
    with pytest.raises(ValueError):
        from_long_dataframe(df,curve_columns=["p","trial"],time_column="t")
    df=long_df(); df.loc[1,"condition"]="B"
    with pytest.raises(ValueError):
        from_long_dataframe(df,curve_columns=["p","trial"],time_column="t",metadata_columns=["condition"])

def test_irregular_adapter_gap_protection():
    df=pd.DataFrame({"p":[1,1,1],"t":[0.,0.2,1.0],"x":[0.,.2,1.],"y":[0.,.1,.5]})
    x=from_irregular_long_dataframe(df,curve_columns=["p"],time_column="t",grid=np.linspace(0,1,6),max_gap=.3)
    assert np.isnan(x.values[0,2:5]).all()

def test_resample_no_extrapolation():
    x=from_long_dataframe(long_df(),curve_columns=["p","trial"],time_column="t")
    y=resample_to_grid(x,np.array([-0.1,0,0.25,1,1.1]))
    assert np.isnan(y.values[:,0]).all() and np.isnan(y.values[:,-1]).all()

def test_interpolate_short_gaps_only():
    x=from_long_dataframe(long_df(),curve_columns=["p","trial"],time_column="t")
    v=x.values.copy(); v[0,1,:]=np.nan
    m=x.with_values(v)
    filled=interpolate_short_gaps(m,max_gap=1.0,method="linear")
    assert np.isfinite(filled.values[0,1]).all()
    unfilled=interpolate_short_gaps(m,max_gap=.4,method="linear")
    assert np.isnan(unfilled.values[0,1]).all()

def test_smoothing_is_explicit_and_preserves_gap():
    x=from_long_dataframe(long_df(),curve_columns=["p","trial"],time_column="t")
    v=x.values.copy(); v[0,1,0]=np.nan
    with pytest.warns(UserWarning):
        out=smooth_trajectories(x.with_values(v),method="gaussian",sigma=1)
    assert np.isnan(out.values[0,1,0])
    with pytest.warns(UserWarning):
        with pytest.raises(ValueError):
            smooth_trajectories(x,method="bad")

def test_time_coordinate_and_landmark_transforms():
    x=from_long_dataframe(long_df(),curve_columns=["p","trial"],time_column="t",coordinate_system="pixels",time_unit="s")
    nt=normalize_time(x)
    assert nt.time_unit=="normalized" and np.allclose(nt.time,[0,.5,1])
    nc=normalize_coordinates(x,width=2,height=2)
    assert nc.coordinate_system=="normalized"
    centered=center_on_landmark(nc,landmark_x=.5,landmark_y=.5)
    assert centered.coordinate_system=="landmark_relative"
