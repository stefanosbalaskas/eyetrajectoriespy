"""R73-A independent full-original source Gaussian replay numerical/refusal tests."""
from __future__ import annotations

from hashlib import sha256
import json

import numpy as np
import pytest

from scripts import audit_w3_r73_independent_original_heteroskedastic as a
from scripts import run_w3_r73_new_predictor_heteroskedastic_gaussian_bands as source


def _refused(b,d,s,v):
    return {
        "study":a.STUDY,"block":b,"design":d,"support":s,"variance":v,
        "source_seed":a._seed(b,d,s,v,"source"),
        "wild_seed":a._seed(b,d,s,v,"wild"),
        "estimated_seed":a._seed(b,d,s,v,"estimated"),
        "source_units":72 if d=="curve" else 36,
        "observed_curves":72 if d=="curve" else 108,
        "completed":False,"refused":True,
        "exception":{"type":"PreservedSyntheticRefusal","message":"not completed"},
        "coverage":{m:None for m in a.METHODS},
        "not_calibrated_90pct_simultaneous_bands":True,
        "release_authorized":False,
    }


def _fixture(folder,*,real_case=None):
    folder.mkdir(parents=True,exist_ok=True)
    data=[_refused(b,d,s,v) for b in range(a.BLOCKS)
          for d in a.DESIGNS for s in a.SUPPORT for v in a.VARIANCE]
    if real_case is not None:
        for index,x in enumerate(data):
            if (x["block"],x["design"],x["support"],x["variance"])==(
                real_case["block"],real_case["design"],real_case["support"],
                real_case["variance"]):
                data[index]=real_case
                break
    report=source.summarize(data)
    (folder/"cases.json").write_text(json.dumps(data,sort_keys=True)+"\n")
    (folder/"summary.json").write_text(json.dumps(report,sort_keys=True)+"\n")
    (folder/"source-commit.txt").write_text(a.CHECKOUT+"\n")
    _hash(folder)
    return folder


def _hash(folder):
    names=("cases.json","summary.json","source-commit.txt")
    (folder/"SHA256SUMS").write_text("".join(
        sha256((folder/n).read_bytes()).hexdigest()+"  "+n+"\n"
        for n in names))


def test_frozen_new_seeds_full_design_and_exact_heterogeneous_covariance():
    assert a.TOTAL==256 and a.BLOCKS==32 and a.B==999
    assert a.CHECKOUT=="9d09b04ba49d6be34d16339c92eef457f71fcf31"
    assert a.METHODS==(
        "original_wild_HC1","estimated_HC2_Gaussian","known_heteroskedastic_Gaussian")
    assert a._seed(0,"curve","ordinary","constant","source")==a._seed(
        0,"curve","extreme","predictor_heteroskedastic","source")
    assert a._wilson(0,32)[0]==0.


@pytest.mark.parametrize("design",a.DESIGNS)
@pytest.mark.parametrize("support",a.SUPPORT)
def test_real_source_original_X_Y_wild_and_HC2_arrays_independently_replayed(design,support):
    original=source.evaluate(0,design,support,"predictor_heteroskedastic")
    assert original["completed"],original["exception"]
    independent=a.source_case(original)
    assert independent["completed"]
    assert independent["coverage"]==original["coverage"]
    assert np.isfinite(independent["ratio2"])
    assert original["unit_scale_max"]==(4. if support=="extreme" else
                                        original["unit_scale_max"])


def test_original_seed_and_tampered_X_Y_unit_scaling_refused():
    orig=source.evaluate(0,"curve","extreme","predictor_heteroskedastic")
    assert orig["completed"],orig["exception"]
    orig["source_seed"]+=1
    with pytest.raises(ValueError,match="source or withheld"):
        a.source_case(orig)
    orig=source.evaluate(0,"curve","extreme","predictor_heteroskedastic")
    orig["unit_scales"][0]=1.
    with pytest.raises(ValueError,match="independently reconstructed source differs"):
        a.source_case(orig)
    orig=source.evaluate(0,"curve","extreme","predictor_heteroskedastic")
    orig["full_Y_native_unit_mean"][0][0][0]+=.01
    with pytest.raises(ValueError,match="independently reconstructed source differs"):
        a.source_case(orig)


def test_tampered_HC2_maxima_or_truth_inclusion_cannot_be_accepted():
    orig=source.evaluate(0,"curve","extreme","predictor_heteroskedastic")
    assert orig["completed"]
    orig["estimated_HC2_999_maxima"][0]+=.3
    with pytest.raises(ValueError,match="independently reconstructed source differs"):
        a.source_case(orig)
    orig=source.evaluate(0,"curve","extreme","predictor_heteroskedastic")
    orig["coverage"]["known_heteroskedastic_Gaussian"]=not orig["coverage"][
        "known_heteroskedastic_Gaussian"]
    with pytest.raises(ValueError,match="inclusion falsified"):
        a.source_case(orig)


def test_all_256_missing_source_cases_are_preserved_and_not_fabricated(tmp_path):
    folder=_fixture(tmp_path/"all_refused")
    evidence=a.audit(folder)
    assert evidence["original_source_cases"]==256
    assert evidence["full_original_wild_maxima_independently_reconstructed"]==0
    assert evidence["results"]["curve"]["ordinary"]["constant"]["source_failures"]==32
    assert not evidence["release_authorized"]
    assert evidence["calibrated_90pct_full_grid_claim"] is False
    assert evidence["archive_SHA256_members"]==3
    assert not evidence["estimated_HC2_not_promoted_to_public_inference"] is False


def test_original_single_real_source_archive_and_SHA256_checks(tmp_path):
    real=source.evaluate(0,"curve","extreme","predictor_heteroskedastic")
    assert real["completed"]
    p=_fixture(tmp_path/"one_real",real_case=real)
    independent=a.audit(p)
    cell=independent["results"]["curve"]["extreme"]["predictor_heteroskedastic"]
    assert cell["original_cases_complete"]==1
    assert cell["source_failures"]==31
    assert independent["full_original_wild_maxima_independently_reconstructed"]==999
    assert independent["full_original_HC2_Gaussian_maxima_independently_reconstructed"]==999
    with pytest.raises(ValueError,match="checkout"):
        a.audit(p,expected_checkout="0"*40)
    path=p/"cases.json"
    path.write_bytes(path.read_bytes()+b"\n")
    with pytest.raises(ValueError,match="SHA256"):
        a.audit(p)


def test_duplicate_case_identity_or_forged_calibration_release_rejected(tmp_path):
    p=_fixture(tmp_path/"duplicate")
    rows=json.loads((p/"cases.json").read_text())
    rows[0]["block"]=31
    (p/"cases.json").write_text(json.dumps(rows,sort_keys=True)+"\n")
    _hash(p)
    with pytest.raises(ValueError,match="incomplete/duplicate"):
        a.audit(p)
    p=_fixture(tmp_path/"forged")
    report=json.loads((p/"summary.json").read_text())
    report["release_authorized"]=True
    (p/"summary.json").write_text(json.dumps(report,sort_keys=True)+"\n")
    _hash(p)
    with pytest.raises(ValueError,match="qualification/seed"):
        a.audit(p)
