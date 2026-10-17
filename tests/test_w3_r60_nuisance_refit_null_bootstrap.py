"""R60 conditional Gaussian fitted-H0 null bootstrap numerical contracts."""
import hashlib
import json
import math

import numpy as np
import pytest

from scripts import run_w3_r60_nuisance_refit_null_bootstrap as r60
from scripts import run_w3_r59_independent_null_replication as r59


def test_new_independent_source_draw_seed_and_frozen_denominators():
    assert r60.MASTER_SEED != r59.MASTER_SEED
    assert r60.DRAW_SEED != r60.MASTER_SEED
    assert r60.BLOCKS == 4 and r60.B == 31
    assert r60.SOURCE_SLOTS == 8
    assert r60.BOOT_SLOTS == 248
    assert r60.FITS == 512
    assert r60.OPTIMIZER_START_SLOTS == 1536
    with pytest.raises(ValueError,match="outside"):
        r60.source(4,r60.SUPPORT[0])


def test_new_Gaussian_null_source_and_H0_covariance_gls():
    data = r60.source(0, r60.SUPPORT[0])
    other = r60.source(0, r60.SUPPORT[1])
    assert data["true_slope_variance"] == other["true_slope_variance"] == 0.
    assert data["removed_slope_L2"] > 0.
    assert data["X"].shape[0] == data["y"].shape[0]
    assert not np.array_equal(data["x"],other["x"])
    fitted = r60.nested_on(data)
    assert fitted["status"] in ("accepted","refused")
    assert len(fitted["null_fit"]["original_starts"]) == 2
    assert len(fitted["alternative_fit"]["original_starts"]) == 4
    if fitted["status"] == "accepted":
        beta,covs,theta=r60.h0_gls_covariance(
            data,fitted["null_fit"],fitted["observed_reference"])
        assert len(covs)==24
        assert theta[1] == 0.
        assert all(np.all(np.diag(L)>0) for _,L in covs)
        pseudo,seed=r60.pseudo_under_h0(
            data,beta,covs,0,r60.SUPPORT[0],0)
        pseudo_again,_=r60.pseudo_under_h0(
            data,beta,covs,0,r60.SUPPORT[0],0)
        pseudo_next,_=r60.pseudo_under_h0(
            data,beta,covs,0,r60.SUPPORT[0],1)
        np.testing.assert_array_equal(pseudo["y"],pseudo_again["y"])
        assert not np.array_equal(pseudo["y"],pseudo_next["y"])
        assert not np.array_equal(data["y"],pseudo["y"])
        np.testing.assert_array_equal(pseudo["X"],data["X"])
        np.testing.assert_array_equal(pseudo["w"],data["w"])
        assert seed != r60.DRAW_SEED-1
        with pytest.raises(ValueError,match="unregistered"):
            r60.pseudo_under_h0(
                data,beta,covs,4,r60.SUPPORT[0],0)


def test_research_failures_remain_on_original_denominator():
    rows=[r60.empty_case(b,s)
          for b in range(r60.BLOCKS) for s in r60.SUPPORT]
    for r in rows:
        r["bootstrap"]=[r60.empty_draw(i) for i in range(r60.B)]
    result=r60.summarize(rows)
    assert result["recorded_source_cases"]==8
    assert result["recorded_H0_bootstrap_draw_slots"]==248
    assert result["recorded_optimizer_start_slots"]==1536
    assert not result["release_authorized"]
    assert result["no_independent_evaluation_calibration_study"]
    for cell in result["strata"].values():
        assert cell["fully_qualified_original_and_31_refit_bootstrap_sources"]==0
        assert cell["accepted_bootstrap_draws"]==0
        assert cell["recorded_bootstrap_draw_slots"]==4*r60.B
    with pytest.raises(ValueError,match="denominator"):
        r60.summarize(rows[:-1])


def test_empirical_add_one_rank_grid_is_explicit():
    assert r60.B==31
    assert 1/(r60.B+1) == .03125
    assert 2/(r60.B+1) == .0625
    assert r60.ORIGINAL_CUTOFF>0
    assert r60.ORIGINAL_ALPHA==.05


def test_manifest_exact_original_four_shards_and_tampering(tmp_path,monkeypatch):
    monkeypatch.setenv("GITHUB_SHA","frozen-R60-Gaussian-PR-merge")
    parts=tmp_path/"parts"
    rows=[r60.empty_case(b,s)
          for b in range(r60.BLOCKS) for s in r60.SUPPORT]
    for row in rows:
        row["bootstrap"]=[r60.empty_draw(i) for i in range(r60.B)]
    for start,stop in r60.SHARDS:
        folder=parts/str(start)
        folder.mkdir(parents=True)
        payload=json.dumps(
            [r for r in rows if start<=r["block"]<stop],
            sort_keys=True,indent=2)+"\n"
        (folder/"cases.json").write_bytes(payload.encode("utf-8"))
        (folder/"manifest.json").write_text(json.dumps(
            {"study":r60.STUDY,"start":start,"stop":stop,
             "new_source_seed":r60.MASTER_SEED,
             "new_draw_seed":r60.DRAW_SEED,
             "checkout":"frozen-R60-Gaussian-PR-merge",
             "source_count":2,
             "sha256_cases":hashlib.sha256(payload.encode()).hexdigest()}
        )+"\n")
    r60.aggregate(tmp_path/"complete",parts)
    assert (tmp_path/"complete"/"summary.json").exists()
    (parts/"0"/"cases.json").write_text("tampered")
    with pytest.raises(ValueError,match="SHA256"):
        r60.aggregate(tmp_path/"bad",parts)
