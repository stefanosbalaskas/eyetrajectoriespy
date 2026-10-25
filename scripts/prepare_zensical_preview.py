"""Create a reversible Zensical classic-theme build config (never production).

Reads the repository's canonical mkdocs.yml as text to preserve !python/name
YAML tags. Does not rewrite, deploy or change mkdocs.yml.
"""
from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "mkdocs.yml"
PREVIEW = ROOT / ".zensical-preview.mkdocs.yml"

def main() -> None:
    config = CANONICAL.read_text(encoding="utf-8")
    if config.count("theme:\n  name: material\n") != 1:
        raise ValueError("Canonical MkDocs Material theme declaration has changed.")
    if "hooks:" in config:
        raise ValueError("Zensical presently lacks MkDocs hooks support: reject preview.")
    if "\nsite_dir:" in config:
        raise ValueError("Explicit existing site_dir: review before writing preview output.")
    if "  - mkdocstrings:" not in config or "  - search\n" not in config:
        raise ValueError("Known source search/mkdocstrings plugins absent; review preview assumptions.")
    # Use same docs_dir/src paths and identical MkDocs config except the two
    # preview-specific settings: a classic theme and isolated output folder.
    preview = "site_dir: build/zensical-preview-site\n" + config.replace(
        "theme:\n  name: material\n",
        "theme:\n  name: material\n  variant: classic\n",
        1,
    )
    PREVIEW.write_text(preview, encoding="utf-8")
    print(f"Prepared isolated {PREVIEW.name} from canonical mkdocs.yml.")
    print("Production mkdocs.yml and deployed site/ are untouched.")

if __name__ == "__main__":
    main()
