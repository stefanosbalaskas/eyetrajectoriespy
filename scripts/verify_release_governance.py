"""Verify repository/tag governance before production publication."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import urllib.error
import urllib.parse
import urllib.request



ROOT = Path(__file__).resolve().parents[1]

_REQUIRED_DECLARATIONS = {
    "portable_result_schema_qualified",
    "environment_capture_qualified",
    "canonical_examples_qualified",
    "release_build_smoke_qualified",
    "testpypi_trusted_publishing_configured",
    "testpypi_rehearsal_completed",
    "main_protected",
    "issue_64_closed",
    "pypi_trusted_publishing_configured",
    "pypi_environment_required_reviewer",
    "exact_main_ci_required",
}


def _release_readiness() -> dict[str, object]:
    return json.loads(
        (ROOT / "RELEASE_READINESS.json").read_text(encoding="utf-8")
    )


def _verify_declared_release_readiness() -> None:
    readiness = _release_readiness()
    if readiness.get("production_release_ready") is not True:
        raise RuntimeError(
            "production release blocked: RELEASE_READINESS.json is not armed"
        )
    gates = readiness.get("gates", {})
    missing = sorted(
        name
        for name in _REQUIRED_DECLARATIONS
        if gates.get(name) is not True
    )
    if missing:
        raise RuntimeError(
            "production release blocked: readiness declarations are not "
            f"complete: {missing}"
        )

REQUIRED_CHECKS = {
    "package",
    "test (ubuntu-latest, 3.11)",
    "test (ubuntu-latest, 3.12)",
    "test (ubuntu-latest, 3.13)",
    "test (windows-latest, 3.11)",
    "test (windows-latest, 3.12)",
    "test (windows-latest, 3.13)",
    "test (macos-latest, 3.11)",
    "test (macos-latest, 3.12)",
    "test (macos-latest, 3.13)",
    "docs-build",
    "examples",
    "scikit-fda",
    "FDApy sparse / Python 3.11",
    "FDApy sparse / Python 3.12",
    "performance-envelope",
}


def _github_json(url: str, token: str) -> object:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "eyetrajectoriespy-release-gate",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"GitHub release-gate request failed: {exc.code} {url}: {body}"
        ) from exc


def verify_release_governance(
    *,
    repository: str,
    commit: str,
    tag: str,
    token: str,
) -> None:
    _verify_declared_release_readiness()
    api = f"https://api.github.com/repos/{repository}"

    branch = _github_json(f"{api}/branches/main", token)
    if not isinstance(branch, dict) or not branch.get("protected"):
        raise RuntimeError(
            "production release blocked: main is not protected"
        )
    main_sha = branch["commit"]["sha"]
    if main_sha != commit:
        raise RuntimeError(
            "production release blocked: release tag does not point to current "
            f"main HEAD ({commit} != {main_sha})"
        )

    issue = _github_json(f"{api}/issues/64", token)
    if not isinstance(issue, dict) or issue.get("state") != "closed":
        raise RuntimeError(
            "production release blocked: release-readiness issue #64 is open"
        )

    encoded_tag = urllib.parse.quote(tag, safe="")
    tag_ref = _github_json(f"{api}/git/ref/tags/{encoded_tag}", token)
    if not isinstance(tag_ref, dict):
        raise RuntimeError("production release tag reference is unavailable")
    tag_object = tag_ref["object"]
    if tag_object.get("type") != "tag":
        raise RuntimeError(
            "production release blocked: the version tag must be annotated"
        )

    annotated = _github_json(f"{api}/git/tags/{tag_object['sha']}", token)
    if not isinstance(annotated, dict):
        raise RuntimeError("annotated tag object is unavailable")
    verification = annotated.get("verification") or {}
    if not verification.get("verified"):
        raise RuntimeError(
            "production release blocked: annotated version tag is not "
            "cryptographically verified by GitHub"
        )
    if annotated["object"]["sha"] != commit:
        raise RuntimeError(
            "production release blocked: annotated tag target differs from "
            "the declared release commit"
        )

    check_runs = _github_json(
        f"{api}/commits/{commit}/check-runs?per_page=100",
        token,
    )
    if not isinstance(check_runs, dict):
        raise RuntimeError("commit check-run response is unavailable")
    passed = {
        run["name"]
        for run in check_runs.get("check_runs", [])
        if run.get("status") == "completed"
        and run.get("conclusion") in {"success", "neutral", "skipped"}
    }
    missing = sorted(REQUIRED_CHECKS - passed)
    if missing:
        raise RuntimeError(
            "production release blocked: required exact-main checks are "
            f"missing or not successful: {missing}"
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--tag", required=True)
    args = parser.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN is required for governance verification")
    verify_release_governance(
        repository=args.repository,
        commit=args.commit,
        tag=args.tag,
        token=token,
    )
    print("production release governance gate passed")


if __name__ == "__main__":
    main()
