"""R75 prospectively frozen new-source SE×correlation decomposition contracts."""
from __future__ import annotations

from hashlib import sha256
import json

import numpy as np
import pytest

from scripts import run_w3_r75_new_true_SE_vs_HC3_correlation as r75
from scripts import run_w3_r71_new_known_gaussian_band_oracle as r71
from scripts.run_w3_fixed_truth_interval_pilot import independent_hc1_oracle


def _refused(b,c,s,v):
    n,trials,design=r75.config_info(c)
    return {
        "study":r75.STUDY,"block":b,"config":c,"design":design,
        "support":s,"variance":v,
        "source_seed":r75.seed(b,c,s,v,"source"),
        "gaussian_seed":r75.seed(b,c,s,v,"gaussian"),
        "wild_seed":r75.seed(b,c,s,v,"wild"),
        "native_units":n,"observed_curves":n*trials,
        "completed":False,"refused":True,
        "exception":{"type":"PreservedSourceRefusal","message":"not numerically accepted"},
        "not_90pct_calibrated":True,"release_authorized":False,
        "no_MNAR_missingness":True,
    }


def _grid():
    return [_refused(b,c,s,v) for b in range(r75.BLOCKS)
            for c in r75.CONFIGS for s in r75.SUPPORT
            for v in r75.VARIANCES]


def test_seeds_frozen_source_count_and_refuse_unregistered_source():
    assert r75.SOURCE_SEED==202610207575
    assert r75.GAUSSIAN_SEED==202610207576
    assert r75.WILD_SEED==202610207577
    assert r75.SOURCE_CASES==256 and r75.BLOCKS==32 and r75.B==999
    assert r75.SHARDS==((0,8),(8,16),(16,24),(24,32))
    assert r75.CELLS==(
        "true_SE/true_corr","HC3_SE/true_corr",
        "true_SE/HC3_corr","HC3_SE/HC3_corr")
    assert r75.config_info("curve_standard")==(72,1,"curve")
    assert r75.config_info("participant_standard")==(36,3,"participant")
    assert len({r75.seed(b,c,s,v,"gaussian") for b in range(32)
                for c in r75.CONFIGS for s in r75.SUPPORT
                for v in r75.VARIANCES})==256
    with pytest.raises(ValueError,match="frozen NEW"):
        r75.seed(32,"curve_standard","ordinary","constant","source")


@pytest.mark.parametrize("config",r75.CONFIGS)
def test_primitive_Gaussian_innovations_exactly_paired_across_leverage_and_scale(config):
    _,_,truth,X,Y,a=r75.simulate(0,config,"ordinary","constant")
    _,_,truth2,XX,Z,b=r75.simulate(0,config,"extreme","constant")
    _,_,truth3,XXX,ZZ,c=r75.simulate(0,config,"extreme","predictor_heteroskedastic")
    np.testing.assert_array_equal(truth,truth2)
    np.testing.assert_array_equal(truth,truth3)
    np.testing.assert_array_equal(X[1:-1],XX[1:-1])
    np.testing.assert_array_equal(XX,XXX)
    assert XX[0,1]==-4 and XX[-1,1]==4
    np.testing.assert_array_equal(a,np.ones(len(a)))
    np.testing.assert_array_equal(c,1+.75*np.abs(XXX[:,1]))
    assert c[0]==c[-1]==4
    residual=Y-np.einsum("np,ptd->ntd",X,truth)
    extreme=Z-np.einsum("np,ptd->ntd",XX,truth)
    hetero=ZZ-np.einsum("np,ptd->ntd",XXX,truth)
    np.testing.assert_allclose(residual,extreme,atol=4e-14,rtol=0)
    np.testing.assert_allclose(hetero,extreme*c[:,None,None],atol=5e-14,rtol=0)


@pytest.mark.parametrize("config",r75.CONFIGS)
def test_HC3_slope_factor_and_Gaussian_reference_algebra(config):
    _,_,_,X,Y,scale=r75.simulate(0,config,"extreme","predictor_heteroskedastic")
    beta,_=independent_hc1_oracle(X,Y)
    factor,se,hat=r75.estimated_HC3_slope_factor(X,Y,beta)
    projector=np.linalg.inv(X.T@X)@X.T
    a=projector[1]
    residual=Y-np.einsum("np,ptd->ntd",X,beta)
    expected=((a/(1-hat))[:,None,None]*residual).reshape(len(X),-1)
    np.testing.assert_allclose(factor,expected,atol=1e-13,rtol=0)
    np.testing.assert_allclose(se.reshape(-1),np.sqrt(np.sum(expected**2,axis=0)),
                               atol=1e-13,rtol=0)
    n,trials,design=r75.config_info(config)
    true_se=r75.exact_heterogeneous_slope_se(X,scale,design)
    np.testing.assert_allclose(
        true_se,
        np.sqrt(np.sum((a*scale)**2)*r71.unit_covariance_variance(design)),
        atol=1e-14,rtol=0,
    )
    rng=np.random.default_rng(825)
    true=r75.true_correlation_maxima(design,rng)
    hc3=r75.estimated_correlation_maxima(factor,se,rng)
    assert len(true)==len(hc3)==999
    assert np.isfinite(true).all() and np.isfinite(hc3).all()
    assert 1.<np.quantile(true,.90,method="higher")<5.


