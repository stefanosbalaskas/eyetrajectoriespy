import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "evidence" / "nonlinear_evidence.json"


def _data():
    return json.loads(REGISTRY.read_text(encoding="utf-8"))


def test_nonlinear_evidence_registry_has_unique_verified_ids_and_dois():
    data = _data()
    verified = data["verified"]
    ids = [entry["id"] for entry in verified]
    dois = [entry["doi"].lower() for entry in verified]

    assert len(verified) >= 16
    assert len(ids) == len(set(ids))
    assert len(dois) == len(set(dois))
    assert all("/" in doi for doi in dois)


def test_nonlinear_evidence_registry_uses_declared_tiers_and_primary_index_sources():
    data = _data()
    allowed = {
        "direct_behavioral_gaze",
        "direct_eye_or_pupil_signal",
        "general_methodology",
    }
    for entry in data["verified"]:
        assert entry["tier"] in allowed
        assert entry["method_tags"]
        assert entry["supports"]
        assert entry["does_not_support"]
        source = entry["verification_source"].lower()
        assert "wikipedia.org" not in source
        assert "medium.com" not in source


def test_direct_eye_movement_evidence_anchors_are_retained():
    data = _data()
    by_id = {entry["id"]: entry for entry in data["verified"]}

    assert by_id["anderson2013_rqa_eye_movements"]["tier"] == "direct_behavioral_gaze"
    assert by_id["gurtner2019_rqa_mental_imagery"]["tier"] == "direct_behavioral_gaze"
    assert by_id["korda2018_lle_eye_movements"]["tier"] == "direct_eye_or_pupil_signal"
    assert by_id["mesin2013_pupil_rqa"]["tier"] == "direct_eye_or_pupil_signal"
    assert by_id["piu2019_pupil_crqa"]["tier"] == "direct_eye_or_pupil_signal"
    assert by_id["fink2024_dynamic_pupil_methods"]["tier"] == "direct_eye_or_pupil_signal"


def test_unverified_candidates_are_explicitly_non_novelty_evidence():
    data = _data()
    candidates = data["unverified_candidates"]

    assert len(candidates) == 5
    for entry in candidates:
        assert entry["status"] == "not_verified_in_2026-09-23_audit"
        note = entry["note"].lower()
        assert "do not cite" in note or "use verified" in note

    rule = data["interpretation_rule"].lower()
    assert "not evidence" in rule
    assert "novelty" in rule


def test_verified_dois_are_present_in_nonlinear_references():
    data = _data()
    references = (ROOT / "docs" / "methods" / "references.md").read_text(
        encoding="utf-8"
    )
    for entry in data["verified"]:
        assert entry["doi"] in references


def test_unverified_candidate_titles_stay_outside_ordinary_bibliography_and_guide():
    data = _data()
    text = "\n".join(
        [
            (ROOT / "docs" / "methods" / "references.md").read_text(encoding="utf-8"),
            (ROOT / "docs" / "guides" / "nonlinear-dynamics.md").read_text(
                encoding="utf-8"
            ),
        ]
    ).lower()

    for entry in data["unverified_candidates"]:
        assert entry["title"].lower() not in text
