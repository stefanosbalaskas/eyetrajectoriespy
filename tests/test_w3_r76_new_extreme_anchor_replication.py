"""R76 pre-outcome source/provenance, anchor, covariance and package contracts."""
from __future__ import annotations

from hashlib import sha256
import json

import numpy as np
import pytest

from scripts import run_w3_r76_new_extreme_anchor_replication as r76
from scripts import run_w3_r71_new_known_gaussian_band_oracle as r71
from scripts.run_w3_fixed_truth_interval_pilot import independent_hc1_oracle


def refused(b,c,s,v):
    n,trials,design=r76.config_info(c)
    return {
        "study":r76.STUDY,"block":b,"config":c,"design":design,
        "support":s,"variance":v,
        "source_seed":r76.seed(b,c,s,v,"source"),
        "gaussian_seed":r76.seed(b,c,s,v,"gaussian"),
        "wild_seed":r76.seed(b,c,s,v,"wild"),
        "native_units":n,"observed_curves":n*trials,
        "number_of_extreme_anchor_units":r76.ANCHORS[s],
        "completed":False,"refused":True,
        "exception":{"type":"PreservedSourceRefusal","message":"unaccepted"},
        "not_90pct_calibrated":True,"release_authorized":False,
        "no_MNAR_missingness":True,
    }


def grid():
    return [refused(b,c,s,v) for b in range(r76.BLOCKS)
            for c in r76.CONFIGS for s in r76.SUPPORT for v in r76.VARIANCES]


def test_frozen_design_and_rejected_source_identity():
    assert (r76.SOURCE_SEED,r76.GAUSSIAN_SEED,r76.WILD_SEED)==(
        202610207676,202610207677,202610207678)
    assert r76.BLOCKS==32 and r76.B==999 and r76.SOURCE_CASES==512
    assert r76.ANCHORS=={
        "two_anchors":2,"four_anchors":4,"eight_anchors":8,"sixteen_anchors":16}
    assert r76.SHARDS==tuple((i,i+4) for i in range(0,32,4))
    assert len({r76.seed(b,c,s,v,"gaussian") for b in range(32)
                for c in r76.CONFIGS for s in r76.SUPPORT
                for v in r76.VARIANCES})==512
    for design in r76.CONFIGS:
        assert r76.config_info(design)[0] in (36,72)
    with pytest.raises(ValueError,match="frozen NEW"):
        r76.seed(32,"curve_standard","two_anchors","constant","source")
    with pytest.raises(ValueError,match="frozen NEW"):
        r76.seed(0,"curve_standard","unknown","constant","source")


