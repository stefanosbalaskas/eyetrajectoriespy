"""Generate auditable nonlinear-method evidence pages from the JSON registry."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "evidence" / "nonlinear_evidence.json"
ROOT_OUTPUT = ROOT / "NONLINEAR_EVIDENCE_AUDIT.md"
SITE_OUTPUT = ROOT / "docs" / "methods" / "nonlinear-evidence-audit.md"
TICK = chr(96)

_ALLOWED_TIERS = {
    "direct_behavioral_gaze",
    "direct_eye_or_pupil_signal",
    "general_methodology",
}


def _load() -> dict:
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        raise RuntimeError("unsupported nonlinear evidence schema_version")
    if not data.get("audit_date"):
        raise RuntimeError("nonlinear evidence audit_date is required")
    verified = data.get("verified", [])
    if not verified:
        raise RuntimeError("nonlinear evidence registry has no verified entries")
    identifiers = [entry.get("id") for entry in verified]
    if any(not value for value in identifiers):
        raise RuntimeError("every verified nonlinear evidence entry needs an id")
    duplicates = sorted(
        identifier
        for identifier, count in Counter(identifiers).items()
        if count > 1
    )
    if duplicates:
        raise RuntimeError(f"duplicate nonlinear evidence ids: {duplicates}")
    dois = [entry.get("doi", "").lower() for entry in verified]
    duplicate_dois = sorted(
        doi for doi, count in Counter(dois).items() if doi and count > 1
    )
    if duplicate_dois:
        raise RuntimeError(f"duplicate nonlinear evidence DOIs: {duplicate_dois}")

    required = {
        "id",
        "tier",
        "method_tags",
        "citation",
        "doi",
        "verification_source",
        "supports",
        "does_not_support",
    }
    for entry in verified:
        missing = sorted(required - set(entry))
        if missing:
            raise RuntimeError(
                f"verified nonlinear evidence entry {entry.get('id')!r} "
                f"is missing fields: {missing}"
            )
        if entry["tier"] not in _ALLOWED_TIERS:
            raise RuntimeError(
                f"invalid evidence tier {entry['tier']!r} for {entry['id']}"
            )
        if not entry["doi"] or "/" not in entry["doi"]:
            raise RuntimeError(f"invalid DOI for {entry['id']}")
        if not entry["method_tags"]:
            raise RuntimeError(f"method_tags cannot be empty for {entry['id']}")

    for entry in data.get("unverified_candidates", []):
        if entry.get("status") != "not_verified_in_2026-09-23_audit":
            raise RuntimeError(
                "unverified candidates must retain the explicit audit status"
            )
        if not entry.get("title") or not entry.get("note"):
            raise RuntimeError("unverified candidates need a title and note")
    return data


def _tier_title(tier: str) -> str:
    return {
        "direct_behavioral_gaze": "Direct behavioral-gaze evidence",
        "direct_eye_or_pupil_signal": "Direct eye/pupil signal evidence",
        "general_methodology": "General methodological evidence",
    }[tier]


def _render(data: dict, *, site: bool) -> str:
    lines: list[str] = []
    if site:
        lines += ["---", "title: Nonlinear evidence audit", "---", ""]
    lines += [
        "# Nonlinear evidence audit",
        "",
        f"**Audit date:** {data['audit_date']}",
        "",
        data["scope"],
        "",
        "## Evidence rule",
        "",
        data["interpretation_rule"],
        "",
        "The evidence tiers are intentionally descriptive:",
        "",
    ]
    for key in (
        "direct_behavioral_gaze",
        "direct_eye_or_pupil_signal",
        "general_methodology",
    ):
        lines.append(f"- **{_tier_title(key)}:** {data['evidence_tiers'][key]}")
    lines += [
        "",
        "A verified citation supports only the claim stated in **Supports**. "
        "The **Does not support** field is part of the scientific contract and "
        "prevents a nearby real paper from being used to justify a stronger claim.",
        "",
    ]

    for tier in (
        "direct_behavioral_gaze",
        "direct_eye_or_pupil_signal",
        "general_methodology",
    ):
        lines += [f"## {_tier_title(tier)}", ""]
        for entry in data["verified"]:
            if entry["tier"] != tier:
                continue
            tags = ", ".join(f"{TICK}{tag}{TICK}" for tag in entry["method_tags"])
            lines += [
                f"### {entry['citation']}",
                "",
                f"- **DOI:** https://doi.org/{entry['doi']}",
                f"- **Method tags:** {tags}",
                f"- **Verification source:** {entry['verification_source']}",
                f"- **Supports:** {entry['supports']}",
                f"- **Does not support:** {entry['does_not_support']}",
                "",
            ]

    lines += [
        "## Unverified candidate citations from the research report",
        "",
        "The following entries were present in the supplied research report but "
        "were not recovered by the exact-title/author verification pass used for "
        "this audit. They are **not treated as false citations**, and their absence "
        "from this search is **not evidence of novelty or nonexistence**. They are "
        "excluded from the package bibliography unless independently verified.",
        "",
    ]
    for entry in data.get("unverified_candidates", []):
        lines += [
            f"### {entry['title']}",
            "",
            f"- **Attributed authors:** {entry['attributed_authors']}",
            f"- **Attributed year:** {entry['attributed_year']}",
            f"- **Audit status:** {TICK}{entry['status']}{TICK}",
            f"- **Action:** {entry['note']}",
            "",
        ]

    lines += [
        "## Package evidence hierarchy",
        "",
        f"1. **Embedding + recurrence/RQA:** core methodology with direct behavioral eye-movement precedent.",
        f"2. **Local divergence / Rosenstein LLE + surrogate testing:** advanced methodology; LLE has direct eye-movement signal precedent, but behavioral-scanpath interpretation remains conditional and requires stronger safeguards.",
        f"3. **Empirical Poincare return-map stability:** experimental observational descriptor; no claim of classical Floquet stability is made.",
        f"4. **Classical Floquet, monodromy, numerical continuation, SINDy/Koopman/neural ODEs:** outside the raw-gaze core unless an explicit validated dynamical model is introduced.",
        "",
        "## Novelty language",
        "",
        "The package does not infer novelty from a failed literature or package search. "
        'Allowed wording is limited to statements such as "no implementation was '
        'identified in the searches performed" or "not verified in this audit."',
        "",
    ]
    if site:
        lines += [
            "See also the [nonlinear dynamics guide](../guides/nonlinear-dynamics.md), "
            "[method comparison](method-comparison.md), and [references](references.md).",
            "",
        ]
    else:
        lines += [
            "Website evidence page: "
            "https://stefanosbalaskas.github.io/eyetrajectoriespy/methods/nonlinear-evidence-audit/",
            "",
        ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail when committed generated evidence pages differ from the registry",
    )
    args = parser.parse_args()

    data = _load()
    outputs = {
        ROOT_OUTPUT: _render(data, site=False),
        SITE_OUTPUT: _render(data, site=True),
    }
    stale: list[str] = []
    for path, expected in outputs.items():
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != expected:
                stale.append(str(path.relative_to(ROOT)))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(expected, encoding="utf-8")

    if stale:
        raise RuntimeError(
            "generated nonlinear evidence pages are stale: "
            + ", ".join(stale)
            + "; run python scripts/generate_nonlinear_evidence_audit.py"
        )
    print(
        "nonlinear evidence audit OK: "
        f"{len(data['verified'])} verified sources, "
        f"{len(data.get('unverified_candidates', []))} unverified candidates"
    )


if __name__ == "__main__":
    main()
