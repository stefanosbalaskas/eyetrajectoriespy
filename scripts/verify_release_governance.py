"""Verify exact-main governance before creating a production GitHub release."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import time
import urllib.error
import urllib.request


ROOT = Path(__file__).resolve().parents[1]

_GITHUB_RELEASE_DECLARATIONS = {
    "portable_result_schema_qualified",
    "environment_capture_qualified",
    "canonical_examples_qualified",
    "release_build_smoke_qualified",
    "main_protected",
    "issue_64_closed",
    "exact_main_ci_required",
    "functional_simulation_qualification_qualified",
    "functional_simulation_stress_recorded",
    "sparse_native_validation_qualified",
}

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
    "release-readiness",
    "recovery",
    "stress-evidence",
    "sparse-performance",
    "stress-recovery",
    "noise-variance-recovery",
}


def _release_readiness() -> dict[str, object]:
    return json.loads(
        (ROOT / "RELEASE_READINESS.json").read_text(encoding="utf-8")
    )


def _verify_declared_github_release_readiness() -> None:
    readiness = _release_readiness()
    if readiness.get("github_release_ready") is not True:
        raise RuntimeError(
            "GitHub release blocked: RELEASE_READINESS.json is not armed "
            "for GitHub release"
        )
    gates = readiness.get("gates", {})
    missing = sorted(
        name
        for name in _GITHUB_RELEASE_DECLARATIONS
        if gates.get(name) is not True
    )
    if missing:
        raise RuntimeError(
            "GitHub release blocked: readiness declarations are incomplete: "
            f"{missing}"
        )


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


def _passed_checks(repository: str, commit: str, token: str) -> set[str]:
    api = f"https://api.github.com/repos/{repository}"
    check_runs = _github_json(
        f"{api}/commits/{commit}/check-runs?per_page=100",
        token,
    )
    if not isinstance(check_runs, dict):
        raise RuntimeError("commit check-run response is unavailable")
    return {
        run["name"]
        for run in check_runs.get("check_runs", [])
        if run.get("status") == "completed"
        and run.get("conclusion") in {"success", "neutral", "skipped"}
    }


def verify_release_governance(
    *,
    repository: str,
    commit: str,
    token: str,
    wait_seconds: int = 0,
    poll_seconds: int = 20,
) -> None:
    _verify_declared_github_release_readiness()
    api = f"https://api.github.com/repos/{repository}"

    branch = _github_json(f"{api}/branches/main", token)
    if not isinstance(branch, dict) or not branch.get("protected"):
        raise RuntimeError("GitHub release blocked: main is not protected")
    main_sha = branch["commit"]["sha"]
    if main_sha != commit:
        raise RuntimeError(
            "GitHub release blocked: release commit is not current main HEAD "
            f"({commit} != {main_sha})"
        )

    issue = _github_json(f"{api}/issues/64", token)
    if not isinstance(issue, dict) or issue.get("state") != "closed":
        raise RuntimeError(
            "GitHub release blocked: release-readiness issue #64 is open"
        )

    deadline = time.monotonic() + max(wait_seconds, 0)
    while True:
        passed = _passed_checks(repository, commit, token)
        missing = sorted(REQUIRED_CHECKS - passed)
        if not missing:
            return
        if time.monotonic() >= deadline:
            raise RuntimeError(
                "GitHub release blocked: required exact-main checks are "
                f"missing or not successful: {missing}"
            )
        time.sleep(max(poll_seconds, 1))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--wait-seconds", type=int, default=0)
    parser.add_argument("--poll-seconds", type=int, default=20)
    args = parser.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN is required for governance verification")
    verify_release_governance(
        repository=args.repository,
        commit=args.commit,
        token=token,
        wait_seconds=args.wait_seconds,
        poll_seconds=args.poll_seconds,
    )
    print("GitHub release governance gate passed")


if __name__ == "__main__":
    main()
