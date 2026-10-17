"""Prospectively frozen W3 R59 Gaussian true-null replication and refusal tests."""
import hashlib
import json

import numpy as np
import pytest

from scripts import run_w3_r57_nested_zero_nonnegative_reml as r57
from scripts import run_w3_r58_boundary_null_reference as r58
from scripts import run_w3_r59_independent_null_replication as r59


def test_new_128_primitive_source_contract():
    assert r59.MASTER_SEED not in (r57.MASTER_SEED, r58.MASTER_SEED)
    assert r59.BLOCKS == 128 and r59.PARTICIPANTS == 24
    assert r59.SLOTS == 256
    assert r59.FITS == 512
    assert r59.STARTS == 1536
    assert len(r59.SHARDS) == 8
    a = r59.independent_source(0, r59.SUPPORT[0])
    b = r59.independent_source(0, r59.SUPPORT[1])
    c = r59.independent_source(1, r59.SUPPORT[0])
    old = r58.independent_source(0, r59.SUPPORT[0])
    np.testing.assert_array_equal(a[0]["participant_slope"],
                                  b[0]["participant_slope"])
    assert not np.array_equal(a[0]["participant_slope"],
                              c[0]["participant_slope"])
    assert not np.array_equal(a[0]["participant_slope"],
                              old[0]["participant_slope"])
    with pytest.raises(ValueError, match="outside"):
        r59.independent_source(128, r59.SUPPORT[0])


def test_true_structural_zero_source_refusal_and_candidate_not_qualified():
    row = r59.evaluate(0, r59.SUPPORT[0])
    assert row["source_status"] == "ok"
    assert row["generating_state"] == "true_zero"
    assert row["true_slope_variance"] == 0.
    assert row["slope_innovation_L2_removed"] > 0.
    assert len(row["null_fit"]["original_starts"]) == 2
    assert len(row["alternative_fit"]["original_starts"]) == 4
    comp = row["comparison"]
    if comp["status"] == "ok":
        assert comp["candidate_half_chisquare_p"] == pytest.approx(
            r58.candidate_boundary_pvalue(comp["nonnegative_deviance"])
        )
        assert comp["candidate_nominal_005_exceedance"] is (
            comp["nonnegative_deviance"] > r59.CRITICAL
        )
    else:
        assert comp["candidate_nominal_005_exceedance"] is None
    assert not comp["null_reference_validated"]
    assert not row["release_authorized"]


def empty():
    return [r59.empty_case(b,s) for b in range(r59.BLOCKS)
            for s in r59.SUPPORT]


def test_full_256_case_and_1536_start_denominator_retained():
    rows = empty()
    q = r59.summary(rows)
    assert q["recorded_cases"] == 256
    assert q["recorded_H0_H1_model_slots"] == 512
    assert q["recorded_optimizer_start_slots"] == 1536
    assert not q["release_authorized"]
    assert q["both_leverage_candidate_comparisons_accepted"] == 0
    for cell in q["strata"].values():
        assert cell["nested_reference_numeric_refusals"] == 128
        assert cell["candidate_exceedance_Wilson95_accepted_only"] is None
    with pytest.raises(ValueError, match="denominator"):
        r59.summary(rows[:-1])
    with pytest.raises(ValueError, match="denominator"):
        r59.summary(rows[:-1] + [rows[0]])


def test_paired_exceedance_paths_cannot_be_counted_as_independent():
    rows = empty()
    for b, ordinary, extreme in (
        (0, True, False),
        (1, False, True),
        (2, True, True),
        (3, False, False),
    ):
        for support, reject in zip(r59.SUPPORT,(ordinary,extreme)):
            row = next(r for r in rows
                       if r["block"] == b and r["support"] == support)
            row["comparison"].update(
                status="ok", candidate_nominal_005_exceedance=reject,
                nonnegative_deviance=3. if reject else 0.,
                H1_selected_exact_zero=not reject,
            )
    q = r59.summary(rows)
    assert q["both_leverage_candidate_comparisons_accepted"] == 4
    assert q["paired_ordinary_only_exceedance"] == 1
    assert q["paired_extreme_only_exceedance"] == 1
    assert q["paired_both_exceedances"] == 1
    assert q["paired_neither_exceedances"] == 1


def test_sha256_exact_original_shard_partition_refuses_tamper(tmp_path,monkeypatch):
    monkeypatch.setenv("GITHUB_SHA","prospectively-frozen-r59-merge")
    rows = empty()
    folder=tmp_path/"shards"
    for start,stop in r59.SHARDS:
        path=folder/f"new-{start}"
        path.mkdir(parents=True)
        batch = [r for r in rows if start <= r["block"] < stop]
        r58.write_json(path/"cases.json", batch)
        r58.write_json(path/"manifest.json", {
            "study": r59.STUDY, "start": start, "stop": stop,
            "new_seed": r59.MASTER_SEED,
            "checkout": "prospectively-frozen-r59-merge",
            "records": len(batch),
            "sha256_cases": hashlib.sha256(
                (path/"cases.json").read_bytes()).hexdigest(),
        })
    r59.aggregate(tmp_path/"complete",folder)
    assert len((tmp_path/"complete"/"SHA256SUMS").read_text().splitlines()) == 3
    (folder/"new-0"/"cases.json").write_text("tamper")
    with pytest.raises(ValueError,match="SHA256"):
        r59.aggregate(tmp_path/"tampered",folder)
