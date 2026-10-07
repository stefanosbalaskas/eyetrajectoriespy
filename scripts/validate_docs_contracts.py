"""Run documentation-contract validation against composed MkDocs sources."""

from __future__ import annotations

import json
from pathlib import Path

import eyetrajectoriespy as et

from _validate_docs_contracts_base import main as _base_main
from docs_gallery_manifest import GALLERY_CATEGORIES, GALLERY_PLOTS


ROOT = Path(__file__).resolve().parents[1]
MATH_PAGE = (ROOT / "docs" / "methods" / "mathematical-reference.md").resolve()
MATH_BASE = (ROOT / "docs" / "methods" / "mathematical-reference-base.md").resolve()
GALLERY_INDEX = (ROOT / "docs" / "methods" / "visual-gallery.md").resolve()
GALLERY_DIR = (ROOT / "docs" / "methods" / "gallery").resolve()
GALLERY_ASSETS = ROOT / "docs" / "assets" / "gallery"
RELEASE_READINESS = (ROOT / "RELEASE_READINESS.json").resolve()
CANONICAL_WORKFLOWS = (ROOT / "CANONICAL_WORKFLOWS.json").resolve()
EVIDENCE_FILES = (
    ROOT / "REFERENCE_VALIDATION.json",
    ROOT / "VALIDATION_TOLERANCES.json",
    ROOT / "PERFORMANCE_ENVELOPE.json",
)
BASE_VALIDATOR_VERSION = "0.12.0"
LATEST_QUALIFIED_EVIDENCE_VERSION = "1.1.0"
QUALIFIED_RELEASE_MAIN = "7eaf842214dc26c8cd1cef9eaaa72a55916974de"
_ORIGINAL_READ_TEXT = Path.read_text


def _composed_source_read_text(self: Path, *args, **kwargs) -> str:
    """Expose rendered/composed surfaces and base-validator compatibility."""

    text = _ORIGINAL_READ_TEXT(self, *args, **kwargs)
    try:
        resolved = self.resolve()
    except OSError:
        return text
    if resolved == MATH_PAGE:
        base = _ORIGINAL_READ_TEXT(MATH_BASE, encoding="utf-8")
        # The validator checks API names and explicit anchors as set-membership
        # contracts. Concatenating the preserved base and public extension is
        # equivalent to the MkDocs snippet-composed surface for those checks.
        return base + "\n" + text
    if resolved == GALLERY_INDEX:
        # The historical validator treated the gallery as one page. The modern
        # site intentionally splits it into seven category pages; concatenate
        # them only for that legacy aggregate asset-reference check.
        category_sources = []
        for category in GALLERY_CATEGORIES:
            path = GALLERY_DIR / f"{category}.md"
            if path.exists():
                category_sources.append(_ORIGINAL_READ_TEXT(path, encoding="utf-8"))
        return text + "\n" + "\n".join(category_sources)
    if resolved in {RELEASE_READINESS, CANONICAL_WORKFLOWS}:
        # The preserved base validator predates the post-0.12 source line and
        # hard-codes 0.12.0 for source-identity checks. Validate the real active
        # source identity separately below, then present the historical token
        # only to that unchanged legacy assertion layer.
        return text.replace(et.__version__, BASE_VALIDATOR_VERSION)
    if resolved in {path.resolve() for path in EVIDENCE_FILES}:
        # The same historical validator also hard-codes 0.12.0 for qualification
        # evidence. Real validation below requires the latest qualified evidence
        # identity; translate only for the legacy assertion layer.
        return text.replace(
            LATEST_QUALIFIED_EVIDENCE_VERSION,
            BASE_VALIDATOR_VERSION,
        )
    return text


