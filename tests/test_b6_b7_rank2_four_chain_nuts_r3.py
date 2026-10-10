"""Research-only rank-two four-chain rotation-invariant population contracts."""
from dataclasses import replace
from hashlib import sha256
import json
import numpy as np
import pytest

from scripts.run_b6_b7_rank2_likelihood_contract import generate_case, rotate_factor
from scripts.run_b6_b7_rank2_four_chain_nuts_r3 import (
    STUDY, DESIGNS, source_seed, invariant_functionals, write_case,
)


def test_declared_datasets_have_separate_seeds_and_matched_prior():
    assert DESIGNS == ("paired", "asynchronous")
    seeds = [source_seed(design) for design in DESIGNS]
    assert len(set(seeds)) == 2
    assert all(isinstance(seed, int) for seed in seeds)
    assert all(generate_case(seed, paired=(design=="paired"), near_tied=False,
                             participants=4).exact_matched_prior
               for seed, design in zip(seeds, DESIGNS))
    with pytest.raises(ValueError, match="unknown"):
        source_seed("near_tied")


@pytest.mark.parametrize("paired", [True, False])
def test_rank2_functionals_are_rotationally_invariant(paired):
    case = generate_case(871231+int(paired), paired=paired,
                         near_tied=False, participants=3)
    rng = np.random.default_rng(65431)
    mean = rng.normal(size=(4, 120, 2, 5)) * 0.1
    load = rng.normal(size=(4, 120, 2, 5, 2)) * 0.15
    ang = .71
    R = np.array([[np.cos(ang),-np.sin(ang)],
                  [np.sin(ang),np.cos(ang)]])
    rotated = load @ R
    a = invariant_functionals(case, mean, load)
    b = invariant_functionals(case, mean, rotated)
    assert len(a) == 15 and a.keys() == b.keys()
    for name in a:
        aa, truth = a[name]
        bb, truth_b = b[name]
        assert aa.shape == (4, 120)
        assert np.isfinite(aa).all()
        assert np.allclose(aa, bb, rtol=1e-11, atol=1e-11)
        assert np.isclose(truth, truth_b)


def test_invariant_functionals_reject_wrong_rank_or_chain_count():
    case = generate_case(81118, paired=True, near_tied=False, participants=3)
    m = np.zeros((4, 120, 2, 5))
    L = np.zeros((4, 120, 2, 5, 2))
    with pytest.raises(ValueError, match="rank-two"):
        invariant_functionals(case, m, L[..., :1])
    with pytest.raises(ValueError, match="rank-two"):
        invariant_functionals(case, m[:2], L[:2])


def test_failure_including_evidence_sha_and_flags(tmp_path):
    row = {
        "study": STUDY, "design":"paired",
        "status": "failed", "error_type": "TestFailure",
        "error": "preserved", "generation_seed": 3,
    }
    write_case(row, tmp_path)
    evidence = json.loads((tmp_path/"evidence.json").read_text())
    assert evidence["attempts"] == 1 and evidence["fit_exceptions"] == 1
    assert not evidence["release_authorized"]
    assert not evidence["SBC_completed"] and not evidence["rank2_posterior_qualified"]
    for item in (tmp_path/"SHA256SUMS").read_text().splitlines():
        digest, path = item.split("  ")
        assert sha256((tmp_path/path).read_bytes()).hexdigest() == digest


def test_nonconverged_fit_is_not_dropped(tmp_path):
    row = {
        "study": STUDY, "design":"paired", "status": "ok",
        "reference_checks": {"all_identified_functionals_pass_exploratory_screen":False},
    }
    write_case(row, tmp_path)
    evidence=json.loads((tmp_path/"evidence.json").read_text())
    assert evidence["fit_exceptions"] == 0
    assert evidence["screen_failure"] == 1
    assert evidence["attempts"] == 1
