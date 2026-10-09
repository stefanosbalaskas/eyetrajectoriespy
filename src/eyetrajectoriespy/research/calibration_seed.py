"""Reproducible independent seed namespace for UNQUALIFIED research calibration.

The inputs (programme, master seed, batch/shard number, scenario, replicate)
uniquely define the counter to a 63-bit cryptographic seed mapping. This is
deterministic and collision-resistant, not a proof of mathematical uniqueness;
the batch aggregator also rejects observed collisions and repeated replicate IDs.
"""
from __future__ import annotations

from hashlib import blake2b
import json


def calibration_replicate_seed(
    programme: str, *, master_seed: int, shard_id: int,
    scenario: str, replicate: int,
) -> int:
    if not isinstance(programme,str) or not programme.strip():
        raise ValueError("programme must be nonempty")
    if not isinstance(scenario,str) or not scenario.strip():
        raise ValueError("scenario must be nonempty")
    for value,name in ((master_seed,"master_seed"),(shard_id,"shard_id"),
                       (replicate,"replicate")):
        if (isinstance(value,bool) or not isinstance(value,int) or
            value<0 or value>=2**63):
            raise ValueError(f"{name} must be nonnegative integer < 2**63")
    key=json.dumps(
        [programme,master_seed,shard_id,scenario,replicate],
        separators=(",",":"),ensure_ascii=True,
    ).encode("ascii")
    hashed=blake2b(key,digest_size=8,person=b"eye-calibr-2026").digest()
    return int.from_bytes(hashed,"big") & (2**63-1)


def calibration_manifest(
    programme: str, *, master_seed: int, shard_id: int,
    records_per_scenario: int, case_files: tuple[str,...],
) -> dict:
    """Metadata only; does not change inferential qualification."""
    if records_per_scenario<1 or not isinstance(records_per_scenario,int):
        raise ValueError("records_per_scenario must be positive integer")
    calibration_replicate_seed(
        programme,master_seed=master_seed,shard_id=shard_id,
        scenario="manifest_validation",replicate=0,
    )
    return {
        "schema_version":1,"programme":programme,
        "master_seed":master_seed,"shard_id":shard_id,
        "replicates_per_scenario":records_per_scenario,
        "case_files":list(case_files),
        "seed_derivation":"blake2b_63bit_programme_seed_shard_scenario_replicate",
        "seed_uniqueness_mathematically_guaranteed":False,
        "observed_collisions_must_fail_aggregation":True,
        "scientific_inference_qualified":False,
        "release_authorized":False,
    }
