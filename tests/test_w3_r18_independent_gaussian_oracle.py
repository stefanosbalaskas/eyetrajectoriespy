"""Predeclared numerical invariants for the R18 Gaussian-oracle replication."""
import numpy as np
import pytest
from scripts import run_w3_r18_independent_gaussian_oracle as r18
from scripts import run_w3_r17_independent_96block_calibration as r17
from scripts import run_w3_r16_leverage_covariance_factorial as r16


def test_separate_seed_and_reproducible_original_source():
    assert r18.MASTER_SEED not in (r16.SEED,r17.MASTER_SEED)
    a=r18.generate(0,"ordinary_independent")
    b=r18.generate(0,"ordinary_independent")
    assert a[1].provenance["fresh_master_seed"]==r18.MASTER_SEED
    assert a[1].provenance["interpolation_performed"] is False
    assert len(set(a[3]))==96
    for x,y in zip(a[1].values,b[1].values):
        np.testing.assert_array_equal(x,y)


@pytest.mark.parametrize("support,model",[
    ("ordinary_independent","legendre5"),
    ("ordinary_independent","cubic_spline13"),
    ("ordinary_dependent","legendre5"),
    ("ordinary_dependent","cubic_spline13")
])
def test_independent_block_variance_and_projection_contract(support,model):
    row=r18.evaluate(0,support,model)
    assert row["status"]=="ok",row["exception"]
    np.testing.assert_allclose(row["oracle_se"]**2,row["oracle_variance_R16"],atol=2e-7,rtol=0)
    assert row["independent_covariance_difference"]<2e-7
    np.testing.assert_allclose(
        row["gaussian_error_z_continuous_truth"],
        row["gaussian_error_z_projected"]+row["projection_shift_oracle_SE"],
        rtol=0,atol=1e-10)
    assert not row["inference_qualified"]
    assert not row["release_authorized"]


def test_wilson_boundaries_and_failure_inclusive_groups():
    assert r18.wilson(0,0) is None
    assert r18.wilson(0,192)[0]==0.
    assert r18.wilson(192,192)[1]==1.
    assert r18.BLOCKS==192
    assert r18.EXPECTED==768
    a=r18.evaluate(0,"ordinary_independent","legendre5")
    b=dict(a,block=1,status="failed",exception={"type":"Fixture","message":"retain"})
    s=r18.summarize([a,b])
    assert s["recorded_evaluations"]==2
    assert s["completed_evaluations"]==1
    assert s["failed_evaluations"]==1
    assert s["missing_evaluations"]==766
    assert not s["general_empirical_coverage_qualified"]
    assert not s["production_release_ready"]
