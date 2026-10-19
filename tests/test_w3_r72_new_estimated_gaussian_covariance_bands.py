"""R72 source independence, HC2 estimated covariance and failure-inclusive audit gates."""
from __future__ import annotations

from hashlib import sha256
import json
import math

import numpy as np
import pytest

from scripts import run_w3_r72_new_estimated_gaussian_covariance_bands as r72
from scripts import run_w3_r71_new_known_gaussian_band_oracle as r71
from scripts.run_w3_fixed_truth_interval_pilot import independent_hc1_oracle


def _refused(block,design,support):
    return {
        "study":r72.STUDY,"block":block,"design":design,"support":support,
        "source_seed":r72.source_seed(block,design),
        "wild_seed":r72.wild_seed(block,design,support),
        "estimated_gaussian_seed":r72.gaussian_seed(block,design,support),
        "completed":False,"refused":True,
        "exception":{"type":"SyntheticRefusal","message":"preserved"},
        "coverage":{k:None for k in r72.METHODS},
        "calibrated_90pct_simultaneous_band":False,
        "source_law_not_a_real_data_covariance_estimator":True,
        "release_authorized":False,
    }


def _grid():
    return [_refused(b,d,s) for b in range(r72.BLOCKS)
            for d in r72.DESIGNS for s in r72.SUPPORT]


def test_frozen_new_source_identity_and_no_oracle_covariance_used_to_fit():
    assert r72.BLOCKS==32 and r72.SOURCE_CASES==128
    assert r72.DRAW_B==999
    assert r72.SHARDS==((0,8),(8,16),(16,24),(24,32))
    assert len({r72.SOURCE_SEED,r72.GAUSSIAN_SEED,r72.WILD_SEED,
                r71.SOURCE_SEED,r71.ORACLE_SEED,r71.WILD_SEED})==6
    assert r72.METHODS==("original_wild_HC1",
                          "estimated_HC2_Gaussian","known_Gaussian_law")
    assert r72.CONFIDENCE==.9 and r72.QUANTILE=="higher"
    for method in r72.METHODS:
        assert method in _grid()[0]["coverage"]
    with pytest.raises(ValueError,match="registered"):
        r72.source_seed(32,"curve")
    with pytest.raises(ValueError,match="registered"):
        r72.gaussian_seed(0,"curve","invalid")


@pytest.mark.parametrize("design",r72.DESIGNS)
def test_new_source_leverage_pair_shares_Gaussian_innovations_but_not_old_r71(design):
    _,_,truth,X,Y=r72.simulate(0,design,"ordinary")
    _,_,again,Z,W=r72.simulate(0,design,"extreme")
    np.testing.assert_array_equal(truth,again)
    np.testing.assert_array_equal(X[1:-1],Z[1:-1])
    assert Z[0,1]==-4 and Z[-1,1]==4
    ordinary_noise=Y-np.einsum("np,ptd->ntd",X,truth)
    extreme_noise=W-np.einsum("np,ptd->ntd",Z,truth)
    np.testing.assert_allclose(ordinary_noise,extreme_noise,atol=3e-14,rtol=0)
    _,_,_,_,oldY=r71.simulate(0,design,"ordinary")
    assert not np.array_equal(Y,oldY)
    _,_,_,_,nextY=r72.simulate(1,design,"ordinary")
    assert not np.array_equal(Y,nextY)


def test_HC2_residual_covariance_factor_and_seed_do_not_use_known_DGP():
    _,_,truth,X,Y=r72.simulate(0,"curve","extreme")
    beta,hc1=independent_hc1_oracle(X,Y)
    a=r72.hc2_gaussian_covariance_maxima(X,Y,beta,seed=123)
    b=r72.hc2_gaussian_covariance_maxima(X,Y,beta,seed=123)
    np.testing.assert_array_equal(a["maxima"],b["maxima"])
    assert a["maxima"].shape==(999,)
    assert a["estimated_se"].shape==(31,2)
    assert np.isfinite(a["estimated_se"]).all()
    assert np.all(a["estimated_se"]>0)
    assert max(a["unit_hat"])<1
    assert a["critical"]==np.quantile(a["maxima"],.9,method="higher")
    assert a["covariance_effective_rank_upper"]==min(72-2,62)
    beta_other=beta.copy()
    beta_other[1]+=0.001
    changed=r72.hc2_gaussian_covariance_maxima(X,Y,beta_other,seed=123)
    assert not np.array_equal(changed["estimated_se"],a["estimated_se"])
    with pytest.raises(ValueError,match="shape"):
        r72.hc2_gaussian_covariance_maxima(X[:40],Y,beta,seed=123)


