"""R50 strict independent source, covariance misspec and shard integrity tests."""
import hashlib
import json
import os

import numpy as np
import pytest

from scripts import run_w3_r49_nuisance_refit_bootstrap_t as r49
from scripts import run_w3_r50_independent_bootstrap_calibration as r50


def test_prespecified_new_source_quantile_denominators():
    assert r50.SOURCE_SEED!=r49.SOURCE_SEED
    assert r50.DRAW_SEED!=r49.DRAW_SEED
    assert r50.BLOCKS==24 and r50.PARTICIPANTS==24
    assert r50.N_BOOT==63 and r50.PREFIX_BOOT==31
    assert r50.N_CASES==48
    assert r50.N_INTERVALS==240
    assert r50.N_BOOT_ATTEMPTS==3024
    assert r50.N_SOLVER_STARTS==6240
    assert r50.METHODS==(
        "generating_covariance_oracle_conditional_CR2",
        "correct_family_fitted_conditional_CR2",
        "correct_family_refit_bootstrap_t_31_prefix",
        "correct_family_refit_bootstrap_t_63",
        "wrong_shared_slope_fitted_conditional_CR2",
    )
    assert r50.FAMILIES==("predictor_scaled_slope","shared_slope")
    assert r50.KKT_TOL==.001


def test_new_independent_primitive_blocks_and_paired_support():
    a=r50.original_source(0,r50.SUPPORT[0])
    paired=r50.original_source(0,r50.SUPPORT[1])
    another=r50.original_source(1,r50.SUPPORT[0])
    previous=r49.source(0,r49.SUPPORT[0])
    np.testing.assert_array_equal(
        a[0]["participant_intercept"],
        paired[0]["participant_intercept"])
    assert not np.array_equal(
        a[0]["participant_intercept"],
        another[0]["participant_intercept"])
    assert not np.array_equal(
        a[0]["participant_intercept"],
        previous[0]["participant_intercept"])
    assert paired[2][np.flatnonzero(paired[3]==0)[0]]==pytest.approx(3.)
    assert paired[2][np.flatnonzero(paired[3]==1)[0]]==pytest.approx(-2.5)
    with pytest.raises(ValueError,match="outside"):
        r50.original_source(24,r50.SUPPORT[0])


def test_correct_family_is_byte_compatible_with_original_r49_solver():
    data=r50.native_problem(0,r50.SUPPORT[0])
    historical=r49.fit_nuisance(data)
    prospective=r50.four_component_physical_fit(data,r50.FAMILIES[0])
    assert prospective["status"]==historical["status"]
    assert prospective["numerical_starts"]==historical["numerical_starts"]
    assert len(prospective["numerical_starts"])==2
    assert "oracle_covariance" not in [
        "source_parameters","source_true_variance","generating_innovations"]


def test_wrong_covariance_uses_equivalent_numerical_gate():
    data=r50.native_problem(0,r50.SUPPORT[0])
    bad=r50.four_component_physical_fit(data,r50.FAMILIES[1])
    assert len(bad["numerical_starts"])==2
    assert bad["status"] in ("accepted","refused")
    if bad["status"]=="accepted":
        assert bad["physical_projected_KKT"]<=.001
        assert bad["global_optimum_proven"] is False
        assert len(bad["working_blocks"])==24
        assert all(np.linalg.eigvalsh(x).min()>0 for x in bad["working_blocks"])
    with pytest.raises(ValueError,match="unregistered"):
        r50.four_component_physical_fit(data,"oracle_true")


def test_new_parametric_seed_reproducible_without_true_oracle():
    data=r50.native_problem(0,r50.SUPPORT[0])
    correct=r50.four_component_physical_fit(data,r50.FAMILIES[0])
    assert correct["status"]=="accepted",correct.get("reason")
    stripped={k:v for k,v in data.items() if k!="oracle_covariance"}
    y1,seed=r50.draw_from_observed_fit(
        stripped,correct["working_blocks"],0,r50.SUPPORT[0],0)
    y2,seed2=r50.draw_from_observed_fit(
        stripped,correct["working_blocks"],0,r50.SUPPORT[0],0)
    assert seed==seed2
    np.testing.assert_array_equal(y1,y2)
    assert np.isfinite(y1).all()
    assert not np.array_equal(y1,data["y"])


def _refused_source(block,support):
    starts=[{"label":name,"status":"not_attempted"}
            for name,_ in r49.START_RATIOS]
    return {
        "study":r50.STUDY,"block":block,"support":support,
        "source_status":"failed",
        "original_correct_nuisance":{
            "status":"not_attempted","numerical_starts":starts},
        "original_wrong_nuisance":{
            "status":"not_attempted","numerical_starts":starts},
        "intervals":[r50.refused_method(m,"source_refusal")
                     for m in r50.METHODS],
        "bootstrap_refit_attempts":[
            {"replicate":i,"status":"not_attempted",
             "numerical_starts":starts}
            for i in range(r50.N_BOOT)],
    }


def test_original_denominator_records_all_refusals_without_survivor_selection():
    bad=_refused_source(0,r50.SUPPORT[0])
    stats=r50.summary([bad])
    assert stats["recorded_source_cases"]==1
    assert stats["recorded_interval_slots"]==5
    assert stats["recorded_bootstrap_attempts"]==63
    assert stats["recorded_nuisance_optimizer_start_slots"]==130
    assert stats["planned_nuisance_optimizer_start_slots"]==6240
    assert not stats["complete_original_failure_inclusive_design"]
    assert stats["source_generation_failures"]==1
    assert not stats["release_authorized"]
    with pytest.raises(ValueError,match="duplicate"):
        r50.summary([bad,bad])


def test_three_checksums_and_full_shard_aggregation_rejects_missing_or_duplicate(tmp_path,monkeypatch):
    monkeypatch.setenv("GITHUB_SHA","r50-ci-source-test")
    shards=tmp_path/"parts"
    for start,stop in ((0,8),(8,16),(16,24)):
        path=shards/f"r50-{start:02d}"
        path.mkdir(parents=True)
        cases=[_refused_source(b,s) for b in range(start,stop)
               for s in r50.SUPPORT]
        r50._write_json(path/"cases.json",cases)
        m={
            "study":r50.STUDY,"start":start,"stop":stop,
            "block_count":stop-start,"source_cases":len(cases),
            "source_seed":r50.SOURCE_SEED,
            "source_commit":"r50-ci-source-test",
            "cases_sha256":hashlib.sha256(
                (path/"cases.json").read_bytes()).hexdigest(),
        }
        r50._write_json(path/"manifest.json",m)
    merged=tmp_path/"merged"
    r50.aggregate(merged,shards)
    result=json.loads((merged/"summary.json").read_text())
    assert result["complete_original_failure_inclusive_design"]
    assert result["source_generation_failures"]==48
    assert result["recorded_bootstrap_attempts"]==3024
    assert result["recorded_nuisance_optimizer_start_slots"]==6240
    with (merged/"SHA256SUMS").open() as f:
        checks=f.read().strip().splitlines()
    for line in checks:
        digest,name=line.split("  ")
        assert hashlib.sha256((merged/name).read_bytes()).hexdigest()==digest
    (shards/"r50-16"/"manifest.json").unlink()
    with pytest.raises(ValueError,match="exactly three"):
        r50.aggregate(tmp_path/"should_fail",shards)
