"""R64 32-block, paired zero/half/full true-slope and null-bootstrap contracts."""
from __future__ import annotations

import hashlib
import json
import math

import numpy as np
import pytest

from scripts import run_w3_r64_nonzero_slope_detection_pilot as r64
from scripts import run_w3_r63_independent_null_replication as r63
from scripts import run_w3_r62_independent_outer_null_bootstrap as r62


def test_prespecified_new_independent_source_effect_and_optimizer_budget():
    assert len({r64.MASTER_SEED,r64.DRAW_SEED,
                r63.MASTER_SEED,r63.DRAW_SEED,
                r62.MASTER_SEED,r62.DRAW_SEED})==6
    assert r64.BLOCKS==32 and r64.PARTICIPANTS==24
    assert r64.LEVELS==("zero","half","full")
    assert r64.MULTIPLIERS=={"zero":0.,"half":.5,"full":1.}
    assert r64.CASES==192
    assert r64.B==63
    assert r64.DRAWS==12096
    assert r64.NESTED_MODELS==24576
    assert r64.OPTIMIZER_STARTS==73728
    assert len(r64.SHARDS)==8
    assert set(r64.SHARDS)=={(i,i+4) for i in range(0,32,4)}
    assert r64.ALPHA==r63.ORIGINAL_ALPHA
    assert r64.CLASSICAL==r63.ORIGINAL_CUTOFF
    assert (1+2)/(r64.B+1)==.046875
    assert (1+3)/(r64.B+1)==.0625


def test_native_source_matched_structural_slope_variance_and_mean_preservation():
    z=r64.source(0,r64.SUPPORT[0],"zero")
    h=r64.source(0,r64.SUPPORT[0],"half")
    f=r64.source(0,r64.SUPPORT[0],"full")
    assert z["true_slope_variance"]==0.
    assert h["true_slope_variance"]==pytest.approx(.00050625)
    assert f["true_slope_variance"]==pytest.approx(.002025)
    for label in ("X","w","group","time","trial","x"):
        np.testing.assert_array_equal(z[label],h[label])
        np.testing.assert_array_equal(h[label],f[label])
    np.testing.assert_allclose(
        h["y"],.5*(z["y"]+f["y"]),rtol=1e-12,atol=2e-12)
    np.testing.assert_allclose(z["retained_slope_component_L2"],0.,atol=0.)
    np.testing.assert_allclose(
        h["retained_slope_component_L2"]*2,
        f["retained_slope_component_L2"],rtol=1e-13)
    assert not np.array_equal(z["y"],f["y"])
    independent=r64.source(1,r64.SUPPORT[0],"zero")
    assert not np.array_equal(z["y"],independent["y"])
    extreme=r64.source(0,r64.SUPPORT[1],"zero")
    assert not np.array_equal(z["x"],extreme["x"])
    with pytest.raises(ValueError,match="primitive"):
        r64.source(32,r64.SUPPORT[0],"zero")
    with pytest.raises(ValueError,match="undeclared"):
        r64.source(0,r64.SUPPORT[0],"positive")


def test_original_frozen_REML_and_positive_source_gaussian_bootstrap_seed():
    source=r64.source(0,r64.SUPPORT[0],"half")
    fit=r63.nested_on(source)
    assert fit["status"] in ("accepted","refused")
    assert len(fit["null_fit"]["original_starts"])==2
    assert len(fit["alternative_fit"]["original_starts"])==4
    if fit["status"]=="accepted":
        beta,cov,theta=r63.h0_gls_covariance(
            source,fit["null_fit"],fit["observed_reference"])
        assert theta[1]==0.
        a,seed=r64.conditional_h0_response(
            source,beta,cov,0,r64.SUPPORT[0],"half",62)
        b,seed2=r64.conditional_h0_response(
            source,beta,cov,0,r64.SUPPORT[0],"half",62)
        assert seed==seed2
        assert len(cov)==24
        np.testing.assert_array_equal(a["y"],b["y"])
        _,unrelated=r64.conditional_h0_response(
            source,beta,cov,0,r64.SUPPORT[0],"full",62)
        assert seed!=unrelated
    with pytest.raises(ValueError,match="index"):
        r64.conditional_h0_response(
            source,np.zeros(source["X"].shape[1]),[],0,r64.SUPPORT[0],"half",63)


def _all_refused():
    rows=[r64.empty_case(b,s,l)
          for b in range(r64.BLOCKS)
          for s in r64.SUPPORT for l in r64.LEVELS]
    for row in rows:
        row["bootstrap"]=[r64.empty_draw(j) for j in range(r64.B)]
    return rows


def test_full_fixed_denominator_and_failure_inclusive_power_label():
    records=_all_refused()
    out=r64.summarize(records)
    assert out["recorded_source_cases"]==192
    assert out["recorded_gaussian_conditional_H0_draw_slots"]==12096
    assert out["nested_H0_H1_model_fit_slots"]==24576
    assert out["optimizer_start_records"]==73728
    assert out["conditional_candidate_p_grid_denominator"]==64
    assert out["exploratory_detection_not_validated_power"]
    assert not out["release_authorized"]
    for cell in out["strata"].values():
        assert cell["complete_63_draw_sources"]==0
        assert cell["refused_incomplete_sources"]==32
        assert cell["refusal_as_nonrejection_all_source_lower"]==0.
        assert cell["refusal_as_rejection_all_source_upper"]==1.
        assert not cell["null_size_or_power_qualified"]
    with pytest.raises(ValueError,match="missing/duplicated"):
        r64.summarize(records[:-1])
    records=_all_refused()
    records[0]["bootstrap"][1]["draw"]=22
    with pytest.raises(ValueError,match="slots"):
        r64.summarize(records)


def test_full_shard_sha256_bytes_and_original_case_identity_refusal(tmp_path,monkeypatch):
    monkeypatch.setenv("GITHUB_SHA","research-fixture-checkout")
    parts=tmp_path/"parts"
    rows=_all_refused()
    for i,j in r64.SHARDS:
        target=parts/f"part-{i}"
        target.mkdir(parents=True)
        sub=[z for z in rows if i<=z["block"]<j]
        raw=(json.dumps(sub,sort_keys=True,allow_nan=False,indent=2)+"\n").encode()
        (target/"cases.json").write_bytes(raw)
        (target/"manifest.json").write_bytes((json.dumps({
            "study":r64.STUDY,"start":i,"stop":j,
            "source_seed":r64.MASTER_SEED,
            "draw_seed":r64.DRAW_SEED,
            "checkout":"research-fixture-checkout",
            "source_cases":len(sub),
            "sha256_cases":hashlib.sha256(raw).hexdigest(),
        },sort_keys=True,indent=2)+"\n").encode())
    r64.aggregate(tmp_path/"original-aggregate",parts)
    assert (tmp_path/"original-aggregate"/"SHA256SUMS").exists()
    (parts/"part-0"/"cases.json").write_bytes(b"altered original evidence")
    with pytest.raises(ValueError,match="SHA256"):
        r64.aggregate(tmp_path/"refused",parts)
