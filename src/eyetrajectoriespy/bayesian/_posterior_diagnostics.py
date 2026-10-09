"""Experimental posterior diagnostics for identifiable Bayesian functionals.

This optional dependency is imported lazily so docs/plot collection can import
the installed package without PyMC or ArviZ. These diagnostics are research-only.
"""
from __future__ import annotations
import numpy as np

def _identified_chain_diagnostics(draws:np.ndarray)->dict:
    """Rank Rhat, bulk/tail ESS and MCSE of an invariant scalar functional.

    This is the only correct level for evaluating rank-1 covariance
    functionals when loading signs are not identified. Raw loading
    Rhat remains separately available and is never silently ignored.
    """
    import arviz as az
    a=np.asarray(draws,dtype=float)
    if a.ndim!=2 or a.shape[0]<2 or a.shape[1]<20 or not np.isfinite(a).all():
        raise ValueError("need >=2 finite chains with >=20 draws for diagnostics")
    fields={
        "rank_rhat":float(np.asarray(az.rhat(a,method="rank"))),
        "bulk_ess":float(np.asarray(az.ess(a,method="bulk"))),
        "tail_ess":float(np.asarray(az.ess(a,method="tail"))),
        # Portable approximate MCSE from the marginal SD and bulk ESS.
        # This is NOT ArviZ's spectral MCSE estimator or a convergence gate.
        "mcse_mean_bulk_ess_approx":float(
            np.std(a.reshape(-1),ddof=1)/np.sqrt(
                float(np.asarray(az.ess(a,method="bulk"))))),
    }
    if not all(np.isfinite(v) and v>=0 for v in fields.values()):
        raise ValueError("invalid identifiable population diagnostic")
    return fields


