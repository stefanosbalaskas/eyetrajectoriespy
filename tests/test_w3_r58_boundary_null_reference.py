"""R58 frozen denominators, candidate reference and tamper/refusal tests."""
import hashlib
import json
import math

import numpy as np
import pytest

from scripts import run_w3_r57_nested_zero_nonnegative_reml as r57
from scripts import run_w3_r58_boundary_null_reference as r58


def test_new_independent_source_contract():
    assert r58.MASTER_SEED != r57.MASTER_SEED
    assert r58.BLOCKS == 24 and r58.PARTICIPANTS == 24
    assert len(r58.SHARDS) == 6
    assert r58.N_SOURCE_CASES == 96
    assert r58.N_MODEL_FITS == 192
    assert r58.N_SOLVER_STARTS == 576
    a = r58.independent_source(0, r58.SUPPORT[0])
    b = r58.independent_source(0, r58.SUPPORT[1])
    c = r58.independent_source(1, r58.SUPPORT[0])
    old = r57.independent_source(0, r58.SUPPORT[0])
    np.testing.assert_array_equal(
        a[0]["participant_slope"], b[0]["participant_slope"]
    )
    assert not np.array_equal(
        a[0]["participant_slope"], c[0]["participant_slope"]
    )
    assert not np.array_equal(
        a[0]["participant_slope"], old[0]["participant_slope"]
    )
    with pytest.raises(ValueError, match="unregistered"):
        r58.independent_source(r58.BLOCKS, r58.SUPPORT[0])


def test_half_chisquare_candidate_boundary_atom_and_critical():
    assert r58.CRITICAL == pytest.approx(2.705543454095404, rel=1e-12)
    assert r58.candidate_boundary_pvalue(0.) == 1.0
    assert r58.candidate_boundary_pvalue(r58.CRITICAL) == pytest.approx(.05)
    assert r58.candidate_boundary_pvalue(r58.CRITICAL + .01) < .05
    assert r58.candidate_boundary_pvalue(.01) > .05
    with pytest.raises(ValueError):
        r58.candidate_boundary_pvalue(float("nan"))
    with pytest.raises(ValueError):
        r58.candidate_boundary_pvalue(-1.)


def test_wilson_precision_is_not_inferred_from_paired_case_number():
    assert r58.wilson_95(0, 0) is None
    ci = r58.wilson_95(0, 24)
    assert ci[0] == pytest.approx(0.)
    assert .13 < ci[1] < .15
    lo, hi = r58.wilson_95(12, 24)
    assert .30 < lo < .32 and .68 < hi < .70
    for k, n in ((-1, 24), (25, 24), (2, 0)):
        with pytest.raises(ValueError):
            r58.wilson_95(k, n)


def fake_rows():
    return [r58.empty_case(b, s, state)
            for b in range(r58.BLOCKS)
            for s in r58.SUPPORT for state in r58.STATES]


def test_refusals_remain_in_full_source_and_numerical_denominator():
    rows = fake_rows()
    report = r58.summarize(rows)
    assert report["recorded_case_slots"] == 96
    assert report["recorded_optimizer_start_slots"] == 576
    cell = report["strata"][r58.SUPPORT[0] + "/true_zero"]
    assert cell["accepted_comparisons"] == 0
    assert cell["nested_reference_nonaccepted_or_refused"] == 24
    assert cell["wilson95_conditional_on_accepted_calculations"] is None
    assert cell["all_source_rejection_fraction_upper_if_refusals_rejected"] == 1.
    assert not report["candidate_reference_validated"]
    assert not report["pointwise_CR2_90pct_qualified"]
    assert not report["release_authorized"]
    with pytest.raises(ValueError, match="complete unique"):
        r58.summarize(rows[:-1])
    with pytest.raises(ValueError, match="complete unique"):
        r58.summarize(rows[:-1] + [rows[0]])


def test_rejection_uncertainty_is_separated_from_refusal_bounds():
    rows = fake_rows()
    first = next(r for r in rows
                 if r["support"] == r58.SUPPORT[0]
                 and r["generating_state"] == "true_zero")
    first["nested_comparison"].update({
        "status": "ok", "candidate_nominal_005_rejection": True,
        "selected_exact_zero": False, "nonnegative_deviance": 4.,
    })
    cells = r58.summarize(rows)["strata"]
    cell = cells[r58.SUPPORT[0] + "/true_zero"]
    assert cell["accepted_comparisons"] == 1
    assert cell["candidate_reference_rejections"] == 1
    assert cell["wilson95_conditional_on_accepted_calculations"] == pytest.approx([.2065, 1.], abs=.001)
    assert cell["all_source_rejection_fraction_lower_if_refusals_not_rejected"] == pytest.approx(1/24)
    assert cell["all_source_rejection_fraction_upper_if_refusals_rejected"] == 1.


def test_actual_gaussian_pair_keeps_all_optimizer_starts():
    rows = r58.evaluate_pair(0, r58.SUPPORT[0])
    assert len(rows) == 2
    assert {r["generating_state"] for r in rows} == set(r58.STATES)
    assert all(r["source_status"] == "ok" for r in rows)
    assert all(len(r["null_fit"]["original_starts"]) == 2 for r in rows)
    assert all(len(r["alternative_fit"]["original_starts"]) == 4
               for r in rows)
    for r in rows:
        comp = r["nested_comparison"]
        if comp["status"] == "ok":
            t = comp["nonnegative_deviance"]
            assert comp["candidate_nominal_005_rejection"] == (t > r58.CRITICAL)
            assert comp["candidate_half_chi_square_p"] == pytest.approx(
                r58.candidate_boundary_pvalue(t)
            )
        else:
            assert comp["candidate_nominal_005_rejection"] is None


def test_original_source_archive_rejects_tampering(tmp_path, monkeypatch):
    monkeypatch.setenv("GITHUB_SHA", "frozen-r58-merge-checkout")
    parts = tmp_path / "parts"
    rows = fake_rows()
    for a, b in r58.SHARDS:
        folder = parts / f"source-{a}"
        folder.mkdir(parents=True)
        batch = [r for r in rows if a <= r["block"] < b]
        r58.write_json(folder / "cases.json", batch)
        r58.write_json(folder / "manifest.json", {
            "study": r58.STUDY, "start": a, "stop": b,
            "seed": r58.MASTER_SEED,
            "original_checkout": "frozen-r58-merge-checkout",
            "records": len(batch),
            "SHA256_cases": hashlib.sha256(
                (folder / "cases.json").read_bytes()).hexdigest(),
        })
    r58.aggregate(tmp_path / "complete", parts)
    sums = (tmp_path / "complete" / "SHA256SUMS").read_text().splitlines()
    assert len(sums) == 3
    (parts / "source-0" / "cases.json").write_text("corrupted")
    with pytest.raises(ValueError, match="SHA256"):
        r58.aggregate(tmp_path / "tampered", parts)


def test_nonfinite_json_not_accepted(tmp_path):
    with pytest.raises(ValueError):
        r58.write_json(tmp_path / "bad.json", {"error": math.nan})
