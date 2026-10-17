"""W3 fixed-truth calibration contract tests; failures are not ignored."""
import sys
from pathlib import Path
import numpy as np
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.run_w3_fixed_truth_interval_pilot import (
    BOOTSTRAP_DRAWS, CONFIDENCE, DESIGNS, PLANNED_BLOCKS, ORACLE_ATOL,
    TIME_SHAPE, audit, evaluate, independent_hc1_oracle, simulate, wilson,
)


def test_independent_hc1_oracle_matches_hand_computed_single_time():
    X=np.array([[1.,-1.],[1.,0.],[1.,1.],[1.,2.]],dtype=float)
    Y=np.zeros((4,TIME_SHAPE[1],TIME_SHAPE[2]),dtype=float)
    Y[:,0,0]=[0.,1.2,1.9,3.3]
    beta,se=independent_hc1_oracle(X,Y)
    residual=Y[:,0,0]-X@np.linalg.lstsq(X,Y[:,0,0],rcond=None)[0]
    inv=np.linalg.inv(X.T@X)
    manual_var=4/(4-2)*sum(
        ((X[i]@inv)**2)*residual[i]**2 for i in range(4)
    )
    np.testing.assert_allclose(beta[:,0,0],np.linalg.lstsq(X,Y[:,0,0],rcond=None)[0])
    np.testing.assert_allclose(se[:,0,0],np.sqrt(manual_var),atol=2e-12)


@pytest.mark.parametrize("design",DESIGNS)
def test_predeclared_replication_does_not_count_trials_as_units(design):
    gaze,frame,truth,X,y=simulate(0,design)
    assert truth.shape==TIME_SHAPE
    assert y.shape==(len(X),TIME_SHAPE[1],TIME_SHAPE[2])
    if design=="participant":
        assert len(X)==36 and gaze.n_curves==108
        for i in range(36):
            assert frame.condition.iloc[3*i:3*i+3].nunique()==1
    else:
        assert len(X)==72 and gaze.n_curves==72


def test_genuinely_fresh_generating_blocks():
    a,*_=simulate(0,"curve")
    b,*_=simulate(1,"curve")
    assert not np.array_equal(a.values,b.values)
    with pytest.raises(ValueError,match="ledger"):
        simulate(PLANNED_BLOCKS,"curve")
    with pytest.raises(ValueError,match="design"):
        simulate(0,"other")


@pytest.mark.parametrize("design",DESIGNS)
def test_actual_pointwise_hc1_and_bootstrap_oracles(design):
    # The contracted full run uses 199 replicates; tests use the same budget.
    row=evaluate(0,design)
    assert row["completed"],row["exception"]
    assert row["bootstrap_draws"]==BOOTSTRAP_DRAWS
    assert row["maximum_coefficient_oracle_difference"]<=ORACLE_ATOL
    assert row["maximum_hc1_oracle_difference"]<=ORACLE_ATOL
    assert np.isfinite(row["bootstrap_critical_slope"])
    assert 0<=row["slope_pointwise_cell_inclusion_rate"]<=1
    assert row["calibration_qualified"] is False
    assert row["release_authorized"] is False


def test_failure_inclusive_denominators_and_nonqualification():
    good=evaluate(0,"curve")
    failed=dict(good,design="participant",completed=False,
                exception={"type":"ControlledError","message":"retained"})
    results=audit([good,failed],blocks=2)
    assert results["status"]=="incomplete_with_retained_failures"
    assert len(results["missing_cases"])==2
    assert results["failures"]==1
    assert results["design"]["participant"]["coverage"][
        "slope_simultaneous_coefficient_included"]["attempted_denominator"]==2
    assert results["scientific_coverage_qualification_passed"] is False
    with pytest.raises(ValueError,match="duplicate"):
        audit([good,good],blocks=1)


def test_wilson_interval_bounds_include_point_estimate():
    for k in (0,1,5,9,10):
        low,high=wilson(k,10)
        assert 0<=low<=k/10<=high<=1
    assert wilson(0,0) is None
