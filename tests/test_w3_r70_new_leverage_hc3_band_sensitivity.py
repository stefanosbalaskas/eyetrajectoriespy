"""Frozen W3 R70 new-source 2x2 wild-residual/HC3 studentization contracts."""
from __future__ import annotations

from hashlib import sha256
import json

import numpy as np
import pytest

from scripts import run_w3_r70_new_leverage_hc3_band_sensitivity as r70
from scripts.run_w3_fixed_truth_interval_pilot import independent_hc1_oracle


def _case(block,design,support,complete=True):
    n=72 if design=="curve" else 36
    cells={}
    if complete:
        for key in r70.CELLS:
            a,s=key.split("/")
            # all 999 values persisted, allowing independent quantile audit
            cells[key]={
                "adjustment":a,"studentization":s,"draw_count":999,
                "quantile_method":"higher",
                "slope_wild_max_draws":[2.]*999,
                "family_wild_max_draws":[2.5]*999,
                "slope_critical":2.,"family_critical":2.5,
                "observed_slope_truth_max_pivot":1.,
                "observed_family_truth_max_pivot":1.,
                "slope_simultaneous_truth_included":True,
                "joint_family_truth_included":True,
                "slope_median_band_width":.3,
                "same_fitted_source_and_wild_multiplier_vectors":True,
            }
    return {
        "study":r70.STUDY,"block":block,"design":design,"support":support,
        "source_seed":r70.SOURCE_SEED+10007*block+r70.DESIGNS.index(design),
        "draw_seed":r70.seed_for(block,design,support),
        "independent_units":n,"observed_curves":72 if design=="curve" else 108,
        "completed":complete,
        "exception":None if complete else {"type":"ControlledSourceRefusal","message":"kept"},
        "maximum_original_HC1_coefficient_oracle_error":0. if complete else None,
        "maximum_original_HC1_SE_oracle_error":0. if complete else None,
        "maximum_original_wild_999_coefficient_oracle_error":0. if complete else None,
        "max_hat":.05 if support=="ordinary" else .5,
        "min_hat":.001,
        "hc3_to_hc1_median_se_ratio":1.1,
        "pointwise_HC1_slope_cell_truth_fraction":.86 if complete else None,
        "cells":cells,
        "raw_999_draws_archived_for_independent_max_quantiles":True,
        "no_calibrated_90pct_band_claim":True,
        "release_authorized":False,
    }


def _all():
    return [_case(block,design,support)
            for block in range(r70.BLOCKS)
            for design in r70.DESIGNS for support in r70.SUPPORT]


def test_predeclared_NEW_primitive_source_and_wild_draw_counts():
    assert r70.BLOCKS==32 and r70.SOURCE_CASES==128
    assert r70.SOURCE_SEED==202610197070
    assert r70.DRAW_SEED==202610197071
    assert r70.B==999
    assert r70.SHARDS==tuple((i,i+4) for i in range(0,32,4))
    assert r70.CONDITIONAL_MULTIPLIER_ROWS==127872
    assert r70.DERIVED_COEFFICIENT_REPLICATES==511488
    assert set(r70.CELLS)=={
        "unadjusted/hc1","unadjusted/hc3",
        "hc3_residual/hc1","hc3_residual/hc3",
    }
    seeds=[r70.seed_for(b,d,s) for b in range(32)
           for d in r70.DESIGNS for s in r70.SUPPORT]
    assert len(seeds)==len(set(seeds))==128
    with pytest.raises(ValueError,match="outside"):
        r70.seed_for(32,"curve","ordinary")


@pytest.mark.parametrize("design",r70.DESIGNS)
def test_paired_extreme_predictors_share_original_Gaussian_response_innovations(design):
    ordinary,_,truth,XX,Y=r70.simulate(0,design,"ordinary")
    extreme,_,truth2,ZZ,Z=r70.simulate(0,design,"extreme")
    np.testing.assert_array_equal(truth,truth2)
    assert np.array_equal(XX[1:-1],ZZ[1:-1])
    assert XX[0,1]>-1. and XX[-1,1]<1.
    assert ZZ[0,1]==-4. and ZZ[-1,1]==4.
    ordinary_error=Y-np.einsum("np,ptd->ntd",XX,truth,optimize=True)
    extreme_error=Z-np.einsum("np,ptd->ntd",ZZ,truth,optimize=True)
    np.testing.assert_allclose(ordinary_error,extreme_error,rtol=0,atol=3e-14)
    a=r70.numerical_reference(XX,Y)
    b=r70.numerical_reference(ZZ,Z)
    assert b["hat"].max()>a["hat"].max()+.05
    assert (a["hat"]>0).all() and (b["hat"]<1).all()
    assert ordinary.n_curves==extreme.n_curves==(72 if design=="curve" else 108)
    with pytest.raises(ValueError,match="outside"):
        r70.simulate(32,design,"ordinary")


