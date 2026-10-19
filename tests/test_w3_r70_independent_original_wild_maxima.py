"""R70-A independent original 999-draw maxima, source and release integrity."""
from __future__ import annotations

from hashlib import sha256
import json

import pytest

from scripts import audit_w3_r70_independent_original_wild_maxima as a
from scripts import run_w3_r70_new_leverage_hc3_band_sensitivity as source


def _case(b,design,support):
    cells={}
    for name in a.CELLS:
        adj,studentization=name.split("/")
        cells[name]={
            "adjustment":adj,"studentization":studentization,
            "draw_count":999,"quantile_method":"higher",
            "slope_wild_max_draws":[2.]*999,
            "family_wild_max_draws":[3.]*999,
            "slope_critical":2.,"family_critical":3.,
            "observed_slope_truth_max_pivot":1.,
            "observed_family_truth_max_pivot":1.5,
            "slope_simultaneous_truth_included":True,
            "joint_family_truth_included":True,
            "slope_median_band_width":.35,
            "same_fitted_source_and_wild_multiplier_vectors":True,
        }
    return {
        "study":a.STUDY,"block":b,"design":design,"support":support,
        "source_seed":a.SOURCE_SEED+10007*b+a.DESIGNS.index(design),
        "draw_seed":a.DRAW_SEED+100003*b+10007*a.DESIGNS.index(design)+739*a.SUPPORT.index(support),
        "independent_units":72 if design=="curve" else 36,
        "observed_curves":72 if design=="curve" else 108,
        "completed":True,"exception":None,
        "maximum_original_HC1_coefficient_oracle_error":0.,
        "maximum_original_HC1_SE_oracle_error":0.,
        "maximum_original_wild_999_coefficient_oracle_error":0.,
        "max_hat":.05 if support=="ordinary" else .50,
        "min_hat":.01,"hc3_to_hc1_median_se_ratio":1.1,
        "pointwise_HC1_slope_cell_truth_fraction":.89,
        "cells":cells,
        "raw_999_draws_archived_for_independent_max_quantiles":True,
        "no_calibrated_90pct_band_claim":True,"release_authorized":False,
    }


def _rows():
    return [_case(b,d,s) for b in range(a.BLOCKS)
            for d in a.DESIGNS for s in a.SUPPORT]


def _refresh(folder,rows=None):
    folder.mkdir(parents=True,exist_ok=True)
    rows=_rows() if rows is None else rows
    report=source.summary(rows)
    (folder/"cases.json").write_text(json.dumps(rows,sort_keys=True)+"\n")
    (folder/"summary.json").write_text(json.dumps(report,sort_keys=True)+"\n")
    (folder/"source-commit.txt").write_text("c"*40+"\n")
    _hash(folder)
    return folder


def _hash(folder):
    (folder/"SHA256SUMS").write_text("".join(
        sha256((folder/name).read_bytes()).hexdigest()+"  "+name+"\n"
        for name in ("cases.json","summary.json","source-commit.txt")))


def test_independent_higher_quantile_and_original_999_maxima_formula():
    assert a.B==999 and a.SOURCES==128 and a.BLOCKS==32
    assert a.MAX_ATTEMPTED_MULTIPLIER_VECTORS==127872
    assert a.DERIVED_REPLICATES==511488
    assert a.SOURCE_SEED==202610197070 and a.DRAW_SEED==202610197071
    data=[float(i) for i in range(999)]
    assert a._higher_quantile(data)==899.
    assert a._wilson(0,32)[0]==0.
    with pytest.raises(ValueError,match="999"):
        a._higher_quantile(data[:-1])
    with pytest.raises(ValueError,match="999"):
        a._higher_quantile([float("nan")]+data[1:])


