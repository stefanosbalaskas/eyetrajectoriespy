"""R66 prospective independent 128-block matched detection and refusal contracts."""
from __future__ import annotations

import json
import math

import numpy as np
import pytest

from scripts import run_w3_r66_fresh_matched_slope_detection as r66
from scripts import run_w3_r64_nonzero_slope_detection_pilot as r64
from scripts import run_w3_r63_independent_null_replication as core


def test_new_independent_sources_design_and_exact_inferential_reference():
    assert len({r66.MASTER_SEED, r66.DRAW_SEED, r66.PAIRED_RESAMPLE_SEED,
                r64.MASTER_SEED, r64.DRAW_SEED}) == 5
    assert r66.BLOCKS==128 and r66.PARTICIPANTS==24
    assert r66.SUPPORT==r64.SUPPORT
    assert r66.LEVELS==("zero","half","full")
    assert r66.MULTIPLIERS==r64.MULTIPLIERS
    assert r66.B==r64.B==63
    assert r66.CASES==768 and r66.DRAWS==48384
    assert r66.NESTED_MODELS==98304
    assert r66.OPTIMIZER_STARTS==294912
    assert r66.PAIRED_RESAMPLES==20_000
    assert len(r66.SHARDS)==32
    assert set(r66.SHARDS)=={(i,i+4) for i in range(0,128,4)}
    assert r66.ALPHA==r64.ALPHA==.05
    assert r66.CLASSICAL==r64.CLASSICAL
    assert (1+2)/(r66.B+1)==.046875
    assert (1+3)/(r66.B+1)==.0625
    with pytest.raises(ValueError,match="primitive"):
        r66.source(128,r66.SUPPORT[0],"zero")
    with pytest.raises(ValueError,match="undeclared"):
        r66.source(0,r66.SUPPORT[0],"unexpected")


def test_true_slope_signal_is_paired_in_native_uninterpolated_source():
    zero=r66.source(0,r66.SUPPORT[0],"zero")
    half=r66.source(0,r66.SUPPORT[0],"half")
    full=r66.source(0,r66.SUPPORT[0],"full")
    for field in ("X","w","group","time","trial","x"):
        np.testing.assert_array_equal(zero[field],half[field])
        np.testing.assert_array_equal(zero[field],full[field])
    np.testing.assert_allclose(2*half["y"],zero["y"]+full["y"],
                               rtol=1e-12,atol=2e-12)
    assert zero["true_slope_variance"]==0.
    assert half["true_slope_variance"]==pytest.approx(.00050625)
    assert full["true_slope_variance"]==pytest.approx(.002025)
    assert zero["retained_slope_component_L2"]==0.
    assert not np.array_equal(full["y"],r64.source(0,r64.SUPPORT[0],"full")["y"])
    assert not np.array_equal(full["y"],r66.source(1,r66.SUPPORT[0],"full")["y"])
    assert not np.array_equal(zero["x"],r66.source(0,r66.SUPPORT[1],"zero")["x"])


def test_covariance_refitting_null_and_seeded_gaussian_draw_contract():
    data=r66.source(0,r66.SUPPORT[0],"half")
    fitted=core.nested_on(data)
    assert fitted["status"] in ("accepted","refused")
    assert len(fitted["null_fit"]["original_starts"])==2
    assert len(fitted["alternative_fit"]["original_starts"])==4
    if fitted["status"]=="accepted":
        beta,covs,theta=core.h0_gls_covariance(
            data,fitted["null_fit"],fitted["observed_reference"])
        assert theta[1]==0.
        a,seed=r66.conditional_h0_response(
            data,beta,covs,0,r66.SUPPORT[0],"half",62)
        b,again=r66.conditional_h0_response(
            data,beta,covs,0,r66.SUPPORT[0],"half",62)
        assert seed==again
        np.testing.assert_array_equal(a["y"],b["y"])
        assert seed!=r66.conditional_h0_response(
            data,beta,covs,0,r66.SUPPORT[0],"full",62)[1]
        assert not np.array_equal(a["y"],data["y"])
    with pytest.raises(ValueError,match="index"):
        r66.conditional_h0_response(
            data,np.zeros(data["X"].shape[1]),[],0,r66.SUPPORT[0],"half",63)


