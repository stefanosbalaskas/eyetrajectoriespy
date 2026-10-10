"""Independent dense versus PyMC rank-two graph protocol, no sampler promotion."""
from dataclasses import replace
import json
from hashlib import sha256

import numpy as np
import pytest

from scripts.run_b6_b7_rank2_likelihood_contract import (
    generate_case, dense_gaussian_loglike,
)
from scripts.run_b6_b7_rank2_pymc_graph_contract import (
    independent_dense_logposterior, finite_difference_gradient,
    write_artifact,
)


def test_dense_full_posterior_contains_proper_prior_terms():
    case = generate_case(75337, paired=False, near_tied=False, participants=3)
    posterior = independent_dense_logposterior(case)
    likelihood = dense_gaussian_loglike(case)
    assert np.isfinite(posterior)
    assert abs(posterior-likelihood) > 1e-5
    perturbed = replace(case, mean=case.mean+.12)
    assert abs(independent_dense_logposterior(perturbed)-posterior) > 1e-4


def test_finite_differences_shape_and_invalid_step():
    case = generate_case(91273, paired=True, near_tied=True, participants=2)
    grad = finite_difference_gradient(case)
    assert grad.shape == (case.mean.size+case.loading.size,)
    assert np.isfinite(grad).all()
    with pytest.raises(ValueError, match="positive"):
        finite_difference_gradient(case, 0.0)


def test_failed_contract_retains_source_evidence(tmp_path):
    write_artifact({"status": "failed", "error_type": "DiagnosticFailure"},
                   tmp_path)
    assert json.loads((tmp_path/"evidence.json").read_text())["contract_failures"] == 1
    for line in (tmp_path/"SHA256SUMS").read_text().splitlines():
        digest, path = line.split("  ")
        assert sha256((tmp_path/path).read_bytes()).hexdigest() == digest
