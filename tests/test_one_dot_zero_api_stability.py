import json
from pathlib import Path
import runpy

import pytest

import eyetrajectoriespy as et


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = json.loads(
    (ROOT / "ONE_DOT_ZERO_API_STABILITY.json").read_text(encoding="utf-8")
)
DECISION = json.loads(
    (ROOT / "ONE_DOT_ZERO_DECISION.json").read_text(encoding="utf-8")
)


def _freezer_namespace():
    return runpy.run_path(str(ROOT / "scripts" / "freeze_one_dot_zero_api.py"))


def test_frozen_boundary_is_anchored_to_completed_stabilization_baseline():
    assert CONTRACT["boundary_state"] == "frozen_candidate_for_1_0"
    assert CONTRACT["baseline_commit"] == "382c5940e090faf0f74f9bce4e9180a9e14f1eca"
    assert CONTRACT["counts"] == {
        "public_exports": 458,
        "stable_exports": 455,
        "experimental_exports": 3,
        "compatibility_exports": 1,
    }


def test_frozen_sets_partition_historical_boundary_and_are_live_subset():
    stable = set(CONTRACT["stable_exports"])
    experimental = set(CONTRACT["experimental_exports"])
    frozen = stable | experimental

    assert stable.isdisjoint(experimental)
    assert len(stable) == CONTRACT["counts"]["stable_exports"]
    assert len(experimental) == CONTRACT["counts"]["experimental_exports"]
    assert len(frozen) == CONTRACT["counts"]["public_exports"]
    assert frozen <= set(et.__all__)


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


def test_live_api_preserves_frozen_contract_with_no_additions_yet():
    namespace = _freezer_namespace()
    result = namespace["verify_frozen_compatibility"](CONTRACT)

    assert result["frozen_public_exports"] == 458
    assert result["live_public_exports"] == 458
    assert result["missing_frozen_exports"] == []
    assert result["additive_exports"] == []
    assert result["additive_export_count"] == 0
    assert (
        result["stable_signature_schema_sha256"]
        == CONTRACT["stable_signature_schema_sha256"]
    )


def test_additive_1x_export_is_allowed_and_reported(monkeypatch):
    namespace = _freezer_namespace()

    def additive_api(value, *, scale=1.0):
        return value * scale

    name = "compatibility_test_additive_api"
    monkeypatch.setattr(et, name, additive_api, raising=False)
    monkeypatch.setattr(et, "__all__", [*et.__all__, name])

    result = namespace["verify_frozen_compatibility"](CONTRACT)
    assert result["missing_frozen_exports"] == []
    assert result["additive_exports"] == [name]
    assert result["additive_export_count"] == 1


def test_missing_frozen_export_fails_closed(monkeypatch):
    namespace = _freezer_namespace()
    monkeypatch.setattr(
        et,
        "__all__",
        [name for name in et.__all__ if name != "fit_fpca"],
    )

    with pytest.raises(RuntimeError, match="missing frozen 1.0 exports: fit_fpca"):
        namespace["verify_frozen_compatibility"](CONTRACT)


def test_frozen_stable_signature_drift_fails_closed(monkeypatch):
    namespace = _freezer_namespace()

    def incompatible_fit_fpca(trajectories, *, changed_contract=False):
        return trajectories, changed_contract

    monkeypatch.setattr(et, "fit_fpca", incompatible_fit_fpca)

    with pytest.raises(
        RuntimeError,
        match="stable signature/result-schema contract drifted",
    ):
        namespace["verify_frozen_compatibility"](CONTRACT)


def test_duplicate_live_export_still_fails_closed(monkeypatch):
    namespace = _freezer_namespace()
    monkeypatch.setattr(et, "__all__", [*et.__all__, et.__all__[0]])

    with pytest.raises(RuntimeError, match="__all__ contains duplicate names"):
        namespace["verify_frozen_compatibility"](CONTRACT)


def test_api_freeze_does_not_prematurely_authorize_1_0_publication():
    assert DECISION["ready_to_begin_1_0_stabilization"] is True
    assert DECISION["ready_to_publish_1_0"] is False
    assert DECISION["one_dot_zero_stability_promise_activated"] is False
