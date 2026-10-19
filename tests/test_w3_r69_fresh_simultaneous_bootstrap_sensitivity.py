"""R69 prospectively new Gaussian fixed-truth band undercoverage mechanism contracts."""
from __future__ import annotations

import hashlib
import json

import numpy as np
import pytest

from scripts import run_w3_r69_fresh_simultaneous_bootstrap_sensitivity as r69
from scripts.run_w3_fixed_truth_interval_pilot import simulate as old_simulate
from eyetrajectoriespy.function_on_scalar import bootstrap_function_on_scalar_coefficients
from eyetrajectoriespy.workflows import (
    FunctionOnScalarWorkflowConfig,run_function_on_scalar_workflow,
)


def _synthetic(b,design,complete=True):
    n=72 if design=="curve" else 36
    conditions={}
    if complete:
        for m in r69.MULTIPLIERS:
            for budget in r69.BUDGETS:
                conditions[f"{m}/{budget}"]={
                    "multiplier":m,"draws":budget,
                    "seed":r69.draw_seed(b,design,m),
                    "source_units":n,"truth_slope_simultaneous_all_grid":b%3==0,
                    "truth_joint_family_simultaneous_all_grid":b%5==0,
                    "critical_slope":1.7+budget*.00001,
                    "critical_family":2.4+budget*.00001,
                    "slope_median_band_width":.3,
                    "family_median_band_width":.4,
                    "bootstrap_prefix_of_same_999draw_stream":True,
                }
    return {
        "study":r69.STUDY,"block":b,"design":design,
        "source_seed":r69.SEED+10007*b+r69.DESIGNS.index(design),
        "independent_units":n,
        "total_observed_curves":72 if design=="curve" else 108,
        "completed":complete,
        "exception":None if complete else {"type":"ControlledFailure","message":"preserved"},
        "max_beta_oracle_error":0. if complete else None,
        "max_HC1_oracle_error":0. if complete else None,
        "mean_slope_pointwise_truth_inclusion":.89 if complete else None,
        "conditions":conditions,"new_primitive_source_blocks":16,
        "bootstrap_draws_are_not_independent_source_units":True,
        "simultaneous_90pct_coverage_qualified":False,
        "release_authorized":False,
    }


def _all():
    return [_synthetic(b,d) for b in range(r69.BLOCKS) for d in r69.DESIGNS]


def test_design_source_nesting_immutable_seed_and_999draw_count():
    assert r69.SEED==202610196969
    assert r69.BLOCKS==16
    assert r69.SHARDS==((0,4),(4,8),(8,12),(12,16))
    assert r69.DATASETS==32
    assert r69.MULTIPLIERS==("rademacher","normal")
    assert r69.BUDGETS==(199,999)
    assert r69.CONDITIONAL_DRAW_STREAMS==63936
    assert r69.ORACLE_TOL==2e-10
    seeds=[r69.draw_seed(b,d,m) for b in range(16)
           for d in r69.DESIGNS for m in r69.MULTIPLIERS]
    assert len(seeds)==len(set(seeds))==64
    for design in r69.DESIGNS:
        a,_,truth,X,_=r69.simulate(0,design)
        b,*_=r69.simulate(1,design)
        old,*_=old_simulate(0,design)
        assert not np.array_equal(a.values,b.values)
        assert not np.array_equal(a.values,old.values)
        assert truth.shape==(2,len(r69.TIME),2)
        assert len(X)==(72 if design=="curve" else 36)
        assert a.n_curves==(72 if design=="curve" else 108)
    with pytest.raises(ValueError,match="preregistered"):
        r69.simulate(16,"curve")
    with pytest.raises(ValueError,match="frozen"):
        r69.draw_seed(0,"curve","other")


def test_actual_new_source_numerical_oracle_and_four_paired_cells():
    a=r69.evaluate(0,"curve")
    assert a["completed"],a["exception"]
    assert a["max_beta_oracle_error"]<=r69.ORACLE_TOL
    assert a["max_HC1_oracle_error"]<=r69.ORACLE_TOL
    assert len(a["conditions"])==4
    assert 0<=a["mean_slope_pointwise_truth_inclusion"]<=1
    for mult in r69.MULTIPLIERS:
        s=a["conditions"][f"{mult}/199"]
        l=a["conditions"][f"{mult}/999"]
        assert s["seed"]==l["seed"]==r69.draw_seed(0,"curve",mult)
        assert s["source_units"]==l["source_units"]==72
        assert s["bootstrap_prefix_of_same_999draw_stream"]
        assert l["bootstrap_prefix_of_same_999draw_stream"]
    assert not a["release_authorized"]
    assert not a["simultaneous_90pct_coverage_qualified"]


