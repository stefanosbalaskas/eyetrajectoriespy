"""Generate deterministic scientific gallery index/category pages from the manifest."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from docs_gallery_manifest import GALLERY_CATEGORIES, GALLERY_PLOTS


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
GALLERY_DIR = DOCS / "methods" / "gallery"
INDEX = DOCS / "methods" / "visual-gallery.md"

CATEGORY_TITLES = {
    "fpca": "FPCA & uncertainty",
    "sparse-fda": "Sparse FDA",
    "regression": "Functional regression & prediction",
    "mixed-effects": "Mixed effects & repeated measures",
    "geometry-registration": "Geometry & registration",
    "nonlinear": "Nonlinear dynamics & information flow",
    "simulation-validation": "Simulation & validation",
}

CATEGORY_INTROS = {
    "fpca": "Dense/common-grid FPCA, component uncertainty, stability, review, and score/spectrum diagnostics.",
    "sparse-fda": "Native irregular observations, sparse covariance FPCA, and PACE diagnostics without raw common-grid interpolation.",
    "regression": "Functional regression, generalized marginal response models, prediction, and bootstrap inference.",
    "mixed-effects": "Repeated-trial Gaussian functional mixed effects, covariance sensitivity, and random-effect diagnostics.",
    "geometry-registration": "Trajectory geometry, time-warping comparison, landmark registration, and phase representation.",
    "nonlinear": "Recurrence, nonlinear divergence, surrogate testing, and directed-information diagnostics.",
    "simulation-validation": "Known-truth simulation and recovery evidence used to qualify scientific workflows.",
}


def _card(name: str, entry: dict[str, str]) -> str:
    asset = entry["asset"]
    quantity = entry["quantity"]
    equation = entry["equation"]
    example = entry["example"]
    return f"""## `{name}`\n\n![{quantity}](../../assets/gallery/{asset})\n\n**API:** [`{name}()`](../../reference/api.md#{name})  \n**Scientific quantity:** {quantity}  \n**Equation:** [mathematical contract](../mathematical-reference.md#{equation})  \n**Worked example:** [example](../../examples/{example}.md)\n"""


def _write_index(grouped: dict[str, list[tuple[str, dict[str, str]]]]) -> None:
    lines = [
        "---",
        "title: Visual gallery",
        "---",
        "",
        "# Visual gallery",
        "",
        "Every callable public `plot_*` API is represented by one deterministic SVG generated through the real plotting function. Coverage is machine-checked against `eyetrajectoriespy.__all__`; adding or removing a public plot without updating this gallery fails documentation CI.",
        "",
        "The figures are scientific documentation rather than screenshots: each entry links the plotting API to the quantity it displays, the corresponding mathematical/methodological contract, and a worked example.",
        "",
        "| Family | Public plots | Browse |",
        "|---|---:|---|",
    ]
    for category in GALLERY_CATEGORIES:
        title = CATEGORY_TITLES[category]
        count = len(grouped[category])
        lines.append(f"| {title} | {count} | [{title}](gallery/{category}.md) |")
    lines += ["", f"**Total documented public plotting APIs: {sum(len(v) for v in grouped.values())}.**", ""]
    INDEX.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    grouped: dict[str, list[tuple[str, dict[str, str]]]] = defaultdict(list)
    for name, entry in sorted(GALLERY_PLOTS.items()):
        grouped[entry["category"]].append((name, entry))

    GALLERY_DIR.mkdir(parents=True, exist_ok=True)
    _write_index(grouped)

    for category in GALLERY_CATEGORIES:
        title = CATEGORY_TITLES[category]
        lines = [
            "---",
            f"title: {title}",
            "---",
            "",
            f"# {title}",
            "",
            CATEGORY_INTROS[category],
            "",
            f"This page contains **{len(grouped[category])}** deterministic public plotting contracts.",
            "",
        ]
        for name, entry in grouped[category]:
            lines.append(_card(name, entry))
        (GALLERY_DIR / f"{category}.md").write_text(
            "\n".join(lines).rstrip() + "\n",
            encoding="utf-8",
        )

    print(
        "gallery pages OK: "
        f"{len(GALLERY_CATEGORIES)} categories, {len(GALLERY_PLOTS)} public plots"
    )


if __name__ == "__main__":
    main()
