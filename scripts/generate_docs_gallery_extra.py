"""Generate deterministic gallery assets for public plots not covered by the base gallery.

The package test suite already constructs valid, deterministic scientific objects for
all public plotting helpers.  Rather than duplicate dozens of setup recipes here, this
script instruments the public ``plot_*`` calls, runs only tests whose function bodies
exercise still-uncovered plot APIs, and saves the first successful render for each API.
The test assertions still run, so a captured figure is backed by the same contract that
qualifies the plotting helper itself.
"""

from __future__ import annotations

from functools import wraps
import inspect
from pathlib import Path
import sys

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest

import eyetrajectoriespy as et

from docs_gallery_manifest import GALLERY_PLOTS


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "assets" / "gallery"


def _find_figure(value):
    if value is None:
        return None
    if hasattr(value, "savefig"):
        return value
    if hasattr(value, "figure") and hasattr(value.figure, "savefig"):
        return value.figure
    if isinstance(value, np.ndarray):
        for item in value.ravel().tolist():
            found = _find_figure(item)
            if found is not None:
                return found
    if isinstance(value, (tuple, list)):
        for item in value:
            found = _find_figure(item)
            if found is not None:
                return found
    return None


def _save_result(value, filename: str) -> None:
    figure = _find_figure(value)
    if figure is None:
        figure = plt.gcf()
    if figure is None or not hasattr(figure, "savefig"):
        raise RuntimeError(f"could not locate Matplotlib figure for {filename}")
    figure.tight_layout()
    figure.savefig(
        OUTPUT / filename,
        format="svg",
        bbox_inches="tight",
        metadata={"Date": None, "Creator": "eyetrajectoriespy docs gallery"},
    )


class _SelectPlotTests:
    def __init__(self, plot_names: set[str]):
        self.plot_names = plot_names

    def pytest_collection_modifyitems(self, session, config, items):
        selected = []
        deselected = []
        for item in items:
            function = getattr(item, "function", None)
            if function is None:
                deselected.append(item)
                continue
            try:
                source = inspect.getsource(function)
            except (OSError, TypeError):
                source = ""
            if any(name in source for name in self.plot_names):
                selected.append(item)
            else:
                deselected.append(item)
        if deselected:
            config.hook.pytest_deselected(items=deselected)
        items[:] = selected


def _instrument(plot_names: set[str]) -> dict[str, object]:
    originals: dict[str, object] = {}
    for name in sorted(plot_names):
        original = getattr(et, name)
        originals[name] = original
        asset = GALLERY_PLOTS[name]["asset"]

        @wraps(original)
        def wrapped(*args, __original=original, __asset=asset, **kwargs):
            result = __original(*args, **kwargs)
            destination = OUTPUT / __asset
            if not destination.exists():
                _save_result(result, __asset)
            return result

        setattr(et, name, wrapped)
        module = sys.modules.get(getattr(original, "__module__", ""))
        if module is not None and getattr(module, name, None) is original:
            setattr(module, name, wrapped)
    return originals


def _restore(originals: dict[str, object]) -> None:
    for name, original in originals.items():
        setattr(et, name, original)
        module = sys.modules.get(getattr(original, "__module__", ""))
        if module is not None:
            setattr(module, name, original)


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    matplotlib.rcParams["svg.hashsalt"] = "eyetrajectoriespy-0.12-gallery-complete"

    targets = {
        name
        for name, entry in GALLERY_PLOTS.items()
        if not (OUTPUT / entry["asset"]).exists()
    }
    if not targets:
        print("gallery extension: base generator already covers every public plot")
        return

    originals = _instrument(targets)
    try:
        exit_code = pytest.main(
            [
                str(ROOT / "tests"),
                "-q",
                "--disable-warnings",
                "--maxfail=1",
            ],
            plugins=[_SelectPlotTests(targets)],
        )
    finally:
        _restore(originals)
        plt.close("all")

    if exit_code != pytest.ExitCode.OK:
        raise RuntimeError(
            "selected plotting-contract tests failed while generating gallery assets: "
            f"pytest exit code {int(exit_code)}"
        )

    missing = sorted(
        name
        for name in targets
        if not (OUTPUT / GALLERY_PLOTS[name]["asset"]).exists()
    )
    if missing:
        raise RuntimeError(
            "public plot APIs were not exercised by selected qualified test calls: "
            f"{missing}"
        )

    print(
        "gallery extension OK: captured "
        f"{len(targets)} previously uncovered public plot APIs"
    )


if __name__ == "__main__":
    main()
