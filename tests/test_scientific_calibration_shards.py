"""Deterministic multi-shard simulation evidence and tamper-rejection contracts."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import sys

# Gallery validation executes pytest via its console entry point.
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd
import pytest

from eyetrajectoriespy.research.calibration_seed import (
    calibration_manifest, calibration_replicate_seed,
)
from scripts.aggregate_scientific_calibration_shards import aggregate


def _write_shard(
    root: Path, *, programme="B6", master_seed=97, shard_id=0,
    force_seed=None,
):
    root.mkdir(parents=True,exist_ok=True)
    manifest=calibration_manifest(
        programme,master_seed=master_seed,shard_id=shard_id,
        records_per_scenario=2,case_files=("cases.csv",))
    (root/"manifest.json").write_text(json.dumps(manifest)+"\n")
    records=[]
    for scenario in ("matched_rank1","matched_rank2"):
        for replicate in (0,1):
            seed=calibration_replicate_seed(
                programme,master_seed=master_seed,shard_id=shard_id,
                scenario=scenario,replicate=replicate)
            records.append({
                "scenario":scenario,"replicate":replicate,
                "shard_id":shard_id,
                "seed":seed if force_seed is None else force_seed,
                "status":"failed" if scenario=="matched_rank2" and replicate==0 else "ok",
                "population_mean_mid_90_included":True if replicate==0 else False,
            })
    pd.DataFrame(records).to_csv(root/"cases.csv",index=False)
    (root/"sha256.txt").write_text("".join(
        sha256((root/name).read_bytes()).hexdigest()+"  "+name+"\n"
        for name in ("cases.csv","manifest.json")))
    return root


def test_seed_namespace_is_stable_and_shards_are_distinct():
    a=calibration_replicate_seed(
        "B6",master_seed=97,shard_id=0,scenario="matched_rank1",replicate=0)
    assert a==calibration_replicate_seed(
        "B6",master_seed=97,shard_id=0,scenario="matched_rank1",replicate=0)
    keys=set()
    for shard in range(7):
        for scenario in ("null","alternative","rank2"):
            for replicate in range(90):
                keys.add(calibration_replicate_seed(
                    "F1",master_seed=97,shard_id=shard,
                    scenario=scenario,replicate=replicate))
    assert len(keys)==7*3*90
    with pytest.raises(ValueError,match="shard_id"):
        calibration_replicate_seed(
            "B6",master_seed=97,shard_id=-1,scenario="x",replicate=0)
    with pytest.raises(ValueError,match="scenario"):
        calibration_replicate_seed(
            "B6",master_seed=97,shard_id=1,scenario="",replicate=0)


def test_aggregator_retains_fit_failures_and_conditional_coverage(tmp_path):
    a=_write_shard(tmp_path/"a",shard_id=0)
    b=_write_shard(tmp_path/"b",shard_id=1)
    cases,evidence=aggregate([a,b])
    assert len(cases)==8
    assert evidence["n_shards"]==2
    assert evidence["total_fit_failures"]==2
    assert evidence["observed_duplicate_seeds_rejected"]
    assert evidence["data_integrity_hashes_verified"]
    assert not evidence["scientific_inference_qualified"]
    assert not evidence["publication_authorized"]
    rows=evidence["scenario_summaries"]
    assert len(rows)==2
    by_scenario={json.loads(row["scenario_key"])[0]:row for row in rows}
    assert by_scenario["matched_rank2"]["n_successful"]==2
    assert by_scenario["matched_rank2"]["n_failed"]==2
    assert by_scenario["matched_rank1"]["population_mean_mid_90_included"]["n"]==4


def test_aggregator_rejects_repeat_shard_tampered_bytes_and_colliding_seeds(tmp_path):
    a=_write_shard(tmp_path/"a",shard_id=0)
    b=_write_shard(tmp_path/"b",shard_id=0)
    with pytest.raises(ValueError,match="duplicate shard"):
        aggregate([a,b])
    b=_write_shard(tmp_path/"b",shard_id=1)
    (b/"cases.csv").write_text((b/"cases.csv").read_text()+"\nchanged")
    with pytest.raises(ValueError,match="checksum mismatch"):
        aggregate([a,b])
    b=_write_shard(tmp_path/"b",shard_id=1,force_seed=123)
    with pytest.raises(ValueError,match="seed collision"):
        aggregate([a,b])


def test_aggregator_rejects_mismatched_master_seed(tmp_path):
    a=_write_shard(tmp_path/"a",master_seed=97,shard_id=0)
    b=_write_shard(tmp_path/"b",master_seed=98,shard_id=1)
    with pytest.raises(ValueError,match="master seed"):
        aggregate([a,b])


def test_aggregator_will_not_count_failed_fit_as_success(tmp_path):
    a=_write_shard(tmp_path/"a")
    cases,evidence=aggregate([a])
    scenario={json.loads(x["scenario_key"])[0]:x
              for x in evidence["scenario_summaries"]}
    assert scenario["matched_rank2"]["n_attempted"]==2
    assert scenario["matched_rank2"]["n_successful"]==1
    assert scenario["matched_rank2"]["population_mean_mid_90_included"]["n"]==1


def test_actual_f1_and_f5_full_refit_cases_aggregate_with_original_iteration_alias(tmp_path):
    """Regression for empirical wave #250: F1 persisted iteration, not replicate."""
    from scripts.run_f1_f5_scientific_stress import f1_study,f5_study
    folder=tmp_path/"real-F1-F5"
    folder.mkdir()
    f1,_=f1_study(2,99,20261009,shard_id=0)
    f5,_=f5_study(2,99,20261009,shard_id=0)
    assert len(f1)==16 and len(f5)==48
    assert "iteration" in f1.columns and "replicate" in f1.columns
    assert f1["replicate"].equals(f1["iteration"])
    # Simulate exact archived pre-repair F1 artifact without any edits to it.
    f1.drop(columns=["replicate"]).to_csv(folder/"f1-cases.csv",index=False)
    f5.to_csv(folder/"f5-cases.csv",index=False)
    manifest=calibration_manifest(
        "F1_F5",master_seed=20261009,shard_id=0,
        records_per_scenario=2,case_files=("f1-cases.csv","f5-cases.csv"))
    (folder/"manifest.json").write_text(json.dumps(manifest)+"\n")
    (folder/"sha256.txt").write_text("".join(
        sha256((folder/name).read_bytes()).hexdigest()+"  "+name+"\n"
        for name in ("f1-cases.csv","f5-cases.csv","manifest.json")))
    combined,ev=aggregate([folder])
    assert ev["total_attempts"]==64
    assert ev["total_fit_failures"]==int((combined.status=="failed").sum())
    assert ev["n_shards"]==1 and not ev["scientific_inference_qualified"]
    actual_f1=combined.loc[combined.calibration_method=="f1-cases.csv"]
    assert len(actual_f1)==16
    assert actual_f1.replicate.astype(int).equals(actual_f1.iteration.astype(int))
    assert len([x for x in ev["scenario_summaries"]
                if x["case_file"]=="f1-cases.csv"])==8
    assert len([x for x in ev["scenario_summaries"]
                if x["case_file"]=="f5-cases.csv"])==24
    # Invalid dual aliases must be rejected even with valid file checksums.
    edited=pd.read_csv(folder/"f1-cases.csv")
    edited["replicate"]=edited["iteration"]
    edited.loc[0,"replicate"]=99
    edited.to_csv(folder/"f1-cases.csv",index=False)
    (folder/"sha256.txt").write_text("".join(
        sha256((folder/name).read_bytes()).hexdigest()+"  "+name+"\n"
        for name in ("f1-cases.csv","f5-cases.csv","manifest.json")))
    with pytest.raises(ValueError,match="identifiers disagree"):
        aggregate([folder])
