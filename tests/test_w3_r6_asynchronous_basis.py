"""W3 R6 genuinely asynchronous native-time model reference contracts."""
from pathlib import Path
import sys
import json
import numpy as np
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.run_w3_r6_asynchronous_basis import (
    STUDY,MASTER_SEED,BLOCKS,N_CURVES,MECHANISMS,DEGREE,TIME,DIMS,
    DROPOUT_WINDOW,source,basis,stack_observed,fit_native_basis,
    evaluate,audit,block_mc_ci,
)


def test_genuinely_async_source_and_paired_loss_mechanisms():
    scenarios=[source(0,m) for m in MECHANISMS]
    a=scenarios[0]
    for b in scenarios[1:]:
        for i in range(N_CURVES):
            np.testing.assert_array_equal(a[0].time[i],b[0].time[i])
            np.testing.assert_array_equal(a[0].values[i],b[0].values[i])
        np.testing.assert_array_equal(a[2],b[2])
        np.testing.assert_array_equal(a[5],b[5])
        np.testing.assert_array_equal(a[6],b[6])
    assert not np.allclose(a[5][0],a[5][1],atol=1e-12)
    assert not np.allclose(a[5],TIME[None,:],atol=1e-12)
    assert np.all(np.diff(a[5],axis=1)>0)
    assert not np.array_equal(scenarios[0][4],scenarios[1][4])
    assert not np.array_equal(scenarios[1][4],scenarios[2][4])


@pytest.mark.parametrize("mechanism",MECHANISMS)
def test_irregular_native_observed_timestamps_and_values_unchanged(mechanism):
    full,native,x,lost,p,t,y,mask=source(1,mechanism)
    assert len(native.curve_ids)==N_CURVES
    for i in range(N_CURVES):
        np.testing.assert_array_equal(native.time[i],t[i,mask[i]])
        np.testing.assert_array_equal(native.values[i],y[i,mask[i]])
        np.testing.assert_array_equal(full.values[i],y[i])
        assert np.isfinite(native.values[i]).all()
        assert np.all(np.diff(native.time[i])>0)
    assert int((~mask).sum())==int(lost.sum())*(DROPOUT_WINDOW.stop-DROPOUT_WINDOW.start)


def test_time_basis_has_prespecified_shape_and_true_time_dependence():
    b=basis(np.array([0,.17,.66,1.]))
    assert b.shape==(4,DEGREE+1)
    np.testing.assert_allclose(b[:,0],1.)
    assert np.isfinite(b).all()


@pytest.mark.parametrize("mechanism",MECHANISMS)
def test_actual_source_regression_oracle_and_fail_closed_dense_boundary(mechanism):
    r=evaluate(0,mechanism)
    assert r["status"]=="ok",r["exception"]
    assert r["current_common_grid_W3_refused"]
    assert r["native_async_jitter_verified"]
    assert r["original_values_and_timestamps_preserved"]
    assert r["full_qr_max_delta"]<=2e-8
    assert r["observed_unit_balanced_qr_max_delta"]<=2e-8
    assert r["observed_sample_weighted_qr_max_delta"]<=2e-8
    assert r["n_native_observations"]==N_CURVES*len(TIME)-r["n_lost_curves"]*(DROPOUT_WINDOW.stop-DROPOUT_WINDOW.start)
    assert not r["interval_calibration_qualified"]
    assert not r["irregular_method_qualified"]
    assert json.loads(json.dumps(r))["status"]=="ok"


def test_native_source_weights_represent_source_curve_not_source_point():
    full,native,x,*_=source(0,"mar_x")
    Zu,Yu,su=stack_observed(native,x,unit_balanced=True)
    Zs,Ys,ss=stack_observed(native,x,unit_balanced=False)
    np.testing.assert_array_equal(Zu,Zs)
    np.testing.assert_array_equal(Yu,Ys)
    n=[len(a) for a in native.time]
    cut=0
    for k in n:
        assert np.isclose(np.sum(su[cut:cut+k]**2),1)
        assert np.all(ss[cut:cut+k]==1)
        cut+=k
    assert cut==len(Zu)
    assert len(set(n))>=2


def test_independent_seed_and_wrong_source_checks():
    a=source(0,"mcar")
    b=source(1,"mcar")
    assert not np.array_equal(a[6],b[6])
    with pytest.raises(ValueError,match="outside"):
        source(BLOCKS,"mcar")
    with pytest.raises(ValueError,match="unplanned"):
        source(0,"not-source")


def test_block_bootstrap_source_units_not_time_cells():
    assert block_mc_ci([],seed=1) is None
    data=[.5,-.1,.3,.2]
    a=block_mc_ci(data,seed=3)
    assert a==block_mc_ci(data,seed=3)
    assert a[0]<=np.mean(data)<=a[1]


def test_failure_inclusive_case_ledger():
    good=evaluate(0,"mcar")
    bad=dict(good,mechanism="mar_x",status="failed",
             exception={"type":"ControlledModelFailure"})
    out=audit([good,bad])
    assert out["planned_cases"]==BLOCKS*len(MECHANISMS)
    assert out["recorded_cases"]==2 and out["completed_cases"]==1
    assert out["failures"]==1 and len(out["missing_cases"])==out["planned_cases"]-2
    assert out["groups"]["mcar"]["attempted"]==BLOCKS
    assert not out["model_based_asynchronous_estimator_qualified"]
    with pytest.raises(ValueError,match="duplicate"):
        audit([good,good])
