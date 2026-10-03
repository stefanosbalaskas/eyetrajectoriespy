import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DECISION = json.loads(
    (ROOT / "ONE_DOT_ZERO_DECISION.json").read_text(encoding="utf-8")
)
AUDIT = json.loads(
    (ROOT / "PUBLIC_API_1_0_AUDIT.json").read_text(encoding="utf-8")
)


def test_one_dot_zero_decision_does_not_publish_or_activate_stability():
    assert DECISION["ready_to_begin_1_0_stabilization"] is True
    assert DECISION["ready_to_publish_1_0"] is False
    assert DECISION["one_dot_zero_stability_promise_activated"] is False


def test_no_estimator_is_added_by_version_number():
    assert DECISION["scientific_omission_blocking_1_0"] is False
    assert DECISION["new_estimator_required_before_1_0"] is False
    assert (
        DECISION["interpretation"]["sparse_hierarchical_participant_trial_fda"]
        == "future_candidate_not_a_demonstrated_1_0_blocker"
    )


def test_plotting_contract_remains_one_way():
    assert AUDIT["principles"]["plot_contract"].startswith(
        "every public plot_* API"
    )
    assert AUDIT["principles"]["plot_noncontract"].startswith(
        "not every result object"
    )
    assert DECISION["interpretation"]["plotting"].startswith(
        "public_plot_implies_documented_deterministic_figure"
    )


def test_decision_preserves_known_product_observation_limitations():
    limitations = " ".join(DECISION["known_limitations"])
    assert "synthetic" in limitations
    assert "458 exports" in limitations
    assert "literal 1.0" in limitations


def test_literal_one_dot_zero_requires_fresh_versioned_qualification():
    requirements = " ".join(DECISION["required_before_any_1_0_publication"])
    assert "literal 1.0 version identity" in requirements
    assert "installed 1.0 candidate" in requirements
    assert "release-governance" in requirements


def test_decision_is_anchored_to_exact_qualified_and_merged_programme_state():
    evidence = DECISION["evidence"]
    assert DECISION["programme_checkpoint_main"] == "4917260e093600481cbc007b33a1cd3abce6619d"
    assert evidence["public_surface_audit"]["merged_main"] == "9061262a6084c3b1c5e046124bfc798f1e287be1"
    assert evidence["real_use_observation"]["qualified_head"] == "b5b14be63a077c110f398965491844f85eb1c886"
    assert evidence["real_use_observation"]["merged_main"] == "3fc19e221d0efb6c7e7a282db4804bd1c2b31e4b"
    assert evidence["canonical_reproducibility_case_study"]["qualified_head"] == "17b93c47b1ed992bc2cf3417a83ee4c849043887"
    assert evidence["canonical_reproducibility_case_study"]["merged_main"] == "4917260e093600481cbc007b33a1cd3abce6619d"
