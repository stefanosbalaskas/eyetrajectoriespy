"""Apply the post-0.12 sparse-MFPCA plotting/API development tranche.

This is a branch-only, fail-closed migration used to keep version contracts and
large public-export files synchronized while developing 0.12.1.dev0.
"""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.12.1.dev0"
PREVIOUS = "0.12.0"


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def write(path: str, text: str) -> None:
    (ROOT / path).write_text(text, encoding="utf-8")


def replace_once(path: str, old: str, new: str) -> None:
    text = read(path)
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{path}: expected exactly one replacement target, found {count}: {old!r}")
    write(path, text.replace(old, new, 1))


def set_json_version(path: str, field: str) -> None:
    target = ROOT / path
    payload = json.loads(target.read_text(encoding="utf-8"))
    if payload.get(field) != PREVIOUS:
        raise RuntimeError(f"{path}: expected {field}={PREVIOUS!r}, got {payload.get(field)!r}")
    payload[field] = VERSION
    target.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def update_public_api() -> None:
    path = "src/eyetrajectoriespy/__init__.py"
    text = read(path)
    version_old = '__version__ = "0.12.0"'
    if text.count(version_old) != 1:
        raise RuntimeError("package version declaration drifted")
    text = text.replace(version_old, f'__version__ = "{VERSION}"', 1)

    import_anchor = '''from .sparse_multivariate import (\n    fit_sparse_mfpca,\n    sparse_mfpca_reporting_text,\n    sparse_mfpca_score_frame,\n)\n'''
    import_block = import_anchor + '''from .sparse_multivariate_plotting import (\n    plot_sparse_mfpca_component,\n    plot_sparse_mfpca_covariance_blocks,\n    plot_sparse_mfpca_cross_covariance,\n    plot_sparse_mfpca_score_diagnostics,\n)\n'''
    if text.count(import_anchor) != 1:
        raise RuntimeError("sparse multivariate import anchor drifted")
    text = text.replace(import_anchor, import_block, 1)

    all_anchor = '    "SparseMFPCAResult",\n'
    all_block = all_anchor + '''    "plot_sparse_mfpca_component",\n    "plot_sparse_mfpca_covariance_blocks",\n    "plot_sparse_mfpca_cross_covariance",\n    "plot_sparse_mfpca_score_diagnostics",\n'''
    if text.count(all_anchor) != 1:
        raise RuntimeError("SparseMFPCAResult __all__ anchor drifted")
    text = text.replace(all_anchor, all_block, 1)
    write(path, text)


def update_release_metadata() -> None:
    replace_once("pyproject.toml", 'version = "0.12.0"', f'version = "{VERSION}"')
    replace_once("CITATION.cff", "version: 0.12.0\n", f"version: {VERSION}\n")
    replace_once("CITATION.cff", "date-released: 2026-10-01\n", "date-released: 2026-10-02\n")

    readiness_path = ROOT / "RELEASE_READINESS.json"
    readiness = json.loads(readiness_path.read_text(encoding="utf-8"))
    if readiness.get("current_development_version") != PREVIOUS:
        raise RuntimeError("RELEASE_READINESS current development version drifted")
    if readiness.get("production_release_ready") is not False or readiness.get("github_release_ready") is not False:
        raise RuntimeError("post-0.12 development must begin with publication readiness disarmed")
    readiness["current_development_version"] = VERSION
    notes = readiness.setdefault("notes", [])
    note = (
        "0.12.1.dev0 is a post-0.12 visualization/API development line. "
        "It adds sparse-MFPCA plotting helpers only; 0.12.0 remains the immutable published stable release."
    )
    if note not in notes:
        notes.append(note)
    readiness_path.write_text(json.dumps(readiness, indent=2) + "\n", encoding="utf-8")

    for filename in (
        "CANONICAL_WORKFLOWS.json",
        "REFERENCE_VALIDATION.json",
        "VALIDATION_TOLERANCES.json",
        "PERFORMANCE_ENVELOPE.json",
    ):
        set_json_version(filename, "package_version")


