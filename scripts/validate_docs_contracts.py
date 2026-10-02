"""Run documentation-contract validation against composed MkDocs sources."""

from __future__ import annotations

from pathlib import Path

import eyetrajectoriespy as et

from _validate_docs_contracts_base import main as _base_main
from docs_gallery_manifest import GALLERY_CATEGORIES, GALLERY_PLOTS


ROOT = Path(__file__).resolve().parents[1]
MATH_PAGE = (ROOT / "docs" / "methods" / "mathematical-reference.md").resolve()
MATH_BASE = (ROOT / "docs" / "methods" / "mathematical-reference-base.md").resolve()
_ORIGINAL_READ_TEXT = Path.read_text


def _snippet_aware_read_text(self: Path, *args, **kwargs) -> str:
    """Expose the rendered mathematical-reference surface to source validation."""

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
    return text


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
        if not all(entry.get(key, "").strip() for key in ("asset", "category", "quantity", "equation", "example"))
    )
    if missing_metadata:
        raise RuntimeError(
            "gallery manifest entries require asset/category/quantity/equation/example: "
            f"{missing_metadata}"
        )

    print(
        "plot gallery manifest OK: "
        f"{len(public_plots)} public plotting APIs, exact coverage"
    )


def main() -> None:
    Path.read_text = _snippet_aware_read_text
    try:
        _base_main()
        _validate_complete_gallery_manifest()
    finally:
        Path.read_text = _ORIGINAL_READ_TEXT


if __name__ == "__main__":
    main()
