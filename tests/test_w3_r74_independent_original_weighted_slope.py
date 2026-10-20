"""R74-A independently implemented source-level numerical and refusal contracts."""
from __future__ import annotations

from hashlib import sha256
import json

import numpy as np
import pytest

from scripts import audit_w3_r74_independent_original_weighted_slope as a
from scripts import run_w3_r74_new_weighted_slope_hc2_hc3 as source


def _refusal(b,c,s,v):
    n,trials,design=a.config_info(c)
    return {
        "study":a.STUDY,"block":b,"config":c,"design":design,
        "support":s,"variance":v,
        "source_seed":a.frozen_seed(b,c,s,v,"source"),
        "gaussian_seed":a.frozen_seed(b,c,s,v,"gaussian"),
        "wild_seed":a.frozen_seed(b,c,s,v,"wild"),
        "native_units":n,"trials_per_unit":trials,"observed_curves":n*trials,
        "completed":False,"refused":True,
        "exception":{"type":"FrozenTestSourceRefusal","message":"failure recorded"},
        "method_truth_included":{name:None for name in a.METHODS},
        "no_calibrated_90pct_simultaneous_method":True,
        "no_source_missingness_or_MNAR":True,
        "release_authorized":False,
    }


def _rows():
    return [_refusal(b,c,s,v) for b in range(a.BLOCKS) for c in a.CONFIGS
            for s in a.SUPPORT for v in a.VARIANCE]


def _archive(path,accepted=None):
    path.mkdir(parents=True,exist_ok=True)
    rows=_rows()
    if accepted is not None:
        target=(accepted["block"],accepted["config"],accepted["support"],accepted["variance"])
        for i,q in enumerate(rows):
            if (q["block"],q["config"],q["support"],q["variance"])==target:
                rows[i]=accepted
                break
    (path/"cases.json").write_text(json.dumps(rows,sort_keys=True)+"\n")
    (path/"summary.json").write_text(json.dumps(source.summarize(rows),sort_keys=True)+"\n")
    (path/"source-commit.txt").write_text(a.ORIGINAL_CHECKOUT+"\n")
    _hash(path)
    return path


def _hash(path):
    names=("cases.json","summary.json","source-commit.txt")
    (path/"SHA256SUMS").write_text("".join(
        sha256((path/n).read_bytes()).hexdigest()+"  "+n+"\n" for n in names))


def test_prespecified_original_identity_and_heterogeneous_covariance():
    assert a.ORIGINAL_CHECKOUT=="4031d3dbe5cfc5617bd939c8ea9cd00d17376bd9"
    assert a.BLOCKS==32 and a.N==512 and a.B==999
    assert a.CONFIGS==(
        "curve_small","curve_standard","participant_small","participant_standard")
    assert a.config_info("participant_small")==(24,3,"participant")
    assert a.config_info("curve_small")==(36,1,"curve")
    assert a._wilson(0,32)[0]==0.
    assert np.all(a.unit_base_variance("participant")>.04**2/3)
    with pytest.raises(ValueError,match="unknown independent-unit"):
        a.config_info("not-configured")


@pytest.mark.parametrize("config",a.CONFIGS)
def test_independent_original_gaussian_source_X_Y_and_noise_pairing(config):
    X,Y,truth,scale=a.source_law(0,config,"extreme","predictor_heteroskedastic")
    _,frame,expected,XX,YY,scales=source.simulate(
        0,config,"extreme","predictor_heteroskedastic")
    np.testing.assert_allclose(X,XX,atol=0,rtol=0)
    np.testing.assert_allclose(Y,YY,atol=4e-14,rtol=0)
    np.testing.assert_allclose(truth,expected[1],atol=2e-14,rtol=0)
    np.testing.assert_allclose(scale,scales,atol=0,rtol=0)
    assert scale[0]==scale[-1]==4.


@pytest.mark.parametrize("config",("curve_small","participant_small"))
def test_independently_replay_real_wild_pooled_HC2_and_weighted_HC2_HC3_maxima(config):
    row=source.evaluate(0,config,"extreme","predictor_heteroskedastic")
    assert row["completed"],row["exception"]
    independently=a.verify_source(row)
    assert independently["completed"]
    assert independently["inclusion"]==row["method_truth_included"]
    assert len(independently["critical"])==5
    assert np.isfinite(independently["se_ratio"]["weighted_slope_HC3_Gaussian"])


