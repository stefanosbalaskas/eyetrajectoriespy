"""R74 research-only prospective NEW-source slope-specific HC2/HC3 contracts."""
from __future__ import annotations

from hashlib import sha256
import json

import numpy as np
import pytest

from scripts import run_w3_r74_new_weighted_slope_hc2_hc3 as r74
from scripts import run_w3_r71_new_known_gaussian_band_oracle as r71
from scripts import run_w3_r72_new_estimated_gaussian_covariance_bands as r72
from scripts.run_w3_fixed_truth_interval_pilot import independent_hc1_oracle


def _refused(block,config,support,variance):
    n,trials,design=r74.config_info(config)
    return {
        "study":r74.STUDY,"block":block,"config":config,"design":design,
        "support":support,"variance":variance,
        "source_seed":r74.seed(block,config,support,variance,"source"),
        "gaussian_seed":r74.seed(block,config,support,variance,"gaussian"),
        "wild_seed":r74.seed(block,config,support,variance,"wild"),
        "completed":False,"refused":True,
        "exception":{"type":"SyntheticOriginalSourceRefusal","message":"failure included"},
        "no_calibrated_90pct_simultaneous_method":True,
        "no_source_missingness_or_MNAR":True,
        "release_authorized":False,
    }


def _grid():
    return [_refused(b,c,s,v) for b in range(r74.BLOCKS)
            for c in r74.CONFIGS for s in r74.SUPPORT for v in r74.VARIANCE]


def test_frozen_new_sources_small_and_standard_unit_denominators():
    assert r74.BLOCKS==32 and r74.SOURCE_CASES==512
    assert r74.SOURCE_SEED==202610197474
    assert r74.GAUSSIAN_SEED==202610197475
    assert r74.WILD_SEED==202610197476
    assert r74.B==999 and r74.CONF==.90
    assert r74.CONFIGS==(
        "curve_small","curve_standard","participant_small","participant_standard")
    assert r74.SHARDS==tuple((x,x+4) for x in range(0,32,4))
    expected={"curve_small":(36,1,"curve"),"curve_standard":(72,1,"curve"),
              "participant_small":(24,3,"participant"),
              "participant_standard":(36,3,"participant")}
    assert {key:r74.config_info(key) for key in r74.CONFIGS}==expected
    assert len({r74.seed(b,c,s,v,"gaussian") for b in range(32)
                for c in r74.CONFIGS for s in r74.SUPPORT
                for v in r74.VARIANCE})==512
    assert len({r74.SOURCE_SEED,r74.GAUSSIAN_SEED,r74.WILD_SEED,
                r72.SOURCE_SEED,r72.GAUSSIAN_SEED,r72.WILD_SEED})==6
    with pytest.raises(ValueError,match="outside prospective"):
        r74.seed(32,"curve_small","ordinary","constant","source")


@pytest.mark.parametrize("config",r74.CONFIGS)
def test_gaussian_unit_innovations_matched_across_supports_and_variance(config):
    base=r74.simulate(0,config,"ordinary","constant")
    ext=r74.simulate(0,config,"extreme","constant")
    hetero=r74.simulate(0,config,"extreme","predictor_heteroskedastic")
    _,_,truth,X,Y,scale=base
    _,_,true2,Z,W,s2=ext
    _,_,true3,ZZ,WW,s3=hetero
    np.testing.assert_array_equal(truth,true2)
    np.testing.assert_array_equal(truth,true3)
    np.testing.assert_array_equal(X[1:-1],Z[1:-1])
    np.testing.assert_array_equal(Z,ZZ)
    assert Z[0,1]==-4. and Z[-1,1]==4.
    np.testing.assert_array_equal(scale,np.ones(len(X)))
    np.testing.assert_array_equal(s3,1+.75*np.abs(Z[:,1]))
    assert s3[0]==s3[-1]==4.
    source_err=Y-np.einsum("np,ptd->ntd",X,truth,optimize=True)
    extreme_err=W-np.einsum("np,ptd->ntd",Z,truth,optimize=True)
    hetero_err=WW-np.einsum("np,ptd->ntd",ZZ,truth,optimize=True)
    np.testing.assert_allclose(source_err,extreme_err,atol=4e-14,rtol=0)
    np.testing.assert_allclose(hetero_err,extreme_err*s3[:,None,None],
                               atol=6e-14,rtol=0)


def test_true_heteroskedastic_law_slope_weights_are_not_pooled():
    _,_,_,X,Y,scale=r74.simulate(
        0,"curve_standard","extreme","predictor_heteroskedastic")
    exact=r74.true_slope_se(X,scale,"curve")
    inv=np.linalg.inv(X.T@X)
    a=(inv@X.T)[1]
    direct=np.sqrt(np.sum((a*scale)**2)*r71.unit_covariance_variance("curve"))
    np.testing.assert_allclose(exact,direct,atol=1e-14,rtol=0)
    common=np.sqrt(inv[1,1]*r71.unit_covariance_variance("curve"))
    assert np.all(exact>common*2)


