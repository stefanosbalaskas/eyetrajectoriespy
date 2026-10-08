"""Execute the runnable Python blocks of the 1.2 candidate research articles."""

from __future__ import annotations

import os
from pathlib import Path
import re
from tempfile import TemporaryDirectory

import matplotlib

matplotlib.use("Agg")

ROOT = Path(__file__).resolve().parents[1]
PAGES = (
    "docs/articles/choosing-the-ten-workflows.md",
    "docs/articles/reproducible-workflow-bundles.md",
)


def main() -> None:
    original = Path.cwd()
    executed = 0
    try:
        with TemporaryDirectory(prefix="et-docs-") as temp:
            os.chdir(temp)
            for page in PAGES:
                source = (ROOT / page).read_text(encoding="utf-8")
                blocks = re.findall(r"^`{3}python\s*\n(.*?)^`{3}", source, re.M | re.S)
                if not blocks:
                    raise RuntimeError(f"Missing executable example in {page}")
                ns: dict[str, object] = {"__name__": "__docs_example__"}
                for index, code in enumerate(blocks, start=1):
                    exec(compile(code, f"{page}:example-{index}", "exec"), ns)
                    executed += 1
                if page.endswith("reproducible-workflow-bundles.md"):
                    assert Path("fpca-component.svg").is_file(), "Workflow figure not exported"
                    assert Path("my-analysis-bundle/SHA256SUMS").is_file(), "Workflow checksums not exported"
    finally:
        os.chdir(original)
    print(f"PASS: executed {executed} candidate article code blocks")


if __name__ == "__main__":
    main()
