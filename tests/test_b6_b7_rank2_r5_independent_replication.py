"""R5 common-truth independent-block scientific contracts."""
from copy import deepcopy
from hashlib import sha256
import json
import numpy as np
import pytest

pytest.importorskip("arviz")

from scripts.run_b6_b7_rank2_controlled_observation_r4 import (
    paired_cases, verify_matched_case_design, SEED as R4_SEED,
)
from scripts.run_b6_b7_rank2_r5_independent_replication import (
    REPLICATES,replicate_seed,functional_family,functional_report,
    paired_block_audit,write_case,
)


def test_all_r5_replication_seeds_are_unique_and_not_r4():
    seeds=[replicate_seed(r) for r in REPLICATES]
    assert len(seeds)==len(set(seeds))
    assert R4_SEED not in seeds
    with pytest.raises(ValueError,match="prespecified"):
        replicate_seed(100)


def test_independent_generating_truth_and_matching_schedules():
    a=paired_cases(replicate_seed(0),4)
    b=paired_cases(replicate_seed(1),4)
    assert not np.array_equal(a["paired"].mean,b["paired"].mean)
    for replicate in (0,1):
        for n in (4,12):
            assert verify_matched_case_design(
                paired_cases(replicate_seed(replicate),n))["matched_design_verified"]


def test_schedule_traces_nested_in_n_within_one_replication():
    seed=replicate_seed(2)
    small=paired_cases(seed,4)
    large=paired_cases(seed,12)
    for design in ("paired","asynchronous"):
        np.testing.assert_array_equal(small[design].mean,large[design].mean)
        np.testing.assert_array_equal(small[design].loading,large[design].loading)
        for i in range(4):
            np.testing.assert_array_equal(small[design].gaze.time[i],
                                          large[design].gaze.time[i])
            np.testing.assert_array_equal(small[design].gaze.values[i],
                                          large[design].gaze.values[i],strict=False)


def test_functional_family_and_full_15_report():
    assert functional_family("x_mean_quarter")=="mean"
    assert functional_family("xy_covariance_midpoint")=="crosscovariance"
    assert functional_family("y_variance_midpoint")=="variance"
    with pytest.raises(ValueError,match="unexpected"):
        functional_family("raw_loading_1")
    keys=[f"{v}_{p}" for v in
          ("x_mean","y_mean","x_variance","y_variance","xy_covariance")
          for p in ("quarter","midpoint","three_quarters")]
    diagnostics={"functionals":{
        k:{"posterior_mean":.05,"single_dataset_truth_value":.1,
           "posterior_q05":-.1,"posterior_q95":.2,
           "single_dataset_90pct_interval_contains_truth":True,
           "mcse_mean_spectral":.01,"rank_rhat":1.002,
           "bulk_ess":900,"tail_ess":800,
           "passes_declared_functional_screen":True}
        for k in keys}}
    out=functional_report(diagnostics)
    assert len(out)==15
    assert np.isclose(out["x_mean_midpoint"]["single_dataset_signed_error_not_bias"],-.05)
    assert np.isclose(out["x_variance_midpoint"]["posterior_90pct_interval_width"],.3)


def _cell(design,n,replicate=0,screen=True,status="ok"):
    seed=replicate_seed(replicate)
    return {"replicate":replicate,"design":design,"participants":n,
        "independent_generating_block_seed":seed,"status":status,
        "reference_checks":{
            "all_identified_functionals_pass_exploratory_screen":screen}
            if status=="ok" else None,
        "per_functional_evidence":{"x_mean_midpoint":{
            "family":"mean","generating_truth":1.0,
            "single_dataset_signed_error_not_bias":.1 if design=="paired" else -.2,
            "posterior_90pct_interval_width":.4 if design=="paired" else .5,
            "passes_declared_screen":screen}} if status=="ok" else {}}


def test_block_audit_failure_inclusive_and_correlated_cells():
    cells=[_cell(d,n,screen=not(d=="paired" and n==4))
           for d in ("paired","asynchronous") for n in (4,12)]
    result=paired_block_audit(cells,0)
    assert result["planned_cells"]==4 and not result["missing_cells"]
    assert result["computational_screen_passes"]==3
    assert result["independent_generating_blocks"]==1
    assert result["paired_schedule_descriptive_contrasts_by_n"]["4"]["x_mean_midpoint"][
        "paired_minus_async_signed_error"]==pytest.approx(.3)
    assert not result["nominal_coverage_qualified"]
    missing=paired_block_audit(cells[:-1],0)
    assert len(missing["missing_cells"])==1
    with pytest.raises(ValueError,match="duplicate"):
        paired_block_audit(cells+[deepcopy(cells[0])],0)
    with pytest.raises(ValueError,match="generating block"):
        paired_block_audit([_cell("paired",4,1)],0)


def test_source_failure_preservation(tmp_path):
    x=_cell("paired",4,status="failed")
    write_case(x,tmp_path)
    assert json.loads((tmp_path/"evidence.json").read_text())["fit_exceptions"]==1
    for line in (tmp_path/"SHA256SUMS").read_text().splitlines():
        digest,name=line.split("  ")
        assert sha256((tmp_path/name).read_bytes()).hexdigest()==digest
