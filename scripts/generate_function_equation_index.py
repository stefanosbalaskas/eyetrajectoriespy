"""Generate repository and website function-to-equation indexes."""

from __future__ import annotations

import argparse
import difflib
from pathlib import Path

from eyetrajectoriespy import list_mathematical_contracts


ROOT = Path(__file__).resolve().parents[1]
ROOT_TARGET = ROOT / "FUNCTION_EQUATION_INDEX.md"
DOCS_TARGET = ROOT / "docs" / "reference" / "function-equation-index.md"
TICK = chr(96)


def _formula_block(equation: str) -> list[str]:
    return ["$$", equation, "$$"]


def _render(*, site: bool) -> str:
    lines: list[str] = []
    if site:
        lines += ["---", "title: Function → equation index", "---", ""]
    lines += [
        "# Function → equation index",
        "",
        "Generated from the public mathematical-contract registry in "
        f"{TICK}eyetrajectoriespy.mathematical_contracts{TICK}.",
        "",
        "The equations below are implementation contracts, not claims of methodological novelty. "
        "See the linked expanded reference for assumptions, derivations, and scope limits.",
        "",
    ]

    for contract in list_mathematical_contracts():
        lines += [f"## {contract.title}", ""]
        functions = ", ".join(
            f"{TICK}{name}(){TICK}" for name in contract.public_api
        )
        lines += [f"**Functions:** {functions}", ""]
        for equation in contract.equations:
            lines += _formula_block(equation) + [""]
        lines += [f"**Scope:** {contract.scope}", ""]
        if site:
            lines += [
                f"[Expanded mathematical reference](../methods/mathematical-reference.md#{contract.site_anchor})",
                "",
            ]
        else:
            lines += [
                "Expanded reference: "
                "https://stefanosbalaskas.github.io/eyetrajectoriespy/"
                f"methods/mathematical-reference/#{contract.site_anchor}",
                "",
            ]

    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if committed generated indexes differ from the registry.",
    )
    args = parser.parse_args()

    expected = {
        ROOT_TARGET: _render(site=False),
        DOCS_TARGET: _render(site=True),
    }

    if args.check:
        stale = [
            str(path.relative_to(ROOT))
            for path, content in expected.items()
            if not path.exists() or path.read_text(encoding="utf-8") != content
        ]
        if stale:
            for path, content in expected.items():
                if not path.exists():
                    continue
                actual = path.read_text(encoding="utf-8")
                if actual == content:
                    continue
                diff = difflib.unified_diff(
                    actual.splitlines(),
                    content.splitlines(),
                    fromfile=str(path.relative_to(ROOT)),
                    tofile=f"{path.relative_to(ROOT)} (generated)",
                    lineterm="",
                )
                print("\n".join(diff))
            raise SystemExit(
                "generated mathematical indexes are stale: " + ", ".join(stale)
            )
        print(f"function-equation indexes OK: {len(list_mathematical_contracts())} contracts")
        return

    for path, content in expected.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        print(f"wrote {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
