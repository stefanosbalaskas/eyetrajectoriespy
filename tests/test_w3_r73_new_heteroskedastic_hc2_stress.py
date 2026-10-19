"""R73 frozen new-source heteroskedastic Gaussian and HC2 stress contracts."""
from __future__ import annotations

from hashlib import sha256
import json

import numpy as np
import pytest

from scripts import run_w3_r73_new_predictor_heteroskedastic_gaussian_bands as r73
from scripts import run_w3_r72_new_estimated_gaussian_covariance_bands as r72
from scripts import run_w3_r71_new_known_gaussian_band_oracle as r71


def _refusal(b,d,s,v):
    return {
        "study":r73.STUDY,"block":b,"design":d,"support":s,"variance":v,
        "source_seed":r73.seed_for(b,d,s,v,"source"),
        "wild_seed":r73.seed_for(b,d,s,v,"wild"),
        "estimated_seed":r73.seed_for(b,d,s,v,"estimated"),
        "completed":False,"refused":True,
        "exception":{"type":"FrozenTestRefusal","message":"preserved"},
        "not_calibrated_90pct_simultaneous_bands":True,
        "release_authorized":False,
    }


def _grid():
    return [_refusal(b,d,s,v) for b in range(r73.BLOCKS)
            for d in r73.DESIGNS for s in r73.SUPPORT for v in r73.VARIANCE]


def test_predeclared_seed_source_grid_and_no_release():
    assert r73.BLOCKS==32 and r73.SOURCE_CASES==256
    assert r73.DRAW_B==999 and r73.CONFIDENCE==.9
    assert r73.SOURCE_SEED==202610197373
    assert r73.WILD_SEED==202610197374
    assert r73.ESTIMATED_SEED==202610197375
    assert r73.VARIANCE==("constant","predictor_heteroskedastic")
    assert r73.SHARDS==((0,8),(8,16),(16,24),(24,32))
    assert len({r73.SOURCE_SEED,r73.WILD_SEED,r73.ESTIMATED_SEED,
                r72.SOURCE_SEED,r72.WILD_SEED,r72.GAUSSIAN_SEED,
                r71.SOURCE_SEED})==7
    seeds=[r73.seed_for(b,d,s,v,"estimated")
           for b in range(32) for d in r73.DESIGNS
           for s in r73.SUPPORT for v in r73.VARIANCE]
    assert len(set(seeds))==256
    with pytest.raises(ValueError,match="outside"):
        r73.seed_for(32,"curve","ordinary","constant","source")


@pytest.mark.parametrize("design",r73.DESIGNS)
@pytest.mark.parametrize("support",r73.SUPPORT)
def test_fresh_heteroskedastic_source_shares_primitive_innovations(design,support):
    _,_,truth,X,Y,sc=r73.simulate(0,design,support,"constant")
    _,_,true2,XX,Z,hetero=r73.simulate(
        0,design,support,"predictor_heteroskedastic")
    np.testing.assert_array_equal(truth,true2)
    np.testing.assert_array_equal(X,XX)
    np.testing.assert_array_equal(sc,np.ones(len(X)))
    np.testing.assert_array_equal(hetero,1.+.75*np.abs(X[:,1]))
    base=Y-np.einsum("np,ptd->ntd",X,truth,optimize=True)
    stressed=Z-np.einsum("np,ptd->ntd",XX,truth,optimize=True)
    np.testing.assert_allclose(
        stressed,base*hetero[:,None,None],rtol=0,atol=5e-14)
    if support=="extreme":
        assert hetero[0]==hetero[-1]==4
    old,_,_,_,_=r72.simulate(0,design,support)
    fresh,_,_,_,_,_=r73.simulate(0,design,support,"constant")
    assert not np.array_equal(old.values,fresh.values)


@pytest.mark.parametrize("design",r73.DESIGNS)
def test_heterogeneous_exact_slope_oracle_reduces_to_common_covariance_when_constant(design):
    _,_,truth,X,Y,unit=r73.simulate(0,design,"extreme","constant")
    est=r73.exact_heteroskedastic_slope_se(X,unit,design)
    np.testing.assert_allclose(
        est,r71.true_slope_standard_errors(X,design),atol=2e-13,rtol=0)
    _,_,_,XX,YY,hetero=r73.simulate(
        0,design,"extreme","predictor_heteroskedastic")
    assert np.array_equal(X,XX)
    known=r73.exact_heteroskedastic_slope_se(XX,hetero,design)
    weights=(np.linalg.inv(X.T@X)@X.T)[1]
    scalar=np.sum((weights*hetero)**2)
    np.testing.assert_allclose(known, np.sqrt(scalar*r71.unit_covariance_variance(design)))
    assert np.all(known>est)
    with pytest.raises(ValueError,match="design mismatch"):
        r73.exact_heteroskedastic_slope_se(X,np.ones(len(X)-1),design)


