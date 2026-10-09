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
