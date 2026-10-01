"""One-shot, fail-closed identity alignment for the 0.12.0rc1 qualification branch.

Temporary branch tooling only. PERFORMANCE_ENVELOPE.json is deliberately left
at 0.11.0 until fresh exact-version RC performance evidence is generated.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = "0.12.0rc1"
OLD = "0.11.0"


def replace_exact(path: str, old: str, new: str, count: int = 1) -> None:
    file_path = ROOT / path
    text = file_path.read_text(encoding="utf-8")
    observed = text.count(old)
    if observed != count:
        raise RuntimeError(
            f"{path}: expected {count} occurrences of {old!r}, found {observed}"
        )
    file_path.write_text(text.replace(old, new), encoding="utf-8")


def set_json_version(path: str) -> None:
    file_path = ROOT / path
    payload = json.loads(file_path.read_text(encoding="utf-8"))
    if payload.get("package_version") != OLD:
        raise RuntimeError(
            f"{path}: expected package_version={OLD!r}, got "
            f"{payload.get('package_version')!r}"
        )
    payload["package_version"] = TARGET
    file_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    if f'version = "{TARGET}"' not in pyproject:
        raise RuntimeError("pyproject.toml is not aligned to 0.12.0rc1")
    citation = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    if f"version: {TARGET}" not in citation:
        raise RuntimeError("CITATION.cff is not aligned to 0.12.0rc1")

    replace_exact(
        "src/eyetrajectoriespy/__init__.py",
        f'__version__ = "{OLD}"',
        f'__version__ = "{TARGET}"',
    )
    replace_exact(
        "tests/test_public_api.py",
        f'assert et.__version__=="{OLD}"',
        f'assert et.__version__=="{TARGET}"',
    )

    for path in (
        "CANONICAL_WORKFLOWS.json",
        "REFERENCE_VALIDATION.json",
        "VALIDATION_TOLERANCES.json",
    ):
        set_json_version(path)

    readiness_path = ROOT / "RELEASE_READINESS.json"
    readiness = json.loads(readiness_path.read_text(encoding="utf-8"))
    if readiness.get("current_development_version") != OLD:
        raise RuntimeError("RELEASE_READINESS.json version anchor changed")
    for gate in (
        "sparse_mfpca_recovery_qualified",
        "sparse_mfpca_comparator_sensitivity_recorded",
        "sparse_mfpca_observation_stress_recorded",
        "sparse_mfpca_performance_qualified",
    ):
        if readiness.get("gates", {}).get(gate) is not True:
            raise RuntimeError(f"required pre-RC gate is not qualified: {gate}")
    readiness["current_development_version"] = TARGET
    readiness["production_release_ready"] = False
    readiness["github_release_ready"] = False
    readiness["gates"]["sparse_mfpca_rc_exact_version_performance_qualified"] = False
    readiness["notes"].append(
        "0.12.0rc1 exact-version qualification starts only after governance-hardening "
        "PR #133 and all seven sparse-MFPCA promotion criteria pass on protected main."
    )
    readiness["notes"].append(
        "Publication remains jointly disarmed during RC qualification. Fresh exact-version "
        "performance plus the complete PR and post-merge exact-main matrices are required "
        "before a separate governance-only publication-arming change."
    )
    readiness_path.write_text(json.dumps(readiness, indent=2) + "\n", encoding="utf-8")

    validator = ROOT / "scripts" / "validate_docs_contracts.py"
    validator_text = validator.read_text(encoding="utf-8")
    quoted_old = f'"{OLD}"'
    if validator_text.count(quoted_old) != 3:
        raise RuntimeError(
            "validate_docs_contracts.py no longer has the expected three 0.11.0 anchors"
        )
    validator.write_text(
        validator_text.replace(quoted_old, f'"{TARGET}"'),
        encoding="utf-8",
    )

    roadmap = ROOT / "docs" / "methods" / "status-roadmap.md"
    roadmap_text = roadmap.read_text(encoding="utf-8")
    roadmap_anchor = (
        "The current stable pre-1.0 line is **0.11.0**. It was published on "
        "29 September 2026."
    )
    if roadmap_text.count(roadmap_anchor) != 1:
        raise RuntimeError("status-roadmap release-line anchor changed")
    roadmap.write_text(
        roadmap_text.replace(
            roadmap_anchor,
            "The current release-candidate line is **0.12.0rc1**. The current stable "
            "pre-1.0 line remains **0.11.0**, published on 29 September 2026.",
        ),
        encoding="utf-8",
    )

    readme = ROOT / "README.md"
    readme_text = readme.read_text(encoding="utf-8")
    stable_line = (
        "> **Current stable release:** `0.11.0` was published on 29 September 2026 "
        "from exact protected-main commit `2616675ad2dfc095bf17a442c1d350ba88fd030a`. "
        "Production release workflow #13 completed successfully, including GitHub "
        "Release creation, production PyPI Trusted Publishing, digital attestations, "
        "and a fresh `eyetrajectoriespy==0.11.0` production-PyPI installation smoke test.\n"
    )
    if readme_text.count(stable_line) != 1:
        raise RuntimeError("README stable-release anchor changed")
    readme_text = readme_text.replace(
        stable_line,
        stable_line
        + ">\n> **Current release candidate under qualification:** `0.12.0rc1` freezes the "
        "qualified native sparse multivariate FPCA/joint-PACE 0.12 surface. "
        "Publication remains disarmed until fresh exact-version performance, the "
        "complete RC pull-request matrix, and the post-merge exact-main matrix pass.\n",
    )
    install_anchor = (
        "The immutable qualified release candidate remains available for reproducibility:\n\n"
        "```bash\n"
        "pip install --pre eyetrajectoriespy==0.11.0rc1\n"
        "```\n"
    )
    if readme_text.count(install_anchor) != 1:
        raise RuntimeError("README prerelease-install anchor changed")
    readme_text = readme_text.replace(
        install_anchor,
        "Current 0.12 release candidate under qualification:\n\n"
        "```bash\n"
        "pip install --pre eyetrajectoriespy==0.12.0rc1\n"
        "```\n\n"
        + install_anchor,
    )
    readme.write_text(readme_text, encoding="utf-8")

    changelog = ROOT / "CHANGELOG.md"
    changelog_text = changelog.read_text(encoding="utf-8")
    heading = "## Unreleased — 0.12 development"
    if changelog_text.count(heading) != 1:
        raise RuntimeError("CHANGELOG 0.12 heading changed")
    changelog_text = changelog_text.replace(
        heading,
        "## 0.12.0rc1 — 2026-10-01\n\n"
        "- Promote the feature-frozen, fully qualified 0.12 sparse-MFPCA/joint-PACE "
        "surface to the first release candidate without adding scientific behavior or "
        "changing analytical defaults.\n"
        "- Preserve direct block-covariance estimation and full-covariance joint PACE as "
        "canonical; two-stage and mGSFPCA routes remain sensitivity evidence only.\n"
        "- Require fresh exact-0.12.0rc1 performance and complete PR/exact-main "
        "qualification before publication can be armed.\n"
        "- Keep GitHub/PyPI publication readiness jointly disarmed throughout this RC "
        "qualification change."
    )
    changelog_text = changelog_text.replace(
        "- Keep GitHub/PyPI publication readiness disarmed and retain active package "
        "identity 0.11.0 until a separate exact-version RC alignment/qualification change.\n",
        "- Enter exact-version `0.12.0rc1` qualification only after the separate RC "
        "decision/governance-hardening PR is merged.\n",
    )
    changelog.write_text(changelog_text, encoding="utf-8")

    validation = ROOT / "VALIDATION.md"
    validation_text = validation.read_text(encoding="utf-8")
    validation_anchor = (
        "`0.11.0` is the current published stable pre-1.0 release. Published\n"
        "`0.11.0rc1` remains an immutable prerelease record."
    )
    if validation_text.count(validation_anchor) != 1:
        raise RuntimeError("VALIDATION current-target anchor changed")
    validation.write_text(
        validation_text.replace(
            validation_anchor,
            "`0.12.0rc1` is the current release-candidate line under exact-version "
            "qualification. `0.11.0` remains the current published stable pre-1.0 "
            "release; published `0.11.0rc1` remains immutable."
        ),
        encoding="utf-8",
    )

    release_process = ROOT / "docs" / "release-process.md"
    release_text = release_process.read_text(encoding="utf-8")
    release_anchor = "# Coordinated GitHub Release and PyPI publication\n"
    if release_text.count(release_anchor) != 1:
        raise RuntimeError("release-process title anchor changed")
    rc_section = """

