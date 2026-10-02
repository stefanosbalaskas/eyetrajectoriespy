"""Temporary deterministic patcher for the post-0.12 documentation tranche."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def patch(path, old, new):
    p = ROOT / path
    text = p.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"{path}: patch anchor count={text.count(old)}")
    p.write_text(text.replace(old, new, 1), encoding="utf-8")


def main():
    patch(
        "docs/methods/status-roadmap.md",
        "## 0.12 final-promotion checkpoint\n\nThe current development line is **0.12.0**.\n\nThe sparse-MFPCA/joint-PACE methodology surface is frozen. Production-installed `0.12.0rc1` observation is complete, so the next release step is literal final `0.12.0` exact-version qualification. This checkpoint adds no methodology and does not reopen tuning, estimator, or API decisions.",
        "## Current stable scientific surface — 0.12.0\n\n`0.12.0` is the current stable release.\n\nThe 0.12 sparse-MFPCA/joint-PACE line is complete and frozen. The package is not currently committed to another estimator tranche.\n\nNear-term work prioritizes:\n\n- real-use and API audit;\n- documentation and worked examples;\n- complete plotting/gallery coverage;\n- public benchmark/case-study material;\n- software/methodology dissemination;\n- evaluation of 1.0 API-stability requirements.\n\nFuture methodology is evidence-driven rather than version-number-driven.",
    )

    path = "docs/guides/sparse-irregular-fpca.md"
    patch(path, "# Sparse irregular FPCA with PACE", "# Sparse univariate FPCA / PACE")
    patch(
        path,
        "!!! note \"Current backend and native roadmap\"\n    In 0.9.1, `fit_sparse_fpca_fdapy()` is an explicitly backend-named\n    compatibility path. FDApy is not a core dependency. The 0.10 development\n    branch now contains the native `fit_sparse_fpca()` estimator, while FDApy\n    remains a validation/reference implementation. See the\n    [0.10 development contract](../development/native-sparse-fpca.md).",
        "!!! success \"Stable native univariate sparse workflow\"\n    `fit_sparse_fpca()` is the stable native univariate sparse FPCA/PACE route. FDApy remains an optional compatibility/reference backend rather than a core dependency.\n\n!!! info \"Need jointly modelled sparse x/y gaze?\"\n    `fit_sparse_fpca()` models one functional coordinate. For jointly observed sparse planar gaze with direct $C_{xy}(s,t)$ estimation and joint PACE scores, use [`fit_sparse_mfpca()`](sparse-multivariate-fpca.md).",
    )
    patch(path, "## Native 0.10 development estimator", "## Native stable estimator")
    patch(path, "## Current 0.9.1 compatibility backend: FDApy PACE interoperability", "## Optional FDApy compatibility/reference backend")
    patch(path, "## Why only one gaze dimension?", "## Why this page remains univariate")
    patch(
        path,
        "The current public contract is deliberately **univariate sparse PACE**.\n\nFDApy supports sparse multivariate functional-data representations and sparse MFPCA. However, the documented MFPCA score transform currently uses numerical integration or inner-product scores rather than PACE conditional-expectation scoring.\n\nTherefore:\n\n- `fit_sparse_fpca_fdapy(..., dimension=\"x\")` is a valid sparse univariate PACE analysis of x(t);\n- fitting y(t) separately is another univariate analysis;\n- two separate univariate analyses are **not** equivalent to joint multivariate FPCA of [x(t), y(t)];\n- eyetrajectoriespy does not label the current adapter “multivariate PACE.”",
        "This page documents the univariate route. Two separate univariate sparse analyses are **not** equivalent to joint multivariate FPCA of [x(t), y(t)] because they omit cross-channel covariance. Stable native joint x/y PACE is documented separately in the [sparse planar MFPCA / joint PACE guide](sparse-multivariate-fpca.md). The optional FDApy adapter remains explicitly backend-named and should not be relabelled as the native joint estimator.",
    )

    path = "docs/concepts/decision-map.md"
    patch(
        path,
        "| Where does gaze move over trial time? | joint 2-D MFPCA | harmonize stimulus geometry first |\n| Are curves sampled at different times? | native irregular trajectories | do not force a grid during import |",
        "| Joint x/y trajectories already represented on a defensible common grid | `fit_mfpca()` | harmonize stimulus geometry first |\n| Sparse/irregular **paired x/y** samples with the same retained timestamps per curve | `fit_sparse_mfpca()` | verify paired timestamps; retain native samples; declare smoothing/noise/PSD policy |\n| Sparse/irregular single functional coordinate | `fit_sparse_fpca()` | retain native samples; do not manufacture dense trajectories |\n| Are curves sampled at different times? | native irregular trajectories | do not force a grid during import |",
    )
    patch(
        path,
        "## If the sample times are irregular\n\nStart with <code>from_irregular_long_dataframe_native()</code>.",
        "## If the sample times are irregular\n\n**Are x and y jointly observed at the same retained timestamps?** If yes and the paired planar covariance is the target, use `fit_sparse_mfpca()`. If no, do not silently align the channels into the joint estimator.\n\nStart with <code>from_irregular_long_dataframe_native()</code>.",
    )

    patch(
        "mkdocs.yml",
        "          - Sparse irregular / PACE FPCA: guides/sparse-irregular-fpca.md",
        "          - Sparse univariate FPCA / PACE: guides/sparse-irregular-fpca.md\n          - Sparse planar MFPCA / joint PACE: guides/sparse-multivariate-fpca.md",
    )
    patch(
        "mkdocs.yml",
        "          - Sparse PACE FPCA: examples/sparse-pace-fpca.md",
        "          - Sparse PACE FPCA: examples/sparse-pace-fpca.md\n          - Sparse planar MFPCA / joint PACE: examples/sparse-mfpca.md",
    )

    css = ROOT / "docs/assets/extra.css"
    text = css.read_text(encoding="utf-8")
    if ".et-hero" not in text:
        text += """\n\n.et-hero { display:grid; grid-template-columns:minmax(0,1.05fr) minmax(320px,.95fr); gap:2rem; align-items:center; margin:1.2rem 0 2.2rem; }\n.et-hero img { width:100%; max-height:420px; object-fit:contain; }\n.et-version-pill { display:inline-block; padding:.28rem .65rem; border:1px solid var(--et-line); border-radius:999px; font-size:.82rem; font-weight:650; }\n@media (max-width:800px) { .et-hero { grid-template-columns:1fr; } }\n"""
        css.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
