"""No Bayesian promotion from a targeted same-dataset convergence recheck."""
from hashlib import sha256
import json

import pytest
pytest.importorskip("arviz")  # optional Bayesian dependency absent from core CI

from scripts.run_b6_rank1_prior_sbc_pilot import SEED, fresh_seed
from scripts.run_b6_rank1_sbc_r2_refit import (
    CONFIG, PRIMARY, TARGET_REPLICATE, original_dataset_seed,
    summarize_reliability, preserve,
)


def test_exact_source_seed_and_prespecified_full_budget():
    assert original_dataset_seed() == fresh_seed(SEED, 1)
    assert TARGET_REPLICATE == 1
    assert CONFIG["chains"] == 4
    assert CONFIG["draws_per_chain"] == 800
    assert CONFIG["warmup_per_chain"] == 1200


def row(status="ok", screen=True, contains=True):
    return {
        "status": status, "all_functional_screen_passed": screen,
        "primary_targets": {
            t: {"interval_contains_truth": contains} for t in PRIMARY
        } if status == "ok" else {},
    }


def test_failure_screen_and_interval_denominators_are_distinct():
    r = summarize_reliability([row(), row(screen=False), row("failed")])
    assert r["attempts"] == 3
    assert r["completed_fits"] == 2
    assert r["computational_screen_passes"] == 1
    assert r["conditional_calibration_denominator"] == 1
    assert r["end_to_end_reliability_denominator"] == 3
    for t in PRIMARY:
        assert r["targets"][t]["truth_in_interval_completed_fits"] == 2
        assert r["targets"][t]["truth_in_interval_adequately_sampled"] == 1
        assert r["targets"][t]["end_to_end_screen_and_interval_successes"] == 1
    assert not r["posterior_calibration_qualified"]


def test_preserves_fit_failure_and_checksum(tmp_path):
    r = row("failed")
    r["error"] = "example"
    preserve(r, tmp_path)
    assert json.loads((tmp_path/"evidence.json").read_text())["fit_failures"] == 1
    for line in (tmp_path/"SHA256SUMS").read_text().splitlines():
        digest, path = line.split("  ")
        assert sha256((tmp_path/path).read_bytes()).hexdigest() == digest


def test_invalid_records_do_not_silently_qualify():
    with pytest.raises(ValueError, match="at least one"):
        summarize_reliability([])
    with pytest.raises(ValueError, match="target"):
        summarize_reliability([{"status": "ok", "all_functional_screen_passed": True,
                                "primary_targets": {}}])
