"""Safety tests for the unqualified, nonpublishing literal 1.2.0 transition."""
from __future__ import annotations
import json
from pathlib import Path
import tomllib

ROOT = Path(__file__).resolve().parents[1]

def read_json(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))

def test_final_is_staged_but_not_publishable():
    with (ROOT / "pyproject.toml").open("rb") as f:
        assert tomllib.load(f)["project"]["version"] == "1.2.0"
    readiness = read_json("RELEASE_READINESS.json")
    assert readiness["current_development_version"] == "1.2.0"
    assert readiness["production_release_ready"] is False
    assert readiness["github_release_ready"] is False
    assert readiness["testpypi_publication_ready"] is False

def test_rc2_recorded_performance_is_immutable_historical_evidence():
    history = read_json("validation/performance/PERFORMANCE_ENVELOPE-1.2.0rc2.json")
    assert history["package_version"] == "1.2.0rc2"
    assert history["environment"]["packages"]["eyetrajectoriespy"] == "1.2.0rc2"
    assert history["qualification_run_id"] == 39945467014
    # Until fresh final-version measurements are recorded, RC2 is not final evidence.
    current = read_json("PERFORMANCE_ENVELOPE.json")
    assert current["package_version"] == "1.2.0rc2"
    assert current["environment"]["packages"]["eyetrajectoriespy"] == "1.2.0rc2"

def test_scientific_exclusions_survive_stable_candidate():
    scope = read_json("RELEASE_SCOPE_1_2_PROPOSAL.json")
    assert set(scope["scientific_blockers_open"]) == {289, 296}
    assert scope["frozen_root_compatibility"]["root_promotion_authorized"] is False
    assert scope["bundled_unqualified_experimental_module"]["public_contract_frozen"] is False
    assert scope["bundled_unqualified_experimental_module"]["supported_in_proposed_ten_workflow_api"] is False
    assert len(scope["candidate_workflows"]) == 10
    assert len(scope["bundled_unqualified_experimental_module"]["named_experimental_helpers"]) == 12
