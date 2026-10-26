"""Prepare three reproducible, strictly non-deploying site design variants.

Two candidates retain the exact MkDocs Material generator; the third uses
Zensical 0.0.72 with its documented modern theme. No production config, docs
or generated Pages site is rewritten. We operate on raw YAML text because the
source includes pymdown Python-name YAML tags.
"""
from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRODUCTION = ROOT / "mkdocs.yml"
STYLES = {
    "scientific": "assets/design-previews/scientific-portal.css",
    "developer": "assets/design-previews/developer-docs.css",
}
NAMES = ("scientific", "developer", "zensical-modern")
THEME = "theme:\n  name: material\n"
CSS_ANCHOR = "  - assets/accessibility-refinements.css\n"


def prepare(original: str, variant: str) -> str:
    if variant not in NAMES:
        raise ValueError(f"Unknown candidate {variant}")
    if original.count(THEME) != 1 or original.count(CSS_ANCHOR) != 1:
        raise ValueError("Theme declaration or final stylesheet has changed")
    if "\nsite_dir:" in original or original.startswith("site_dir:"):
        raise ValueError("Refuse to override an existing production site_dir")
    if variant == "zensical-modern":
        if "\nhooks:" in original:
            raise ValueError("Zensical does not support MkDocs hooks")
        candidate = original.replace(THEME, THEME + "  variant: modern\n", 1)
        candidate = candidate.replace(
            CSS_ANCHOR,
            CSS_ANCHOR + "  - assets/design-previews/zensical-modern-contrast.css\n",
            1,
        )
    else:
        css_path = STYLES[variant]
        if not (ROOT / "docs" / css_path).is_file():
            raise FileNotFoundError(css_path)
        candidate = original.replace(CSS_ANCHOR, CSS_ANCHOR + f"  - {css_path}\n", 1)
    return "site_dir: build/design-previews/" + variant + "\n" + candidate


def main() -> None:
    original = PRODUCTION.read_text(encoding="utf-8")
    outputs = {}
    for variant in NAMES:
        file = ROOT / f".design-{variant}.mkdocs.yml"
        file.write_text(prepare(original, variant), encoding="utf-8")
        outputs[variant] = str(file.relative_to(ROOT))
    assert PRODUCTION.read_text(encoding="utf-8") == original
    print("Isolated configuration files: " + ", ".join(outputs.values()))
    print("No production builder, stylesheet order or published URLs changed.")


if __name__ == "__main__":
    main()
