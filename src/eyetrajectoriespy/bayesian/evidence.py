"""B5 experimental backend-independent posterior evidence infrastructure.

All posterior probabilities are conditional on the input posterior draws and
declared model; none implies frequentist coverage, model truth, or algorithm
calibration. No Bayesian runtime dependency is imposed on stable users.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import pandas as pd
from scipy.special import logsumexp


@dataclass(frozen=True)
class BayesianFunctionalDraws:
    """Functional posterior with shape (chains, draws, time, dimensions)."""

    values: np.ndarray
    time: np.ndarray
    dimension_names: tuple[str, ...]
    provenance: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        values = np.array(self.values, dtype=float, copy=True)
        time = np.array(self.time, dtype=float, copy=True)
        if values.ndim != 4 or min(values.shape) < 1:
            raise ValueError("posterior values must have shape (chains, draws, time, dimensions)")
        if time.shape != (values.shape[2],) or len(time) < 2 or not np.all(np.isfinite(time)) or not np.all(np.diff(time) > 0):
            raise ValueError("posterior time must be finite, matching and strictly increasing")
        if len(self.dimension_names) != values.shape[3] or len(set(self.dimension_names)) != values.shape[3]:
            raise ValueError("dimension names must match the last posterior dimension and be unique")
        if not np.isfinite(values).all():
            raise ValueError("posterior draws must all be finite; do not hide failures")
        values.setflags(write=False)
        time.setflags(write=False)
        object.__setattr__(self, "values", values)
        object.__setattr__(self, "time", time)
        object.__setattr__(self, "dimension_names", tuple(self.dimension_names))
        object.__setattr__(self, "provenance", dict(self.provenance))

    @property
    def sample_count(self) -> int:
        return self.values.shape[0] * self.values.shape[1]


@dataclass(frozen=True)
class BayesianCredibleBand:
    center: np.ndarray
    lower: np.ndarray
    upper: np.ndarray
    coverage: float
    scope: str
    evidence: Mapping[str, Any]


def _coverage(coverage: float) -> float:
    if isinstance(coverage, bool) or not np.isfinite(coverage) or not 0 < coverage < 1:
        raise ValueError("coverage must be strictly between 0 and 1")
    return float(coverage)


def bayesian_credible_band(
    posterior: BayesianFunctionalDraws, *,
    coverage: float = .95, simultaneous: bool = False,
) -> BayesianCredibleBand:
    """Draw-derived pointwise quantiles or posterior gridwise sup-t bands.

    Simultaneous = posterior sup-absolute-standardized-deviation quantile
    across *all times and dimensions*. No unobserved continuous-time
    simultaneity and no repeated-sampling frequentist coverage are claimed.
    """
    if not isinstance(posterior, BayesianFunctionalDraws):
        raise TypeError("expected BayesianFunctionalDraws")
    c = _coverage(coverage)
    flat = posterior.values.reshape(-1, *posterior.values.shape[2:])
    if len(flat) < 20:
        raise ValueError("at least 20 posterior curves required for empirical bands")
    center = np.mean(flat, axis=0)
    if simultaneous:
        sd = flat.std(axis=0, ddof=1)
        z = np.divide(
            np.abs(flat - center), sd[None, ...],
            out=np.zeros_like(flat), where=sd[None, ...] > 1e-14,
        )
        if np.any((sd <= 1e-14) & (np.ptp(flat, axis=0) > 1e-10)):
            raise RuntimeError("posterior zero-variance numerical instability")
        width = np.quantile(np.max(z, axis=(1, 2)), c) * sd
        lower, upper = center-width, center+width
        scope = "posterior_gridwise_joint_all_time_and_dimensions"
    else:
        lower = np.quantile(flat, (1-c)/2, axis=0)
        upper = np.quantile(flat, 1-(1-c)/2, axis=0)
        scope = "posterior_pointwise_equal_tailed"
    return BayesianCredibleBand(
        center=center, lower=lower, upper=upper, coverage=c,
        scope=scope, evidence={
            "posterior_samples": len(flat),
            "conditional_on_prior_likelihood_and_sampler": True,
            "frequentist_coverage_qualified": False,
            "continuous_time_simultaneity": False,
            "empirical_gridwise_joint_content_only": bool(simultaneous),
            "experimental": True,
        },
    )


def bayesian_functional_probability(
    posterior: BayesianFunctionalDraws, *,
    event: str, threshold: float, dimension: str,
) -> dict[str, Any]:
    """Posterior probability of one explicitly named curve event."""
    if not isinstance(posterior, BayesianFunctionalDraws):
        raise TypeError("expected BayesianFunctionalDraws")
    if dimension not in posterior.dimension_names:
        raise ValueError("dimension must name one posterior channel")
    if not np.isfinite(threshold):
        raise ValueError("threshold must be finite and prespecified")
    selected = posterior.values[..., posterior.dimension_names.index(dimension)]
    if event == "above_all":
        success = (selected > threshold).all(axis=-1)
    elif event == "below_all":
        success = (selected < threshold).all(axis=-1)
    elif event == "integrated_mean_above":
        mean = np.trapezoid(selected, x=posterior.time, axis=-1) / (posterior.time[-1]-posterior.time[0])
        success = mean > threshold
    else:
        raise ValueError("event must be above_all, below_all or integrated_mean_above")
    return {
        "event": event, "threshold": float(threshold), "dimension": dimension,
        "posterior_probability": float(success.mean()),
        "n_posterior_curves": posterior.sample_count,
        "posterior_monte_carlo_se_naive": float(np.sqrt(success.mean()*(1-success.mean())/success.size)),
        "naive_monte_carlo_se_ignores_chain_autocorrelation": True,
        "conditional_posterior_event_probability_not_p_value": True,
    }


def _predictive_check(
    replicated: np.ndarray, observed: np.ndarray, *,
    source: str, statistic: str,
) -> pd.DataFrame:
    draws = np.asarray(replicated, dtype=float)
    truth = np.asarray(observed, dtype=float)
    if draws.ndim != 4 or truth.ndim != 3 or draws.shape[1:] != truth.shape:
        raise ValueError("predictive draws require (draws, curves, time, dimensions), observed matching 3-D")
    if len(draws) < 10 or not np.isfinite(draws).all() or not np.isfinite(truth).all():
        raise ValueError(">=10 finite predictive draws and finite observations required")
    if statistic == "grand_mean":
        simulated = draws.mean(axis=(1, 2))
        measured = truth.mean(axis=(0, 1))
    elif statistic == "pointwise_sd":
        simulated = draws.std(axis=(1, 2), ddof=0)
        measured = truth.std(axis=(0, 1), ddof=0)
    else:
        raise ValueError("statistic must be grand_mean or pointwise_sd")
    return pd.DataFrame({
        "dimension_index": np.arange(truth.shape[-1]),
        "observed_statistic": measured,
        "predictive_median": np.median(simulated, axis=0),
        "predictive_q025": np.quantile(simulated, .025, axis=0),
        "predictive_q975": np.quantile(simulated, .975, axis=0),
        "posterior_predictive_tail_probability": np.mean(simulated >= measured[None, :], axis=0),
        "statistic": statistic,
        "source": source,
        "scientific_calibration_qualified": False,
    })


def bayesian_prior_predictive_check(
    prior_predictive: np.ndarray, observed: np.ndarray, *, statistic: str = "grand_mean",
) -> pd.DataFrame:
    """Descriptive prior predictive adequacy; requires actual simulated data."""
    return _predictive_check(prior_predictive, observed, source="prior_predictive", statistic=statistic)


def bayesian_posterior_predictive_check(
    posterior_predictive: np.ndarray, observed: np.ndarray, *, statistic: str = "grand_mean",
) -> pd.DataFrame:
    """Descriptive posterior predictive adequacy; not a formal p-value test."""
    return _predictive_check(posterior_predictive, observed, source="posterior_predictive", statistic=statistic)


def bayesian_diagnostics_frame(inference_data: Any, *, var_names: list[str] | None = None) -> pd.DataFrame:
    """ArviZ diagnostics: Rhat, bulk/tail ESS and MCSE, if supported.

    Rhat requires multiple chains. Missing diagnostics stay missing, never
    spuriously pass. Divergence count is surfaced when sample_stats holds it.
    """
    try:
        import arviz as az
    except ImportError as e:
        raise ImportError("Install optional eyetrajectoriespy[bayesian] for ArviZ diagnostics") from e
    if not hasattr(inference_data, "posterior"):
        raise TypeError("ArviZ InferenceData with posterior group required")
    posterior = inference_data.posterior
    names = var_names if var_names is not None else list(posterior.data_vars)
    if not names or any(n not in posterior.data_vars for n in names):
        raise ValueError("var_names must be present in the InferenceData posterior")
    divergences = None
    if hasattr(inference_data, "sample_stats") and "diverging" in inference_data.sample_stats:
        divergences = int(np.asarray(inference_data.sample_stats["diverging"]).sum())
    rows = []
    for name in names:
        current = posterior[[name]]
        def read(method: str, **kwargs) -> float:
            try:
                fn = getattr(az, method)
                result = fn(current, var_names=[name], **kwargs)
                raw = np.asarray(result[name], dtype=float)
                return float(np.nanmin(raw)) if method == "ess" else float(np.nanmax(raw)) if method == "rhat" else float(np.nanmax(raw))
            except (ValueError, TypeError, RuntimeError):
                return float("nan")
        n_chains = int(posterior.sizes.get("chain", 0))
        rows.append({
            "variable": name,
            "n_chains": n_chains,
            "n_draws_per_chain": int(posterior.sizes.get("draw", 0)),
            "rhat_max": read("rhat") if n_chains >= 2 else np.nan,
            "ess_bulk_min": read("ess", method="bulk"),
            "ess_tail_min": read("ess", method="tail"),
            "mcse_mean_max": read("mcse", method="mean"),
            "divergences": divergences,
            "convergence_qualified": False,
            "status": "descriptive_diagnostics_only",
        })
    return pd.DataFrame(rows)


def bayesian_calibration_study(
    known_truth: np.ndarray, posterior_parameter_draws: np.ndarray, *,
    bins: int = 10, random_state: int = 1,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Rank SBC for independently simulated prior-truth/posterior pairs.

    Only scalar parameter per replicate is supported. The calling workflow
    must independently generate truth from the *actual prior*, observations
    from the likelihood and posterior draws with no truth-conditioned tuning.
    """
    truth = np.asarray(known_truth, dtype=float)
    draws = np.asarray(posterior_parameter_draws, dtype=float)
    if truth.ndim != 1 or draws.ndim != 2 or draws.shape[0] != len(truth):
        raise ValueError("truth must be (replicates,), posterior draws (replicates, draws)")
    if len(truth) < 5 or draws.shape[1] < 10 or not np.isfinite(truth).all() or not np.isfinite(draws).all():
        raise ValueError(">=5 finite replicates and >=10 finite posterior draws required")
    if isinstance(bins, bool) or not isinstance(bins, int) or not 2 <= bins <= draws.shape[1]+1:
        raise ValueError("invalid SBC bin count")
    rng = np.random.default_rng(random_state)
    ranks = (draws < truth[:, None]).sum(axis=1)
    ties = (draws == truth[:, None]).sum(axis=1)
    ranks += np.asarray([rng.integers(0, int(t)+1) for t in ties])
    counts, boundaries = np.histogram(ranks, bins=np.linspace(0, draws.shape[1]+1, bins+1))
    frame = pd.DataFrame({"bin": np.arange(bins), "rank_start": boundaries[:-1],
                          "rank_end": boundaries[1:], "count": counts})
    return frame, {
        "n_replicates": len(truth), "n_draws_per_replicate": draws.shape[1],
        "seed": random_state, "tie_handling": "randomized",
        "actual_prior_likelihood_sampling_verified": False,
        "independent_replicates_verified": False,
        "sbc_uniformity_qualified": False,
        "observed_rank_mean": float(ranks.mean()),
    }


