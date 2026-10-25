"""Generate two independent, nondeploying MkDocs navigation builds.

Always build both the unpruned baseline and the navigation.prune candidate from
the SAME production configuration, regardless of which mode is deployed.
This makes the experiment a permanent rollback regression after promotion.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "mkdocs.yml"
UNPRUNED = ROOT / ".navigation-unpruned-preview.mkdocs.yml"
PRUNED = ROOT / ".navigation-prune-preview.mkdocs.yml"
ANCHOR = "    - navigation.indexes\n"
FEATURE = "    - navigation.prune\n"


def prepare(source: str, *, pruned: bool) -> str:
    if source.count(ANCHOR) != 1:
        raise ValueError("Expected exactly one Material navigation.indexes feature")
    if source.count(FEATURE) > 1:
        raise ValueError("Duplicate navigation.prune flags")
    if "    - navigation.expand" in source:
        raise ValueError("Pruning incompatible with navigation.expand")
    if "\nsite_dir:" in source or source.startswith("site_dir:"):
        raise ValueError("Unexpected production site_dir; cannot isolate builds")
    # Retain one and only one feature when pruned; omit it otherwise. A comment
    # immediately above the feature may remain as a harmless YAML comment.
    stripped = source.replace(FEATURE, "")
    if pruned:
        stripped = stripped.replace(ANCHOR, ANCHOR + FEATURE, 1)
    target = "build/navigation-prune-site" if pruned else "build/navigation-baseline-site"
    return stripped.rstrip() + f"\nsite_dir: {target}\n"


def main() -> None:
    original = SOURCE.read_text(encoding="utf-8")
    UNPRUNED.write_text(prepare(original, pruned=False), encoding="utf-8")
    PRUNED.write_text(prepare(original, pruned=True), encoding="utf-8")
    if SOURCE.read_text(encoding="utf-8") != original:
        raise AssertionError("Generator cannot modify the production MkDocs config")
    print(f"Paired isolated builds ready: {UNPRUNED.name}; {PRUNED.name}")
    print(f"Production flag enabled: {FEATURE in original}")


if __name__ == "__main__":
    main()
