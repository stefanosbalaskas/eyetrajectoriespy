from __future__ import annotations

from pathlib import Path
import tomllib


ROOT = Path(__file__).resolve().parents[1]


def test_external_fda_backends_are_not_core_runtime_dependencies() -> None:
    """General FDA reference/interop libraries must remain outside core runtime."""
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    core = {str(item).lower() for item in data["project"]["dependencies"]}

    forbidden = ("fdapy", "scikit-fda", "fdasrsf")
    for package in forbidden:
        assert not any(package in requirement for requirement in core), (
            f"{package} must remain optional/reference-only, not a core runtime dependency"
        )


def test_fdapy_sparse_backend_stays_explicitly_backend_named() -> None:
    """The transitional FDApy path must not masquerade as the native estimator."""
    source = (ROOT / "src" / "eyetrajectoriespy" / "sparse.py").read_text(
        encoding="utf-8"
    )
    assert "def fit_sparse_fpca_fdapy(" in source
    assert "def fit_sparse_fpca(" not in source