def _tiny_complete_decisions():
    rows=[]
    for b in range(r66.BLOCKS):
        for s in r66.SUPPORT:
            for level in r66.LEVELS:
                rejected=(s==r66.SUPPORT[1] and level=="full" and b<16)
                rows.append({"block":b,"support":s,"level":level,
                    "bootstrap_5pct_exceedance":rejected,
                    "conditional_bootstrap_p":.03125 if rejected else .125})
    return rows


def test_prospectively_matched_128_block_interaction_and_bootstrap():
    rows=_tiny_complete_decisions()
    a=r66.prospective_paired_matched_diagnostics(rows)
    b=r66.prospective_paired_matched_diagnostics(rows)
    assert a==b
    assert a["complete_six_cell_blocks"]==128
    assert a["incomplete_six_cell_blocks"]==0
    result=a["paired_contrast_results"]
    assert result["ordinary_zero_to_full"][
        "difference_in_candidate_rejection_fraction_complete"]==0.
    assert result["extreme_zero_to_full"][
        "difference_in_candidate_rejection_fraction_complete"]==16/128
    p=result["extreme_minus_ordinary_zero_to_full"]
    assert p["difference_in_candidate_rejection_fraction_complete"]==16/128
    lo,hi=p["prospective_95pct_primitive_block_bootstrap_percentile"]
    assert 0<=lo<=16/128<=hi<=1.
    assert not a["nominal_type_I_or_power_qualification"]
    assert not a["release_authorized"]


def test_refused_source_keeps_full_denominator_and_withholds_ci():
    rows=_tiny_complete_decisions()
    rows[0]["conditional_bootstrap_p"]=None
    rows[0]["bootstrap_5pct_exceedance"]=None
    out=r66.prospective_paired_matched_diagnostics(rows)
    assert out["incomplete_six_cell_blocks"]==1
    p=out["paired_contrast_results"]["extreme_minus_ordinary_zero_to_full"]
    assert p["complete_blocks"]==127
    assert p["missing_or_refused_blocks"]==1
    assert p["prospective_95pct_primitive_block_bootstrap_percentile"] is None
    assert p["full_denominator_lower_bound"]<=p[
        "difference_in_candidate_rejection_fraction_complete"]<=p[
        "full_denominator_upper_bound"] + .02
    rows=_tiny_complete_decisions()
    rows[0]["bootstrap_5pct_exceedance"]=True
    with pytest.raises(ValueError,match="decision"):
        r66.prospective_paired_matched_diagnostics(rows)
    rows=_tiny_complete_decisions()
    rows[0]["conditional_bootstrap_p"]=.02
    with pytest.raises(ValueError,match="p grid"):
        r66.prospective_paired_matched_diagnostics(rows)


def test_full_768_case_failure_ledger_and_missing_archive_fail_closed(tmp_path):
    rows=[r66.empty_case(b,s,level)
          for b in range(r66.BLOCKS) for s in r66.SUPPORT for level in r66.LEVELS]
    for row in rows:
        row["bootstrap"]=[r66.empty_draw(i) for i in range(r66.B)]
    aggregate=r66.summarize(rows)
    assert aggregate["recorded_source_cases"]==768
    assert aggregate["recorded_gaussian_conditional_H0_draw_slots"]==48384
    assert aggregate["nested_H0_H1_model_fit_slots"]==98304
    assert aggregate["optimizer_start_records"]==294912
    assert aggregate["prospective_matched_primitive_block_diagnostics"][
        "incomplete_six_cell_blocks"]==128
    assert not aggregate["release_authorized"]
    for entry in aggregate["strata"].values():
        assert entry["refused_incomplete_sources"]==128
        assert entry["refusal_as_nonrejection_all_source_lower"]==0.
        assert entry["refusal_as_rejection_all_source_upper"]==1.
    with pytest.raises(ValueError,match="missing/duplicated"):
        r66.summarize(rows[:-1])
    with pytest.raises(ValueError,match="32 original source-shard|32 source|original source"):
        r66.aggregate(tmp_path/"none",tmp_path/"missing")
