"""R54 prospective moving-box active Gaussian nuisance derivative contracts."""
import hashlib
import json

import numpy as np
import pytest

from scripts import run_w3_r49_nuisance_refit_bootstrap_t as r49
from scripts import run_w3_r53_local_reml_influence as r53
from scripts import run_w3_r54_boundary_active_set_influence as r54


def test_R54_intentionally_replays_R53_sources_without_claiming_new_replication():
    assert r54.SOURCE_SEED==r53.SOURCE_SEED
    assert r54.DIRECTION_SEED!=r53.DIRECTION_SEED
    assert r54.BLOCKS==4 and r54.PARTICIPANTS==24
    assert r54.N_SOURCE==8 and r54.N_DIRECTION==16
    assert r54.N_REFIT_SLOTS==32 and r54.N_REML_FIT_SLOTS==40
    assert r54.N_START_SLOTS==80
    assert r54.STRICT_DIMENSIONLESS_KKT_MARGIN==.001
    assert r54.ACTIVE_RATIO_RTOL==1e-5
    first=r54.original_data(0,r54.SUPPORT[0])
    earlier=r53.problem(0,r53.SUPPORT[0])
    np.testing.assert_array_equal(first["y"],earlier["y"])
    np.testing.assert_array_equal(first["X"],earlier["X"])


def test_reference_bound_derivative_includes_unweighted_residual_and_WLS_projection():
    data=r54.original_data(0,r54.SUPPORT[0])
    ref,gradient,raw=r54.reference_and_gradient(data)
    original=r49.fit_nuisance(data)
    assert original["status"]=="accepted",original.get("reason")
    assert ref==pytest.approx(original["reference_variance"])
    assert raw>r54.REFERENCE_FLOOR
    assert gradient.shape==data["y"].shape
    rng=np.random.default_rng(721)
    d=rng.standard_normal(len(data["y"]))
    step=1e-5
    plus={**data,"y":data["y"]+step*d/np.sqrt(data["w"])}
    minus={**data,"y":data["y"]-step*d/np.sqrt(data["w"])}
    centered=(r54.reference_and_gradient(plus)[0]-
              r54.reference_and_gradient(minus)[0])/(2*step)
    assert centered==pytest.approx(gradient@d,rel=1e-6,abs=1e-7)


def test_original_R53_slope_variance_is_on_a_positive_moving_lower_ratio_face():
    data=r54.original_data(0,r54.SUPPORT[0])
    fit=r49.fit_nuisance(data)
    assert fit["status"]=="accepted"
    low,high=r54.active_signature(fit)
    assert low==(1,)
    assert high==()
    assert fit["components"]["participant_slope"]>0
    assert fit["components"]["participant_slope"]==pytest.approx(
        fit["reference_variance"]*r49.BOUND_LOW,rel=1e-8)
    result=r54.local_active_face(data,fit)
    assert result["status"] in ("ok","refused")
    if result["status"]=="ok":
        assert result["active_low"]==(1,)
        assert result["moving_active_bound_explicit"]
        J=result["theta_response_jacobian"]
        dref=result["reference_response_gradient"]
        np.testing.assert_allclose(J[1],r49.BOUND_LOW*dref,
                                   atol=1e-9,rtol=1e-9)


def test_original_interior_source_uses_full_nuisance_J_without_silent_reclassification():
    data=r54.original_data(3,r54.SUPPORT[0])
    fit=r49.fit_nuisance(data)
    assert fit["status"]=="accepted"
    assert r54.active_signature(fit)==((),())
    result=r54.local_active_face(data,fit)
    assert result["status"]=="ok",result.get("reason")
    assert result["active_low"]==()
    assert result["active_high"]==()
    assert result["theta_response_jacobian"].shape==(4,len(data["y"]))


def test_active_signature_and_full_planned_refusal_ledger():
    fake={"status":"accepted","reference_variance":2.,
          "components":{k:1. for k in
                        ("participant_intercept","participant_slope","trial","sensor")}}
    assert r54.active_signature(fake)==((),())
    fake["components"]["participant_slope"]=2*r49.BOUND_LOW
    assert r54.active_signature(fake)[0]==(1,)
    row={
        "block":0,"support":r54.SUPPORT[0],
        "original_fit":{
            "status":"not_attempted",
            "numerical_starts":[{"label":n,"status":"not_attempted"}
                                for n,_ in r49.START_RATIOS],
        },
        "active_face":{"status":"refused","reason":"source"},
        "directions":[r54.direction_record(i)
                      for i in range(r54.DIRECTIONS)],
    }
    summary=r54.summary([row])
    assert summary["planned_direction_records"]==16
    assert summary["recorded_direction_records"]==2
    assert summary["recorded_attempted_plus_minus_refits"]==0
    assert summary["planned_optimizer_start_slots"]==80
    assert not summary["full_source_and_direction_denominator_preserved"]
    assert summary["active_set_switch_is_refusal_not_success"]
    assert not summary["release_authorized"]
    with pytest.raises(ValueError,match="duplicate"):
        r54.summary([row,row])


def test_json_artifact_retains_explicit_failed_active_set(tmp_path):
    records={
        "active_face":{"active_low":(1,),"reference_gradient":np.array([1.,2.])},
        "numeric_refusals":["switch","box"],
    }
    target=tmp_path/"active.json"
    r54._write(target,records)
    decoded=json.loads(target.read_text())
    assert decoded["active_face"]["active_low"]==[1]
    assert decoded["active_face"]["reference_gradient"]==[1.,2.]
    with pytest.raises(ValueError):
        r54._write(target,{"missing_gradient":float("nan")})
