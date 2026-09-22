"""Validate nonlinear-method evidence integrity and novelty-language contracts."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "evidence" / "nonlinear_evidence.json"
REFERENCES = ROOT / "docs" / "methods" / "references.md"
GUIDE = ROOT / "docs" / "guides" / "nonlinear-dynamics.md"
AUDIT = ROOT / "docs" / "methods" / "nonlinear-evidence-audit.md"

_ALLOWED_TIERS = {
    "direct_behavioral_gaze",
    "direct_eye_or_pupil_signal",
    "general_methodology",
}

_FORBIDDEN_SOURCE_HOST_FRAGMENTS = (
    "wikipedia.org",
    "medium.com",
)

_FORBIDDEN_NOVELTY_PHRASES = (
    "confirming novelty",
    "confirms novelty",
    "confirmed novelty",
    "proving novelty",
    "proves novelty",
    "proof of novelty",
)

_REQUIRED_IDS = {
    "anderson2013_rqa_eye_movements",
    "gurtner2019_rqa_mental_imagery",
    "korda2018_lle_eye_movements",
    "mesin2013_pupil_rqa",
    "piu2019_pupil_crqa",
    "fink2024_dynamic_pupil_methods",
    "eckmann1987_recurrence_plots",
    "marwan2007_recurrence_review",
    "coco_dale2014_crqa",
    "wallot_leonardi2018_crqa_tutorial",
    "fraser_swinney1986_ami",
    "kennel1992_fnn",
    "rosenstein1993_lle",
    "kantz1994_lle",
    "schreiber_schmitz1996_iaaft",
    "schreiber_schmitz2000_surrogates",
}


def _load() -> dict:
    return json.loads(REGISTRY.read_text(encoding="utf-8"))


def main() -> None:
    data = _load()
    verified = data.get("verified", [])
    unverified = data.get("unverified_candidates", [])

    ids = {entry["id"] for entry in verified}
    missing_required = sorted(_REQUIRED_IDS - ids)
    if missing_required:
        raise RuntimeError(
            f"nonlinear evidence registry lost required verified sources: {missing_required}"
        )
    if len(ids) != len(verified):
        raise RuntimeError("nonlinear evidence registry contains duplicate verified ids")

    bad_tiers = sorted(
        {
            entry["tier"]
            for entry in verified
            if entry["tier"] not in _ALLOWED_TIERS
        }
    )
    if bad_tiers:
        raise RuntimeError(f"invalid nonlinear evidence tiers: {bad_tiers}")

    bad_sources = sorted(
        entry["id"]
        for entry in verified
        if any(
            token in entry["verification_source"].lower()
            for token in _FORBIDDEN_SOURCE_HOST_FRAGMENTS
        )
    )
    if bad_sources:
        raise RuntimeError(
            "verified nonlinear evidence must not rely on Wikipedia/Medium: "
            f"{bad_sources}"
        )

    reference_text = REFERENCES.read_text(encoding="utf-8")
    guide_text = GUIDE.read_text(encoding="utf-8")
    audit_text = AUDIT.read_text(encoding="utf-8")

    missing_dois = sorted(
        entry["doi"]
        for entry in verified
        if entry["doi"] not in reference_text
    )
    if missing_dois:
        raise RuntimeError(
            "verified nonlinear evidence DOIs missing from references page: "
            f"{missing_dois}"
        )

    ordinary_scientific_text = "\n".join((reference_text, guide_text))
    leaked_unverified = sorted(
        entry["title"]
        for entry in unverified
        if entry["title"].lower() in ordinary_scientific_text.lower()
    )
    if leaked_unverified:
        raise RuntimeError(
            "unverified candidate citations leaked into ordinary scientific docs: "
            f"{leaked_unverified}"
        )

    audit_missing = sorted(
        entry["title"]
        for entry in unverified
        if entry["title"] not in audit_text
    )
    if audit_missing:
        raise RuntimeError(
            f"generated evidence audit lost unverified-candidate records: {audit_missing}"
        )

    scan_paths = [
        ROOT / "README.md",
        ROOT / "NONLINEAR_EVIDENCE_AUDIT.md",
        *sorted((ROOT / "docs").rglob("*.md")),
    ]
    novelty_violations: list[str] = []
    for path in scan_paths:
        text = path.read_text(encoding="utf-8").lower()
        for phrase in _FORBIDDEN_NOVELTY_PHRASES:
            if phrase in text:
                novelty_violations.append(
                    f"{path.relative_to(ROOT)} contains {phrase!r}"
                )
    if novelty_violations:
        raise RuntimeError(
            "failed-search novelty claims are prohibited: "
            + "; ".join(novelty_violations)
        )

    required_guide_language = (
        "direct eye-movement signal-analysis precedent",
        "not independent observations",
        "Do not call it a monodromy matrix",
    )
    missing_guide_language = [
        phrase for phrase in required_guide_language if phrase not in guide_text
    ]
    if missing_guide_language:
        raise RuntimeError(
            "nonlinear guide lost required interpretation boundaries: "
            f"{missing_guide_language}"
        )

    print(
        "nonlinear evidence integrity OK: "
        f"{len(verified)} verified sources, "
        f"{len(unverified)} unverified candidates, "
        f"{len(_REQUIRED_IDS)} required evidence anchors"
    )


if __name__ == "__main__":
    main()
