"""R61 covariance law, native witness, provenance and refusal tests."""
import hashlib
import json

import numpy as np
import pytest

from scripts import run_w3_r61_H0_Gaussian_covariance_fidelity as r61


def test_new_source_seed_and_exact_raw_native_design_contract():
    assert r61.SOURCE_SEED != r61.DRAW_SEED
    assert r61.BLOCKS == 4 and r61.N == 24
    assert r61.M == 1024 and len(r61.SHARDS) == 4
    data=r61.new_source(0,r61.SUPPORT[0])
    assert data["true_slope_variance"]==0.
    assert data["original_slope_contribution_L2"]>0.
    assert set(r61.design_witness(data))=={
        "X","y","w","group","time","trial","x"}
    with pytest.raises(ValueError,match="outside"):
        r61.new_source(4,r61.SUPPORT[0])


def test_one_native_raw_fitted_H0_Gaussian_draw_fidelity():
    out=r61.inspect_H0_fidelity(0,r61.SUPPORT[0],draws=128)
    assert out["study"]==r61.STUDY
    assert out["native_synthetic_source"]["y"]
    assert out["true_generating_random_slope_variance"]==0.
    assert not out["release_authorized"]
    if out["source_status"]=="accepted":
        assert out["n_original_participant_covariances"]==24
        assert out["maximum_H0_kernel_to_cholesky_covariance_error"]<=1e-8
        assert len(out["fidelity_records"])==2
        assert out["fitted_H0_theta"][1]==0.
        assert all(v["max_weighted_backtransform_whitening_error"]<=2e-8
                   for v in out["fidelity_records"])
    else:
        assert out["source_error"] is not None


def test_original_failure_slots_survive_without_pseudocalibration():
    rows=[{"block":b,"support":s,"source_status":"refused",
           "n_original_participant_covariances":0,"fidelity_records":[],
           "maximum_H0_kernel_to_cholesky_covariance_error":None}
          for b in range(r61.BLOCKS) for s in r61.SUPPORT]
    result=r61.summarize(rows)
    assert result["recorded_source_variants"]==8
    assert result["refused_source_cases"]==8
    assert result["completed_participant_covariance_identity_checks"]==0
    assert result["max_analytic_covariance_identity_error"] is None
    assert not result["release_authorized"]
    with pytest.raises(ValueError,match="identities"):
        r61.summarize(rows[:-1])


def test_exact_SHA256_and_same_checkout_fails_on_tampering(tmp_path,monkeypatch):
    monkeypatch.setenv("GITHUB_SHA","R61-new-original-merge")
    rows=[{"block":b,"support":s,"source_status":"refused",
           "n_original_participant_covariances":0,"fidelity_records":[],
           "maximum_H0_kernel_to_cholesky_covariance_error":None}
          for b in range(r61.BLOCKS) for s in r61.SUPPORT]
    parts=tmp_path/"parts"
    for start,stop in r61.SHARDS:
        folder=parts/f"part-{start}"
        folder.mkdir(parents=True)
        raw=json.dumps([v for v in rows if start<=v["block"]<stop],
                       sort_keys=True,indent=2)+"\n"
        (folder/"cases.json").write_bytes(raw.encode("utf-8"))
        (folder/"manifest.json").write_text(json.dumps({
            "study":r61.STUDY,"start":start,"stop":stop,
            "source_seed":r61.SOURCE_SEED,
            "draw_seed":r61.DRAW_SEED,
            "checkout":"R61-new-original-merge",
            "rows":2,"sha256_cases":hashlib.sha256(raw.encode()).hexdigest(),
        })+"\n")
    r61.aggregate(tmp_path/"all",parts)
    assert (tmp_path/"all"/"SHA256SUMS").exists()
    (parts/"part-0"/"cases.json").write_text("altered original")
    with pytest.raises(ValueError,match="SHA256"):
        r61.aggregate(tmp_path/"tampered",parts)