def test_actual_independent_source_maxima_and_source_count_fixture(tmp_path):
    folder=_refresh(tmp_path/"original")
    out=a.verify_archive(folder,"c"*40)
    assert out["original_archive_SHA256_verified"]==3
    assert out["independent_primitive_source_blocks"]==32
    assert out["original_source_cases"]==128
    assert out["original_wild_max_draw_statistics_rechecked"]==128*4*2*999
    assert out["independent_999draw_slope_and_family_criticals_recomputed"]==128*4*2
    assert out["full_source_coverage"]["curve"]["ordinary"]["unadjusted/hc1"]["included"]==32
    assert len(out["original_failure_cases"])==0
    assert out["unqualified_90pct_coverage"]
    assert not out["release_authorized"]


def test_real_family_only_truth_can_be_included_with_narrower_slope_band_excluded(tmp_path):
    rows=_rows()
    cell=rows[0]["cells"]["hc3_residual/hc3"]
    cell["observed_slope_truth_max_pivot"]=2.5
    cell["slope_simultaneous_truth_included"]=False
    cell["observed_family_truth_max_pivot"]=2.8
    cell["joint_family_truth_included"]=True
    folder=_refresh(tmp_path/"family_only",rows)
    reconstructed=a.verify_archive(folder,"c"*40)
    assert reconstructed["original_source_cases"]==128
    assert reconstructed["full_source_coverage"]["curve"]["ordinary"]["hc3_residual/hc3"]["included"]==31
    assert reconstructed["full_source_coverage"]["curve"]["ordinary"]["hc3_residual/hc3"]["family_included"]==32


def test_forged_checkout_SHA_or_missing_source_fails_closed(tmp_path):
    folder=_refresh(tmp_path/"a")
    with pytest.raises(ValueError,match="checkout"):
        a.verify_archive(folder,"d"*40)
    path=folder/"cases.json"
    path.write_bytes(path.read_bytes()+b" ")
    with pytest.raises(ValueError,match="SHA256"):
        a.verify_archive(folder,"c"*40)
    folder=_refresh(tmp_path/"b")
    rows=json.loads((folder/"cases.json").read_text())
    rows[0]["block"]=31
    (folder/"cases.json").write_text(json.dumps(rows,sort_keys=True)+"\n")
    _hash(folder)
    with pytest.raises(ValueError,match="grid"):
        a.verify_archive(folder,"c"*40)


def test_tampered_wild_critical_or_truth_decision_is_detected(tmp_path):
    folder=_refresh(tmp_path/"a")
    rows=json.loads((folder/"cases.json").read_text())
    rows[0]["cells"]["unadjusted/hc1"]["slope_critical"]+=.05
    (folder/"cases.json").write_text(json.dumps(rows,sort_keys=True)+"\n")
    _hash(folder)
    with pytest.raises(ValueError,match="slope critical"):
        a.verify_archive(folder,"c"*40)
    folder=_refresh(tmp_path/"b")
    rows=json.loads((folder/"cases.json").read_text())
    rows[0]["cells"]["unadjusted/hc1"]["slope_simultaneous_truth_included"]=False
    (folder/"cases.json").write_text(json.dumps(rows,sort_keys=True)+"\n")
    _hash(folder)
    with pytest.raises(ValueError,match="truth inclusion"):
        a.verify_archive(folder,"c"*40)


def test_false_release_claim_and_wrong_joint_family_raw_max_refused(tmp_path):
    folder=_refresh(tmp_path/"a")
    summary=json.loads((folder/"summary.json").read_text())
    summary["release_authorized"]=True
    (folder/"summary.json").write_text(json.dumps(summary,sort_keys=True)+"\n")
    _hash(folder)
    with pytest.raises(ValueError,match="mismatch"):
        a.verify_archive(folder,"c"*40)
    folder=_refresh(tmp_path/"b")
    rows=json.loads((folder/"cases.json").read_text())
    rows[0]["cells"]["unadjusted/hc1"]["family_wild_max_draws"][0]=1.
    (folder/"cases.json").write_text(json.dumps(rows,sort_keys=True)+"\n")
    _hash(folder)
    with pytest.raises(ValueError,match="family raw"):
        a.verify_archive(folder,"c"*40)
