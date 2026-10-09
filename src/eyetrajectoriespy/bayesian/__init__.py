"""Unpublished B5/B6/B8 Bayesian research layer; never a stable root export."""
from .evidence import (
    BayesianFunctionalDraws, BayesianCredibleBand,
    bayesian_prior_predictive_check, bayesian_posterior_predictive_check,
    bayesian_diagnostics_frame, bayesian_credible_band,
    bayesian_functional_probability, bayesian_calibration_study,
    bayesian_predictive_comparison, export_bayesian_analysis,
)
__all__ = [
    "BayesianFunctionalDraws", "BayesianCredibleBand",
    "bayesian_prior_predictive_check", "bayesian_posterior_predictive_check",
    "bayesian_diagnostics_frame", "bayesian_credible_band",
    "bayesian_functional_probability", "bayesian_calibration_study",
    "bayesian_predictive_comparison", "export_bayesian_analysis",
]