@pytest.mark.parametrize("config",r75.CONFIGS)
def test_actual_original_W3_and_full_four_crossed_reference_cells(config):
    source=r75.evaluate(0,config,"extreme","predictor_heteroskedastic")
    assert source["completed"],source["exception"]
    assert source["refused"] is False
    assert source["OLS_HC1_package_oracle_error"]<=r75.TOL
    assert source["W3_wild_package_critical_error"]<=r75.TOL
    assert set(source["raw_reference_maxima"])==set(r75.MAX_ARRAYS)
    for name in r75.MAX_ARRAYS:
        assert len(source["raw_reference_maxima"][name])==999
        assert source["reference_criticals"][name]==np.quantile(
            source["raw_reference_maxima"][name],.90,method="higher")
    assert set(source["cell_truth_included"])==set(r75.CELLS)
    assert source["cell_observed_pivots"]["true_SE/true_corr"]==source[
        "cell_observed_pivots"]["true_SE/HC3_corr"]
    assert source["cell_observed_pivots"]["HC3_SE/true_corr"]==source[
        "cell_observed_pivots"]["HC3_SE/HC3_corr"]
    for name in r75.CELLS:
        c=name.split("/")[1]
        assert source["cell_truth_included"][name]==(
            source["cell_observed_pivots"][name]<=source["reference_criticals"][c])
    assert not source["release_authorized"]
    assert source["no_MNAR_missingness"]


def test_complete_256_source_grid_keeps_refusals_and_no_calibration_claim():
    rows=_grid()
    summary=r75.summarize(rows)
    assert summary["source_cases"]==256
    assert summary["new_independent_primitive_blocks"]==32
    assert summary["original_wild_999_multiplier_positions"]==256*999
    assert summary["known_Gaussian_maxima"]==256*999
    assert summary["HC3_Gaussian_maxima"]==256*999
    assert summary["reference_draws_not_independent_source_replications"]
    assert not summary["release_authorized"]
    for c in r75.CONFIGS:
        for s in r75.SUPPORT:
            for v in r75.VARIANCES:
                rec=summary["results"][c][s][v]
                assert rec["refused"]==32
                assert rec["coverage"]["true_SE/true_corr"]["failure_inclusive_upper"]==1.
    rows.pop()
    with pytest.raises(ValueError,match="incomplete or duplicated"):
        r75.summarize(rows)
    rows=_grid()
    rows[0]["release_authorized"]=True
    with pytest.raises(ValueError,match="withheld calibration"):
        r75.summarize(rows)


def test_all_four_sha256_shards_preserve_original_checkout(tmp_path,monkeypatch):
    monkeypatch.setenv("GITHUB_SHA","b"*40)
    pieces=tmp_path/"parts"
    cases=_grid()
    for lo,hi in r75.SHARDS:
        part=pieces/f"shard-{lo}"
        part.mkdir(parents=True)
        rows=[x for x in cases if lo<=x["block"]<hi]
        raw=(json.dumps(rows,indent=2,sort_keys=True)+"\n").encode()
        (part/"cases.json").write_bytes(raw)
        (part/"manifest.json").write_text(json.dumps({
            "study":r75.STUDY,"start":lo,"stop":hi,
            "source_seed":r75.SOURCE_SEED,"gaussian_seed":r75.GAUSSIAN_SEED,
            "wild_seed":r75.WILD_SEED,"number_cases":len(rows),
            "source_checkout":"b"*40,
            "cases_sha256":sha256(raw).hexdigest(),
        }))
    target=tmp_path/"out"
    r75.aggregate(target,pieces)
    report=json.loads((target/"summary.json").read_text())
    assert report["source_cases"]==256
    assert len((target/"SHA256SUMS").read_text().splitlines())==3
    tamper=pieces/"shard-0"/"cases.json"
    tamper.write_bytes(tamper.read_bytes()+b" ")
    with pytest.raises(ValueError,match="SHA256"):
        r75.aggregate(tmp_path/"reject",pieces)
