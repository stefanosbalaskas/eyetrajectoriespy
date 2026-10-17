"""True-zero/positive R56 independent Gaussian source and numerical ledger."""
import hashlib
import json

import numpy as np
import pytest

from scripts import run_w3_r16_leverage_covariance_factorial as r16
from scripts import run_w3_r53_local_reml_influence as r53
from scripts import run_w3_r55_active_face_switch_profile as r55
from scripts import run_w3_r56_true_zero_slope_diagnostic as r56


def test_new_primitive_blocks_and_prespecified_denominators():
    assert r56.MASTER_SEED not in (r53.SOURCE_SEED,r55.REUSED_SOURCE_SEED)
    assert r56.BLOCKS==16 and r56.PARTICIPANTS==24
    assert r56.SLOPE_STATES==("true_zero","true_positive")
    assert r56.N_PAIRED_DESIGNS==32 and r56.N_CASES==64
    assert r56.N_OPTIMIZER_STARTS==128
    assert r56.SHARDS==((0,4),(4,8),(8,12),(12,16))
    a=r56.independent_primitive_source(0,r56.SUPPORT[0])
    b=r56.independent_primitive_source(0,r56.SUPPORT[1])
    independent=r56.independent_primitive_source(1,r56.SUPPORT[0])
    old=r53.source(0,r53.SUPPORT[0])
    np.testing.assert_array_equal(
        a[0]["participant_slope"],b[0]["participant_slope"])
    assert not np.array_equal(
        a[0]["participant_slope"],independent[0]["participant_slope"])
    assert not np.array_equal(
        a[0]["participant_slope"],old[0]["participant_slope"])
    with pytest.raises(ValueError,match="unregistered"):
        r56.independent_primitive_source(16,r56.SUPPORT[0])


def test_true_zero_source_is_exact_counterfactual_slope_removal():
    paired,description=r56.paired_source_data(0,r56.SUPPORT[0])
    zero=paired["true_zero"]
    positive=paired["true_positive"]
    raw=r56.independent_primitive_source(0,r56.SUPPORT[0])[0]
    expected=(
        r16.SIGMA_RANDOM_SLOPE*
        raw["participant_slope"][positive["group"].astype(int),0,0,0]*
        positive["x"]*(1+.25*positive["time"]))
    np.testing.assert_allclose(
        positive["y"]-zero["y"],expected,rtol=1e-13,atol=1e-13)
    np.testing.assert_array_equal(positive["w"],zero["w"])
    np.testing.assert_array_equal(positive["X"],zero["X"])
    np.testing.assert_array_equal(positive["group"],zero["group"])
    assert positive["truth"]==zero["truth"]
    assert description["same_Gaussian_innovations_for_both_slope_states"]
    assert description["source_slope_contribution_norm"]>0


def test_true_zero_and_positive_share_participants_and_supports_not_trials():
    ordinary,_=r56.paired_source_data(1,r56.SUPPORT[0])
    extreme,_=r56.paired_source_data(1,r56.SUPPORT[1])
    a=ordinary["true_zero"];b=extreme["true_zero"]
    np.testing.assert_array_equal(a["group"],b["group"])
    np.testing.assert_array_equal(a["time"],b["time"])
    np.testing.assert_array_equal(a["trial"],b["trial"])
    assert not np.array_equal(a["x"],b["x"])


def test_refusal_ledger_keeps_all_original_slope_state_slots():
    rows=[r56._empty_case(block,s,state)
          for block in range(r56.BLOCKS)
          for s in r56.SUPPORT for state in r56.SLOPE_STATES]
    result=r56.summarize(rows)
    assert result["complete_failure_inclusive_original_source_denominator"]
    assert result["planned_source_slope_state_cases"]==64
    assert result["recorded_source_slope_state_cases"]==64
    assert result["recorded_original_two_start_optimizer_outcome_slots"]==128
    assert result["new_independent_Gaussian_primitive_blocks"]==16
    assert result["no_true_zero_boundary_null_typeI_power_calibration"]
    assert not result["release_authorized"]
    assert all(z["source_generation_refusals"]==16
               for z in result["strata"].values())
    with pytest.raises(ValueError,match="duplicate"):
        r56.summarize(rows+[rows[0]])


def test_aggregator_rejects_original_shard_corruption(tmp_path,monkeypatch):
    monkeypatch.setenv("GITHUB_SHA","original-R56-Gaussian-merge-sha")
    folder=tmp_path/"original-shards"
    for start,stop in r56.SHARDS:
        p=folder/f"primitive-{start}"
        p.mkdir(parents=True)
        rows=[r56._empty_case(b,s,z) for b in range(start,stop)
              for s in r56.SUPPORT for z in r56.SLOPE_STATES]
        r56._write(p/"cases.json",rows)
        r56._write(p/"manifest.json",{
            "study":r56.STUDY,"block_start":start,"block_stop":stop,
            "new_source_seed":r56.MASTER_SEED,
            "original_GitHub_merge_checkout":"original-R56-Gaussian-merge-sha",
            "cases_sha256":hashlib.sha256(
                (p/"cases.json").read_bytes()).hexdigest(),
            "records":len(rows),
        })
    output=tmp_path/"complete"
    r56.aggregate(output,folder)
    result=json.loads((output/"summary.json").read_text())
    assert result["complete_failure_inclusive_original_source_denominator"]
    (folder/"primitive-0"/"cases.json").write_text("tampered")
    with pytest.raises(ValueError,match="SHA256 corrupted"):
        r56.aggregate(tmp_path/"wrong",folder)


def test_nonfinite_original_source_evidence_is_not_serialized(tmp_path):
    with pytest.raises(ValueError):
        r56._write(tmp_path/"no.json",{"invalid":np.array([np.nan])})