def test_independent_HC1_oracle_exact_and_HC3_adjustment_algebra():
    _,_,truth,X,Y=r70.simulate(0,"participant","extreme")
    ref=r70.numerical_reference(X,Y)
    beta,se=independent_hc1_oracle(X,Y)
    np.testing.assert_allclose(ref["beta"],beta,atol=2e-10,rtol=0)
    np.testing.assert_allclose(ref["se"]["hc1"],se,atol=2e-10,rtol=0)
    np.testing.assert_allclose(ref["adjusted_residual"],
                               ref["residual"]/(1-ref["hat"])[:,None,None])
    assert np.isfinite(ref["se"]["hc3"]).all()
    assert np.isfinite(ref["se"]["hc1"]).all()


def test_original_W3_999_wild_multiplier_and_critical_contracts_actually_pass():
    row=r70.evaluate(0,"curve","ordinary")
    assert row["completed"],row["exception"]
    assert row["maximum_original_HC1_coefficient_oracle_error"]<=r70.ORACLE_TOL
    assert row["maximum_original_HC1_SE_oracle_error"]<=r70.ORACLE_TOL
    assert row["maximum_original_wild_999_coefficient_oracle_error"]<=r70.ORACLE_TOL
    assert len(row["cells"])==4
    assert not row["no_calibrated_90pct_band_claim"] is False
    assert row["release_authorized"] is False
    for k,c in row["cells"].items():
        assert len(c["slope_wild_max_draws"])==999
        assert len(c["family_wild_max_draws"])==999
        assert c["slope_critical"]==np.quantile(
            c["slope_wild_max_draws"],.90,method="higher")
        assert c["family_critical"]==np.quantile(
            c["family_wild_max_draws"],.90,method="higher")
        assert c["slope_simultaneous_truth_included"]==(
            c["observed_slope_truth_max_pivot"]<=c["slope_critical"])


def test_failure_inclusive_32block_128case_grid_and_no_release(tmp_path):
    rows=_all()
    report=r70.summary(rows)
    assert report["independent_primitive_generating_blocks"]==32
    assert report["paired_dataset_cases"]==128
    assert report["conditional_rademacher_multiplier_vectors"]==127872
    assert report["derived_crossed_bootstrap_coefficient_replicates"]==511488
    assert report["results"]["curve"]["ordinary"]["completed"]==32
    assert report["results"]["participant"]["extreme"]["cells"][
        "hc3_residual/hc3"]["successful_source_inclusions"]==32
    assert report["matched_diagnostics"]["participant/extreme/HC3_full_minus_HC1_original"][
        "same_status"]==32
    assert report["no_calibrated_90pct_pointwise_or_simultaneous_claim"]
    assert report["release_authorized"] is False
    row=next(x for x in rows if x["block"]==7 and x["design"]=="participant"
             and x["support"]=="extreme")
    row.update(_case(7,"participant","extreme",complete=False))
    failed=r70.summary(rows)
    assert failed["results"]["participant"]["extreme"]["refused"]==1
    assert failed["results"]["participant"]["extreme"]["cells"][
        "unadjusted/hc1"]["source_cases_failed"]==1
    assert failed["matched_diagnostics"]["participant/extreme/HC3_full_minus_HC1_original"][
        "source_refusals"]==1


def test_duplicate_case_missing_maximum_array_or_calibration_claim_refused():
    rows=_all()
    rows[0]["block"]=31
    with pytest.raises(ValueError,match="grid"):
        r70.summary(rows)
    rows=_all()
    rows[0]["cells"]["unadjusted/hc1"]["slope_wild_max_draws"].pop()
    with pytest.raises(ValueError,match="wild draw maxima"):
        r70.summary(rows)
    rows=_all()
    rows[0]["no_calibrated_90pct_band_claim"]=False
    with pytest.raises(ValueError,match="provenance"):
        r70.summary(rows)


def test_all_eight_source_shards_sha256_original_checkout_integrity(tmp_path,monkeypatch):
    monkeypatch.setenv("GITHUB_SHA","d"*40)
    parts=tmp_path/"original_parts"
    for lo,hi in r70.SHARDS:
        folder=parts/f"blocks-{lo}"
        folder.mkdir(parents=True)
        rows=[_case(block,design,support)
              for block in range(lo,hi)
              for design in r70.DESIGNS for support in r70.SUPPORT]
        raw=(json.dumps(rows,sort_keys=True,indent=2)+"\n").encode()
        (folder/"cases.json").write_bytes(raw)
        (folder/"manifest.json").write_text(json.dumps({
            "study":r70.STUDY,"source_seed":r70.SOURCE_SEED,
            "draw_seed":r70.DRAW_SEED,
            "start":lo,"stop":hi,"number_cases":len(rows),
            "source_checkout":"d"*40,
            "cases_sha256":sha256(raw).hexdigest(),
        }))
    dest=tmp_path/"original_aggregate"
    r70.aggregate(dest,parts)
    report=json.loads((dest/"summary.json").read_text())
    assert report["paired_dataset_cases"]==128
    assert len((dest/"SHA256SUMS").read_text().splitlines())==3
    path=parts/"blocks-0"/"cases.json"
    path.write_bytes(path.read_bytes()+b"!")
    with pytest.raises(ValueError,match="SHA256"):
        r70.aggregate(tmp_path/"invalid",parts)
