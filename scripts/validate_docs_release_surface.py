"""Validate active public release status against the published 1.2.0 source."""

from __future__ import annotations
import json
from pathlib import Path
import re
import tomllib

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    status = json.loads((ROOT / "docs/release-surface.json").read_text(encoding="utf-8"))
    readiness = json.loads((ROOT / "RELEASE_READINESS.json").read_text(encoding="utf-8"))
    api = json.loads((ROOT / "WORKFLOW_API_AUDIT.json").read_text(encoding="utf-8"))
    with (ROOT / "pyproject.toml").open("rb") as f:
        source_version = tomllib.load(f)["project"]["version"]

    assert status["schema_version"] == 2
    stable = status["published_stable_version"]
    assert re.fullmatch(r"\d+\.\d+\.\d+", stable)
    assert stable == status["current_source_version"] == source_version
    assert source_version == readiness["current_development_version"]
    assert status["source_published"] is True
    assert status["previous_stable_version"] == "1.1.0"
    assert status["public_workflow_availability"] == "published_stable_module_scoped"
    assert status["experimental_workflow_helpers_stable"] is False
    assert status["github_release_url"].endswith("/releases/tag/v1.2.0")
    assert status["pypi_release_url"].endswith("/eyetrajectoriespy/1.2.0/")
    assert readiness["production_release_ready"] is readiness["github_release_ready"] is False
    assert not api["root_exports_promoted"]

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    home = (ROOT / "docs/index.md").read_text(encoding="utf-8")
    start = (ROOT / "docs/start/index.md").read_text(encoding="utf-8")
    quick = (ROOT / "docs/quickstart.md").read_text(encoding="utf-8")
    release_status = (ROOT / "docs/news/release-status.md").read_text(encoding="utf-8")
    for name, content in (("README",readme),("home",home),("start",start),("quickstart",quick),("release status",release_status)):
        assert stable in content, f"{name} missing stable version"
        assert f"eyetrajectoriespy=={stable}" in content, f"{name} stable install mismatch"
        assert "experimental" in content.lower() or name in {"quickstart","release status"}, f"{name} omits scientific scope"
        assert "unpublished 1.2" not in content.lower(), f"{name} stale release status"

    roadmap = (ROOT / "docs/methods/status-roadmap.md").read_text(encoding="utf-8")
    assert "current stable production release is **1.2.0**" in roadmap
    assert "24 October 2026" in roadmap
    assert "1.1.0" in roadmap

    guide = (ROOT / "docs/workflows/workflow-orchestration.md").read_text(encoding="utf-8")
    assert "pip install eyetrajectoriespy==1.2.0" in guide
    assert "module-scoped" in guide
    assert "experimental" in guide.lower()
    for path in ("docs/articles/choosing-the-ten-workflows.md","docs/articles/reproducible-workflow-bundles.md"):
        content = (ROOT / path).read_text(encoding="utf-8")
        assert "1.2.0" in content and "pip install eyetrajectoriespy==1.2.0" in content

    figures = re.findall(r"!\[[^\]]*\]\(([^)]+\.svg)\)", readme)
    figures = [fig for fig in figures if not fig.startswith("https://img.shields.io/")]
    assert figures, "README has no local diagram"
    for fig in figures:
        assert not fig.startswith(("http://","https://"))
        image = (ROOT / fig).resolve()
        assert image.is_relative_to(ROOT) and image.is_file(), f"README image is untracked: {fig}"
    print(f"PASS stable={stable} published status + scope; README SVGs={len(figures)}")


if __name__ == "__main__":
    main()
