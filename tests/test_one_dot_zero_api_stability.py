import json
from pathlib import Path
import runpy

import eyetrajectoriespy as et


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = json.loads(
    (ROOT / "ONE_DOT_ZERO_API_STABILITY.json").read_text(encoding="utf-8")
)
DECISION = json.loads(
    (ROOT / "ONE_DOT_ZERO_DECISION.json").read_text(encoding="utf-8")
)


def test_frozen_boundary_is_anchored_to_completed_stabilization_baseline():
    assert CONTRACT["boundary_state"] == "frozen_candidate_for_1_0"
    assert CONTRACT["baseline_commit"] == "382c5940e090faf0f74f9bce4e9180a9e14f1eca"
    assert CONTRACT["counts"] == {
        "public_exports": 458,
        "stable_exports": 455,
        "experimental_exports": 3,
        "compatibility_exports": 1,
    }


def test_stable_and_experimental_sets_partition_exact_public_namespace():
    stable = set(CONTRACT["stable_exports"])
    experimental = set(CONTRACT["experimental_exports"])
    assert stable.isdisjoint(experimental)
    assert stable | experimental == set(et.__all__)
    assert len(stable) == CONTRACT["counts"]["stable_exports"]
    assert len(experimental) == CONTRACT["counts"]["experimental_exports"]


def test_only_reviewed_experimental_apis_are_outside_1_0_guarantee():
    assert CONTRACT["experimental_exports"] == [
        "conditional_transfer_entropy",
        "discrete_transfer_entropy",
        "return_map_stability",
    ]
    assert CONTRACT["compatibility_exports"] == ["fit_sparse_fpca_fdapy"]
    assert "fit_sparse_fpca_fdapy" in CONTRACT["stable_exports"]


def test_stabilization_introduces_no_deprecation_or_removal():
    policy = CONTRACT["semver_policy"]
    assert policy["deprecations_authorized"] == []
    assert policy["removals_authorized"] == []
    assert policy["no_mass_rename"] is True
    assert policy["stable_names_signatures_and_result_schema_fields"] is True
    assert policy["experimental_apis_outside_1_0_compatibility_guarantee"] is True


def test_live_api_exactly_reproduces_frozen_contract():
    namespace = runpy.run_path(str(ROOT / "scripts" / "freeze_one_dot_zero_api.py"))
    assert namespace["build_contract"]() == CONTRACT


def test_api_freeze_does_not_prematurely_authorize_1_0_publication():
    assert DECISION["ready_to_begin_1_0_stabilization"] is True
    assert DECISION["ready_to_publish_1_0"] is False
    assert DECISION["one_dot_zero_stability_promise_activated"] is False
