"""R74-A source-level 512-case and 2,045,952 wild/Gaussian maximum audit gates."""
from __future__ import annotations

from hashlib import sha256
import json

import numpy as np
import pytest

from scripts import audit_w3_r74_independent_original_weighted_slope as audit
from scripts import run_w3_r74_new_weighted_slope_hc2_hc3 as source


def _refused(b,c,s,v):
    n,trials,design=audit._info(c)
    return {
        "study":audit.STUDY,"block":b,"config":c,"design":design,
        "support":s,"variance":v,
        "source_seed":audit._seed(b,c,s,v,"source"),
        "gaussian_seed":audit._seed(b,c,s,v,"gaussian"),
        "wild_seed":audit._seed(b,c,s,v,"wild"),
        "native_units":n,"trials_per_unit":trials,"observed_curves":n*trials,
        "completed":False,"refused":True,
        "exception":{"type":"SyntheticSourceRefusal","message":"preserved"},
        "method_truth_included":{m:None for m in audit.METHODS},
        "no_calibrated_90pct_simultaneous_method":True,
        "no_source_missingness_or_MNAR":True,
        "release_authorized":False,
    }


def _original(folder,accepted=None):
    folder.mkdir(parents=True,exist_ok=True)
    rows=[_refused(b,c,s,v) for b in range(audit.BLOCKS)
          for c in audit.CONFIGS for s in audit.SUPPORT for v in audit.VARIANCE]
    if accepted is not None:
        key=lambda row:(row["block"],row["config"],row["support"],row["variance"])
        for i,row in enumerate(rows):
            if key(row)==key(accepted):
                rows[i]=accepted
                break
    report=source.summarize(rows)
    (folder/"cases.json").write_text(json.dumps(rows,sort_keys=True)+"\n")
    (folder/"summary.json").write_text(json.dumps(report,sort_keys=True)+"\n")
    (folder/"source-commit.txt").write_text(audit.CHECKOUT+"\n")
    _hash(folder)
    return folder


def _hash(folder):
    names=("cases.json","summary.json","source-commit.txt")
    (folder/"SHA256SUMS").write_text("".join(
        sha256((folder/n).read_bytes()).hexdigest()+"  "+n+"\n" for n in names))


def test_original_source_frozen_domain_and_all_512_independent_block_pairs():
    assert audit.BLOCKS==32 and audit.SOURCES==512 and audit.B==999
    assert audit.CHECKOUT=="4031d3dbe5cfc5617bd939c8ea9cd00d17376bd9"
    assert len(audit.CONFIGS)==4 and len(audit.METHODS)==5
    assert audit._seed(0,"curve_small","ordinary","constant","source")==audit._seed(
        0,"curve_small","extreme","predictor_heteroskedastic","source")
    assert audit._wilson(0,32)[0]==0.
    with pytest.raises(ValueError,match="out of bounds"):
        audit._seed(32,"curve_small","ordinary","constant","source")


@pytest.mark.parametrize("config",audit.CONFIGS)
def test_gaussian_X_Y_full_source_independent_of_original_simulator(config):
    b,c,s,v=0,config,"extreme","predictor_heteroskedastic"
    original=source.simulate(b,c,s,v)
    X,Y,truth,scale=audit.reconstruct_original_gaussian(b,c,s,v)
    np.testing.assert_allclose(X,original[3],atol=0,rtol=0)
    np.testing.assert_allclose(Y,original[4],atol=5e-14,rtol=0)
    np.testing.assert_allclose(truth,original[2][1],atol=5e-14,rtol=0)
    np.testing.assert_array_equal(scale,original[5])
    assert scale[0]==scale[-1]==4


@pytest.mark.parametrize("config",("curve_small","participant_small"))
def test_real_original_source_wild_and_three_gaussian_maxima_reconstructed(config):
    row=source.evaluate(0,config,"extreme","predictor_heteroskedastic")
    assert row["completed"],row["exception"]
    verified=audit.reconstruct_source(row)
    assert verified["completed"]
    assert verified["coverage"]==row["method_truth_included"]
    assert verified["ratio2"]==pytest.approx(row["mean_weighted_HC2_to_true_SE"])
    assert verified["ratio3"]==pytest.approx(row["mean_weighted_HC3_to_true_SE"])


def test_source_truth_SE_and_raw_maxima_tampering_refused():
    row=source.evaluate(0,"curve_small","extreme","predictor_heteroskedastic")
    assert row["completed"]
    row["method_SE_grids"]["weighted_slope_HC2_Gaussian"][0][0]*=1.5
    with pytest.raises(ValueError,match="original numerical mismatch"):
        audit.reconstruct_source(row)
    row=source.evaluate(0,"curve_small","extreme","predictor_heteroskedastic")
    row["method_999_raw_maxima"]["weighted_slope_HC3_Gaussian"][0]+=.15
    with pytest.raises(ValueError,match="original numerical mismatch"):
        audit.reconstruct_source(row)
    row=source.evaluate(0,"curve_small","extreme","predictor_heteroskedastic")
    row["method_truth_included"]["known_heteroskedastic_Gaussian"]=not row[
        "method_truth_included"]["known_heteroskedastic_Gaussian"]
    with pytest.raises(ValueError,match="truth inclusion cannot be reproduced"):
        audit.reconstruct_source(row)


def test_complete_original_denominator_preserves_all_refusals_and_release_hold(tmp_path):
    folder=_original(tmp_path/"all_refused")
    report=audit.audit_original(folder)
    assert report["original_source_cases"]==512
    assert report["original_source_complete"]==0
    assert report["original_source_refused"]==512
    assert report["original_wild_maxima_replayed"]==0
    assert report["per_cell"]["curve_small"]["ordinary"]["constant"]["failed"]==32
    assert report["original_SHA256_members_verified"]==3
    assert report["no_nominal_90pct_coverage_qualified"]
    assert not report["release_authorized"]


def test_one_actual_original_case_and_immutable_SHA256_gates(tmp_path):
    row=source.evaluate(0,"curve_small","extreme","predictor_heteroskedastic")
    assert row["completed"],row["exception"]
    folder=_original(tmp_path/"original_one",accepted=row)
    report=audit.audit_original(folder)
    assert report["original_source_complete"]==1
    assert report["original_source_refused"]==511
    assert report["original_wild_maxima_replayed"]==999
    assert report["original_estimated_Gaussian_maxima_replayed"]==3*999
    assert report["original_source_truth_decisions_reproduced"]==5
    with pytest.raises(ValueError,match="checkout"):
        audit.audit_original(folder,expected_checkout="f"*40)
    (folder/"cases.json").write_bytes((folder/"cases.json").read_bytes()+b" ")
    with pytest.raises(ValueError,match="SHA256"):
        audit.audit_original(folder)


def test_duplicate_source_and_fake_90pct_public_release_claims_refused(tmp_path):
    folder=_original(tmp_path/"original")
    rows=json.loads((folder/"cases.json").read_text())
    rows[0]["block"]=31
    (folder/"cases.json").write_text(json.dumps(rows,sort_keys=True)+"\n")
    _hash(folder)
    with pytest.raises(ValueError,match="duplicate or missing"):
        audit.audit_original(folder)
    folder=_original(tmp_path/"original2")
    report=json.loads((folder/"summary.json").read_text())
    report["release_authorized"]=True
    (folder/"summary.json").write_text(json.dumps(report,sort_keys=True)+"\n")
    _hash(folder)
    with pytest.raises(ValueError,match="aggregate contract"):
        audit.audit_original(folder)