@pytest.mark.parametrize("config",r76.CONFIGS)
def test_original_innovations_paired_across_anchor_numbers_and_variance(config):
    previous=None
    for s in r76.SUPPORT:
        _,_,truth,X,Y,one=r76.simulate(0,config,s,"constant")
        _,_,other_truth,XX,YY,unequal=r76.simulate(
            0,config,s,"predictor_heteroskedastic")
        n=len(X)
        m=r76.ANCHORS[s]
        assert np.count_nonzero(np.abs(X[:,1])==4)==m
        np.testing.assert_array_equal(X,XX)
        np.testing.assert_array_equal(truth,other_truth)
        assert np.all(X[:m//2,1]==-4.)
        assert np.all(X[-m//2:,1]==4.)
        assert np.max(np.abs(X[m//2:n-m//2,1]))<.95
        np.testing.assert_array_equal(one,np.ones(n))
        np.testing.assert_array_equal(unequal,1+.75*np.abs(X[:,1]))
        residue=Y-np.einsum("np,ptd->ntd",X,truth)
        hetero=YY-np.einsum("np,ptd->ntd",XX,other_truth)
        np.testing.assert_allclose(hetero,residue*unequal[:,None,None],
                                   atol=5e-14,rtol=0)
        if previous is not None:
            np.testing.assert_allclose(previous,residue,atol=5e-14,rtol=0)
        previous=residue


@pytest.mark.parametrize("config",r76.CONFIGS)
@pytest.mark.parametrize("support",("two_anchors","sixteen_anchors"))
def test_weighted_HC3_exact_oracle_and_analytic_slope_information(config,support):
    _,_,truth,X,Y,sigma=r76.simulate(1,config,support,
                                     "predictor_heteroskedastic")
    beta,hc1=independent_hc1_oracle(X,Y)
    factor,se,hat=r76.estimated_HC3_slope_factor(X,Y,beta)
    a=(np.linalg.inv(X.T@X)@X.T)[1]
    residual=Y-np.einsum("np,ptd->ntd",X,beta)
    expected=((a/(1-hat))[:,None,None]*residual).reshape(len(X),-1)
    np.testing.assert_allclose(factor,expected,atol=1e-13,rtol=0)
    np.testing.assert_allclose(se.reshape(-1),
                               np.sqrt(np.sum(expected**2,axis=0)),
                               atol=1e-13,rtol=0)
    assert (hat>0).all() and (hat<1).all()
    _,_,design=r76.config_info(config)
    true=r76.exact_heterogeneous_slope_se(X,sigma,design)
    np.testing.assert_allclose(
        true,np.sqrt(np.sum((a*sigma)**2)*r71.unit_covariance_variance(design)),
        atol=1e-14,rtol=0)
    weight=(a*sigma)**2
    weight=weight/np.sum(weight)
    assert 1<=1/np.sum(weight**2)<=len(X)
    assert 0<weight[np.abs(X[:,1])==4].sum()<1
    assert np.isfinite(hc1).all()


@pytest.mark.parametrize("config",r76.CONFIGS)
def test_actual_W3_and_crossed_reference_one_new_source(config):
    case=r76.evaluate(0,config,"two_anchors","predictor_heteroskedastic")
    assert case["completed"],case["exception"]
    assert not case["refused"]
    assert case["number_of_extreme_anchor_units"]==2
    assert case["OLS_HC1_package_oracle_error"]<=r76.TOL
    assert case["W3_wild_package_critical_error"]<=r76.TOL
    assert 0<case["effective_slope_variance_units"]<=case["native_units"]
    assert 0<case["anchor_slope_variance_share"]<1
    assert case["HC3_SE_to_true_SE_min"]<=case["HC3_SE_to_true_SE_p10"]
    for name in r76.MAX_ARRAYS:
        samples=case["raw_reference_maxima"][name]
        assert len(samples)==999 and np.isfinite(samples).all()
        assert case["reference_criticals"][name]==np.quantile(
            samples,.90,method="higher")
    for name in r76.CELLS:
        assert case["cell_truth_included"][name]==(
            case["cell_observed_pivots"][name]<=
            case["reference_criticals"][name.split("/")[1]])
    assert case["release_authorized"] is False


def test_all_512_cases_failure_inclusive_and_no_release():
    rows=grid()
    report=r76.summarize(rows)
    assert report["source_cases"]==512 and report[
        "new_independent_primitive_blocks"]==32
    assert report["original_wild_999_multiplier_positions"]==512*999
    assert report["known_Gaussian_maxima"]==512*999
    assert report["HC3_Gaussian_maxima"]==512*999
    assert report["no_90pct_simultaneous_band_calibration"]
    assert report["release_authorized"] is False
    assert report["anchor_counts"]==[2,4,8,16]
    for c in r76.CONFIGS:
        for s in r76.SUPPORT:
            for v in r76.VARIANCES:
                rec=report["results"][c][s][v]
                assert rec["refused"]==32 and rec["complete"]==0
    rows.pop()
    with pytest.raises(ValueError,match="incomplete or duplicated"):
        r76.summarize(rows)
    rows=grid()
    rows[0]["number_of_extreme_anchor_units"]=7
    with pytest.raises(ValueError,match="provenance"):
        r76.summarize(rows)
    rows=grid()
    rows[0]["release_authorized"]=True
    with pytest.raises(ValueError,match="withheld calibration"):
        r76.summarize(rows)


def test_eight_SHA256_shards_require_pinned_original_checkout(tmp_path,monkeypatch):
    monkeypatch.setenv("GITHUB_SHA","d"*40)
    pieces=tmp_path/"parts"
    cases=grid()
    for lo,hi in r76.SHARDS:
        part=pieces/f"shard-{lo}"
        part.mkdir(parents=True)
        rows=[x for x in cases if lo<=x["block"]<hi]
        raw=(json.dumps(rows,indent=2,sort_keys=True)+"\n").encode()
        (part/"cases.json").write_bytes(raw)
        (part/"manifest.json").write_text(json.dumps({
            "study":r76.STUDY,"start":lo,"stop":hi,
            "source_seed":r76.SOURCE_SEED,"gaussian_seed":r76.GAUSSIAN_SEED,
            "wild_seed":r76.WILD_SEED,"number_cases":len(rows),
            "source_checkout":"d"*40,"cases_sha256":sha256(raw).hexdigest(),
        }))
    out=tmp_path/"result"
    r76.aggregate(out,pieces)
    summary=json.loads((out/"summary.json").read_text())
    assert summary["source_cases"]==512
    assert len((out/"SHA256SUMS").read_text().splitlines())==3
    bad=pieces/"shard-0"/"cases.json"
    bad.write_bytes(bad.read_bytes()+b" ")
    with pytest.raises(ValueError,match="SHA256"):
        r76.aggregate(tmp_path/"reject",pieces)
