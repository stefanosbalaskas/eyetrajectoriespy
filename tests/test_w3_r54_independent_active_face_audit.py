"""R54 read-only physical KKT and immutable evidence tamper contracts."""
import hashlib
import json

import pytest

from scripts.audit_w3_r54_original_active_face_independent import (
    LOW,close,signature,validate_fit,verify_SHA256,
)


def _valid():
    starts=[
        {"label":"interior","status":"ok","optimizer_success":True,
         "negative_loglik":100.,"physical_projected_KKT":.0002,
         "ratios":[.2,.25,.3,1.],
         "objective_reconstruction_error":0.},
        {"label":"spread","status":"ok","optimizer_success":True,
         "negative_loglik":100.,"physical_projected_KKT":.0001,
         "ratios":[.2,.25,.3,1.],
         "objective_reconstruction_error":0.},
    ]
    return {
        "status":"accepted","numerical_starts":starts,
        "selected_start":"spread","selected_NLL":100.,
        "physical_projected_KKT":.0001,"reference_variance":.02,
        "components":{
            "participant_intercept":.003,
            "participant_slope":.02*LOW,
            "trial":.004,
            "sensor":.005,
        },
    }


def test_frozen_physical_fit_rejects_false_numerical_KKT_acceptance():
    base=_valid()
    assert validate_fit(base,"valid")=="spread"
    base["physical_projected_KKT"]=.02
    with pytest.raises(ValueError,match="selected fit KKT"):
        validate_fit(base,"forged KKT")
    base=_valid()
    for s in base["numerical_starts"]:
        s["physical_projected_KKT"]=.02
    with pytest.raises(ValueError,match="false numerical fit acceptance"):
        validate_fit(base,"no physical KKT qualified starts")


def test_frozen_likelihood_reconstruction_and_start_selection():
    base=_valid()
    base["numerical_starts"][0]["objective_reconstruction_error"]=.001
    with pytest.raises(ValueError,match="reconstruction"):
        validate_fit(base,"falsified likelihood")
    base=_valid()
    base["numerical_starts"][1]["negative_loglik"]=101.
    with pytest.raises(ValueError,match="selected fit NLL"):
        validate_fit(base,"selected likelihood outside observed minimum")


def test_box_face_signature_uses_positive_observed_reference():
    x=_valid()
    assert signature(x)==[[1],[]]
    x["components"]["participant_slope"]=.01
    assert signature(x)==[[],[]]


def test_original_SHA256_and_source_identity_fail_closed(tmp_path):
    for name,body in (
        ("cases.json","[]\n"),("summary.json","{}\n"),
        ("source-commit.txt","matching-original-sha\n"),
    ):
        (tmp_path/name).write_text(body)
    h={name:hashlib.sha256((tmp_path/name).read_bytes()).hexdigest()
       for name in ("cases.json","summary.json","source-commit.txt")}
    (tmp_path/"SHA256SUMS").write_text("".join(
        v+"  "+k+"\n" for k,v in h.items()))
    # Exact verified source identity must be passed by caller.
    assert verify_SHA256(tmp_path,h["cases.json"],"matching-original-sha")==h
    (tmp_path/"cases.json").write_text("[tampered]")
    with pytest.raises(ValueError,match="SHA256 mismatch"):
        verify_SHA256(tmp_path,h["cases.json"],"matching-original-sha")
    with pytest.raises(ValueError,match="mismatch"):
        close(1.,2.,"fabricated pivotal error")
