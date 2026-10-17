"""R62 full-source independence, Gaussian H0 refit and failure-inclusive metrics."""
import hashlib
import json
import math

import numpy as np
import pytest

from scripts import run_w3_r62_independent_outer_null_bootstrap as r62
from scripts import run_w3_r60_nuisance_refit_null_bootstrap as r60
from scripts import run_w3_r59_independent_null_replication as r59


def test_independent_outer_Gaussian_null_source_and_bootstrap_denominators():
    assert len({r62.MASTER_SEED, r62.DRAW_SEED,
                r59.MASTER_SEED, r60.MASTER_SEED}) == 4
    assert r62.BLOCKS == 32 and r62.B == 63
    assert r62.SOURCE_SLOTS == 64
    assert r62.BOOT_SLOTS == 4032
    assert r62.FITS == 8192
    assert r62.OPTIMIZER_START_SLOTS == 24576
    assert len(r62.SHARDS) == 8
    assert set(r62.SHARDS) == {(k,k+4) for k in range(0,32,4)}
    with pytest.raises(ValueError, match="outside"):
        r62.source(32,r62.SUPPORT[0])


def test_new_synthetic_Gaussian_truth_zero_and_distinct_native_leverage():
    a=r62.source(0,r62.SUPPORT[0])
    b=r62.source(0,r62.SUPPORT[1])
    assert a["true_slope_variance"] == b["true_slope_variance"] == 0.
    assert a["removed_slope_L2"] > 0. and b["removed_slope_L2"] > 0.
    assert a["X"].shape == b["X"].shape
    assert not np.array_equal(a["x"],b["x"])
    fit=r62.nested_on(a)
    assert fit["status"] in ("accepted","refused")
    assert len(fit["null_fit"]["original_starts"])==2
    assert len(fit["alternative_fit"]["original_starts"])==4
    if fit["status"]=="accepted":
        beta,blocks,theta=r62.h0_gls_covariance(
            a,fit["null_fit"],fit["observed_reference"])
        assert theta[1]==0.
        pseudo,seed=r62.pseudo_under_h0(
            a,beta,blocks,0,r62.SUPPORT[0],62)
        repeated,reseed=r62.pseudo_under_h0(
            a,beta,blocks,0,r62.SUPPORT[0],62)
        assert seed==reseed
        np.testing.assert_array_equal(pseudo["y"],repeated["y"])
        assert not np.array_equal(pseudo["y"],a["y"])


def test_complete_refusal_ledger_and_source_confidence_intervals():
    rows=[r62.empty_case(block,support)
          for block in range(r62.BLOCKS) for support in r62.SUPPORT]
    for case in rows:
        case["bootstrap"]=[r62.empty_draw(j) for j in range(r62.B)]
    out=r62.summarize(rows)
    assert out["recorded_source_cases"]==64
    assert out["recorded_H0_bootstrap_draw_slots"]==4032
    assert out["recorded_optimizer_start_slots"]==24576
    assert out["paired_both_complete"]==0
    assert out["paired_bootstrap_neither_exceedances"]==0
    for c in out["strata"].values():
        assert c["source_cases_with_all_63_numerical_bootstrap_refits"]==0
        assert c["source_cases_with_refused_or_incomplete_bootstrap"]==32
        assert c["bootstrap_candidate_nominal_005_Wilson95_complete_sources"] is None
        assert c["bootstrap_all_source_lower_refusals_as_nonrejection"]==0.
        assert c["bootstrap_all_source_upper_refusals_as_rejection"]==1.
        assert c["recorded_bootstrap_draw_slots"]==32*63
    with pytest.raises(ValueError,match="missing or duplicated"):
        r62.summarize(rows[:-1])


def test_add_one_rank_grid_fixed_before_new_outer_sources():
    assert 1/(r62.B+1)==1/64
    assert 3/(r62.B+1)==.046875
    assert 4/(r62.B+1)==.0625
    assert r62.ORIGINAL_ALPHA==.05
    assert math.isclose(
        .5*math.erfc(math.sqrt(r62.ORIGINAL_CUTOFF/2)),.05,
        abs_tol=1e-12)


def test_original_exact_shards_fail_closed_on_sha256_and_source_collision(tmp_path,monkeypatch):
    monkeypatch.setenv("GITHUB_SHA","R62-frozen-source-head")
    cases=[r62.empty_case(b,s)
           for b in range(r62.BLOCKS) for s in r62.SUPPORT]
    for case in cases:
        case["bootstrap"]=[r62.empty_draw(j) for j in range(r62.B)]
    parts=tmp_path/"parts"
    for start,stop in r62.SHARDS:
        target=parts/f"part-{start}"
        target.mkdir(parents=True)
        raw=json.dumps(
            [case for case in cases if start<=case["block"]<stop],
            sort_keys=True,indent=2)+"\n"
        (target/"cases.json").write_text(raw)
        (target/"manifest.json").write_text(json.dumps({
            "study":r62.STUDY,"start":start,"stop":stop,
            "new_source_seed":r62.MASTER_SEED,
            "new_draw_seed":r62.DRAW_SEED,
            "checkout":"R62-frozen-source-head",
            "source_count":2*(stop-start),
            "sha256_cases":hashlib.sha256(raw.encode()).hexdigest(),
        })+"\n")
    r62.aggregate(tmp_path/"complete",parts)
    assert (tmp_path/"complete"/"summary.json").exists()
    (parts/"part-0"/"cases.json").write_text("tampered")
    with pytest.raises(ValueError,match="SHA256"):
        r62.aggregate(tmp_path/"tampered",parts)
