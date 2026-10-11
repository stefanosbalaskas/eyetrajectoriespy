"""W3 controlled bootstrap-t/studentization and nested-n source contracts."""
from pathlib import Path
import sys
import numpy as np
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.run_w3_hc1_restudenization_nested_n import (
    INDEPENDENT_BLOCKS, UNIT_COUNTS, DESIGNS, WILD_DRAWS, MAX_N,
    bootstrap_weights, generate, independent_restudentized_maxima,
    evaluate, audit,
)
from scripts.run_w3_fixed_truth_interval_pilot import independent_hc1_oracle


@pytest.mark.parametrize("design",DESIGNS)
def test_same_block_participant_sample_nested_over_n(design):
    a,da,ta,Xa,Ya=generate(1,design,36)
    b,db,tb,Xb,Yb=generate(1,design,144)
    np.testing.assert_array_equal(a.values,b.values[:a.n_curves])
    np.testing.assert_array_equal(Xa,Xb[:36])
    np.testing.assert_array_equal(Ya,Yb[:36])
    np.testing.assert_array_equal(ta,tb)
    assert len(Xa)==36 and len(Xb)==144
    assert a.n_curves==(108 if design=="participant" else 36)
    if design=="participant":
        assert da["condition"].iloc[:3].nunique()==1
        assert db["condition"].iloc[:3].nunique()==1


def test_independent_generating_blocks_do_not_reuse_data():
    a,*_=generate(0,"curve",36)
    b,*_=generate(1,"curve",36)
    assert not np.array_equal(a.values,b.values)
    with pytest.raises(ValueError,match="ledger"):
        generate(INDEPENDENT_BLOCKS,"curve",36)
    with pytest.raises(ValueError,match="outside planned"):
        generate(0,"curve",37)


@pytest.mark.parametrize("design",DESIGNS)
def test_wild_weights_nested_across_sample_sizes(design):
    w=bootstrap_weights(2,design)
    assert w.shape==(WILD_DRAWS,MAX_N)
    assert set(np.unique(w))=={-1.,1.}
    np.testing.assert_array_equal(w[:,:36],w[:,:72][:,:36])


def test_independent_studentization_recomputes_pseudo_residual_se():
    g,d,truth,X,Y=generate(0,"curve",36)
    weights=bootstrap_weights(0,"curve")[:12,:36]
    fixed,rest,ref=independent_restudentized_maxima(X,Y,weights)
    assert fixed.shape==rest.shape==(12,)
    assert np.isfinite(fixed).all() and np.isfinite(rest).all()
    assert np.max(np.abs(fixed-rest))>1e-8
    _,oracle=independent_hc1_oracle(X,Y)
    np.testing.assert_allclose(ref,oracle,atol=1e-12,rtol=0)


@pytest.mark.parametrize("design",DESIGNS)
def test_replicate_fit_checks_actual_package_band_and_hc1(design):
    row=evaluate(0,design,36)
    assert row["status"]=="ok",row["exception"]
    assert row["coef_oracle_max_delta"]<=2e-10
    assert row["hc1_oracle_max_delta"]<=2e-10
    assert row["fixed_HC1_package_band_agreement"]
    assert isinstance(row["fixed_HC1_full_grid_slope_coverage"],bool)
    assert isinstance(row["restudentized_HC1_full_grid_slope_coverage"],bool)
    assert row["calibration_qualified"] is False
    assert row["release_authorized"] is False


def test_audit_retains_missing_and_negative_scientific_cases():
    row=evaluate(0,"curve",36)
    incomplete=audit([row])
    assert incomplete["planned_cases"]==INDEPENDENT_BLOCKS*len(DESIGNS)*len(UNIT_COUNTS)
    assert incomplete["source_cases_present"]==1
    assert len(incomplete["missing_cases"])==incomplete["planned_cases"]-1
    assert incomplete["not_144_independent_blocks"]
    assert incomplete["coverage_qualified"] is False
    with pytest.raises(ValueError,match="duplicate"):
        audit([row,row])
