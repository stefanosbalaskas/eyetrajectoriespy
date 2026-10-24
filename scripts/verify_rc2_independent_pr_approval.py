"""Validate RC2 independent approval, or the explicit owner-directed recovery policy.

The original PR #475 was merged with no reviews. This later policy amendment
allows only the real owner to dispatch manually, with existing protected-main CI
and PyPI environment approval unchanged. No independent review is fabricated.
"""
from __future__ import annotations

import json
import os
from urllib.request import Request, urlopen
from pathlib import Path

OWNER = "stefanosbalaskas"
REPO = "stefanosbalaskas/eyetrajectoriespy"
AUTHORIZATION_PR = 475
EXPECTED_AUTHORIZATION_HEAD = "b21e16afc3b3c2e01c6b77c2182429189ece21e9"


def validate_external_review(pr: dict, reviews: list[dict]) -> str:
    if (pr.get("number") != AUTHORIZATION_PR
        or pr.get("base", {}).get("ref") != "main"
        or not pr.get("merged")
        or not pr.get("merged_at")):
        raise RuntimeError("RC2 authorization PR must be merged into main")
    head = pr.get("head", {}).get("sha")
    if not isinstance(head, str) or len(head) != 40:
        raise RuntimeError("RC2 authorization PR has no immutable head SHA")
    author = (pr.get("user") or {}).get("login")
    if not author:
        raise RuntimeError("Cannot determine RC2 authorization PR author")
    # Reject stale approvals: latest submitted review for each reviewer, and
    # only an APPROVED review of the exact final PR head is acceptable.
    latest = {}
    for review in reviews:
        login = (review.get("user") or {}).get("login")
        if not login or review.get("state") == "PENDING":
            continue
        latest[login] = review
    for login, review in latest.items():
        if (login.lower() not in {OWNER.lower(), author.lower()}
            and (review.get("user") or {}).get("type") == "User"
            and review.get("state") == "APPROVED"
            and review.get("commit_id") == head):
            return login
    raise RuntimeError(
        "Production blocked: independent human APPROVED review of exact "
        "RC2 arming PR #475 head is missing"
    )


def validate_owner_manual_dispatch(
    pr: dict, ledger: dict, *, actor: str, event_name: str,
    repository: str, git_ref: str, target: str,
) -> str:
    """Owner-only alternative, explicitly documented after unreviewed PR #475 merge."""
    if (pr.get("number") != AUTHORIZATION_PR
        or pr.get("base", {}).get("ref") != "main"
        or not pr.get("merged") or not pr.get("merged_at")
        or pr.get("head", {}).get("sha") != EXPECTED_AUTHORIZATION_HEAD
        or (pr.get("user") or {}).get("login", "").lower() != OWNER):
        raise RuntimeError("Owner release blocked: immutable RC2 authorization PR mismatch")
    if (ledger.get("candidate_version") != "1.2.0rc2"
        or ledger.get("authorization_pr_number") != AUTHORIZATION_PR
        or ledger.get("owner_manual_dispatch_fallback_authorized") is not True
        or ledger.get("independent_human_release_review_recorded") is not False
        or ledger.get("narrow_scope_approved_for_release") is not True
        or ledger.get("pypi_environment_review_required") is not True):
        raise RuntimeError("Owner release blocked: explicit recorded recovery policy missing")
    if (actor.lower() != OWNER
        or event_name != "workflow_dispatch"
        or repository != REPO
        or git_ref != "refs/heads/main"
        or target not in {"production", "resume-production"}):
        raise RuntimeError("Owner release blocked: authenticated manual main dispatch required")
    return OWNER


def _github_get(api_path: str, token: str):
    request = Request(
        "https://api.github.com" + api_path,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urlopen(request, timeout=20) as response:
        return json.load(response)


def main() -> None:
    if os.getenv("GITHUB_REPOSITORY") != REPO or os.getenv("GITHUB_REF") != "refs/heads/main":
        raise RuntimeError("RC2 release requires exact main of canonical repository")
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GitHub token required for verified RC2 authorization")
    prefix = f"/repos/{REPO}/pulls/{AUTHORIZATION_PR}"
    pr = _github_get(prefix, token)
    actor = os.getenv("GITHUB_ACTOR", "")
    if actor.lower() == OWNER:
        ledger_path = Path(__file__).resolve().parents[1] / "RC2_PUBLICATION_REVIEW.json"
        ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
        validate_owner_manual_dispatch(
            pr, ledger, actor=actor, event_name=os.getenv("GITHUB_EVENT_NAME", ""),
            repository=os.getenv("GITHUB_REPOSITORY", ""),
            git_ref=os.getenv("GITHUB_REF", ""),
            target=os.getenv("RELEASE_TARGET", ""),
        )
        print("RC2 explicit OWNER manual dispatch verified; no independent review claimed")
        return
    reviews = []
    for page in range(1, 11):
        batch = _github_get(f"{prefix}/reviews?per_page=100&page={page}", token)
        if not isinstance(batch, list):
            raise RuntimeError("Unexpected GitHub review response")
        reviews.extend(batch)
        if len(batch) < 100:
            break
    reviewer = validate_external_review(pr, reviews)
    print(f"RC2 independent release approval verified: {reviewer}, PR #{AUTHORIZATION_PR}")


if __name__ == "__main__":
    main()
