"""Unpublished B5/B6/B8 Bayesian research layer; never a stable root export."""
from .sparse_score_baseline import BayesianSparseScoreBenchmark, fit_bayesian_sparse_score_baseline
from .function_on_scalar import BayesianFunctionOnScalarFit, fit_bayesian_function_on_scalar
from .evidence import (
    BayesianFunctionalDraws, BayesianCredibleBand,
    bayesian_prior_predictive_check, bayesian_posterior_predictive_check,
    bayesian_diagnostics_frame, bayesian_credible_band,
    bayesian_functional_probability, bayesian_calibration_study,
    bayesian_predictive_comparison, export_bayesian_analysis,
)
__all__ = [
    "BayesianSparseScoreBenchmark", "fit_bayesian_sparse_score_baseline",
    "BayesianFunctionOnScalarFit", "fit_bayesian_function_on_scalar",
    "BayesianFunctionalDraws", "BayesianCredibleBand",
    "bayesian_prior_predictive_check", "bayesian_posterior_predictive_check",
    "bayesian_diagnostics_frame", "bayesian_credible_band",
    "bayesian_functional_probability", "bayesian_calibration_study",
    "bayesian_predictive_comparison", "export_bayesian_analysis",
]
