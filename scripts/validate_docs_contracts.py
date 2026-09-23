"""Validate documentation navigation, math, gallery, and API-link contracts."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def _nav_paths(node):
    if isinstance(node, str):
        yield node
    elif isinstance(node, list):
        for item in node:
            yield from _nav_paths(item)
    elif isinstance(node, dict):
        for value in node.values():
            yield from _nav_paths(value)


def main() -> None:
    config_text = (ROOT / "mkdocs.yml").read_text(encoding="utf-8")
    nav = re.findall(
        r":\s+([A-Za-z0-9_./-]+\.md)\s*$",
        config_text,
        flags=re.MULTILINE,
    )
    missing_nav = sorted(path for path in nav if not (DOCS / path).exists())
    if missing_nav:
        raise RuntimeError(f"missing MkDocs nav targets: {missing_nav}")

    math_page = (DOCS / "methods" / "mathematical-reference.md").read_text(
        encoding="utf-8"
    )
    root_math = (ROOT / "MATHEMATICAL_CONTRACTS.md").read_text(encoding="utf-8")
    required_math = {
        "functional_trapezoid_weights()",
        "fit_mfpca()",
        "fit_multilevel_fpca()",
        "fit_compositional_fpca()",
        "multiplier_functional_mean_band()",
        "wild_bootstrap_fpca_projection()",
        "fpca_wild_bootstrap_projection_family_test()",
        "fpca_wild_bootstrap_family_test_monte_carlo_diagnostics()",
        "split_conformal_fpca_anomaly()",
        "delay_embed_trajectory()",
        "recurrence_matrix()",
        "recurrence_radius_profile()",
        "rqa_parameter_sensitivity()",
        "bootstrap_rqa_metric_means()",
        "windowed_rqa_trajectory_set()",
        "estimate_largest_lyapunov_rosenstein()",
        "estimate_largest_lyapunov_kantz()",
        "kantz_parameter_sensitivity()",
        "lyapunov_parameter_sensitivity()",
        "surrogate_nonlinearity_test()",
        "return_map_stability()",
    }
    missing_math_api = sorted(name for name in required_math if name not in math_page)
    if missing_math_api:
        raise RuntimeError(
            f"mathematical reference is missing API contracts: {missing_math_api}"
        )
    if math_page.count("$") < 20 or root_math.count("$") < 10:
        raise RuntimeError("mathematical contract pages lost expected LaTeX blocks")

    math_fragments: set[str] = set()
    for markdown_path in DOCS.rglob("*.md"):
        source = markdown_path.read_text(encoding="utf-8")
        math_fragments.update(
            re.findall(r"mathematical-reference\.md#([A-Za-z0-9_-]+)", source)
        )
    missing_fragments = sorted(
        fragment
        for fragment in math_fragments
        if f"{{ #{fragment} }}" not in math_page
    )
    if missing_fragments:
        raise RuntimeError(
            "mathematical-reference links use undefined explicit anchors: "
            f"{missing_fragments}"
        )

    mathjax = (DOCS / "javascripts" / "mathjax.js").read_text(encoding="utf-8")
    if "document$.subscribe" not in mathjax or "typesetPromise" not in mathjax:
        raise RuntimeError("MathJax instant-navigation hook is incomplete")

    gallery = (DOCS / "methods" / "visual-gallery.md").read_text(encoding="utf-8")
    asset_refs = sorted(set(re.findall(r"\.\./assets/gallery/([^)\s]+\.svg)", gallery)))
    if len(asset_refs) < 16:
        raise RuntimeError("visual gallery must reference at least sixteen SVG figures")
    missing_assets = sorted(
        name for name in asset_refs if not (DOCS / "assets" / "gallery" / name).exists()
    )
    if missing_assets:
        raise RuntimeError(f"gallery assets were not generated: {missing_assets}")

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for required in ("MATHEMATICAL_CONTRACTS.md", "FUNCTION_EQUATION_INDEX.md", "WORKFLOW_ATLAS.md", "Visual gallery", "0.30.0.dev0"):
        if required not in readme:
            raise RuntimeError(f"README integration missing {required!r}")

    public_api = (ROOT / "src" / "eyetrajectoriespy" / "__init__.py").read_text(
        encoding="utf-8"
    )
    documented = (DOCS / "reference" / "api.md").read_text(encoding="utf-8")
    symbols = set(re.findall(r"::: eyetrajectoriespy\.([A-Za-z0-9_]+)", documented))
    unresolved = sorted(name for name in symbols if f'"{name}"' not in public_api)
    if unresolved:
        raise RuntimeError(f"documented API symbols are not exported: {unresolved}")

    print(
        "docs contracts OK: "
        f"{len(nav)} nav targets, "
        f"{len(symbols)} documented API symbols, "
        f"{len(asset_refs)} gallery assets, "
        f"{len(math_fragments)} mathematical deep links"
    )


if __name__ == "__main__":
    main()