def bayesian_predictive_comparison(
    observed: np.ndarray, predictive_draws: np.ndarray, *,
    noise_sd: float, holdout_units: list[str], train_units: list[str],
) -> pd.DataFrame:
    """Heldout pointwise log mixture score under explicit Gaussian noise.

    Samples are assumed conditionally independent *across observations*
    given each draw; sums are descriptive and must not be presented as
    joint longitudinal likelihood without a correct covariance model.
    """
    y = np.asarray(observed, float)
    pred = np.asarray(predictive_draws, float)
    if y.ndim != 3 or pred.ndim != 4 or pred.shape[1:] != y.shape or len(pred) < 10:
        raise ValueError("observed (unit,time,dimension) and predictions (draw,unit,time,dimension)")
    if not np.isfinite(y).all() or not np.isfinite(pred).all():
        raise ValueError("heldout observations and predictions must be finite")
    if not np.isfinite(noise_sd) or noise_sd <= 0:
        raise ValueError("noise_sd must be positive and declared")
    if len(holdout_units) != y.shape[0] or len(set(holdout_units)) != len(holdout_units) or set(holdout_units).intersection(train_units):
        raise ValueError("heldout units must be unique and disjoint from training")
    if not train_units or len(set(train_units)) != len(train_units):
        raise ValueError("training units must have unique identifiers")
    ll = -.5 * ((y[None]-pred)/noise_sd)**2 - np.log(noise_sd*np.sqrt(2*np.pi))
    pointwise = logsumexp(ll, axis=0)-np.log(len(pred))
    return pd.DataFrame({
        "holdout_unit": holdout_units,
        "conditional_pointwise_log_score": pointwise.sum(axis=(1,2)),
        "n_time": y.shape[1], "n_dimensions": y.shape[2],
        "joint_curve_predictive_density_verified": False,
        "training_leakage_guard_passed": True,
    })