## 0.12.0rc1 qualification

Stable `0.11.0` remains the current public release. `0.12.0rc1` freezes the
fully qualified native sparse multivariate FPCA/joint-PACE 0.12 surface. The RC
may correct packaging, documentation, reproducibility, or release-governance
defects, but it must not add a new estimator, hidden default, or unqualified
statistical pathway.

The sequence is:

~~~text
align active version/citation/validation/docs contracts to 0.12.0rc1
        |
        v
generate a fresh exact-version performance envelope
        |
        v
rerun sparse-MFPCA recovery, sensitivity, external comparator,
observation stress, dedicated performance and ordinary package CI
        |
        v
merge exact qualified RC state through protected main
        |
        v
rerun complete exact-main 0.12.0rc1 matrix
        |
        v
arm publication in a separate reviewed governance-only change
        |
        v
manual target=production dispatch only
~~~

Pre-RC evidence is retained as development evidence and is never relabelled as
RC evidence. Publication remains fail-closed until the post-merge exact-main
matrix passes.
"""
    release_process.write_text(
        release_text.replace(release_anchor, release_anchor + rc_section),
        encoding="utf-8",
    )

    readiness_doc = ROOT / "docs" / "release-readiness.md"
    readiness_text = readiness_doc.read_text(encoding="utf-8")
    readiness_anchor = "# Pre-1.0 release-readiness checklist\n"
    if readiness_text.count(readiness_anchor) != 1:
        raise RuntimeError("release-readiness title anchor changed")
    readiness_section = """

