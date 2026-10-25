"""Prepare an isolated Material navigation.prune experiment.

This file deliberately does not change mkdocs.yml or any production builder.
Fail closed if the source structure is different from the audited configuration.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "mkdocs.yml"
DEST = ROOT / ".navigation-prune-preview.mkdocs.yml"
TARGET = "build/navigation-prune-site"


def prepare(source: str) -> str:
    feature_anchor = "    - navigation.indexes\n"
    if source.count(feature_anchor) != 1:
        raise ValueError("Expected exactly one Material navigation.indexes feature")
    if "    - navigation.prune" in source:
        raise ValueError("Production already includes navigation.prune")
    if "    - navigation.expand" in source:
        raise ValueError("Pruning incompatible with navigation.expand")
    if "\nsite_dir:" in source or source.startswith("site_dir:"):
        raise ValueError("Unexpected production site_dir; avoid ambiguous output")
    # Insert a single experimental feature, preserving all other production settings.
    preview = source.replace(
        feature_anchor, feature_anchor + "    - navigation.prune\n", 1
    )
    return preview.rstrip() + f"\nsite_dir: {TARGET}\n"


def main() -> None:
    original = SOURCE.read_text(encoding="utf-8")
    generated = prepare(original)
    DEST.write_text(generated, encoding="utf-8")
    assert SOURCE.read_text(encoding="utf-8") == original
    print(f"Prepared non-deploying navigation-prune preview: {DEST.name}")


if __name__ == "__main__":
    main()