def test_forged_gaussian_source_wild_maxima_or_HC3_truth_refused():
    row=source.evaluate(0,"curve_small","extreme","predictor_heteroskedastic")
    assert row["completed"]
    row["original_X"][0][1]=0.
    with pytest.raises(ValueError,match="original numerical mismatch"):
        a.verify_source(row)
    row=source.evaluate(0,"curve_small","extreme","predictor_heteroskedastic")
    row["method_999_raw_maxima"]["weighted_slope_HC3_Gaussian"][0]+=.5
    with pytest.raises(ValueError,match="original numerical mismatch"):
        a.verify_source(row)
    row=source.evaluate(0,"curve_small","extreme","predictor_heteroskedastic")
    row["method_truth_included"]["known_heteroskedastic_Gaussian"]=not row[
        "method_truth_included"]["known_heteroskedastic_Gaussian"]
    with pytest.raises(ValueError,match="classification changed"):
        a.verify_source(row)


def test_512_original_source_failure_inclusion_and_release_hold(tmp_path):
    folder=_archive(tmp_path/"source")
    result=a.audit(folder)
    assert result["planned_source_cases"]==512
    assert result["original_refused_cases"]==512
    assert result["original_maxima_all_methods_replayed"]==0
    assert result["per_cell"]["curve_small"]["extreme"]["predictor_heteroskedastic"][
        "independent_blocks_attempted"]==32
    assert result["per_cell"]["curve_small"]["extreme"]["predictor_heteroskedastic"][
        "failed_source_cases"]==32
    assert not result["calibrated_90pct_simultaneous_coverage_claim"]
    assert not result["release_authorized"]


def test_actual_accepted_source_keeps_31_other_refusals(tmp_path):
    row=source.evaluate(0,"participant_small","extreme","predictor_heteroskedastic")
    assert row["completed"],row["exception"]
    folder=_archive(tmp_path/"source",accepted=row)
    out=a.audit(folder)
    case=out["per_cell"]["participant_small"]["extreme"]["predictor_heteroskedastic"]
    assert case["completed_source_cases"]==1
    assert case["failed_source_cases"]==31
    assert out["original_wild_maxima_independently_replayed"]==999
    assert out["original_three_Gaussian_maxima_streams_independently_replayed"]==3*999
    assert out["original_maxima_all_methods_replayed"]==4*999


def test_source_archive_SHA_or_original_checkout_or_source_identity_tampered(tmp_path):
    folder=_archive(tmp_path/"source")
    with pytest.raises(ValueError,match="checkout"):
        a.audit(folder,expected_checkout="0"*40)
    path=folder/"cases.json"
    path.write_bytes(path.read_bytes()+b" ")
    with pytest.raises(ValueError,match="SHA256"):
        a.audit(folder)
    folder=_archive(tmp_path/"duplicate")
    data=json.loads((folder/"cases.json").read_text())
    data[0]["block"]=31
    (folder/"cases.json").write_text(json.dumps(data,sort_keys=True)+"\n")
    _hash(folder)
    with pytest.raises(ValueError,match="incomplete/duplicate"):
        a.audit(folder)


def test_false_90pct_calibration_or_release_summary_denied(tmp_path):
    folder=_archive(tmp_path/"source")
    original=json.loads((folder/"summary.json").read_text())
    original["no_90pct_simultaneous_band_calibration"]=False
    (folder/"summary.json").write_text(json.dumps(original,sort_keys=True)+"\n")
    _hash(folder)
    with pytest.raises(ValueError,match="summary/release"):
        a.audit(folder)
    folder=_archive(tmp_path/"release")
    original=json.loads((folder/"summary.json").read_text())
    original["release_authorized"]=True
    (folder/"summary.json").write_text(json.dumps(original,sort_keys=True)+"\n")
    _hash(folder)
    with pytest.raises(ValueError,match="summary/release"):
        a.audit(folder)
