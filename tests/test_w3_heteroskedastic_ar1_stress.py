"""Fresh W3 stress: paired regimes and nested inference-unit boundaries."""
from pathlib import Path
import sys
import numpy as np
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.run_w3_heteroskedastic_ar1_stress import (
    BLOCKS, REGIMES, DESIGNS, UNIT_COUNTS, WILD_DRAWS, source, weights,
    fit_case, audit,
)


@pytest.mark.parametrize("design",DESIGNS)
@pytest.mark.parametrize("regime",REGIMES)
def test_nested_source_data_not_pseudoreplicated(design,regime):
    a,fa,truth,Xa,Ya=source(0,design,36,regime)
    b,fb,truth_b,Xb,Yb=source(0,design,144,regime)
    np.testing.assert_array_equal(a.values,b.values[:a.n_curves])
    np.testing.assert_array_equal(Xa,Xb[:36])
    np.testing.assert_array_equal(Ya,Yb[:36])
    np.testing.assert_array_equal(truth,truth_b)
    assert len(Xb)==144
    assert a.n_curves==(108 if design=="participant" else 36)
    assert b.n_curves==(432 if design=="participant" else 144)
    if design=="participant":
        assert fa.condition.iloc[:3].nunique()==1
        assert fb.condition.iloc[:3].nunique()==1


def test_four_regimes_reuse_design_and_change_noise_not_mean():
    reference=source(0,"curve",36,"iid")
    for scenario in REGIMES[1:]:
        changed=source(0,"curve",36,scenario)
        np.testing.assert_array_equal(reference[3],changed[3])
        np.testing.assert_array_equal(reference[2],changed[2])
        assert not np.array_equal(reference[0].values,changed[0].values)


def test_random_blocks_distinct_and_regime_inputs_fail_closed():
    a,*_=source(0,"curve",36,"iid")
    b,*_=source(1,"curve",36,"iid")
    assert not np.array_equal(a.values,b.values)
    with pytest.raises(ValueError,match="ledger"):
        source(BLOCKS,"curve",36,"iid")
    with pytest.raises(ValueError,match="unplanned"):
        source(0,"curve",73,"iid")
    with pytest.raises(ValueError,match="unplanned"):
        source(0,"curve",36,"unlisted")


def test_wild_draws_reuse_first_units_across_all_nested_sample_sizes():
    for design in DESIGNS:
        w36=weights(2,design,36)
        w144=weights(2,design,144)
        assert w36.shape==(WILD_DRAWS,36)
        assert w144.shape==(WILD_DRAWS,144)
        np.testing.assert_array_equal(w36,w144[:,:36])


@pytest.mark.parametrize("design",DESIGNS)
def test_actual_package_and_independent_bootstrap_references_agree(design):
    row=fit_case(0,design,36,"iid")
    assert row["status"]=="ok",row["exception"]
    assert row["matched_package_fixed_band"]
    assert row["maximum_beta_oracle_error"]<=2e-10
    assert row["maximum_hc1_oracle_error"]<=2e-10
    assert isinstance(row["fixed_contains_slope_truth"],bool)
    assert isinstance(row["refitted_contains_slope_truth"],bool)
    assert not row["calibration_qualified"]
    assert not row["release_authorized"]


@pytest.mark.parametrize("regime",REGIMES)
def test_stress_cells_do_not_crash_or_discard_negative_evidence(regime):
    row=fit_case(1,"participant",36,regime)
    assert row["status"]=="ok",row["exception"]
    assert np.isfinite(row["refitted_critical"])
    assert np.isfinite(row["fixed_critical"])


def test_failure_inclusive_384_case_audit_and_no_premature_qualification():
    good=fit_case(0,"curve",36,"iid")
    bad=dict(good,regime="ar1",status="failed",exception={"type":"controlled"})
    out=audit([good,bad])
    assert out["planned_cases"]==BLOCKS*len(DESIGNS)*len(UNIT_COUNTS)*len(REGIMES)
    assert out["source_case_rows"]==2
    assert out["fitting_or_contract_failures"]==1
    assert len(out["missing_cases"])==out["planned_cases"]-2
    assert out["same_block_n_and_regimes_are_correlated"]
    assert not out["calibration_qualified"]
    with pytest.raises(ValueError,match="duplicate"):
        audit([good,good])
