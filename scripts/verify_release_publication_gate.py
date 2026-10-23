"""Fail-closed, side-effect-free gate for every manually dispatched release target.

This module does not build, publish, create releases, contact PyPI/GitHub, or
change RELEASE_READINESS. The only accepted no-publication action is build-only.
A publication target requires a separately reviewed, explicit readiness decision.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TARGETS = ("build-only", "testpypi", "production", "resume-production")


def verify_publication_policy(readiness: dict, target: str) -> str:
    """Require explicit policy for a release target, refusing missing/false flags."""
    if target not in TARGETS:
        raise ValueError(f"Unrecognized release target: {target!r}")
    if not isinstance(readiness, dict):
        raise RuntimeError("Release-readiness evidence is not a JSON object")
    if target == "build-only":
        return target

    gates = readiness.get("gates")
    if not isinstance(gates, dict):
        raise RuntimeError("Publishing blocked: readiness gate declarations missing")
    if target == "testpypi":
        if (readiness.get("testpypi_publication_ready") is not True
            or gates.get("testpypi_trusted_publishing_configured") is not True):
            raise RuntimeError(
                "TestPyPI publishing blocked: dedicated reviewed TestPyPI "
                "publication readiness/trusted-publishing gate is not armed"
            )
        return target

    # Both new and resumed production uploads need the SAME explicit hold
    # release. No fallback from a successful build, CI, tag or environment var.
    if (readiness.get("production_release_ready") is not True
        or readiness.get("github_release_ready") is not True):
        raise RuntimeError(
            "Production publication blocked: BOTH production_release_ready "
            "and github_release_ready must be explicitly armed"
        )
    for gate in ("pypi_trusted_publishing_configured",
                 "pypi_environment_required_reviewer",
                 "exact_main_ci_required"):
        if gates.get(gate) is not True:
            raise RuntimeError(f"Production publication blocked: {gate} is not armed")
    return target


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True, choices=TARGETS)
    parser.add_argument(
        "--readiness", type=Path, default=ROOT / "RELEASE_READINESS.json"
    )
    args = parser.parse_args()
    readiness = json.loads(args.readiness.read_text(encoding="utf-8"))
    verify_publication_policy(readiness, args.target)
    print(f"Release target policy passed: {args.target} (no publication performed)")


if __name__ == "__main__":
    main()
