"""Rank-one Bayesian rank-SBC and coverage denominator contracts."""
import pytest
pytest.importorskip("arviz")
import numpy as np

from scripts.run_b6_rank1_prior_sbc_pilot import (
    REPLICATES,PRIMARY,SEED,fresh_seed,rank_in_posterior,
    summarize_primary,write_case,
)


def test_new_prior_sbc_namespace_has_four_distinct_fixed_seeds():
    s=[fresh_seed(SEED,r) for r in REPLICATES]
    assert len(s)==len(set(s))==4
    with pytest.raises(ValueError,match="predeclared"):
        fresh_seed(SEED,4)


def test_exact_rank_counts_and_tie_seed_contract():
    assert rank_in_posterior([1.,2.,3.],2.5,11)["posterior_truth_rank"]==2
    assert rank_in_posterior([1.,2.,3.],.5,11)["posterior_truth_rank"]==0
    assert rank_in_posterior([1.,2.,3.],10.,11)["posterior_truth_rank"]==3
    a=rank_in_posterior([2.,2.,2.],2.,918)
    b=rank_in_posterior([2.,2.,2.],2.,918)
    assert a==b and 0<=a["posterior_truth_rank"]<=3
    with pytest.raises(ValueError,match="finite"):
        rank_in_posterior([1.,np.nan],2.,11)


def test_failure_rows_stay_in_denominator_and_histogram_not_promoted():
    rows=[]
    for r in REPLICATES:
        obj={
            "replicate":r,"generation_seed":100+r,
            "status":"failed" if r==3 else "ok",
        }
        if obj["status"]=="ok":
            obj["all_functional_screen_passed"] = r != 1
            obj["primary_targets"]={
                key:{
                    "marginal_90pct_interval_contains_truth":r!=2,
                    "rank":{"posterior_truth_rank":200*r,
                            "rank_histogram_bin_0_to_9":r}}
                for key in PRIMARY}
        rows.append(obj)
    report=summarize_primary(rows)
    assert report["independent_dataset_attempts"]==4
    assert report["failed_fits"]==1
    assert report["nonconverged_exploratory_screen"]==1
    for p in report["primary_targets"].values():
        assert p["fit_attempt_denominator"]==4
        assert p["truth_contained_count"]==2
        assert p["truth_missed_count"]==1
        assert sum(p["sbc_rank_histogram_n10"])==3
        assert p["exact_95pct_binomial_interval_completed_fits_only"][0] < .2
        assert not p["nominal_interval_coverage_qualified"]
    with pytest.raises(ValueError,match="distinct"):
        summarize_primary(rows+[rows[0]])


def test_failed_attempt_evidence_is_preserved_with_sha256(tmp_path):
    from hashlib import sha256
    import json
    row={"replicate":0,"generation_seed":2313,"status":"failed","error_type":"ReferenceError"}
    write_case(row,tmp_path,SEED)
    assert json.loads((tmp_path/"evidence.json").read_text())["fit_failures_this_artifact"]==1
    for line in (tmp_path/"SHA256SUMS").read_text().splitlines():
        digest,path=line.split("  ")
        assert sha256((tmp_path/path).read_bytes()).hexdigest()==digest
