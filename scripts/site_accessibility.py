"""Automated a11y triage for representative built documentation pages.

Uses local axe-core shipped only to the optional browser-test CI job.
No third-party scripts or participant data are sent from the documentation.
Axe automated checks do not certify WCAG conformance.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AXE_PATH = ROOT / "build/site-accessibility/node_modules/axe-core/axe.min.js"
TAGS = ("wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa")


def inspect(page, *, route: str, viewport: str) -> dict:
    if not AXE_PATH.is_file():
        raise FileNotFoundError("Install the pinned local-only axe-core for the browser QA job.")
    page.add_script_tag(path=str(AXE_PATH))
    result = page.evaluate("""async (tags) => {
      const {violations, incomplete, passes} = await window.axe.run(document, {
        runOnly: {type: "tag", values: tags},
        resultTypes: ["violations", "incomplete", "passes"],
      });
      return {
        passes: passes.length,
        needsManualReview: incomplete.length,
        issues: violations.map(v => ({
          id:v.id, impact:v.impact, help:v.help,
          nodes:v.nodes.slice(0, 8).map(n => ({target:n.target, summary:n.failureSummary}))
        }))
      };
    }""", list(TAGS))
    issues = result.get("issues", [])
    result["route"] = route
    result["viewport"] = viewport
    result["highImpact"] = sum(v.get("impact") in ("serious", "critical") for v in issues)
    # Do not mark the site WCAG compliant because checks returned no violations:
    result["disclaimer"] = "Automated snapshot only; manual keyboard/screen-reader review still required."
    return result
