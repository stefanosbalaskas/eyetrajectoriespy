"""Generate an isolated, reversible Zensical Modern build from the live docs config.

The single source of truth is mkdocs.yml: do not duplicate 370 navigation
routes or alter scientific content. The Material builder remains available for
reference and rollback until the browser/search parity gate qualifies.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "mkdocs.yml"
GENERATED = ROOT / ".zensical-modern.generated.mkdocs.yml"

def generate(destination: str = "build/zensical-modern") -> Path:
    original = SOURCE.read_text(encoding="utf-8")
    theme = "theme:\n  name: material\n"
    old_css = "  - assets/site-design-scientific-portal.css\n"
    anchor = "  - assets/accessibility-refinements.css\n"
    assert original.count(theme) == 1, "Material theme anchor unexpectedly changed"
    assert original.count(old_css) == 1, "Existing portal CSS registration changed"
    assert original.count(anchor) == 1, "Stylesheet ordering anchor changed"
    assert "\nhooks:" not in original, "Zensical does not support MkDocs hooks"
    assert not original.startswith("site_dir:") and "\nsite_dir:" not in original
    assert (ROOT / "docs/assets/site-design-zensical-modern.css").is_file()
    candidate = original.replace(theme, theme + "  variant: modern\n", 1)
    candidate = candidate.replace(old_css, "", 1)
    candidate = candidate.replace(
        anchor, anchor + "  - assets/site-design-zensical-modern.css\n", 1
    )
    GENERATED.write_text("site_dir: " + destination + "\n" + candidate, encoding="utf-8")
    assert SOURCE.read_text(encoding="utf-8") == original
    return GENERATED

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--site-dir", default="build/zensical-modern")
    parser.add_argument("--build", action="store_true")
    args = parser.parse_args()
    config = generate(args.site_dir)
    print(f"Reversible selected right-hand design: Zensical Modern, config {config}")
    if args.build:
        subprocess.run(["zensical", "build", "--strict", "--config-file",
                        str(config)], cwd=ROOT, check=True)

if __name__ == "__main__":
    main()