def test_slope_specific_HC2_HC3_factor_weights_and_pooled_R72_reference():
    _,_,_,X,Y,_=r74.simulate(0,"participant_small","extreme",
                             "predictor_heteroskedastic")
    beta,_=independent_hc1_oracle(X,Y)
    candidates,hat=r74.slope_gaussian_candidates(X,Y,beta,normal_seed=912)
    n=len(X)
    residual=(Y-np.einsum("np,ptd->ntd",X,beta)).reshape(n,-1)
    projector=np.linalg.inv(X.T@X)@X.T
    weights=projector[1]
    f2=residual*(weights/np.sqrt(1-hat))[:,None]
    f3=residual*(weights/(1-hat))[:,None]
    np.testing.assert_allclose(
        candidates["weighted_slope_HC2_Gaussian"]["se"].reshape(-1),
        np.sqrt(np.sum(f2**2,axis=0)),atol=1e-13)
    np.testing.assert_allclose(
        candidates["weighted_slope_HC3_Gaussian"]["se"].reshape(-1),
        np.sqrt(np.sum(f3**2,axis=0)),atol=1e-13)
    assert np.all(candidates["weighted_slope_HC3_Gaussian"]["se"]>=
                  candidates["weighted_slope_HC2_Gaussian"]["se"])
    pool=r72.hc2_gaussian_covariance_maxima(X,Y,beta,seed=912)
    np.testing.assert_array_equal(
        candidates["pooled_HC2_Gaussian"]["maxima"],pool["maxima"])
    assert all(len(candidates[m]["maxima"])==999 for m in r74.ESTIMATED)
    assert all(candidates[m]["critical"]==np.quantile(
        candidates[m]["maxima"],.9,method="higher") for m in r74.ESTIMATED)


@pytest.mark.parametrize("config",("curve_small","participant_small"))
def test_real_unmodified_package_W3_wild_and_new_gaussian_maxima(config):
    row=r74.evaluate(0,config,"extreme","predictor_heteroskedastic")
    assert row["completed"],row["exception"]
    assert row["refused"] is False
    assert row["package_OLS_HC1_max_error"]<=r74.TOL
    assert row["package_wild_999_max_critical_error"]<=r74.TOL
    assert len(row["original_X"])==r74.config_info(config)[0]
    assert set(row["method_999_raw_maxima"])==set(r74.METHODS)-{
        "known_heteroskedastic_Gaussian"}
    for m in r74.METHODS:
        assert type(row["method_truth_included"][m]) is bool
        assert row["method_truth_included"][m]==(
            row["method_truth_pivots"][m]<=row["method_criticals"][m])
        assert np.asarray(row["method_SE_grids"][m]).shape==(31,2)
    assert not row["release_authorized"]
    assert row["no_calibrated_90pct_simultaneous_method"]


def test_failure_inclusive_32_independent_block_denominator_and_no_release():
    rows=_grid()
    d=r74.summarize(rows)
    assert d["source_cases"]==512
    assert d["original_wild_multiplier_positions"]==512*999
    assert d["original_gaussian_multiplier_positions"]==512*999
    assert d["derived_gaussian_maxima_across_three_covariances"]==512*999*3
    assert d["new_independent_primitive_blocks"]==32
    assert not d["release_authorized"]
    for c in r74.CONFIGS:
        for s in r74.SUPPORT:
            for v in r74.VARIANCE:
                d1=d["per_cell"][c][s][v]
                assert d1["refused"]==32
                for m in r74.METHODS:
                    assert d1["methods"][m]["fixed_denominator_lower"]==0.
                    assert d1["methods"][m]["fixed_denominator_upper"]==1.
    rows.pop()
    with pytest.raises(ValueError,match="missing or duplicated"):
        r74.summarize(rows)
    rows=_grid()
    rows[0]["release_authorized"]=True
    with pytest.raises(ValueError,match="qualification corrupted"):
        r74.summarize(rows)


def test_exact_checkout_and_eight_shard_SHA256_contract(tmp_path,monkeypatch):
    monkeypatch.setenv("GITHUB_SHA","f"*40)
    rows=_grid()
    parts=tmp_path/"shards"
    for lo,hi in r74.SHARDS:
        folder=parts/f"blocks-{lo}"
        folder.mkdir(parents=True)
        sub=[x for x in rows if lo<=x["block"]<hi]
        raw=(json.dumps(sub,indent=2,sort_keys=True)+"\n").encode()
        (folder/"cases.json").write_bytes(raw)
        (folder/"manifest.json").write_text(json.dumps({
            "study":r74.STUDY,"start":lo,"stop":hi,
            "source_seed":r74.SOURCE_SEED,"gaussian_seed":r74.GAUSSIAN_SEED,
            "wild_seed":r74.WILD_SEED,"source_count":len(sub),
            "original_checkout":"f"*40,"sha256_cases":sha256(raw).hexdigest(),
        }))
    dest=tmp_path/"archive"
    r74.aggregate(dest,parts)
    report=json.loads((dest/"summary.json").read_text())
    assert report["source_cases"]==512
    assert len((dest/"SHA256SUMS").read_text().splitlines())==3
    source_file=parts/"blocks-0"/"cases.json"
    source_file.write_bytes(source_file.read_bytes()+b" ")
    with pytest.raises(ValueError,match="SHA256"):
        r74.aggregate(tmp_path/"bad",parts)