def export_bayesian_analysis(
    posterior: BayesianFunctionalDraws, output_prefix: str | Path, *,
    model_name: str, priors: Mapping[str, Any], diagnostics: Mapping[str, Any],
) -> dict[str, str]:
    """Portable NPZ + JSON with SHA256, no executable pickle serialization."""
    if not isinstance(posterior, BayesianFunctionalDraws):
        raise TypeError("expected BayesianFunctionalDraws")
    if not model_name.strip() or not priors:
        raise ValueError("explicit model name and nonempty priors required")
    output = Path(output_prefix)
    output.parent.mkdir(parents=True, exist_ok=True)
    npz_path = output.with_suffix(".npz")
    json_path = output.with_suffix(".json")
    np.savez_compressed(npz_path, draws=posterior.values, time=posterior.time,
                        dimension_names=np.asarray(posterior.dimension_names, dtype="U"))
    descriptor = {
        "format": "bayesian_posterior_npz_json_v1",
        "model_name": model_name, "priors": dict(priors),
        "diagnostics": dict(diagnostics),
        "provenance": dict(posterior.provenance),
        "posterior_shape": list(posterior.values.shape),
        "sha256_npz": sha256(npz_path.read_bytes()).hexdigest(),
        "posterior_sampling_calibrated": False,
        "production_inference_qualified": False,
    }
    json_path.write_text(json.dumps(descriptor, indent=2, sort_keys=True, allow_nan=False)+"\n")
    return {"npz": str(npz_path), "json": str(json_path), "sha256_npz": descriptor["sha256_npz"]}