def test_actual_new_source_unmodified_original_W3_and_HC2_oracles():
    x=r73.evaluate(0,"curve","extreme","predictor_heteroskedastic")
    assert x["completed"],x["exception"]
    assert x["refused"] is False
    assert x["package_OLS_HC1_oracle_error"]<=r73.TOL
    assert x["package_wild_critical_oracle_error"]<=r73.TOL
    assert len(x["original_wild_999_maxima"])==999
    assert len(x["estimated_HC2_999_maxima"])==999
    assert len(x["full_X"])==72
    assert len(x["full_Y_native_unit_mean"])==72
    assert np.asarray(x["full_Y_native_unit_mean"]).shape==(72,31,2)
    assert x["unit_scale_max"]==4.
    for m in r73.METHODS:
        assert type(x["coverage"][m]) is bool
        assert x["coverage"][m]==(x["pivots"][m]<=x["criticals"][m])
    assert x["criticals"]["original_wild_HC1"]==np.quantile(
        x["original_wild_999_maxima"],.90,method="higher")
    assert x["criticals"]["estimated_HC2_Gaussian"]==np.quantile(
        x["estimated_HC2_999_maxima"],.90,method="higher")
    assert not x["release_authorized"]
    assert x["not_calibrated_90pct_simultaneous_bands"]


def test_full_32_independent_denominators_preserve_all_source_refusals():
    rows=_grid()
    result=r73.summarize(rows)
    assert result["source_cases"]==256
    assert result["new_primitive_independent_generating_blocks"]==32
    assert result["original_source_wild_multiplier_draw_positions"]==256*999
    assert result["source_estimated_Gaussian_draw_positions"]==256*999
    assert result["release_authorized"] is False
    for design in r73.DESIGNS:
        for support in r73.SUPPORT:
            for variance in r73.VARIANCE:
                data=result["per_cell"][design][support][variance]
                assert data["attempted"]==32 and data["failed"]==32
                for m in r73.METHODS:
                    rec=data["methods"][m]
                    assert rec["full_denominator_lower"]==0.
                    assert rec["full_denominator_upper"]==1.
    rows.pop()
    with pytest.raises(ValueError,match="missing/duplicate"):
        r73.summarize(rows)
    rows=_grid()
    rows[0]["release_authorized"]=True
    with pytest.raises(ValueError,match="release flag"):
        r73.summarize(rows)


def test_four_immutable_source_shards_reconstruct_exact_256_case_grid(tmp_path,monkeypatch):
    monkeypatch.setenv("GITHUB_SHA","a"*40)
    parts=tmp_path/"parts"
    rows=_grid()
    for lo,hi in r73.SHARDS:
        part=parts/f"part-{lo}"
        part.mkdir(parents=True)
        cases=[x for x in rows if lo<=x["block"]<hi]
        raw=(json.dumps(cases,sort_keys=True,indent=2)+"\n").encode()
        (part/"cases.json").write_bytes(raw)
        (part/"manifest.json").write_text(json.dumps({
            "study":r73.STUDY,"start":lo,"stop":hi,
            "source_seed":r73.SOURCE_SEED,"wild_seed":r73.WILD_SEED,
            "estimated_seed":r73.ESTIMATED_SEED,
            "checkout":"a"*40,"source_cases":len(cases),
            "cases_sha256":sha256(raw).hexdigest()}))
    target=tmp_path/"complete"
    r73.aggregate(target,parts)
    assert len((target/"SHA256SUMS").read_text().splitlines())==3
    assert json.loads((target/"summary.json").read_text())["source_cases"]==256
    changed=parts/"part-0"/"cases.json"
    changed.write_bytes(changed.read_bytes()+b"tamper")
    with pytest.raises(ValueError,match="SHA256"):
        r73.aggregate(tmp_path/"bad",parts)