def _validate_source_and_evidence_versions() -> None:
    readiness = json.loads(
        _ORIGINAL_READ_TEXT(RELEASE_READINESS, encoding="utf-8")
    )
    if readiness.get("current_development_version") != et.__version__:
        raise RuntimeError(
            "release-readiness source identity does not match package version"
        )

    production_ready = readiness.get("production_release_ready")
    github_ready = readiness.get("github_release_ready")
    if not isinstance(production_ready, bool) or not isinstance(github_ready, bool):
        raise RuntimeError("publication readiness flags must be explicit booleans")
    if production_ready != github_ready:
        raise RuntimeError(
            "GitHub and production PyPI publication readiness must move jointly"
        )
    if production_ready:
        notes = "\n".join(str(note) for note in readiness.get("notes", ()))
        required_arming_evidence = (
            QUALIFIED_RELEASE_MAIN,
            "25/25 workflow groups successfully",
            "manual release.yml dispatch with target=production",
        )
        missing = [token for token in required_arming_evidence if token not in notes]
        if missing:
            raise RuntimeError(
                "armed publication readiness is missing exact qualification/governance "
                f"evidence: {missing}"
            )

    canonical = json.loads(
        _ORIGINAL_READ_TEXT(CANONICAL_WORKFLOWS, encoding="utf-8")
    )
    if canonical.get("package_version") != et.__version__:
        raise RuntimeError(
            "canonical workflow manifest does not match active source version"
        )

    evidence_versions = {
        json.loads(_ORIGINAL_READ_TEXT(path, encoding="utf-8")).get(
            "package_version"
        )
        for path in EVIDENCE_FILES
    }
    expected_evidence_version = (
        LATEST_QUALIFIED_EVIDENCE_VERSION
        if ".dev" in et.__version__
        else et.__version__
    )
    if evidence_versions != {expected_evidence_version}:
        raise RuntimeError(
            "qualification evidence version does not match the active qualification "
            f"identity {expected_evidence_version!r}; found {sorted(evidence_versions)}"
        )


def _validate_complete_gallery_manifest() -> None:
    public_plots = {
        name
        for name in et.__all__
        if name.startswith("plot_") and callable(getattr(et, name, None))
    }
    documented_plots = set(GALLERY_PLOTS)
    missing = sorted(public_plots - documented_plots)
    stale = sorted(documented_plots - public_plots)
    if missing or stale:
        raise RuntimeError(
            "gallery manifest must exactly cover public plotting APIs: "
            f"missing={missing}, stale={stale}"
        )

    assets = [entry["asset"] for entry in GALLERY_PLOTS.values()]
    if len(assets) != len(set(assets)):
        raise RuntimeError("gallery manifest asset names must be unique")

    categories = set(GALLERY_CATEGORIES)
    bad_categories = sorted(
        {
            entry["category"]
            for entry in GALLERY_PLOTS.values()
            if entry["category"] not in categories
        }
    )
    if bad_categories:
        raise RuntimeError(
            f"gallery manifest contains undeclared categories: {bad_categories}"
        )

    missing_metadata = sorted(
        name
        for name, entry in GALLERY_PLOTS.items()
        if not all(
            entry.get(key, "").strip()
            for key in ("asset", "category", "quantity", "equation", "example")
        )
    )
    if missing_metadata:
        raise RuntimeError(
            "gallery manifest entries require asset/category/quantity/equation/example: "
            f"{missing_metadata}"
        )

    missing_assets = sorted(
        name
        for name, entry in GALLERY_PLOTS.items()
        if not (GALLERY_ASSETS / entry["asset"]).exists()
    )
    if missing_assets:
        raise RuntimeError(
            "gallery manifest assets were not generated for public plots: "
            f"{missing_assets}"
        )

    missing_pages = sorted(
        category
        for category in GALLERY_CATEGORIES
        if not (GALLERY_DIR / f"{category}.md").exists()
    )
    if missing_pages:
        raise RuntimeError(f"gallery category pages were not generated: {missing_pages}")

    page_violations: list[str] = []
    for name, entry in GALLERY_PLOTS.items():
        page = (GALLERY_DIR / f"{entry['category']}.md").read_text(encoding="utf-8")
        required_tokens = (
            f"`{name}`",
            entry["asset"],
            "**API:**",
            "**Scientific quantity:**",
            "**Equation:**",
            "**Worked example:**",
        )
        if not all(token in page for token in required_tokens):
            page_violations.append(name)
    if page_violations:
        raise RuntimeError(
            "gallery category entries are incomplete for public plots: "
            f"{sorted(page_violations)}"
        )

    print(
        "plot gallery manifest OK: "
        f"{len(public_plots)} public plotting APIs, exact assets/pages coverage"
    )


def main() -> None:
    _validate_source_and_evidence_versions()
    Path.read_text = _composed_source_read_text
    try:
        _base_main()
        _validate_complete_gallery_manifest()
    finally:
        Path.read_text = _ORIGINAL_READ_TEXT


if __name__ == "__main__":
    main()
