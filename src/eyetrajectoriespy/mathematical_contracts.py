"""Programmatic mathematical contracts for public scientific APIs.

The registry is metadata: it does not execute estimators or change numerical
results. It provides one machine-readable source linking scientific functions to
implementation-matched LaTeX, documentation anchors, and scope statements.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True, slots=True)
class MathematicalContract:
    """Mathematical specification attached to one or more public APIs."""

    key: str
    title: str
    public_api: tuple[str, ...]
    equations: tuple[str, ...]
    site_anchor: str
    scope: str


_CONTRACTS = (
    MathematicalContract(
        key="quadrature",
        title="Observed-grid trapezoidal quadrature",
        public_api=("functional_trapezoid_weights",),
        equations=(
            r"w_1=\frac{t_2-t_1}{2},\quad "
            r"w_M=\frac{t_M-t_{M-1}}{2},\quad "
            r"w_m=\frac{(t_m-t_{m-1})+(t_{m+1}-t_m)}{2}",
        ),
        site_anchor="quadrature",
        scope="Strictly increasing observed grids; optional normalization only rescales the weights to sum to one.",
    ),
    MathematicalContract(
        key="fpca",
        title="Quadrature-weighted FPCA / MFPCA",
        public_api=(
            "fit_fpca",
            "fit_mfpca",
            "transform_fpca",
            "reconstruct_fpca",
            "component_trajectories",
        ),
        equations=(
            r"Z_{i,m,d}="
            r"\frac{G_{id}(t_m)-\widehat\mu_d(t_m)}{s_d}\sqrt{w_m}",
            r"\widehat{\mathbf G}^{(K)}_i(t)="
            r"\widehat{\boldsymbol\mu}(t)+"
            r"\sum_{k=1}^{K}\widehat\xi_{ik}\widehat{\boldsymbol\phi}_k(t)",
        ),
        site_anchor="fpca",
        scope="Common-grid functional PCA with explicit channel scaling; retained-component interpretation is conditional on the fitted basis.",
    ),
    MathematicalContract(
        key="functional-l2",
        title="Integrated functional L2 distance",
        public_api=("functional_l2_distance", "pairwise_functional_distances"),
        equations=(
            r"d_{L^2}(\mathbf a,\mathbf b)="
            r"\left[\sum_m w_m\sum_d\omega_d"
            r"\{a_d(t_m)-b_d(t_m)\}^2\right]^{1/2}",
        ),
        site_anchor="functional-l2",
        scope="Complete trajectories on a common grid; optional dimension weights must be non-negative.",
    ),
    MathematicalContract(
        key="multilevel",
        title="Two-level participant / trial decomposition",
        public_api=("fit_multilevel_fpca",),
        equations=(
            r"\mathbf G_{ij}(t)=\boldsymbol\mu(t)+\mathbf U_i(t)+\mathbf V_{ij}(t)",
            r"\mathbf U_i(t)=\overline{\mathbf G}_{i\cdot}(t)-\boldsymbol\mu(t),"
            r"\quad "
            r"\mathbf V_{ij}(t)=\mathbf G_{ij}(t)-\overline{\mathbf G}_{i\cdot}(t)",
        ),
        site_anchor="multilevel",
        scope="Transparent two-level functional ANOVA followed by separate FPCAs; not a full probabilistic functional mixed model.",
    ),
    MathematicalContract(
        key="compositional",
        title="Compositional AOI additive log-ratio transform",
        public_api=(
            "alr_transform",
            "inverse_alr",
            "fit_compositional_fpca",
            "reconstruct_compositional_fpca",
        ),
        equations=(
            r"z_k(t)=\log\frac{p_k^\epsilon(t)}{p_r^\epsilon(t)},\quad k\ne r",
            r"p_k(t)=\frac{q_k(t)}{\sum_{\ell=1}^{K}q_\ell(t)}",
        ),
        site_anchor="compositional",
        scope="Simplex-valued AOI probabilities with explicit reference component and zero-replacement epsilon.",
    ),
    MathematicalContract(
        key="registration",
        title="Landmark registration and phase displacement",
        public_api=("register_to_landmarks", "warping_displacement", "phase_summary"),
        equations=(
            r"\mathbf G_i^{\mathrm{reg}}(t)=\mathbf G_i\{h_i(t)\}",
            r"\Delta_i(t)=h_i(t)-t",
        ),
        site_anchor="registration",
        scope="Monotone piecewise-linear landmark warping; phase is retained rather than silently discarded.",
    ),
    MathematicalContract(
        key="mean-band",
        title="Simultaneous functional mean multiplier band",
        public_api=("multiplier_functional_mean_band",),
        equations=(
            r"M^{(b)}=\max_{m,d}\left|"
            r"\frac{n^{-1/2}\sum_i e_i^{(b)}\{X_{id}(t_m)-\overline X_d(t_m)\}}"
            r"{\widehat\sigma_d(t_m)}\right|",
            r"\overline X_d(t_m)\pm "
            r"c_{1-\alpha}\frac{\widehat\sigma_d(t_m)}{\sqrt n}",
        ),
        site_anchor="mean-band",
        scope="Simultaneous calibration over the observed time-by-dimension grid, with curve or equal-weight participant inference units.",
    ),
    MathematicalContract(
        key="fpcr",
        title="Scalar-on-function regression through FPC scores",
        public_api=("fit_scalar_on_function_regression",),
        equations=(
            r"Y_i=\beta_0+\sum_{k=1}^{K}\beta_k\xi_{ik}"
            r"+\mathbf z_i^\top\boldsymbol\gamma+\varepsilon_i",
            r"\operatorname{logit}\{\Pr(Y_i=1)\}="
            r"\beta_0+\sum_{k=1}^{K}\beta_k\xi_{ik}"
            r"+\mathbf z_i^\top\boldsymbol\gamma",
        ),
        site_anchor="fpcr",
        scope="Score-space approximation; Gaussian and binomial fits have distinct inferential assumptions and no automatic component-selection uncertainty.",
    ),
    MathematicalContract(
        key="wild-bootstrap",
        title="Heteroscedastic Gaussian FPCR wild bootstrap",
        public_api=("wild_bootstrap_fpca_projection",),
        equations=(
            r"Y_i^*=\widehat Y_{i,k}+\widehat\varepsilon_{i,k}W_i",
            r"\widehat{\mathrm{SE}}_0="
            r"\left[\frac{1}{n}\mathbf d_0^\top"
            r"\widehat{\boldsymbol\Lambda}_h\mathbf d_0\right]^{1/2}",
            r"T_0^*="
            r"\frac{\widehat\theta_{0,h}^*-\widehat\theta_{0,g}}"
            r"{\widehat{\mathrm{SE}}_0^*},\quad g=k,\ h\ge g",
        ),
        site_anchor="wild-bootstrap",
        scope="Fixed-regressor Gaussian FPCR with independent curve rows; not clustered wild bootstrap or future-outcome prediction.",
    ),
    MathematicalContract(
        key="simultaneous-wild-bootstrap",
        title="Simultaneous fixed-target wild-bootstrap calibration",
        public_api=("fpca_wild_bootstrap_projection_simultaneous_interval",),
        equations=(
            r"M^{*(b)}=\max_{1\le j\le J}|T_j^{*(b)}|",
        ),
        site_anchor="simultaneous-wild-bootstrap",
        scope="One predeclared fixed-target family using the stored joint root matrix; no adaptive target-family guarantee.",
    ),
    MathematicalContract(
        key="family-tests",
        title="Fixed-family wild-bootstrap hypothesis tests",
        public_api=("fpca_wild_bootstrap_projection_family_test",),
        equations=(
            r"T_j=\frac{\widehat\theta_j-\theta_{0j}}{\widehat{\mathrm{SE}}_j}",
            r"p_j=\frac{1+\sum_{b=1}^{B}"
            r"\mathbb I(|T_j^{*(b)}|\ge |T_j|)}{B+1}",
            r"p_j^{\max}=\frac{1+\sum_{b=1}^{B}"
            r"\mathbb I(M^{*(b)}\ge |T_j|)}{B+1}",
        ),
        site_anchor="family-tests",
        scope="Two-sided post-processing tests for a declared fixed family; strong FWER for arbitrary subsets is not claimed without additional theory.",
    ),
    MathematicalContract(
        key="monte-carlo",
        title="Finite-bootstrap Monte Carlo precision",
        public_api=("fpca_wild_bootstrap_family_test_monte_carlo_diagnostics",),
        equations=(
            r"\widehat q=\frac{r}{B}",
            r"\widehat{\mathrm{MCSE}}="
            r"\sqrt{\frac{\widehat q(1-\widehat q)}{B}}",
        ),
        site_anchor="monte-carlo",
        scope="Simulation precision of retained bootstrap tail probabilities; not scientific-effect uncertainty and not sequential-stopping inference.",
    ),
    MathematicalContract(
        key="conformal",
        title="Split-conformal FPCA anomaly p-value",
        public_api=("split_conformal_fpca_anomaly",),
        equations=(
            r"p_{\mathrm{conf}}="
            r"\frac{1+\sum_{i=1}^{m}\mathbb I(A_i\ge A_{\mathrm{new}})}{m+1}",
        ),
        site_anchor="conformal",
        scope="Marginal curve-level split-conformal interpretation under exchangeability; review flags are never automatic exclusions.",
    ),
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