def test_199prefix_same_multiplier_seed_is_actual_exact_prefix_of_999():
    gaze,frame,truth,X,oracle=r69.simulate(1,"participant")
    config=FunctionOnScalarWorkflowConfig(
        predictors=("condition",),dimensions=r69.DIMS,unit="participant",
        participant_column="participant_id")
    fit=run_function_on_scalar_workflow(gaze,frame,config=config).fit
    for multiplier in r69.MULTIPLIERS:
        seed=r69.draw_seed(1,"participant",multiplier)
        short=bootstrap_function_on_scalar_coefficients(
            fit,n_bootstrap=199,multiplier=multiplier,random_state=seed)
        long=bootstrap_function_on_scalar_coefficients(
            fit,n_bootstrap=999,multiplier=multiplier,random_state=seed)
        np.testing.assert_array_equal(short.multipliers,long.multipliers[:199])
        np.testing.assert_array_equal(
            short.bootstrap_coefficients,long.bootstrap_coefficients[:199])


def test_full_independent_block_denominators_paired_critical_and_refused_source():
    rows=_all()
    result=r69.summarize(rows)
    assert result["independent_primitive_generating_blocks"]==16
    assert result["total_source_dataset_records"]==32
    assert result["original_full_bootstrap_draws_generated_not_prefixes"]==63936
    assert result["per_design"]["curve"]["attempted"]==16
    assert result["per_design"]["participant"]["complete"]==16
    assert result["per_design"]["curve"]["conditions"]["normal/999"][
        "independent_generating_blocks_attempted"]==16
    paired=result["paired_diagnostics"]["curve/rademacher/199_to_999"]
    assert paired["later_only_truth_included"]==0
    assert paired["earlier_only_truth_included"]==0
    assert paired["both_agree"]==16
    assert paired["mean_paired_critical_change_complete"]==pytest.approx(.008)
    assert not result["release_authorized"]
    rows=_all()
    rows[1]=_synthetic(0,"participant",False)
    result=r69.summarize(rows)
    assert result["per_design"]["participant"]["failed"]==1
    assert result["paired_diagnostics"]["participant/normal/199_to_999"][
        "missing_or_failed_primitive_blocks"]==1
    assert result["per_design"]["participant"]["conditions"]["normal/199"][
        "slope_full_denominator_upper"]>=result["per_design"]["participant"]["conditions"]["normal/199"][
        "slope_full_denominator_lower"]


def test_duplicate_source_forged_nominal_clearance_and_fourth_cell_missing_fail_closed():
    rows=_all()
    rows[0]["design"]="participant"
    with pytest.raises(ValueError,match="grid"):
        r69.summarize(rows)
    rows=_all()
    rows[0]["simultaneous_90pct_coverage_qualified"]=True
    with pytest.raises(ValueError,match="release flags"):
        r69.summarize(rows)
    rows=_all()
    rows[0]["conditions"].pop("normal/999")
    with pytest.raises(ValueError,match="lacks paired"):
        r69.summarize(rows)
    rows=_all()
    rows[0]["conditions"]["normal/999"]["seed"]+=1
    with pytest.raises(ValueError,match="provenance"):
        r69.summarize(rows)


def test_preregistered_four_shards_and_SHA256_artifact_provenance(tmp_path,monkeypatch):
    monkeypatch.setenv("GITHUB_SHA","d"*40)
    parts=tmp_path/"parts"
    for lo,hi in r69.SHARDS:
        folder=parts/f"source-{lo}"
        folder.mkdir(parents=True)
        rows=[_synthetic(i,d) for i in range(lo,hi) for d in r69.DESIGNS]
        raw=(json.dumps(rows,indent=2,sort_keys=True)+"\n").encode()
        (folder/"cases.json").write_bytes(raw)
        (folder/"manifest.json").write_text(json.dumps({
            "study":r69.STUDY,"start":lo,"stop":hi,"source_seed":r69.SEED,
            "cases":len(rows),"checkout":"d"*40,
            "sha256_cases":hashlib.sha256(raw).hexdigest(),
        }))
    r69.aggregate(tmp_path/"archive",parts)
    result=json.loads((tmp_path/"archive"/"summary.json").read_text())
    assert result["per_design"]["curve"]["complete"]==16
    assert (tmp_path/"archive"/"source-commit.txt").read_text().strip()=="d"*40
    altered=parts/"source-0"/"cases.json"
    altered.write_bytes(altered.read_bytes()+b" ")
    with pytest.raises(ValueError,match="SHA256"):
        r69.aggregate(tmp_path/"reject",parts)
