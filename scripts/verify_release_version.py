"""Fail-closed version consistency checks for release workflows."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import tomllib

from packaging.version import Version


ROOT = Path(__file__).resolve().parents[1]

_VERSION_JSON_FILES = (
    "CANONICAL_WORKFLOWS.json",
    "REFERENCE_VALIDATION.json",
    "VALIDATION_TOLERANCES.json",
    "PERFORMANCE_ENVELOPE.json",
)


def _package_init_version() -> str:
    text = (ROOT / "src/eyetrajectoriespy/__init__.py").read_text(
        encoding="utf-8"
    )
    match = re.search(r'^__version__\s*=\s*"([^"]+)"', text, flags=re.MULTILINE)
    if match is None:
        raise RuntimeError("package __version__ declaration was not found")
    return match.group(1)


def _citation_version() -> str:
    text = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    match = re.search(
        r"^version:\s*['\"]?([^'\"\s]+)['\"]?\s*$",
        text,
        flags=re.MULTILINE,
    )
    if match is None:
        raise RuntimeError("CITATION.cff version declaration was not found")
    return match.group(1)


def version_contract() -> dict[str, str]:
    with (ROOT / "pyproject.toml").open("rb") as stream:
        project_version = tomllib.load(stream)["project"]["version"]

    versions = {
        "pyproject.toml": project_version,
        "package __version__": _package_init_version(),
        "CITATION.cff": _citation_version(),
    }
    for relative_path in _VERSION_JSON_FILES:
        payload = json.loads(
            (ROOT / relative_path).read_text(encoding="utf-8")
        )
        versions[relative_path] = str(payload["package_version"])

    roadmap = (ROOT / "docs/methods/status-roadmap.md").read_text(
        encoding="utf-8"
    )
    expected_line = (
        f"The current development line is **{project_version}**."
    )
    if expected_line not in roadmap:
        raise RuntimeError(
            "status roadmap does not declare the pyproject version as the "
            "current development line"
        )
    return versions


def verify_version_contract(
    *,
    tag: str | None = None,
    production: bool = False,
) -> str:
    versions = version_contract()
    distinct = set(versions.values())
    if len(distinct) != 1:
        details = ", ".join(
            f"{name}={version}"
            for name, version in versions.items()
        )
        raise RuntimeError(f"release version declarations disagree: {details}")

    version_text = next(iter(distinct))
    parsed = Version(version_text)

    if tag is not None:
        expected_tag = f"v{version_text}"
        if tag != expected_tag:
            raise RuntimeError(
                f"release tag/version mismatch: tag={tag!r}, "
                f"expected={expected_tag!r}"
            )

    if production:
        if tag is None:
            raise RuntimeError("production verification requires a version tag")
        if parsed.is_devrelease:
            raise RuntimeError(
                "development versions must not be published to production PyPI"
            )
        if parsed.local is not None:
            raise RuntimeError(
                "local-version identifiers are not permitted for production"
            )

    return version_text


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag")
    parser.add_argument("--production", action="store_true")
    args = parser.parse_args()
    version = verify_version_contract(
        tag=args.tag,
        production=args.production,
    )
    print(version)


if __name__ == "__main__":
    main()
