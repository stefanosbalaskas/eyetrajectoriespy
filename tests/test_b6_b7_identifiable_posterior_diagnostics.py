"""Rotation- and loading-sign-invariant B6/B7 population diagnostics."""
from __future__ import annotations

import numpy as np
import pytest

from scripts.run_b6_b7_independent_pymc_nuts import _identified_chain_diagnostics


def test_identified_covariance_can_mix_despite_unidentified_loading_sign():
    az=pytest.importorskip("arviz")
    rng=np.random.default_rng(77123)
    # The same rank-one covariance admits L and -L. Raw signed loadings
    # can be split across chains while L^2 is scientifically unchanged.
    load=rng.normal(.35,.05,size=(2,550))
    load[1]*=-1
    raw_loading_rhat=float(np.asarray(az.rhat(load,method="rank")))
    invariant=_identified_chain_diagnostics(load**2)
    assert raw_loading_rhat>1.1
    assert invariant["rank_rhat"]<1.05
    assert invariant["bulk_ess"]>100
    assert invariant["tail_ess"]>100
    assert invariant["mcse_mean_bulk_ess_approx"]>=0


def test_mean_population_diagnostics_have_all_four_convergence_metrics():
    pytest.importorskip("arviz")
    rng=np.random.default_rng(303)
    x=rng.normal(size=(2,250))
    d=_identified_chain_diagnostics(x)
    assert set(d)=={"rank_rhat","bulk_ess","tail_ess","mcse_mean_bulk_ess_approx"}
    assert d["rank_rhat"]>=0
    assert d["bulk_ess"]>0
    assert d["tail_ess"]>0
    assert d["mcse_mean_bulk_ess_approx"]>=0
    with pytest.raises(ValueError,match="finite"):
        _identified_chain_diagnostics(np.full((2,30),np.nan))
    with pytest.raises(ValueError,match=">=2"):
        _identified_chain_diagnostics(x[:1])
