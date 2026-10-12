"""W3 R5 native-observation support research contracts; no API promotion."""
import json
from pathlib import Path
import sys
import numpy as np
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.run_w3_r5_native_observed_support import (
    BLOCKS,N_UNITS,MECHANISMS,MISSING_SLICE,MIDPOINT,TIME,DIMS,
    source,observed_support_fit,ols_unitwise,evaluate,audit,block_mc_interval,
)


def test_same_source_and_loss_uniforms_across_mechanisms():
    obj=[source(0,m) for m in MECHANISMS]
    for other in obj[1:]:
        np.testing.assert_array_equal(obj[0][0].values,other[0].values)
        np.testing.assert_array_equal(obj[0][4],other[4])
        np.testing.assert_array_equal(obj[0][5],other[5])
    assert np.all(obj[0][7]==.35)
    assert not np.array_equal(obj[0][7],obj[1][7])
    assert not np.array_equal(obj[1][7],obj[2][7])


@pytest.mark.parametrize("mechanism",MECHANISMS)
def test_native_timestamps_are_real_samples_not_zeros_or_interpolation(mechanism):
    full,native,frame,truth,x,y,lost,p,mask=source(1,mechanism)
    assert len(native.time)==len(x)==N_UNITS
    assert len(native.values)==N_UNITS
    for i in range(N_UNITS):
        np.testing.assert_array_equal(native.time[i],TIME[mask[i]])
        np.testing.assert_array_equal(native.values[i],y[i,mask[i]])
        assert np.isfinite(native.values[i]).all()
        assert np.array_equal(full.values[i],y[i])
    assert sum(len(v)<len(TIME) for v in native.time)==int(lost.sum())
    assert int((~mask).sum()) == int(lost.sum())*(MISSING_SLICE.stop-MISSING_SLICE.start)


def test_timewise_unweighted_uses_all_genuine_observations_outside_loss():
    full,native,frame,truth,x,y,lost,p,mask=source(0,"mar_x")
    beta,support=observed_support_fit(native,x)
    X=np.column_stack((np.ones(len(x)),x))
    reference=ols_unitwise(X,y.reshape(len(x),-1)).reshape(2,len(TIME),len(DIMS))
    selected=ols_unitwise(X[~lost],y[~lost].reshape(int((~lost).sum()),-1)).reshape(2,len(TIME),len(DIMS))
    expected=support.copy()
    expected[MISSING_SLICE]=N_UNITS-int(lost.sum())
    assert np.array_equal(support,expected)
    np.testing.assert_allclose(beta[:,:MISSING_SLICE.start],reference[:,:MISSING_SLICE.start],atol=2e-10,rtol=0)
    np.testing.assert_allclose(beta[:,MISSING_SLICE],selected[:,MISSING_SLICE],atol=2e-10,rtol=0)
    np.testing.assert_allclose(beta[:,MISSING_SLICE.stop:],reference[:,MISSING_SLICE.stop:],atol=2e-10,rtol=0)


def test_oracle_weighting_only_at_actual_missing_time_support():
    full,native,frame,truth,x,y,lost,p,mask=source(0,"mar_x")
    weighted,support=observed_support_fit(native,x,probability=p)
    unweighted,same_support=observed_support_fit(native,x)
    np.testing.assert_array_equal(support,same_support)
    np.testing.assert_allclose(weighted[:,:MISSING_SLICE.start],unweighted[:,:MISSING_SLICE.start],atol=2e-10,rtol=0)
    np.testing.assert_allclose(weighted[:,MISSING_SLICE.stop:],unweighted[:,MISSING_SLICE.stop:],atol=2e-10,rtol=0)
    assert np.isfinite(weighted).all()
    # x-dependent selection yields genuinely distinct estimates at the gap.
    assert np.max(np.abs(weighted[:,MISSING_SLICE]-unweighted[:,MISSING_SLICE]))>1e-9


@pytest.mark.parametrize("mechanism",MECHANISMS)
def test_real_dense_package_oracles_and_native_source_invariants(mechanism):
    r=evaluate(0,mechanism)
    assert r["status"]=="ok",r["exception"]
    assert r["irregular_input_rejected_by_current_W3"]
    assert r["available_outside_gap_equals_full"]
    assert r["available_inside_gap_equals_explicit_complete_case"]
    assert r["native_source_unchanged"]
    assert r["package_full_ols_oracle_delta"]<=2e-10
    assert r["package_cc_ols_oracle_delta"]<=2e-10
    assert r["n_ever_missing"]+r["n_explicit_complete_units"]==N_UNITS
    assert r["observed_time_support"][MIDPOINT]==r["n_explicit_complete_units"]
    assert r["observed_time_support"][0]==N_UNITS
    assert json.loads(json.dumps(r))["status"]=="ok"
    assert not r["missingness_correction_qualified"]
    if mechanism=="latent_mnar":
        assert r["known_probability_ipw_slope_rmse"] is None
        assert r["mnar_probability_unavailable_to_real_analyst"]
    else:
        assert np.isfinite(r["known_probability_ipw_slope_rmse"])


def test_independent_blocks_and_fail_closed_invalid_source():
    a=source(0,"mcar")
    b=source(1,"mcar")
    assert not np.array_equal(a[0].values,b[0].values)
    with pytest.raises(ValueError,match="outside"):
        source(BLOCKS,"mcar")
    with pytest.raises(ValueError,match="unplanned"):
        source(0,"not-a-method")
    with pytest.raises(ValueError,match="inadequate"):
        ols_unitwise(np.ones((3,2)),np.ones((3,2)))
    with pytest.raises(ValueError,match="weights"):
        ols_unitwise(np.column_stack((np.ones(10),np.arange(10))),np.ones((10,2)),weights=-np.ones(10))


def test_independent_block_mc_not_individual_gaze_samples():
    assert block_mc_interval([],seed=1) is None
    data=[.01,-.04,.05,-.02,.0]
    x=block_mc_interval(data,seed=123)
    assert x==block_mc_interval(data,seed=123)
    assert x[0]<=np.mean(data)<=x[1]


def test_failed_and_missing_case_ids_remain_in_original_audit():
    r=evaluate(0,"mcar")
    fail=dict(r,mechanism="mar_x",status="failed",
              exception={"type":"ControlledMissingSource"})
    res=audit([r,fail])
    assert res["planned_cases"]==BLOCKS*len(MECHANISMS)
    assert res["source_rows_present"]==2
    assert res["completed_cases"]==1
    assert res["failed_cases"]==1
    assert len(res["missing_cases"])==res["planned_cases"]-2
    assert res["groups"]["mcar"]["attempted"]==BLOCKS
    assert not res["confidence_band_calibration_qualified"]
    with pytest.raises(ValueError,match="duplicate"):
        audit([r,r])
