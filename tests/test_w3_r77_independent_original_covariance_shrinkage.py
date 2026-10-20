"""R77-A independent original extreme-anchor replication Gaussian independent audit fixtures."""
from __future__ import annotations

from hashlib import sha256
import json

import numpy as np
import pytest

from scripts import audit_w3_r77_independent_original_covariance_shrinkage as a
from scripts import run_w3_r77_covariance_shrinkage_falsification as orig


def _refusal(b,c,s,v):
    n,trials,design=orig.config_info(c)
    return {
        "study":a.STUDY,"block":b,"config":c,"support":s,"variance":v,
        "design":design,"native_units":n,"observed_curves":n*trials,
        "source_seed":a._seed(b,c,s,v,"source"),
        "gaussian_seed":a._seed(b,c,s,v,"gaussian"),
        "wild_seed":a._seed(b,c,s,v,"wild"),
        "reg025_seed":a._seed(b,c,s,v,"reg025"),
        "reg050_seed":a._seed(b,c,s,v,"reg050"),
        "number_of_extreme_anchor_units":a.ANCHORS[s],
        "completed":False,"refused":True,
        "exception":{"type":"ControlledRefusal","message":"retained for source denominator"},
        "cell_truth_included":{x:None for x in a.CELLS},
        "not_90pct_calibrated":True,"no_MNAR_missingness":True,
        "release_authorized":False,
    }


def _folder(path,accepted=None):
    path.mkdir(parents=True,exist_ok=True)
    rows=[_refusal(b,c,s,v) for b in range(a.BLOCKS)
          for c in a.CONFIGS for s in a.SUPPORT for v in a.VARIANCES]
    if accepted is not None:
        for i,row in enumerate(rows):
            if (row["block"],row["config"],row["support"],row["variance"])==(
                accepted["block"],accepted["config"],accepted["support"],accepted["variance"]):
                rows[i]=accepted
                break
    (path/"cases.json").write_text(json.dumps(rows,sort_keys=True)+"\n")
    (path/"summary.json").write_text(
        json.dumps(orig.summarize(rows),sort_keys=True)+"\n")
    (path/"source-commit.txt").write_text(a.CHECKOUT+"\n")
    _rehash(path)
    return path


def _rehash(path):
    names=("cases.json","summary.json","source-commit.txt")
    (path/"SHA256SUMS").write_text("".join(
        sha256((path/name).read_bytes()).hexdigest()+"  "+name+"\n"
        for name in names))


def test_exact_new_seeds_and_32_independent_source_units():
    assert a.CHECKOUT=="7bf404844078361339d593f27db0d70aeca3de2b"
    assert a.SOURCE_SEED==202610207770
    assert a.GAUSSIAN_SEED==202610207771
    assert a.WILD_SEED==202610207772
    assert a.REG025_SEED==202610207773 and a.REG050_SEED==202610207774
    assert a.N_CASES==256 and a.BLOCKS==32 and a.B==999
    assert len({a._seed(b,c,s,v,"gaussian") for b in range(32)
                for c in a.CONFIGS for s in a.SUPPORT for v in a.VARIANCES})==256
    with pytest.raises(ValueError,match="identity malformed"):
        a._seed(32,"curve_standard","ordinary","constant","source")


@pytest.mark.parametrize("config",a.CONFIGS)
def test_independent_source_X_Y_and_999_wild_true_HC3_maxima(config):
    source=orig.evaluate(0,config,"two_anchors","predictor_heteroskedastic")
    assert source["completed"],source["exception"]
    verified=a.check_case(source)
    assert verified["completed"]
    assert verified["cell_truth_included"]==source["cell_truth_included"]
    assert verified["wild_HC1"]==source["wild_HC1_truth_included"]
    assert np.isfinite(verified["HC3_SE_to_true_SE_mean"])


