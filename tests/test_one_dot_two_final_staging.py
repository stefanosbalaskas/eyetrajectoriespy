"""Safety tests for published stable 1.2.0 and postpublication interlocks."""
from __future__ import annotations
import json
from pathlib import Path
import tomllib

ROOT = Path(__file__).resolve().parents[1]

def read_json(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))

def test_final_source_published_and_production_readiness_disarmed_after_release():
    with (ROOT / "pyproject.toml").open("rb") as f:
        assert tomllib.load(f)["project"]["version"] == "1.2.0"
    readiness = read_json("RELEASE_READINESS.json")
    assert readiness["current_development_version"] == "1.2.0"
    assert readiness["production_release_ready"] is False
    assert readiness["github_release_ready"] is False
    approval = read_json("FINAL_1_2_PUBLICATION_APPROVAL.json")
    assert approval["published_final_version"] is True
    assert approval["production_workflow_run_id"] == 40128358042
    assert approval["publication_commit"] == "c1cd95ad718327550f7e55393ff38582872f7a94"
    assert readiness["testpypi_publication_ready"] is False

def test_rc2_recorded_performance_is_immutable_historical_evidence():
    history = read_json("validation/performance/PERFORMANCE_ENVELOPE-1.2.0rc2.json")
    assert history["package_version"] == "1.2.0rc2"
    assert history["environment"]["packages"]["eyetrajectoriespy"] == "1.2.0rc2"
    assert history["qualification_run_id"] == 39945467014
    # The final benchmark is a distinct, real GitHub Actions 1.2.0 measurement.
    current = read_json("PERFORMANCE_ENVELOPE.json")
    final_archive = read_json("validation/performance/PERFORMANCE_ENVELOPE-1.2.0.json")
    assert current == final_archive
    assert current["package_version"] == "1.2.0"
    assert current["environment"]["packages"]["eyetrajectoriespy"] == "1.2.0"
    assert current["qualification_run_id"] == 40121535785
    assert current["qualification_commit"] == "54cfd4207d0c4463601ca7fc5ab5113e2738457d"
    assert current["artifact_id"] == 12572080532
    assert current["raw_artifact_member_sha256"] == "022c5f3d30b336d9769c1afcbb5dc902a61ecfbf36011e7c7fca4fd70c894872"
    assert read_json("REFERENCE_VALIDATION.json")["package_version"] == "1.2.0"
    assert read_json("VALIDATION_TOLERANCES.json")["package_version"] == "1.2.0"
    original = read_json("validation/reference/REFERENCE_VALIDATION-1.2.0rc2.json")
    active = read_json("REFERENCE_VALIDATION.json")
    assert original["package_version"] == "1.2.0rc2"
    active["package_version"] = "1.2.0rc2"
    assert active == original

def test_scientific_exclusions_survive_stable_candidate():
    scope = read_json("RELEASE_SCOPE_1_2_PROPOSAL.json")
    assert set(scope["scientific_blockers_open"]) == {289, 296}
    assert scope["frozen_root_compatibility"]["root_promotion_authorized"] is False
    assert scope["bundled_unqualified_experimental_module"]["public_contract_frozen"] is False
    assert scope["bundled_unqualified_experimental_module"]["supported_in_proposed_ten_workflow_api"] is False
    assert len(scope["candidate_workflows"]) == 10
    assert len(scope["bundled_unqualified_experimental_module"]["named_experimental_helpers"]) == 12
