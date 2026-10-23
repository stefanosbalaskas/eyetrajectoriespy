"""E5 RC2 release-content review: negative gates; this PR does not publish."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[1]
_SPEC = importlib.util.spec_from_file_location(
    "validate_e5_rc2_content_review",
    _ROOT / "scripts" / "validate_e5_rc2_content_review.py",
)
assert _SPEC is not None and _SPEC.loader is not None
e5 = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(e5)


def inputs():
    return [
        e5.read("E5_RC2_CONTENT_REVIEW.json"),
        e5.read("RELEASE_SCOPE_1_2_PROPOSAL.json"),
        e5.read("RC2_PUBLICATION_REVIEW.json"),
        e5.read("RELEASE_READINESS.json"),
        e5.read("EXPERIMENTAL_WORKFLOW_AUDIT.json"),
    ]


def test_e5_evidence_supports_only_an_explicit_experimental_reviewer_choice():
    assert e5.validate_content_review(*inputs()) == {
        "version": "1.2.0rc2", "E5_source_technical_jobs": 3,
        "status": "independent_review_pending",
        "experimental_helpers": 12, "stable_root_promotions": 0,
        "publication_authorized": False,
    }


@pytest.mark.parametrize("key", e5.PENDING)
def test_no_unreviewed_approval_or_hidden_publish(key):
    data = inputs()
    data[0][key] = True
    with pytest.raises(RuntimeError, match="Human approval/publication"):
        e5.validate_content_review(*data)


@pytest.mark.parametrize("key", [
    "production_release_ready", "github_release_ready", "testpypi_publication_ready",
])
def test_publication_readiness_must_remain_disabled(key):
    data = inputs()
    data[3][key] = True
    with pytest.raises(RuntimeError, match="Human approval/publication"):
        e5.validate_content_review(*data)


def test_exact_rc2_e5_evidence_cannot_be_renamed_or_fabricated():
    for key, value in [
        ("run_id", 1), ("source_commit", "0" * 40),
        ("qualified_jobs", 2), ("python_versions", ["3.12"]),
    ]:
        data = inputs()
        data[0]["e5_evidence"][key] = value
        with pytest.raises(RuntimeError, match="E5 evidence"):
            e5.validate_content_review(*data)


def test_bundled_importable_helpers_cannot_be_hidden_or_promoted():
    data = inputs()
    data[0]["imported_helper_names"].pop()
    with pytest.raises(RuntimeError, match="Experimental"):
        e5.validate_content_review(*data)
    data = inputs()
    data[1]["bundled_unqualified_experimental_module"]["public_contract_frozen"] = True
    with pytest.raises(RuntimeError, match="Experimental"):
        e5.validate_content_review(*data)
    data = inputs()
    data[0]["stable_root_promotions"] = 1
    with pytest.raises(RuntimeError, match="root API"):
        e5.validate_content_review(*data)


@pytest.mark.parametrize("issue", [289, 296])
def test_open_scientific_blockers_cannot_be_dropped(issue):
    data = inputs()
    data[0]["open_scientific_issues"].remove(issue)
    with pytest.raises(RuntimeError, match="Scientific inference"):
        e5.validate_content_review(*data)


def test_human_decision_is_required_separately():
    data = inputs()
    data[0]["reviewer_decision_required"] = ""
    with pytest.raises(RuntimeError, match="Required E5"):
        e5.validate_content_review(*data)
    data = inputs()
    data[2]["independent_human_release_review_recorded"] = True
    with pytest.raises(RuntimeError, match="Human approval/publication"):
        e5.validate_content_review(*data)
