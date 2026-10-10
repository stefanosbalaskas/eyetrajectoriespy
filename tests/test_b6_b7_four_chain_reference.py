"""Four-chain posterior reference contracts, sign-invariant functionals, fail closed."""
import pytest
pytest.importorskip("arviz")
import numpy as np

from scripts.run_b6_b7_four_chain_reference import (
    DESIGNS, SCREEN, declared_seed, identified_functionals,
    numerical_reference_diagnostics, run_one, write_case, source_truth,
)


def test_new_designs_and_seeds_do_not_reuse_prior_ninefit_namespace():
    assert len(DESIGNS) == 3 and SCREEN["min_bulk_ess"] == 400
    assert declared_seed(20261219, DESIGNS[0], 0) != declared_seed(20261219, DESIGNS[0], 1)
    assert declared_seed(20261219, DESIGNS[0], 0) != declared_seed(20261219, DESIGNS[1], 0)
    with pytest.raises(ValueError, match="declared"):
        declared_seed(20261219, DESIGNS[0], 2)
    with pytest.raises(ValueError, match="undeclared"):
        run_one(design="B7_rank2", replicate=0)


@pytest.mark.parametrize("design", DESIGNS)
def test_exact_prior_generated_truth_geometry(design):
    seed = declared_seed(20261219, design, 0)
    gaze, grid, noise, dimensions, mean, covariance, prior_sd = source_truth(seed, design)
    d = len(dimensions)
    assert len(grid) in (23, 27)
    assert covariance.shape == (len(grid)*d, len(grid)*d)
    assert mean.shape == (len(grid), d)
    assert prior_sd == .45 and len(noise) == d
    assert np.linalg.eigvalsh(covariance).min() > -1e-9
    if design.endswith("asynchronous"):
        assert any(np.isnan(vals).any() for vals in gaze.values)


def test_four_chain_identified_functionals_invariant_under_loading_sign():
    rng = np.random.default_rng(3017)
    n, q = 23, 5
    grid = np.linspace(0, 1, n)
    mean = rng.normal(size=(4, 600, 2, q))
    load = rng.normal(size=(4, 600, 2, q, 1))
    truth_mu = np.zeros((n, 2))
    truth_cov = np.zeros((2*n, 2*n))
    obj = identified_functionals(mean, load, grid, ("x", "y"), truth_mu, truth_cov)
    changed = identified_functionals(mean, -load, grid, ("x", "y"), truth_mu, truth_cov)
    assert len(obj) == 15
    assert set(obj) == set(changed)
    for key in obj:
        np.testing.assert_array_equal(obj[key][0], changed[key][0])
    assert all(np.min(v[0]) >= 0 for k, v in obj.items() if "_variance_" in k)
    assert obj["xy_covariance_midpoint"][0].shape == (4, 600)


def test_explicit_single_dataset_truth_is_not_claimed_coverage():
    import arviz as az
    rng = np.random.default_rng(2026301)
    d = rng.normal(size=(4, 750))
    idata = az.from_dict(
        posterior={"x": d},
        sample_stats={
            "diverging": np.zeros_like(d, dtype=int),
            "energy": rng.normal(size=d.shape),
            "tree_depth": np.ones_like(d, dtype=int)*4,
        })
    summaries = numerical_reference_diagnostics(idata, {"x_mid": (d, 0.0)})
    assert summaries["sampler"]["divergences"] == 0
    assert summaries["sampler"]["sample_stats_chains"] == 4
    assert summaries["functionals"]["x_mid"]["single_dataset_90pct_interval_contains_truth"]
    assert not summaries["functionals"]["x_mid"]["nominal_interval_coverage_qualified"]
    assert not summaries["independent_posterior_scientifically_qualified"]


def test_json_sha256_failure_inclusive_ledger(tmp_path):
    from hashlib import sha256
    import json
    row = {"design": DESIGNS[0], "status": "failed", "error_type": "NumericalError"}
    write_case(row, tmp_path, 20261219)
    checks = (tmp_path/"SHA256SUMS").read_text().splitlines()
    for line in checks:
        digest, name = line.split("  ")
        assert sha256((tmp_path/name).read_bytes()).hexdigest() == digest
    assert json.loads((tmp_path/"evidence.json").read_text())["fit_exceptions_in_this_shard"] == 1
    assert json.loads((tmp_path/"evidence.json").read_text())["release_authorized"] is False
