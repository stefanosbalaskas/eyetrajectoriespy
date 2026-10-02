"""Programmatic mathematical contracts for public scientific APIs.

The established registry is preserved byte-for-byte in
``_mathematical_contracts_base``. This extension layer adds the stable 0.12
sparse-planar MFPCA / joint-PACE contract without rewriting earlier contracts.
The registry remains metadata only; it does not execute or alter estimators.
"""

from __future__ import annotations

import pandas as pd

from ._mathematical_contracts_base import (
    MathematicalContract,
    _CONTRACTS as _BASE_CONTRACTS,
)


_SPARSE_MFPCA_CONTRACT = MathematicalContract(
    key="sparse-mfpca-joint-pace",
    title="Native sparse multivariate FPCA / joint PACE",
    public_api=("fit_sparse_mfpca",),
    equations=(
        r"\mathbf X_i(t)=\begin{bmatrix}X_i(t)\\Y_i(t)\end{bmatrix}",
        r"\mathbf C(s,t)=\begin{bmatrix}"
        r"C_{xx}(s,t)&C_{xy}(s,t)\\"
        r"C_{yx}(s,t)&C_{yy}(s,t)"
        r"\end{bmatrix}",
        r"C_{yx}(s,t)=C_{xy}(t,s)",
        r"\int \mathbf C(s,t)\boldsymbol\phi_k(s)\,ds="
        r"\lambda_k\boldsymbol\phi_k(t)",
        r"\widehat{\boldsymbol\Sigma}_i="
        r"\widehat{\mathbf C}_i^{TM}"
        r"+I_{m_i}\otimes\mathbf R_\epsilon+\gamma I",
        r"\widehat\xi_{ik}="
        r"\widehat\lambda_k"
        r"\widehat{\boldsymbol\phi}_{ik}^{\top}"
        r"\widehat{\boldsymbol\Sigma}_i^{-1}"
        r"\{\mathbf y_i-\widehat{\boldsymbol\mu}_i\}",
    ),
    site_anchor="sparse-mfpca-joint-pace",
    scope=(
        "Two jointly observed planar sparse functional coordinates with direct "
        "directional cross-covariance estimation, explicit mean and covariance "
        "bandwidths, full joint PSD handling, declared measurement-error "
        "covariance, and full-covariance joint PACE. Raw sparse curves are not "
        "interpolated to a common grid; automatic bandwidth or arbitrary "
        "cross-channel noise estimation is not implied."
    ),
)

# Keep documentation order: univariate sparse PACE, then joint sparse planar PACE.
_CONTRACTS = (
    *_BASE_CONTRACTS[:3],
    _SPARSE_MFPCA_CONTRACT,
    *_BASE_CONTRACTS[3:],
)


def list_mathematical_contracts() -> tuple[MathematicalContract, ...]:
    """Return all mathematical contracts in stable documentation order."""

    return _CONTRACTS


def get_mathematical_contract(name: str) -> MathematicalContract:
    """Return a mathematical contract by key or registered public function."""

    if not isinstance(name, str):
        raise TypeError("name must be a string")
    for contract in _CONTRACTS:
        if name == contract.key or name in contract.public_api:
            return contract
    raise KeyError(f"No mathematical contract is registered for {name!r}")


def mathematical_contract_frame() -> pd.DataFrame:
    """Return one tidy row per registered public function and its LaTeX contract."""

    rows = []
    for contract in _CONTRACTS:
        latex = "\n\n".join(contract.equations)
        for function in contract.public_api:
            rows.append(
                {
                    "contract_key": contract.key,
                    "title": contract.title,
                    "function": function,
                    "latex": latex,
                    "site_anchor": contract.site_anchor,
                    "scope": contract.scope,
                }
            )
    return pd.DataFrame(rows)
