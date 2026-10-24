"""Fail-closed independent stable-1.2.0 publication authorization.

The historical RC2 owner/PR approval does not authorize a different final
version. This script performs no publication. Exact protected-main CI, OIDC,
version uniqueness, checksums, and the protected PyPI environment remain
separate gates in release.yml.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = "stefanosbalaskas/eyetrajectoriespy"
OWNER = "stefanosbalaskas"
VERSION = "1.2.0"


def verify_final_release_authorization(
    policy: dict, readiness: dict, *, actor: str,
    repository: str, git_ref: str, event_name: str, target: str,
) -> str:
    if not isinstance(policy, dict) or not isinstance(readiness, dict):
        raise RuntimeError("Final publication requires real approval and readiness JSON")
    if (repository != REPO or git_ref != "refs/heads/main"
        or event_name != "workflow_dispatch"
        or actor.lower() != OWNER
        or target not in {"production", "resume-production"}):
        raise RuntimeError("Final 1.2.0 requires a manual release on main by the authenticated repository owner")
    if policy.get("published_final_version") is True:
        raise RuntimeError("Stable 1.2.0 already published; a new release needs a new version")
    if (policy.get("schema_version") != 1
        or policy.get("release_version") != VERSION
        or policy.get("predecessor_tag") != "v1.2.0rc2"
        or policy.get("owner") != OWNER
        or policy.get("approval_state") != "separately_authorized_stable_publication"
        or policy.get("final_version_evidence_complete") is not True
        or policy.get("protected_main_exact_ci_qualified") is not True
        or policy.get("owner_production_publication_approved") is not True
        or policy.get("pypi_environment_review_required") is not True
        or policy.get("root_api_promotion") is not False
        or policy.get("experimental_helpers_stable_promotion") is not False
        or set(policy.get("scientific_issues_open", [])) != {289, 296}):
        raise RuntimeError("Stable 1.2.0 publication blocked: distinct, qualified FINAL approval is missing")
    commit = policy.get("qualification_main_commit")
    if not isinstance(commit, str) or len(commit) != 40 or any(c not in "0123456789abcdef" for c in commit):
        raise RuntimeError("Stable 1.2.0 publication blocked: no immutable qualified-main provenance")
    if (readiness.get("current_development_version") != VERSION
        or readiness.get("github_release_ready") is not True
        or readiness.get("production_release_ready") is not True
        or readiness.get("testpypi_publication_ready") is not False):
        raise RuntimeError("Stable 1.2.0 publication blocked: readiness is not jointly authorized")
    return commit


def main() -> None:
    policy = json.loads((ROOT / "FINAL_1_2_PUBLICATION_APPROVAL.json").read_text(encoding="utf-8"))
    readiness = json.loads((ROOT / "RELEASE_READINESS.json").read_text(encoding="utf-8"))
    commit = verify_final_release_authorization(
        policy, readiness, actor=os.environ.get("GITHUB_ACTOR", ""),
        repository=os.environ.get("GITHUB_REPOSITORY", ""),
        git_ref=os.environ.get("GITHUB_REF", ""),
        event_name=os.environ.get("GITHUB_EVENT_NAME", ""),
        target=os.environ.get("RELEASE_TARGET", ""),
    )
    print(f"Final 1.2.0 separate publication authorization verified; historical exact CI commit: {commit}")


if __name__ == "__main__":
    main()
