"""R75 prospective new Gaussian source SE×correlation 2×2 numeric gates."""
from __future__ import annotations

from hashlib import sha256
import json

import numpy as np
import pytest

from scripts import run_w3_r75_new_se_correlation_factorial as r75
from scripts import run_w3_r74_new_weighted_slope_hc2_hc3 as r74
from scripts import run_w3_r71_new_known_gaussian_band_oracle as r71
from scripts.run_w3_fixed_truth_interval_pilot import independent_hc1_oracle


def _refused(b,d,s,v):
    unit="curve" if d=="curve_standard" else "participant"
    return {
        "study":r75.STUDY,"block":b,"design":d,"support":s,"variance":v,
        "source_seed":r75.random_seed(b,d,s,v,"source"),
        "gaussian_seed":r75.random_seed(b,d,s,v,"gaussian"),
        "completed":False,"refused":True,
        "exception":{"type":"FrozenFailureFixture","message":"excluded only from complete cases"},
        "not_a_qualified_90pct_data_estimated_band":True,
        "real_data_known_covariance_unavailable":True,
        "no_missingness_or_MNAR":True,"release_authorized":False,
    }


def _grid():
    return [_refused(b,d,s,v) for b in range(r75.BLOCKS)
            for d in r75.DESIGNS for s in r75.SUPPORT for v in r75.VARIANCE]


def test_frozen_r75_seed_domains_and_independent_source_block_units():
    assert r75.BLOCKS==32 and r75.N_CASES==256
    assert r75.B==999 and r75.CONF==.90
    assert r75.SOURCE_SEED==202610207575
    assert r75.GAUSSIAN_SEED==202610207576
    assert r75.SHARDS==((0,8),(8,16),(16,24),(24,32))
    assert r75.CELLS==(
        "estimated_SE_estimated_correlation","known_SE_estimated_correlation",
        "estimated_SE_known_correlation","known_SE_known_correlation")
    assert len({r75.random_seed(b,d,s,v,"gaussian")
                for b in range(32) for d in r75.DESIGNS
                for s in r75.SUPPORT for v in r75.VARIANCE})==256
    assert len({r75.random_seed(b,d,"ordinary","constant","source")
                for b in range(32) for d in r75.DESIGNS})==64
    assert r75.SOURCE_SEED not in {r74.SOURCE_SEED,r71.SOURCE_SEED}
    with pytest.raises(ValueError,match="outside"):
        r75.random_seed(32,"curve_standard","ordinary","constant","source")


@pytest.mark.parametrize("design",r75.DESIGNS)
def test_new_Gaussian_pairing_exact_and_heteroskedastic_slope_law(design):
    base=r75.simulate(0,design,"ordinary","constant")
    extreme=r75.simulate(0,design,"extreme","constant")
    hetero=r75.simulate(0,design,"extreme","predictor_heteroskedastic")
    _,_,truth,X,Y,scale=base
    _,_,true2,Z,Q,_=extreme
    _,_,true3,ZZ,QQ,scale2=hetero
    np.testing.assert_array_equal(truth,true2)
    np.testing.assert_array_equal(truth,true3)
    np.testing.assert_array_equal(X[1:-1],Z[1:-1])
    np.testing.assert_array_equal(Z,ZZ)
    assert Z[0,1]==-4. and Z[-1,1]==4.
    assert scale2[0]==scale2[-1]==4.
    a=Y-np.einsum("np,ptd->ntd",X,truth,optimize=True)
    b=Q-np.einsum("np,ptd->ntd",Z,truth,optimize=True)
    c=QQ-np.einsum("np,ptd->ntd",ZZ,truth,optimize=True)
    np.testing.assert_allclose(a,b,atol=5e-14,rtol=0)
    np.testing.assert_allclose(c,b*scale2[:,None,None],atol=6e-14,rtol=0)
    known=r75.true_slope_se(Z,scale2,"curve" if design=="curve_standard" else "participant")
    np.testing.assert_allclose(known,r74.true_slope_se(
        Z,scale2,"curve" if design=="curve_standard" else "participant"),atol=1e-13)