def update_governance_tests() -> None:
    replace_once(
        "tests/test_public_api.py",
        'assert et.__version__=="0.12.0"',
        f'assert et.__version__=="{VERSION}"',
    )

    path = "tests/test_release_hardening.py"
    text = read(path)
    text = text.replace('CURRENT_RELEASE_CANDIDATE = "0.12.0"', f'CURRENT_DEVELOPMENT_VERSION = "{VERSION}"')
    text = text.replace(
        "def test_release_version_contract_agrees_for_release_candidate():\n    module = _load_script(\"verify_release_version.py\")\n    assert module.verify_version_contract() == CURRENT_RELEASE_CANDIDATE\n",
        "def test_release_version_contract_agrees_for_development_line():\n    module = _load_script(\"verify_release_version.py\")\n    assert module.verify_version_contract() == CURRENT_DEVELOPMENT_VERSION\n",
    )
    old = '''def test_release_candidate_version_contract_is_production_eligible():\n    module = _load_script("verify_release_version.py")\n    assert (\n        module.verify_version_contract(\n            tag=f"v{CURRENT_RELEASE_CANDIDATE}",\n            production=True,\n        )\n        == CURRENT_RELEASE_CANDIDATE\n    )\n'''
    new = '''def test_development_version_contract_is_not_production_eligible():\n    module = _load_script("verify_release_version.py")\n    with pytest.raises(RuntimeError, match="development versions"):\n        module.verify_version_contract(\n            tag=f"v{CURRENT_DEVELOPMENT_VERSION}",\n            production=True,\n        )\n'''
    if old not in text:
        raise RuntimeError("production-eligibility release-hardening test drifted")
    text = text.replace(old, new, 1)
    if "CURRENT_RELEASE_CANDIDATE" in text:
        raise RuntimeError("stale CURRENT_RELEASE_CANDIDATE reference remains")
    write(path, text)


def update_docs_contracts() -> None:
    path = "scripts/_validate_docs_contracts_base.py"
    text = read(path)
    expected = 'payload.get("package_version") != "0.12.0"'
    if text.count(expected) != 1:
        raise RuntimeError("ledger package-version validator drifted")
    text = text.replace(expected, f'payload.get("package_version") != "{VERSION}"', 1)
    expected = 'manifest.get("package_version") != "0.12.0"'
    if text.count(expected) != 1:
        raise RuntimeError("workflow manifest version validator drifted")
    text = text.replace(expected, f'manifest.get("package_version") != "{VERSION}"', 1)
    expected = 'release_readiness.get("current_development_version") != "0.12.0"'
    if text.count(expected) != 1:
        raise RuntimeError("release-readiness validator drifted")
    text = text.replace(expected, f'release_readiness.get("current_development_version") != "{VERSION}"', 1)
    write(path, text)

    roadmap = read("docs/methods/status-roadmap.md")
    anchor = "The current stable pre-1.0 line is **0.12.0**.\n"
    if roadmap.count(anchor) != 1:
        raise RuntimeError("roadmap stable-line anchor drifted")
    roadmap = roadmap.replace(
        anchor,
        anchor + f"\nThe current development line is **{VERSION}**. It adds visualization helpers only; the 0.12 estimator remains frozen.\n",
        1,
    )
    write("docs/methods/status-roadmap.md", roadmap)

    readme = read("README.md")
    anchor = "**Stable:** `0.12.0` · **Python:** 3.11–3.13\n"
    if readme.count(anchor) != 1:
        raise RuntimeError("README stable badge anchor drifted")
    readme = readme.replace(
        anchor,
        anchor + f"\n**Development source line:** `{VERSION}` (sparse-MFPCA visualization/API additions; not published).\n",
        1,
    )
    write("README.md", readme)

    guide = read("docs/guides/sparse-multivariate-fpca.md")
    old = '''## Plots\n\nThe 0.12 site includes deterministic documentation-only covariance-block and vector-eigenfunction figures generated directly from public result arrays. Dedicated `plot_sparse_mfpca_*` public helpers are a subsequent API addition rather than a retroactive change to immutable 0.12.0.\n\n![Sparse planar covariance blocks](../assets/gallery/sparse-mfpca-covariance-blocks.svg)\n\n![Sparse planar first eigenfunction](../assets/gallery/sparse-mfpca-eigenfunction.svg)\n'''
    new = '''## Plots\n\nThe post-0.12 development line adds four public visualization helpers without changing the estimator or result schema:\n\n```python\nfrom eyetrajectoriespy import (\n    plot_sparse_mfpca_component,\n    plot_sparse_mfpca_covariance_blocks,\n    plot_sparse_mfpca_cross_covariance,\n    plot_sparse_mfpca_score_diagnostics,\n)\n\nplot_sparse_mfpca_component(fit, component=0)\nplot_sparse_mfpca_covariance_blocks(fit, stage="used")\nplot_sparse_mfpca_cross_covariance(fit, stage="used")\nplot_sparse_mfpca_score_diagnostics(fit)\n```\n\n`stage="used"` visualizes the covariance blocks after the declared PSD policy; `stage="smoothed"` exposes the retained directly smoothed pre-PSD blocks. The cross-covariance plot keeps C_xy and C_yx directional orientation explicit.\n\n![Sparse planar covariance blocks](../assets/gallery/sparse-mfpca-covariance-blocks.svg)\n\n![Sparse planar first eigenfunction](../assets/gallery/sparse-mfpca-eigenfunction.svg)\n'''
    if old not in guide:
        raise RuntimeError("sparse-MFPCA plots guide block drifted")
    write("docs/guides/sparse-multivariate-fpca.md", guide.replace(old, new, 1))


