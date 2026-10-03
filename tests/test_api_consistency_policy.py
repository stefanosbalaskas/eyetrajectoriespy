import inspect
import json
from pathlib import Path

import eyetrajectoriespy as et


ROOT = Path(__file__).resolve().parents[1]
AUDIT_POLICY = json.loads(
    (ROOT / "PUBLIC_API_1_0_AUDIT.json").read_text(encoding="utf-8")
)


def test_public_export_list_has_no_duplicates():
    assert len(et.__all__) == len(set(et.__all__))


def test_reporting_helper_suffix_is_consistent():
    reporting = [
        name
        for name in et.__all__
        if "reporting" in name.lower()
    ]
    assert reporting
    assert all(name.endswith("_reporting_text") for name in reporting)


def test_public_frame_suffix_is_consistent():
    frame_like = [name for name in et.__all__ if "_frame" in name]
    assert frame_like
    assert all(name.endswith("_frame") for name in frame_like)


def test_canonical_bootstrap_randomness_uses_random_state():
    for name in (
        "bootstrap_function_on_scalar_coefficients",
        "bootstrap_functional_mixed_effects_coefficients",
        "bootstrap_generalized_function_on_scalar_coefficients",
    ):
        signature = inspect.signature(getattr(et, name))
        assert "random_state" in signature.parameters


def test_canonical_simultaneous_inference_uses_confidence_level():
    for name in (
        "function_on_scalar_simultaneous_bands",
        "functional_mixed_effects_simultaneous_bands",
        "generalized_function_on_scalar_simultaneous_bands",
    ):
        signature = inspect.signature(getattr(et, name))
        assert "confidence_level" in signature.parameters


def test_post_012_audit_is_observational_not_a_hidden_breaking_change():
    assert AUDIT_POLICY["decision_state"] == "inventory_only_no_1_0_promise"
    assert AUDIT_POLICY["one_dot_zero_commitment"] is False
    assert AUDIT_POLICY["deprecation_candidates"] == []
    assert AUDIT_POLICY["removal_candidates"] == []
    assert AUDIT_POLICY["principles"]["no_mass_rename"] is True
    assert AUDIT_POLICY["principles"]["no_deprecations_authorized"] is True
    assert AUDIT_POLICY["principles"]["no_removals_authorized"] is True


def test_post_012_explicit_audit_overrides_remain_public():
    names = {
        name
        for values in AUDIT_POLICY["explicit_overrides"].values()
        for name in values
    }
    assert names <= set(et.__all__)


def test_plotting_policy_is_one_way():
    assert AUDIT_POLICY["principles"]["plot_contract"].startswith(
        "every public plot_* API"
    )
    assert AUDIT_POLICY["principles"]["plot_noncontract"].startswith(
        "not every result object"
    )