## 0.12.0rc1 qualification state

`0.12.0rc1` is the current release-candidate line under qualification; stable
`0.11.0` remains published and immutable. The pre-RC sparse-MFPCA evidence and
release-governance hardening are green.

Publication remains jointly disarmed. Fresh exact-version performance, the
complete RC pull-request matrix, protected-main merge, and the complete
exact-main RC matrix are required before a separate governance-only arming
change.
"""
    readiness_doc.write_text(
        readiness_text.replace(readiness_anchor, readiness_anchor + readiness_section),
        encoding="utf-8",
    )

    index = ROOT / "docs" / "index.md"
    index_text = index.read_text(encoding="utf-8")
    index_anchor = (
        "Install normally with `pip install eyetrajectoriespy==0.11.0` or "
        "`pip install eyetrajectoriespy`."
    )
    if index_text.count(index_anchor) != 1:
        raise RuntimeError("docs index stable-install anchor changed")
    index.write_text(
        index_text.replace(
            index_anchor,
            index_anchor
            + " The `0.12.0rc1` release candidate is under exact-version qualification; "
            "publication remains disarmed until the RC gates pass."
        ),
        encoding="utf-8",
    )

    release_note = ROOT / "docs" / "releases" / "0.12.0rc1.md"
    if release_note.exists():
        raise RuntimeError("0.12.0rc1 release note already exists")
    release_note.write_text(
        """# eyetrajectoriespy 0.12.0rc1

**Release candidate — qualification opened 1 October 2026**

`0.12.0rc1` freezes the qualified native sparse multivariate FPCA/joint-PACE
surface for jointly observed planar trajectories. It adds no new scientific
behavior beyond the already qualified 0.12 development line.

Retained evidence includes direct directional Cxy/block-covariance estimation,
full joint-operator PSD handling, full-covariance joint PACE, identification-
aware known-truth recovery, grid/ridge sensitivity, two-stage and mGSFPCA 0.2.2
sensitivity, row-level observation-process stress, portability, and dedicated
runtime/peak-memory characterization.

Publication is not armed by this qualification change. Fresh exact-version
performance and complete pull-request/post-merge exact-main matrices must pass
before a separate governance-only arming change.
""",
        encoding="utf-8",
    )

    mkdocs = ROOT / "mkdocs.yml"
    mkdocs_text = mkdocs.read_text(encoding="utf-8")
    nav_anchor = "  - Releases:\n      - 0.11.0: releases/0.11.0.md\n"
    if mkdocs_text.count(nav_anchor) != 1:
        raise RuntimeError("mkdocs release-nav anchor changed")
    mkdocs.write_text(
        mkdocs_text.replace(
            nav_anchor,
            "  - Releases:\n      - 0.12.0rc1: releases/0.12.0rc1.md\n"
            "      - 0.11.0: releases/0.11.0.md\n",
        ),
        encoding="utf-8",
    )

    performance = json.loads(
        (ROOT / "PERFORMANCE_ENVELOPE.json").read_text(encoding="utf-8")
    )
    if performance.get("package_version") != OLD:
        raise RuntimeError(
            "PERFORMANCE_ENVELOPE.json must remain 0.11.0 until fresh RC performance "
            "is generated and committed"
        )


if __name__ == "__main__":
    main()
