"""Independent rank-two Gaussian covariance and marginal-likelihood contracts."""
from dataclasses import replace
import numpy as np
import pytest

from scripts.run_b6_b7_rank2_likelihood_contract import (
    generate_case, observed_design, dense_gaussian_loglike,
    score_marginal_loglike, rotate_factor, population_covariance, full_contract,
)


@pytest.mark.parametrize("paired", [True, False])
@pytest.mark.parametrize("near_tied", [True, False])
def test_independent_dense_loglik_matches_woodbury_under_asynchrony_and_equal_eigenvalues(paired, near_tied):
    case = generate_case(77341, paired=paired, near_tied=near_tied, participants=5)
    assert case.exact_matched_prior is (not near_tied)
    if not paired:
        assert any(np.isnan(v).any() for v in case.gaze.values)
    assert np.isclose(score_marginal_loglike(case), dense_gaussian_loglike(case), rtol=0, atol=1e-7)
    X, y, var = observed_design(case, 0)
    assert X.shape[1] == 10 and X.shape[0] == len(y) == len(var)
    assert var.min() > 0


def test_signed_rotation_equivalence_without_loading_identifiability():
    case = generate_case(93017, paired=False, near_tied=True, participants=5)
    t = .81
    R = np.array([[np.cos(t), -np.sin(t)],[np.sin(t), np.cos(t)]])
    rotated = rotate_factor(case, R)
    np.testing.assert_allclose(population_covariance(case),population_covariance(rotated),atol=1e-12)
    np.testing.assert_allclose(score_marginal_loglike(case),score_marginal_loglike(rotated),atol=1e-9)
    np.testing.assert_allclose(dense_gaussian_loglike(case),dense_gaussian_loglike(rotated),atol=1e-9)
    assert not np.allclose(case.loading,rotated.loading)
    with pytest.raises(ValueError,match="orthogonal"):
        rotate_factor(case, np.ones((2,2)))


def test_near_tied_components_are_explicit_out_of_prior_stress_not_sbc():
    case = generate_case(3107, paired=True, near_tied=True, participants=5)
    cov = population_covariance(case)
    eig = np.linalg.eigvalsh(cov)
    assert eig[-2] > 0
    np.testing.assert_allclose(eig[-2:], [0.09, 0.09], rtol=0, atol=1e-10)


def test_rank_two_likelihood_changes_with_mean_and_data():
    case = generate_case(11477, paired=True, near_tied=False, participants=5)
    altered = replace(case, mean=case.mean + .09)
    assert abs(dense_gaussian_loglike(case)-dense_gaussian_loglike(altered)) > 1e-3
    assert abs(score_marginal_loglike(case)-score_marginal_loglike(altered)) > 1e-3
    for c in (case, altered):
        assert np.isclose(dense_gaussian_loglike(c),score_marginal_loglike(c), atol=1e-8)


def test_complete_contract_preserves_failure_and_promotion_boundaries():
    rows = full_contract()
    assert len(rows)==4 and all(x["mathematical_contract_passed"] for x in rows)
    assert sum(x["exact_matched_prior"] for x in rows)==2
    assert all(not x["posterior_computation_qualified"] for x in rows)
    assert all(not x["coverage_qualified"] and not x["release_authorized"] for x in rows)
