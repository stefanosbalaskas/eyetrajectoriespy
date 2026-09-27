"""Fail if a production PyPI version has already been published."""

from __future__ import annotations

import argparse
import urllib.error
import urllib.parse
import urllib.request


def verify_version_unpublished(
    package: str,
    version: str,
    *,
    index_base: str = "https://pypi.org",
) -> None:
    package_part = urllib.parse.quote(package, safe="")
    version_part = urllib.parse.quote(version, safe="")
    url = f"{index_base.rstrip('/')}/pypi/{package_part}/{version_part}/json"
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "eyetrajectoriespy-release-preflight"},
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            status = getattr(response, "status", 200)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return
        raise RuntimeError(
            f"PyPI preflight failed with HTTP {exc.code}: {url}"
        ) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(
            f"PyPI preflight could not determine version state: {exc}"
        ) from exc

    if status == 200:
        raise RuntimeError(
            f"production release blocked: {package}=={version} already exists "
            "on PyPI; use explicit resume-production only for recovery"
        )
    raise RuntimeError(
        f"PyPI preflight returned unexpected HTTP {status}: {url}"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--index-base", default="https://pypi.org")
    args = parser.parse_args()
    verify_version_unpublished(
        args.package,
        args.version,
        index_base=args.index_base,
    )
    print(f"{args.package}=={args.version} is not published on PyPI")


if __name__ == "__main__":
    main()
