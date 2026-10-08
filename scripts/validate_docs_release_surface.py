"""Check public documentation versions, candidate availability, and README SVGs."""

from __future__ import annotations

import json
from pathlib import Path
import re
import tomllib

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    status = json.loads((ROOT / "docs/release-surface.json").read_text(encoding="utf-8"))
    release = json.loads((ROOT / "RELEASE_READINESS.json").read_text(encoding="utf-8"))
    api = json.loads((ROOT / "WORKFLOW_API_AUDIT.json").read_text(encoding="utf-8"))
    with (ROOT / "pyproject.toml").open("rb") as f:
        source_version = tomllib.load(f)["project"]["version"]

    stable = status["published_stable_version"]
    assert re.fullmatch(r"\d+\.\d+\.\d+", stable)
    assert status["current_candidate_version"] == source_version == release["current_development_version"]
    assert status["candidate_published"] is False
    assert status["public_workflow_availability"] == "candidate_source_only"
    # The separate release-governance validator owns publication interlocks.
    # An armed-but-unpublished RC remains unpublished: this docs audit must not
    # block a later governance-only arming PR by assuming flags stay false.
    assert release["production_release_ready"] == release["github_release_ready"]
    assert not api["root_exports_promoted"]

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    home = (ROOT / "docs/index.md").read_text(encoding="utf-8")
    roadmap = (ROOT / "docs/methods/status-roadmap.md").read_text(encoding="utf-8")
    guide = (ROOT / "docs/workflows/workflow-orchestration.md").read_text(encoding="utf-8")
    for name, content in (("README", readme), ("website homepage", home)):
        assert stable in content and source_version in content, f"{name} version drift"
        assert f"eyetrajectoriespy=={stable}" in content, f"{name} stable install mismatch"
        assert "candidate" in content.lower(), f"{name} missing candidate status"

    assert f"The current release-candidate line is **{source_version}**." in roadmap
    assert stable in roadmap
    assert "pip install eyetrajectoriespy" in guide
    assert "not" in guide.lower() and "candidate" in guide.lower()

    figures = re.findall(r"!\[[^\]]*\]\(([^)]+\.svg)\)", readme)
    # Shields.io version/status badges are intentionally remote and independent
    # of the scientific gallery. All non-badge illustrative SVGs must be local.
    figures = [fig for fig in figures if not fig.startswith("https://img.shields.io/")]
    assert figures, "README must display at least one available SVG"
    for fig in figures:
        assert not fig.startswith(("http://", "https://")), "README illustrations must be repo-relative"
        image = (ROOT / fig).resolve()
        assert image.is_relative_to(ROOT) and image.is_file(), f"README image is untracked: {fig}"

    for path in ("docs/articles/choosing-the-ten-workflows.md",
                 "docs/articles/reproducible-workflow-bundles.md"):
        content = (ROOT / path).read_text(encoding="utf-8")
        assert stable in content and "candidate" in content.lower() and "not" in content.lower()

    print(f"PASS stable={stable} source={source_version} candidate unpublished; README SVGs={len(figures)}")


if __name__ == "__main__":
    main()
