"""R68 NEW independent source numerical-only feasibility contracts."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from scripts import run_w3_r68_new_source_numerical_feasibility as r68
from scripts import run_w3_r63_independent_null_replication as core


def _case(b,s,l):
    return {
        "study":r68.STUDY,"block":b,"support":s,"level":l,
        "source_status":"refused","source_error":"synthetic-only-fixture",
        "true_slope_variance":(r68.MULTIPLIERS[l]*.045)**2,
        "observed":core.nested_on_invalid(),
        "bootstrap":[r68.empty_draw(i) for i in range(r68.B)],
        "original_test_p_value":None,
        "candidate_rejection":None,
        "statistical_power_qualified":False,
        "fitted_CR2_90pct_qualified":False,
        "release_authorized":False,
    }


def _all():
    return [_case(b,s,l) for b in range(r68.BLOCKS)
            for s in r68.SUPPORT for l in r68.LEVELS]


def _start(label,nll,kkt):
    return {
        "label":label,
        "negative_loglik":nll,
        "physical_projected_KKT":kkt,
        "objective_reconstruction_error":0.,
        "status":"ok",
        "optimizer_success":True,
    }


def _nested(*,H0=-100.,H1=-100.02,best_nonstationary=False):
    alt=[
        _start("alt_at_exact_zero",H1,5e-6),
        _start("alt_tiny_positive",H1-.006 if best_nonstationary else H1,9.),
        _start("alt_positive",H1+.0001,6e-6),
        _start("alt_wide",H1+.0002,7e-6),
    ]
    if not best_nonstationary:
        alt[1]["negative_loglik"]=H1+.001
    nonmono=H1>H0
    return {
        "status":"refused" if best_nonstationary or nonmono else "accepted",
        "raw_deviance":None if best_nonstationary else 2*(H0-H1),
        "error":"H0_or_H1_refused_by_original_numerical_gates" if best_nonstationary else
            "nonfinite_or_nonmonotone_nested_gap" if nonmono else None,
        "null_fit":{
            "status":"accepted","selected_NLL":H0,
            "original_starts":[_start("null_compact",H0,2e-6),
                               _start("null_spread",H0+.0001,3e-6)]},
        "alternative_fit":{
            "status":"refused" if best_nonstationary else "accepted",
            "selected_NLL":None if best_nonstationary else H1,
            "original_starts":alt,
        },
    }


def test_frozen_disjoint_gaussian_design_and_denominators():
    assert r68.MASTER_SEED==202610196868
    assert r68.DRAW_SEED==202610196869
    assert r68.BLOCKS==8 and r68.PARTICIPANTS==24
    assert r68.SHARDS==((0,4),(4,8))
    assert r68.CASES==48 and r68.DRAWS==192
    assert r68.NESTED_POSITIONS==480 and r68.START_POSITIONS==1440
    assert r68.B==4
    assert (r68.KKT_TOL,r68.NLL_TOL,r68.NEST_TOL)==(.001,.001,.00001)
    assert set(r68.MULTIPLIERS)=={"zero","half","full"}
    assert r68.MASTER_SEED not in {202610186666,202610186464}
    assert r68.DRAW_SEED not in {202610186667,202610186465}


def test_source_common_nonslope_component_new_seeds_and_native_design():
    a=r68.source(0,r68.SUPPORT[0],"zero")
    b=r68.source(0,r68.SUPPORT[0],"half")
    c=r68.source(0,r68.SUPPORT[0],"full")
    for key in ("X","w","group","time","trial","x"):
        np.testing.assert_array_equal(a[key],b[key])
        np.testing.assert_array_equal(a[key],c[key])
    np.testing.assert_allclose(2*b["y"],a["y"]+c["y"],rtol=1e-12,atol=1e-12)
    assert a["true_slope_variance"]==0.
    assert b["true_slope_variance"]==pytest.approx(.00050625)
    assert c["true_slope_variance"]==pytest.approx(.002025)
    assert not np.array_equal(a["y"],r68.source(1,r68.SUPPORT[0],"zero")["y"])
    with pytest.raises(ValueError,match="outside"):
        r68.source(8,r68.SUPPORT[0],"full")


def test_frozen_H1_gap_vs_KKT_refusal_and_negative_nesting_remain_distinct():
    a=r68.diagnostic(_nested(H0=-120.,H1=-120.02,best_nonstationary=True))
    assert a["H1_best_KKT_exceeds_original_001"] is True
    assert a["H1_eligible_gap_exceeds_original_001"] is True
    assert a["H1_eligible_minus_raw_best_NLL"]==pytest.approx(.006)
    assert a["alternative_status"]=="refused"
    assert a["negative_nested_deviance_beyond_original_tolerance"] is None

    b=r68.diagnostic(_nested(H0=-100.,H1=-99.997))
    assert b["null_status"]=="accepted"
    assert b["alternative_status"]=="accepted"
    assert b["raw_nested_deviance"]==pytest.approx(-.006)
    assert b["negative_nested_deviance_beyond_original_tolerance"] is True
    assert b["H1_eligible_gap_exceeds_original_001"] is False
    assert b["observed_nested_status"]=="refused"

    good=r68.diagnostic(_nested())
    assert good["negative_nested_deviance_beyond_original_tolerance"] is False
    assert good["observed_nested_status"]=="accepted"


def test_full_48_case_192_draw_refusal_inclusive_grid_without_test_power():
    rows=_all()
    report=r68.summarize(rows)
    assert report["matched_original_source_cases"]==48
    assert report["conditional_Gaussian_draw_slots"]==192
    assert report["original_nested_H0_H1_model_positions"]==480
    assert report["original_optimizer_start_slots"]==1440
    assert report["recorded_distinct_attempted_draw_seeds"]==0
    assert report["original_fit_status_counts"]["conditional/not_attempted"]==192
    assert report["original_fit_status_counts"]["observed/not_attempted"]==48
    assert report["num_new_5pct_test_calibrations"]==0
    assert report["no_statistical_candidate_p_or_power"] is True
    assert report["no_original_R66_refusal_repair_or_interval_recovery"] is True
    assert report["release_authorized"] is False
    rows=_all()
    rows[0]["bootstrap"]=rows[0]["bootstrap"][:-1]
    with pytest.raises(ValueError,match="pseudodraw slots"):
        r68.summarize(rows)
    rows=_all()
    rows[1]["block"]=rows[0]["block"]
    rows[1]["support"]=rows[0]["support"]
    rows[1]["level"]=rows[0]["level"]
    with pytest.raises(ValueError,match="missing/duplicate"):
        r68.summarize(rows)
    rows=_all()
    rows[0]["candidate_rejection"]=False
    with pytest.raises(ValueError,match="scientific claim"):
        r68.summarize(rows)


def test_192_full_new_gaussian_draw_seeds_no_collisions():
    seeds=[]
    for block in range(r68.BLOCKS):
        for si,_ in enumerate(r68.SUPPORT):
            for li,_ in enumerate(r68.LEVELS):
                for d in range(r68.B):
                    seeds.append(r68.DRAW_SEED+100003*block+739*si+1009*li+d)
    assert len(set(seeds))==len(seeds)==r68.DRAWS


def test_unchanged_original_nested_estimator_called_without_reclassification(monkeypatch):
    calls=[]
    def fake_nested(data):
        calls.append("nested")
        return core.nested_on_invalid()
    monkeypatch.setattr(r68.core,"nested_on",fake_nested)
    case=r68.evaluate(0,r68.SUPPORT[0],"zero")
    assert calls==["nested"]
    assert case["observed"]["status"]=="not_attempted"
    assert len(case["bootstrap"])==4
    assert all(x["status"]=="not_attempted" for x in case["bootstrap"])
    assert case["candidate_rejection"] is None
    assert case["original_test_p_value"] is None


def test_two_shard_hash_manifest_aggregate_and_tampering_fail_closed(tmp_path,monkeypatch):
    monkeypatch.setenv("GITHUB_SHA","d"*40)
    parts=tmp_path/"parts"
    for start,stop in r68.SHARDS:
        folder=parts/f"part-{start}"
        folder.mkdir(parents=True)
        rows=[_case(b,s,l) for b in range(start,stop)
              for s in r68.SUPPORT for l in r68.LEVELS]
        raw=(json.dumps(rows,sort_keys=True,indent=2)+"\n").encode()
        (folder/"cases.json").write_bytes(raw)
        manifest={
            "study":r68.STUDY,"source_seed":r68.MASTER_SEED,
            "draw_seed":r68.DRAW_SEED,"source_checkout":"d"*40,
            "start":start,"stop":stop,"count":len(rows),
            "sha256_cases":hashlib.sha256(raw).hexdigest(),
        }
        (folder/"manifest.json").write_text(json.dumps(manifest))
    folder=tmp_path/"aggregated"
    r68.aggregate(folder,parts)
    record=json.loads((folder/"summary.json").read_bytes())
    assert record["matched_original_source_cases"]==48
    assert "cases.json" in (folder/"SHA256SUMS").read_text()
    modified=parts/"part-0"/"cases.json"
    modified.write_bytes(modified.read_bytes()+b" ")
    with pytest.raises(ValueError,match="SHA256"):
        r68.aggregate(tmp_path/"refused",parts)