def test_fabricated_wild_or_estimated_correlation_raw_max_refused():
    source=orig.evaluate(0,"curve_standard","two_anchors","predictor_heteroskedastic")
    assert source["completed"]
    source["raw_reference_maxima"]["wild_HC1"][11]+=.1
    with pytest.raises(ValueError,match="independently reconstructed mismatch"):
        a.check_case(source)
    source=orig.evaluate(0,"curve_standard","two_anchors","predictor_heteroskedastic")
    source["raw_reference_maxima"]["HC3_corr"][5]+=.2
    with pytest.raises(ValueError,match="independently reconstructed mismatch"):
        a.check_case(source)


def test_original_gaussian_X_Y_or_true_SE_tamper_fails_closed():
    source=orig.evaluate(0,"curve_standard","two_anchors","predictor_heteroskedastic")
    assert source["completed"]
    source["observed_Y_native_unit_mean"][0][0][0]+=.005
    with pytest.raises(ValueError,match="independently reconstructed mismatch"):
        a.check_case(source)
    source=orig.evaluate(0,"participant_standard","two_anchors","predictor_heteroskedastic")
    source["known_SE_grid"][0][0]*=1.2
    with pytest.raises(ValueError,match="independently reconstructed mismatch"):
        a.check_case(source)


def test_false_truth_inclusion_or_calibration_release_refused():
    source=orig.evaluate(0,"curve_standard","two_anchors","predictor_heteroskedastic")
    assert source["completed"]
    cell="HC3_SE/HC3_corr"
    source["cell_truth_included"][cell]=not source["cell_truth_included"][cell]
    with pytest.raises(ValueError,match="truth inclusion falsified"):
        a.check_case(source)
    source=orig.evaluate(0,"curve_standard","two_anchors","predictor_heteroskedastic")
    source["release_authorized"]=True
    with pytest.raises(ValueError,match="qualification mismatch"):
        a.check_case(source)


def test_refusal_inclusive_original_grid_and_immutable_archive_contract(tmp_path):
    folder=_folder(tmp_path/"refused")
    evidence=a.audit(folder)
    assert evidence["original_source_cases"]==256
    assert evidence["independently_replayed_source_X_Y"]==0
    assert evidence["original_source_refusals"]==256
    assert evidence["original_SHA256_archive_members"]==3
    assert not evidence["release_authorized"]
    assert evidence["source_results"]["curve_standard"]["two_anchors"][
        "predictor_heteroskedastic"]["complete"]==0
    with pytest.raises(ValueError,match="checkout"):
        a.audit(folder,expected_checkout="d"*40)
    (folder/"cases.json").write_bytes((folder/"cases.json").read_bytes()+b" ")
    with pytest.raises(ValueError,match="SHA256"):
        a.audit(folder)


def test_actual_accepted_fixture_replay_and_summary_reconstruction(tmp_path):
    source=orig.evaluate(0,"curve_standard","two_anchors","predictor_heteroskedastic")
    assert source["completed"],source["exception"]
    folder=_folder(tmp_path/"one_original",accepted=source)
    report=a.audit(folder)
    assert report["independently_replayed_source_X_Y"]==1
    assert report["independently_replayed_wild_maxima"]==999
    assert report["independently_replayed_true_correlation_maxima"]==999
    assert report["independently_replayed_HC3_correlation_maxima"]==999
    assert report["independently_replayed_REG025_maxima"]==999
    assert report["independently_replayed_REG050_maxima"]==999
    assert report["source_results"]["curve_standard"]["two_anchors"][
        "predictor_heteroskedastic"]["complete"]==1
    summary=json.loads((folder/"summary.json").read_text())
    summary["release_authorized"]=True
    (folder/"summary.json").write_text(json.dumps(summary,sort_keys=True)+"\n")
    _rehash(folder)
    with pytest.raises(ValueError,match="calibration/identity forged"):
        a.audit(folder)


def test_duplicate_original_source_identity_cannot_inflate_32block_denominator(tmp_path):
    folder=_folder(tmp_path/"duplicate")
    rows=json.loads((folder/"cases.json").read_text())
    rows[0]["block"]=31
    (folder/"cases.json").write_text(json.dumps(rows,sort_keys=True)+"\n")
    _rehash(folder)
    with pytest.raises(ValueError,match="missing/duplicated"):
        a.audit(folder)