def update_gallery_manifest() -> None:
    path = "scripts/docs_gallery_manifest.py"
    text = read(path)
    anchor = '    "plot_sparse_fpca_score_diagnostics": {"asset": "sparse-fpca-score-conditioning.svg", "category": "sparse-fda", "quantity": "PACE conditional-system diagnostics", "equation": "sparse-fpca-pace", "example": "sparse-pace-fpca"},\n'
    if text.count(anchor) != 1:
        raise RuntimeError("sparse gallery manifest anchor drifted")
    addition = anchor + (
        '    "plot_sparse_mfpca_component": {"asset": "sparse-mfpca-component.svg", "category": "sparse-fda", "quantity": "Sparse planar MFPCA component interpretation", "equation": "sparse-mfpca-joint-pace", "example": "sparse-mfpca"},\n'
        '    "plot_sparse_mfpca_covariance_blocks": {"asset": "sparse-mfpca-covariance-blocks-public.svg", "category": "sparse-fda", "quantity": "Full 2x2 sparse planar covariance operator", "equation": "sparse-mfpca-joint-pace", "example": "sparse-mfpca"},\n'
        '    "plot_sparse_mfpca_cross_covariance": {"asset": "sparse-mfpca-cross-covariance.svg", "category": "sparse-fda", "quantity": "Directional Cxy/Cyx cross-covariance surfaces", "equation": "sparse-mfpca-joint-pace", "example": "sparse-mfpca"},\n'
        '    "plot_sparse_mfpca_score_diagnostics": {"asset": "sparse-mfpca-score-diagnostics.svg", "category": "sparse-fda", "quantity": "Joint-PACE conditioning and solve status", "equation": "sparse-mfpca-joint-pace", "example": "sparse-mfpca"},\n'
    )
    write(path, text.replace(anchor, addition, 1))


def main() -> None:
    update_public_api()
    update_release_metadata()
    update_governance_tests()
    update_docs_contracts()
    update_gallery_manifest()
    print(f"applied sparse-MFPCA plotting tranche for {VERSION}")


if __name__ == "__main__":
    main()
