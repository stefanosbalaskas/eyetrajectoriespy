"""Literal RC2 evidence provenance, immutable older RC1 and publication hold."""
from __future__ import annotations

import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def read(path):
    return json.loads((ROOT/path).read_text(encoding="utf-8"))


def test_rc2_performance_is_actual_new_source_evidence_and_archived_exactly():
    m=read("ONE_DOT_TWO_RC2_QUALIFICATION.json")
    p=read("PERFORMANCE_ENVELOPE.json")
    a=read("validation/performance/PERFORMANCE_ENVELOPE-1.2.0rc2.json")
    assert p==a
    source=m["new_literal_source_performance"]
    assert p["package_version"]=="1.2.0rc2"
    assert p["status"]=="qualified"
    assert p["qualification_commit"]==source["source_commit"]
    assert p["qualification_run_id"]==source["github_workflow_run_id"]
    assert p["environment"]["source_commit"]==p["qualification_commit"]
    assert p["environment"]["github_run_id"]==str(source["github_workflow_run_id"])
    assert p["environment"]["packages"]["eyetrajectoriespy"]=="1.2.0rc2"
    assert p["environment"]["thread_limits"]=={
        "MKL_NUM_THREADS":"1","NUMEXPR_NUM_THREADS":"1",
        "OMP_NUM_THREADS":"1","OPENBLAS_NUM_THREADS":"1"
    }
    assert len(p["results"])==6
    assert all(row["repeats"]==3 for row in p["results"])
    assert source["original_artifact_id"]==12497727453
    assert source["original_artifact_member_sha256"]==(
        "8da44ff291614aac2b9e01ae8819bcda67f98e0c33cb7b43dfdfb3b9adbcd3d5"
    )


def test_previously_frozen_rc1_performance_is_not_relabelled_or_deleted():
    old=read("validation/performance/PERFORMANCE_ENVELOPE-1.2.0rc1.json")
    assert old["package_version"]=="1.2.0rc1"
    rc1=read("ONE_DOT_TWO_RC_QUALIFICATION.json")
    assert rc1["package_version"]=="1.2.0rc1"
    assert rc1["historical_one_dot_one_performance_relabelled"] is False


def test_historical_provenance_disarmed_while_owner_publication_request_is_separate():
    m=read("ONE_DOT_TWO_RC2_QUALIFICATION.json")
    r=read("validation/RELEASE_READINESS-1.2.0rc2.json")
    assert m["package_version"]==r["current_development_version"]=="1.2.0rc2"
    assert m["source_release_qualified"] is False
    assert m["production_release_ready"] is False
    assert m["github_release_ready"] is False
    assert m["testpypi_publication_ready"] is False
    assert m["publication_authorized"] is False
    assert m["root_export_promotion_authorized"] is False
    assert m["research_inference_claims_qualified"] is False
    assert sorted(m["open_scientific_issues"])==[289,296]
    assert r["production_release_ready"] is True
    assert r["github_release_ready"] is True
    assert r["testpypi_publication_ready"] is False
    # Historical RC2 authorization is not the active unqualified 1.2.0 source.
    current=read("RELEASE_READINESS.json")
    assert current["current_development_version"] == "1.2.0"
    assert current["production_release_ready"] is False
    assert current["github_release_ready"] is False
