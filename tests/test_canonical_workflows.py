import json
from pathlib import Path

import eyetrajectoriespy as et


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "CANONICAL_WORKFLOWS.json"


def test_canonical_workflow_manifest_is_complete_and_public():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))

    assert data["schema_version"] == 1
    assert data["package_version"] == et.__version__

    workflows = data["workflows"]
    ids = [workflow["id"] for workflow in workflows]
    assert ids == [
        "fpca-exploration",
        "experimental-functional-regression",
        "repeated-trial-mixed-effects",
        "generalized-responses",
        "nonlinear-recurrence",
    ]
    assert len(ids) == len(set(ids))

    public = set(et.__all__)
    allowed_levels = {"canonical", "advanced", "diagnostic", "experimental"}

    for workflow in workflows:
        assert workflow["level"] in allowed_levels
        docs_path = ROOT / workflow["docs"]
        assert docs_path.is_file()

        for role in (
            "entry_points",
            "bootstrap",
            "summaries",
            "reporting",
            "advanced_branches",
            "diagnostic_branches",
            "experimental_branches",
        ):
            for name in workflow.get(role, []):
                assert name in public
                assert hasattr(et, name)

        for name in workflow.get("bootstrap", []):
            assert name.startswith("bootstrap_")
        for name in workflow.get("reporting", []):
            assert name.endswith("_reporting_text")


def test_canonical_workflows_do_not_create_namespace_aliases():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    declared = []
    for workflow in data["workflows"]:
        for role in (
            "entry_points",
            "bootstrap",
            "summaries",
            "reporting",
            "advanced_branches",
            "diagnostic_branches",
            "experimental_branches",
        ):
            declared.extend(workflow.get(role, []))

    # The manifest classifies existing public APIs; 0.55 does not introduce a
    # second wrapper namespace or duplicate aliases solely for documentation.
    assert len(declared) == len(set(declared))
