"""F1/F5 calibration-grid contracts; no inferential gate auto-promotion."""
from __future__ import annotations
import numpy as np
import pandas as pd
import pytest

from scripts.run_f1_f5_scientific_stress import (
    F1_DESIGNS, F5_SCENARIOS, _ordered_fixture, _wilson, f5_study,
)


def test_stress_grid_distinguishes_false_null_assumptions():
    assert F1_DESIGNS["unequal_heteroscedastic_null"]["group_noise_multiplier"] == 2
    assert F1_DESIGNS["clustered_two_trials"]["trials_per_participant"] == 2
    assert F5_SCENARIOS["strong_AR1"]["phi"] == .8
    assert F5_SCENARIOS["iid_heavy_tail"]["heavy_tail"]


def test_known_null_and_two_change_truth_are_reproducible():
    a=_ordered_fixture(111,"strong_AR1","null")
    b=_ordered_fixture(111,"strong_AR1","null")
    np.testing.assert_array_equal(a.values,b.values)
    c=_ordered_fixture(111,"strong_AR1","two_breaks")
    change=c.values-a.values
    np.testing.assert_allclose(change[:12],0,atol=1e-14)
    np.testing.assert_allclose(change[24:],0,atol=1e-14)
    assert np.linalg.norm(change[12:24])>0
    with pytest.raises(ValueError):
        _ordered_fixture(111,"iid_gaussian","invalid")


def test_monte_carlo_intervals_use_only_successful_fits():
    vals=pd.Series([.01,.04,.07,np.nan,.9])
    stats=_wilson(vals,.05)
    assert stats["n_success"]==4
    assert stats["rejections"]==2
    assert stats["rate"]==.5
    assert 0<=stats["wilson_95_interval"][0]<.5
    assert .5<stats["wilson_95_interval"][1]<=1
    assert _wilson(pd.Series([np.nan]),.05)["rate"] is None


def test_f5_block_sensitivity_executes_and_keeps_null_and_breaks():
    cases,summary=f5_study(replicates=2,draws=99,seed=106)
    assert len(cases)==2*3*(1+3+3+1)
    assert set(cases.change)=={"null","one_break","two_breaks"}
    assert set(cases.status).issubset({"ok","failed"})
    assert len(summary)==3*(1+3+3+1)
    assert all(not row["scientific_size_or_power_qualified"] for row in summary)