def test_real_case_original_package_wild_and_estimated_Gaussian_are_separate():
    case=r72.case(0,"curve","ordinary")
    assert case["completed"],case["exception"]
    assert not case["refused"]
    assert case["package_HC1_OLS_max_error"]<=r72.ORACLE_TOL
    assert case["package_wild_max_reference_error"]<=r72.ORACLE_TOL
    assert len(case["estimated_HC2_Gaussian_999_maxima"])==999
    assert len(case["original_wild_999_maxima"])==999
    assert len(case["original_artificial_X"])==72
    assert len(case["original_artificial_Y_unit_means"])==72
    assert len(case["original_function_truth_slope"])==31
    for name in r72.METHODS:
        assert type(case["coverage"][name]) is bool
        assert case["coverage"][name]==(
            case["pivots"][name]<=case["criticals"][name])
    assert not case["calibrated_90pct_simultaneous_band"]
    assert not case["release_authorized"]


def test_full_refusal_ledger_and_wrong_checkout_or_tampered_source_fail_closed(tmp_path,monkeypatch):
    all_rows=_grid()
    report=r72.summarize(all_rows)
    assert report["paired_design_and_support_cases"]==128
    for design in r72.DESIGNS:
        for support in r72.SUPPORT:
            entry=report["per_cell"][design][support]
            assert entry["independent_primitive_blocks"]==32
            assert entry["refused"]==32
            for method in r72.METHODS:
                assert entry["methods"][method]["full_denominator_lower"]==0.
                assert entry["methods"][method]["full_denominator_upper"]==1.
    assert not report["release_authorized"]
    with pytest.raises(ValueError,match="missing/duplicate"):
        r72.summarize(all_rows[:-1])
    monkeypatch.setenv("GITHUB_SHA","f"*40)
    parts=tmp_path/"parts"
    for start,stop in r72.SHARDS:
        folder=parts/f"part{start}"
        folder.mkdir(parents=True)
        rows=[r for r in all_rows if start<=r["block"]<stop]
        raw=(json.dumps(rows,sort_keys=True,indent=2)+"\n").encode("utf-8")
        (folder/"cases.json").write_bytes(raw)
        (folder/"manifest.json").write_bytes((json.dumps({
            "study":r72.STUDY,"start":start,"stop":stop,
            "source_seed":r72.SOURCE_SEED,
            "Gaussian_seed":r72.GAUSSIAN_SEED,
            "wild_seed":r72.WILD_SEED,
            "checkout":"f"*40,
            "source_count":len(rows),
            "sha256_cases":sha256(raw).hexdigest(),
        },sort_keys=True,indent=2)+"\n").encode("utf-8"))
    r72.aggregate(tmp_path/"complete",parts)
    assert len((tmp_path/"complete"/"SHA256SUMS").read_text().splitlines())==3
    (parts/"part0"/"cases.json").write_bytes(b"tampered")
    with pytest.raises(ValueError,match="SHA256"):
        r72.aggregate(tmp_path/"corrupt",parts)
    # A mismatched source checkout fails closed even with correctly hashed data.
    (parts/"part0"/"cases.json").write_bytes((json.dumps(
        [r for r in all_rows if r["block"]<8],sort_keys=True,indent=2)+"\n").encode())
    manifest=json.loads((parts/"part0"/"manifest.json").read_text())
    manifest["sha256_cases"]=sha256((parts/"part0"/"cases.json").read_bytes()).hexdigest()
    manifest["checkout"]="0"*40
    (parts/"part0"/"manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError,match="mixed-checkout"):
        r72.aggregate(tmp_path/"mixed",parts)