def test_weighted_HC3_factor_reference_algebra_independently_checked():
    _,_,_,X,Y,_=r75.simulate(
        0,"curve_standard","extreme","predictor_heteroskedastic")
    beta,_=independent_hc1_oracle(X,Y)
    result=r75.estimated_HC3_correlation(X,Y,beta,gaussian_seed=772)
    n=len(X)
    P=np.linalg.inv(X.T@X)@X.T
    hat=np.sum(X*P.T,axis=1)
    residual=(Y-np.einsum("np,ptd->ntd",X,beta,optimize=True)).reshape(n,-1)
    f=residual*(P[1]/(1-hat))[:,None]
    se=np.sqrt(np.sum(f*f,axis=0)).reshape(31,2)
    np.testing.assert_allclose(se,result["se"],atol=1e-13)
    normals=np.random.default_rng(772).standard_normal((999,n))
    expected=np.max(np.abs(normals@f)/se.reshape(-1)[None],axis=1)
    np.testing.assert_allclose(result["maxima"],expected,atol=2e-10)
    assert result["critical"]==np.quantile(expected,.90,method="higher")
    weights=np.sum(f*f,axis=1)
    np.testing.assert_allclose(result["energy_participation"],
                               weights.sum()**2/np.sum(weights**2))


@pytest.mark.parametrize("design",r75.DESIGNS)
def test_actual_crossed_four_source_inclusion_events_and_unmodified_W3_contract(design):
    row=r75.evaluate(0,design,"extreme","predictor_heteroskedastic")
    assert row["completed"],row["exception"]
    assert row["W3_original_OLS_HC1_oracle_error"]<=r75.TOL
    assert len(row["original_gaussian_999_maxima"])==999
    assert np.asarray(row["true_slope_SE_grid"]).shape==(31,2)
    assert np.asarray(row["estimated_HC3_slope_SE_grid"]).shape==(31,2)
    assert row["estimated_gaussian_critical"]==np.quantile(
        row["original_gaussian_999_maxima"],.9,method="higher")
    expected={
        "estimated_SE_estimated_correlation":
            row["truth_pivot_estimated_SE"]<=row["estimated_gaussian_critical"],
        "known_SE_estimated_correlation":
            row["truth_pivot_known_SE"]<=row["estimated_gaussian_critical"],
        "estimated_SE_known_correlation":
            row["truth_pivot_estimated_SE"]<=row["known_gaussian_critical"],
        "known_SE_known_correlation":
            row["truth_pivot_known_SE"]<=row["known_gaussian_critical"],
    }
    assert row["coverage"]==expected
    assert row["estimated_factor_energy_participation"]>0
    assert row["estimated_factor_energy_participation"]<=row["independent_units"]
    assert not row["release_authorized"]


def test_all_256_failed_sources_remain_in_fixed_32block_denominators_and_false_calibration_refused():
    rows=_grid()
    summary=r75.summarize(rows)
    assert summary["source_cases"]==256
    assert summary["original_conditional_gaussian_vectors"]==256*999
    assert summary["known_law_reference_draws_total"]==65534
    assert summary["all_90pct_inferential_calibration_claims_withheld"]
    for design in r75.DESIGNS:
        for support in r75.SUPPORT:
            for variance in r75.VARIANCE:
                rec=summary["per_cell"][design][support][variance]
                assert rec["complete"]==0 and rec["failed"]==32
                for cell in r75.CELLS:
                    assert rec["inclusions"][cell]["full_denominator_upper"]==1.
    rows.pop()
    with pytest.raises(ValueError,match="omitted/duplicated"):
        r75.summarize(rows)
    rows=_grid()
    rows[0]["release_authorized"]=True
    with pytest.raises(ValueError,match="release invariant"):
        r75.summarize(rows)


def test_original_four_source_shards_and_source_SHA256_refusal(tmp_path,monkeypatch):
    monkeypatch.setenv("GITHUB_SHA","e"*40)
    source=_grid()
    parts=tmp_path/"parts"
    for lo,hi in r75.SHARDS:
        path=parts/f"part-{lo}"
        path.mkdir(parents=True)
        sub=[r for r in source if lo<=r["block"]<hi]
        raw=(json.dumps(sub,sort_keys=True,indent=2)+"\n").encode()
        (path/"cases.json").write_bytes(raw)
        (path/"manifest.json").write_text(json.dumps({
            "study":r75.STUDY,"start":lo,"stop":hi,
            "source_seed":r75.SOURCE_SEED,"gaussian_seed":r75.GAUSSIAN_SEED,
            "original_checkout":"e"*40,"source_count":len(sub),
            "source_cases_sha256":sha256(raw).hexdigest()}))
    dest=tmp_path/"complete"
    r75.aggregate(dest,parts)
    assert len((dest/"SHA256SUMS").read_text().splitlines())==4
    assert json.loads((dest/"summary.json").read_text())["source_cases"]==256
    path=parts/"part-0"/"cases.json"
    path.write_bytes(path.read_bytes()+b"F")
    with pytest.raises(ValueError,match="SHA256"):
        r75.aggregate(tmp_path/"invalid",parts)
