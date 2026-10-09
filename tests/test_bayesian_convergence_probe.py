"""Scientific long-chain diagnostic contracts: retain failures and pair exact data."""
from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd
import pytest

from scripts import run_bayesian_convergence_probe as probe


def test_probes_have_six_pregiven_matched_prior_scenarios():
    assert set(probe.CASES)=={"B6","B7"}
    assert len(probe.CASES["B6"])==2
    assert len(probe.CASES["B7"])==4
    assert set(probe.COVERAGE["B7"])=={
        "x_mean_mid_90_covered","y_mean_mid_90_covered",
        "xy_crosscov_mid_90_covered"}


def test_summary_never_counts_failed_fit_as_a_calibrated_draw():
    rows=[
        {"method":"B6","scenario":"matched_rank1","schedule":"short",
         "status":"ok","population_mean_mid_90_included":True,
         "population_covariance_mid_90_included":False,
         "convergence_rhat_max":1.7,"convergence_ess_bulk_min":12},
        {"method":"B6","scenario":"matched_rank1","schedule":"short",
         "status":"failed","population_mean_mid_90_included":None,
         "population_covariance_mid_90_included":None,
         "convergence_rhat_max":None,"convergence_ess_bulk_min":None},
    ]
    out=probe.summarize(pd.DataFrame(rows))
    assert len(out)==1
    row=out[0]
    assert row["attempted"]==2 and row["completed"]==1 and row["failed"]==1
    assert row["population_mean_mid_90_included"]["denominator"]==1
    assert row["population_covariance_mid_90_included"]["fraction"]==0
    assert row["convergence_rhat_max"]["median"]==1.7
    assert not row["chain_mixing_qualified"]
    assert not row["posterior_coverage_qualified"]


def test_actual_b6_and_b7_population_diagnostics_do_not_promote_science():
    pytest.importorskip("arviz")
    from scripts.run_b6_population_calibration_grid import run_one
    from scripts.run_b7_learned_planar_truth_pilot import _replicate
    b6=run_one(2236,"matched_rank1",draws=20,warmup=22,diagnostics=True)
    b7=_replicate(2257,1,False,20,22,diagnostics=True)
    assert np.isfinite(b6["convergence_rhat_max"])
    assert np.isfinite(b7["convergence_rhat_max"])
    assert b6["population_mean_mid_q90_width"]>0
    assert b7["x_mean_mid_q90_width"]>0
    assert b7["xy_crosscov_mid_q90_width"]>0
    assert 0 <= b7["new_participant_average_pointwise_inclusion"] <= 1
