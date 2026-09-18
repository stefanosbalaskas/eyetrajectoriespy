"""Optional elastic SRVF analysis through the mature :mod:`fdasrsf` backend."""

from __future__ import annotations

import numpy as np

from .types import ElasticFPCAResult, TrajectorySet
from .validation import validate_trajectory_set


def _require_fdasrsf():
    try:
        import fdasrsf as fs
    except ImportError as exc:  # pragma: no cover - depends on optional environment
        raise ImportError(
            "Elastic SRVF analysis requires the optional dependency 'fdasrsf'. "
            "Install eyetrajectoriespy with the 'elastic' extra."
        ) from exc
    return fs


def fit_elastic_fpca(
    trajectories: TrajectorySet,
    *,
    n_components: int = 3,
    rotation: bool = False,
    scale_curves: bool = False,
    lam: float = 0.0,
    method: str = "DP",
) -> ElasticFPCAResult:
    """Fit elastic planar-curve FPCA using ``fdasrsf``.

    Unlike ordinary grid FPCA, elastic analysis aligns curves in the
    square-root velocity framework and explicitly estimates warping functions.
    The function intentionally exposes ``rotation`` and ``scale_curves`` rather
    than normalizing geometry silently: rotation or scale invariance is often
    inappropriate for screen-based eye tracking where absolute layout matters.
    """

    validate_trajectory_set(trajectories, require_complete=True)
    if trajectories.n_dimensions < 2:
        raise ValueError("Elastic curve analysis requires at least two dimensions")
    if n_components < 1:
        raise ValueError("n_components must be positive")
    fs = _require_fdasrsf()
    # fdasrsf expects (n_dimensions, n_samples, n_curves).
    beta = np.transpose(trajectories.values, (2, 1, 0))
    obj = fs.fdacurve(beta, N=trajectories.n_time, scale=scale_curves)
    obj.karcher_mean(rotation=rotation, parallel=False, lam=lam, method=method)
    obj.srvf_align(rotation=rotation, parallel=False, lam=lam, method=method)
    obj.shape_pca(no=n_components)

    betan = np.asarray(obj.betan)
    aligned_values = np.transpose(betan, (2, 1, 0))
    aligned = trajectories.with_values(
        aligned_values,
        provenance_update={
            "elastic_registration": {
                "backend": "fdasrsf",
                "rotation": rotation,
                "scale_curves": scale_curves,
                "lam": lam,
                "method": method,
            }
        },
    )
    gams = np.asarray(getattr(obj, "gams", np.empty((trajectories.n_time, trajectories.n_curves))))
    if gams.shape == (trajectories.n_time, trajectories.n_curves):
        gams = gams.T
    coef = getattr(obj, "coef", None)
    scores = None if coef is None else np.asarray(coef)
    if scores is not None and scores.ndim == 2 and scores.shape[0] != trajectories.n_curves and scores.shape[1] == trajectories.n_curves:
        scores = scores.T
    pd = getattr(obj, "pca", None)
    principal = None if pd is None else np.asarray(pd)
    mean_curve = getattr(obj, "beta_mean", None)
    mean_curve = None if mean_curve is None else np.asarray(mean_curve)
    return ElasticFPCAResult(
        aligned=aligned,
        warping_functions=gams,
        scores=scores,
        principal_directions=principal,
        mean_curve=mean_curve,
        backend="fdasrsf",
        provenance={
            "phase_amplitude_separated": True,
            "timing_warning": (
                "Warping changes traversal timing. Retain and analyze warping functions when latency is meaningful."
            ),
        },
        backend_object=obj,
    )
