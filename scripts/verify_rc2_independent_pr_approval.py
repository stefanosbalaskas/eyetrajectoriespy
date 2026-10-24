"""Require a real independent approval of the exact RC2 arming pull request.

GitHub API evidence, not an assistant-authored JSON flag, is the source of truth.
Runs only for manual production/resume dispatch; never publishes itself.
"""
from __future__ import annotations

import json
import os
from urllib.request import Request, urlopen

OWNER = "stefanosbalaskas"
REPO = "stefanosbalaskas/eyetrajectoriespy"
AUTHORIZATION_PR = 475


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
        raise RuntimeError("GitHub token required for verified external review")
    prefix = f"/repos/{REPO}/pulls/{AUTHORIZATION_PR}"
    pr = _github_get(prefix, token)
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
