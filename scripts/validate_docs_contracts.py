"""Run documentation-contract validation against composed MkDocs sources."""

from __future__ import annotations

from pathlib import Path

from _validate_docs_contracts_base import main as _base_main


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


def main() -> None:
    Path.read_text = _snippet_aware_read_text
    try:
        _base_main()
    finally:
        Path.read_text = _ORIGINAL_READ_TEXT


if __name__ == "__main__":
    main()
