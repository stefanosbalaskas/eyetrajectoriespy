"""Test only identified scalar population chain convergence; do not test raw loading signs."""
import numpy as np
import pytest

from scripts.run_b6_b7_longchain_identified_geometry import (
    identified_mcse_geometry, DESIGNS, METHODS, run_design,
)


def test_identified_longchain_matches_independent_arviz_reference():
    import arviz as az
    rng=np.random.default_rng(987)
    draws=rng.normal(size=(4,1000))
    d=identified_mcse_geometry(draws)
    assert d["chains"]==4 and d["draws_per_chain"]==1000
    np.testing.assert_allclose(d["mcse_mean_spectral"],
       np.asarray(az.mcse(draws,method="mean")).item(),rtol=1e-12)
    np.testing.assert_allclose(d["rank_rhat"],
       np.asarray(az.rhat(draws,method="rank")).item(),rtol=1e-12)
    assert d["bulk_ess"]>400
    assert d["passes_exploratory_identified_screen"]
    assert not d["scientifically_qualified"]
    assert len(d["chain_means"])==4


def test_identified_diagnostic_rejects_bad_shapes_and_chain_offsets():
    rng=np.random.default_rng(784)
    draws=rng.normal(size=(4,700))
    draws[0]+=2.0
    d=identified_mcse_geometry(draws)
    assert d["rank_rhat"]>1.01
    assert not d["passes_exploratory_identified_screen"]
    for sample in [np.ones((1,100)),np.zeros((3,50)),np.full((2,200),np.nan)]:
        with pytest.raises(ValueError,match="full finite chains"):
            identified_mcse_geometry(sample)


def test_independent_reference_model_and_study_contract_are_strictly_predeclared():
    assert set(DESIGNS)=={
      "B6_rank1","B7_rank1_paired","B7_rank1_asynchronous"}
    assert len(METHODS)==3
    with pytest.raises(ValueError,match="unknown research study"):
        run_design(design="B7_rank2")
    with pytest.raises(ValueError,match="too few"):
        run_design(design="B6_rank1",native_draws=99)
