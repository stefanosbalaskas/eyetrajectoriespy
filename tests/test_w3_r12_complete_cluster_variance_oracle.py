"""W3 R12 exact known Gaussian variance and cluster-jackknife source contracts."""
import json
from pathlib import Path
import sys
import numpy as np
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.run_w3_r12_complete_cluster_variance_oracle import (
    BLOCKS,SIZES,PREDICTOR_SCALES,NOMINAL,TIME,MODEL,
    SIGMA_INTERCEPT,SIGMA_RANDOM_SLOPE,SIGMA_TRIAL,SIGMA_SENSOR,
    source,case_data,sufficient_statistics,evaluate,audit,paired_bootstrap,wilson,basis
)


def test_paired_x_support_and_true_complete_native_timing():
    a=source(0,"broad")
    b=source(0,"narrow")
    np.testing.assert_array_equal(a["time"],b["time"])
    np.testing.assert_array_equal(a["n_trials"],b["n_trials"])
    np.testing.assert_allclose(
        b["x"],a["x"]*(PREDICTOR_SCALES["narrow"]/PREDICTOR_SCALES["broad"]),
        atol=1e-14)
    assert not np.array_equal(a["values"],b["values"])
    assert np.all(np.diff(a["time"],axis=2)>0)
    assert len(a["x"])==max(SIZES)
    for n in SIZES:
        gaze,x,part,trial,means=case_data(a,n)
        assert len(np.unique(part))==n
        assert len(gaze.time)==int(a["n_trials"][:n].sum())
        for idx,(t,v) in enumerate(zip(gaze.time,gaze.values)):
            i=int(part[idx]);j=int(trial[idx]%3)
            np.testing.assert_array_equal(t,a["time"][i,j])
            np.testing.assert_array_equal(v[:,0],a["values"][i,j])
            assert len(t)==len(TIME)
    assert not np.array_equal(source(0,"broad")["x"],source(1,"broad")["x"])


def test_known_random_effect_covariance_has_independent_dense_reference():
    src=source(0,"broad")
    gaze,x,part,trial,means=case_data(src,24)
    grams,cross,mcov,oracle,Q,theta,theta_mu,h,nrows=(
        sufficient_statistics(gaze,x,part,means,24))
    # Independently build a single participant's full exact response
    # covariance across its repeated trials and 31 original timepoints.
    owner=0
    idx=np.where(part==owner)[0]
    L=sum(len(gaze.time[j]) for j in idx)
    D=np.empty((L,12));w=np.empty(L)
    a=np.empty(L);b=np.empty(L)
    trial_ids=np.empty(L,dtype=int)
    start=0
    for j in idx:
        t=gaze.time[j]; k=len(t)
        z=basis(t,MODEL)
        D[start:start+k]=np.column_stack([z,z*x[j]])
        w[start:start+k]=1/(len(idx)*k)
        a[start:start+k]=1+.30*t
        b[start:start+k]=float(x[j])*(1+.25*t)
        trial_ids[start:start+k]=int(trial[j])
        start+=k
    assert start==L
    C=(SIGMA_INTERCEPT**2*np.outer(a,a)
       +SIGMA_RANDOM_SLOPE**2*np.outer(b,b)
       +SIGMA_TRIAL**2*(trial_ids[:,None]==trial_ids[None,:])
       +SIGMA_SENSOR**2*np.eye(L))
    direct=(D*w[:,None]).T@C@(D*w[:,None])
    np.testing.assert_allclose(oracle[0],direct,atol=4e-10,rtol=1e-10)
    assert np.min(np.linalg.eigvalsh(direct))>-1e-11
    assert len(theta)==12 and nrows>=24*31
    assert np.isfinite(h@theta_mu)


@pytest.mark.parametrize("n",SIZES)
@pytest.mark.parametrize("support",tuple(PREDICTOR_SCALES))
def test_complete_correct_mean_cluster_inference_methods(n,support):
    row=evaluate(0,support,n)
    assert row["status"]=="ok",row["exception"]
    assert row["all_complete_native_source"]
    assert row["dense_W3_rejected_irregular"]
    assert row["n_participants"]==n
    assert abs(row["model_projection_error"])<5e-6
    assert row["oracle_gaussian_se"]>0
    assert row["n_trials"]>=n
    assert row["n_gaze_samples"]>=31*n
    assert len(row["methods"])==4
    for result in row["methods"].values():
        assert result["se"]>0 and result["width"]>0
        assert isinstance(result["truth_included"],bool)
        assert result["se_divided_by_oracle"]>0
    assert row["methods"]["cr1_t"]["width"] > row["methods"]["cr1_normal"]["width"]
    np.testing.assert_allclose(row["methods"]["known_gaussian_oracle"]["se_divided_by_oracle"],1.,atol=1e-12)
    assert not row["method_qualified"]
    assert json.loads(json.dumps(row))["status"]=="ok"


def test_mc_failure_rows_stay_in_original_audit():
    good=evaluate(0,"broad",24)
    bad=dict(good,predictor_support="narrow",status="failed",
             exception={"type":"ControlledReferenceFailure"})
    d=audit([good,bad])
    assert d["planned_cases"]==BLOCKS*len(SIZES)*len(PREDICTOR_SCALES)
    assert d["recorded_cases"]==2
    assert d["completed_cases"]==1 and d["failed_cases"]==1
    assert len(d["missing_cases"])==d["planned_cases"]-2
    assert not d["release_authorized"]
    with pytest.raises(ValueError,match="duplicated"):
        audit([good,good])


def test_source_constraints_and_seeded_independent_block_bootstrap():
    with pytest.raises(ValueError,match="outside"):
        source(BLOCKS,"broad")
    with pytest.raises(ValueError,match="undeclared"):
        source(0,"auto_best")
    with pytest.raises(ValueError,match="unplanned"):
        case_data(source(0,"broad"),27)
    a=[.2,-.3,.1,.5]
    assert paired_bootstrap(a,123)==paired_bootstrap(a,123)
    assert paired_bootstrap([],123) is None
    assert wilson(0,0) is None
    assert abs(wilson(0,96)[0])<1e-12
    assert wilson(96,96)[1]==1
