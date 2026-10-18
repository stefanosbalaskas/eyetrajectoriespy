"""R63 128 independent source-block, frozen bootstrap and failure-ledger contracts."""
from __future__ import annotations
import hashlib
import json
import math
import numpy as np
import pytest

from scripts import run_w3_r63_independent_null_replication as r63
from scripts import run_w3_r62_independent_outer_null_bootstrap as r62
from scripts import run_w3_r59_independent_null_replication as r59


def test_new_independent_source_budget_and_exact_design():
    assert r63.BLOCKS == 128 and r63.PARTICIPANTS == 24
    assert r63.B == 63
    assert r63.SOURCE_SLOTS == 256
    assert r63.BOOT_SLOTS == 16128
    assert r63.FITS == 32768
    assert r63.OPTIMIZER_START_SLOTS == 98304
    assert len(r63.SHARDS) == 32
    assert set(r63.SHARDS) == {(i,i+4) for i in range(0,128,4)}
    assert len({r63.MASTER_SEED,r63.DRAW_SEED,r62.MASTER_SEED,r62.DRAW_SEED,
                r59.MASTER_SEED}) == 5
    assert r63.ORIGINAL_ALPHA == r62.ORIGINAL_ALPHA == .05
    assert r63.ORIGINAL_CUTOFF == r62.ORIGINAL_CUTOFF
    assert r63.SUPPORT == r62.SUPPORT
    assert math.isclose((1+2)/(r63.B+1),.046875)
    with pytest.raises(ValueError,match="outside"):
        r63.source(128,r63.SUPPORT[0])


def test_new_true_zero_sources_and_paired_leverage_not_recycled():
    original=r63.source(0,r63.SUPPORT[0])
    paired=r63.source(0,r63.SUPPORT[1])
    next_source=r63.source(1,r63.SUPPORT[0])
    past=r62.source(0,r62.SUPPORT[0])
    assert original["true_slope_variance"]==paired["true_slope_variance"]==0.
    assert original["removed_slope_L2"]>0.
    assert paired["removed_slope_L2"]>0.
    assert np.array_equal(original["group"],paired["group"])
    assert not np.array_equal(original["x"],paired["x"])
    assert not np.array_equal(original["y"],next_source["y"])
    assert not np.array_equal(original["y"],past["y"])


def test_frozen_numerical_model_and_add_one_rank_contract():
    sample=r63.source(0,r63.SUPPORT[0])
    fit=r63.nested_on(sample)
    assert fit["status"] in ("accepted","refused")
    assert len(fit["null_fit"]["original_starts"]) == 2
    assert len(fit["alternative_fit"]["original_starts"]) == 4
    if fit["status"]=="accepted":
        beta,cov,theta=r63.h0_gls_covariance(
            sample,fit["null_fit"],fit["observed_reference"])
        assert theta[1]==0.
        assert len(cov)==r63.PARTICIPANTS
        a,seed=r63.pseudo_under_h0(sample,beta,cov,0,r63.SUPPORT[0],0)
        b,seed2=r63.pseudo_under_h0(sample,beta,cov,0,r63.SUPPORT[0],0)
        assert seed==seed2
        np.testing.assert_array_equal(a["y"],b["y"])
        assert not np.array_equal(a["y"],sample["y"])


def test_complete_source_failure_ledger_preserves_128_independent_denominator():
    rows=[r63.empty_case(block,s)
          for block in range(r63.BLOCKS) for s in r63.SUPPORT]
    for row in rows:
        row["bootstrap"]=[r63.empty_draw(j) for j in range(r63.B)]
    out=r63.summarize(rows)
    assert out["recorded_source_cases"]==256
    assert out["recorded_H0_bootstrap_draw_slots"]==16128
    assert out["recorded_optimizer_start_slots"]==98304
    assert out["paired_both_complete"]==0
    for v in out["strata"].values():
        assert v["independent_source_blocks"]==128
        assert v["source_cases_with_refused_or_incomplete_bootstrap"]==128
        assert v["bootstrap_all_source_lower_refusals_as_nonrejection"]==0.
        assert v["bootstrap_all_source_upper_refusals_as_rejection"]==1.
        assert v["bootstrap_candidate_nominal_005_Wilson95_complete_sources"] is None
    with pytest.raises(ValueError,match="missing or duplicated"):
        r63.summarize(rows[:-1])


def test_manifest_tamper_and_wrong_source_checkout_fail_closed(tmp_path,monkeypatch):
    monkeypatch.setenv("GITHUB_SHA","frozen-R63-test-source")
    parts=tmp_path/"parts"
    rows=[r63.empty_case(b,s) for b in range(r63.BLOCKS) for s in r63.SUPPORT]
    for row in rows:
        row["bootstrap"]=[r63.empty_draw(j) for j in range(r63.B)]
    for start,stop in r63.SHARDS:
        path=parts/f"part-{start}"
        path.mkdir(parents=True)
        payload=json.dumps([x for x in rows if start<=x["block"]<stop],
                           sort_keys=True,indent=2)+"\n"
        (path/"cases.json").write_bytes(payload.encode("utf-8"))
        (path/"manifest.json").write_bytes((json.dumps({
            "study":r63.STUDY,
            "start":start,"stop":stop,
            "new_source_seed":r63.MASTER_SEED,
            "new_draw_seed":r63.DRAW_SEED,
            "checkout":"frozen-R63-test-source",
            "source_count":(stop-start)*len(r63.SUPPORT),
            "sha256_cases":hashlib.sha256(payload.encode("utf-8")).hexdigest()
        },sort_keys=True,indent=2)+"\n").encode("utf-8"))
    r63.aggregate(tmp_path/"complete",parts)
    assert (tmp_path/"complete"/"summary.json").exists()
    (parts/"part-0"/"cases.json").write_bytes(b"tampered")
    with pytest.raises(ValueError,match="SHA256"):
        r63.aggregate(tmp_path/"tampered",parts)
