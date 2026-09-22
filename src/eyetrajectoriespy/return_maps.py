"""Experimental empirical Poincare-section and return-map diagnostics."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from .embedding import _curve_index, _require_finite
from .nonlinear_types import (
    LocalReturnMapResult,
    PoincareCrossingResult,
    ReturnMapStabilityResult,
)
from .types import TrajectorySet


def poincare_crossings(
    trajectories: TrajectorySet,
    *,
    curve: int | str,
    section_dimension: str,
    section_value: float,
    direction: str,
    state_dimensions: Sequence[str] | None = None,
) -> PoincareCrossingResult:
    """Interpolate crossings of an explicitly declared scalar section.

    By default, the returned crossing state contains every trajectory dimension
    except the section dimension, avoiding an automatically constant coordinate
    in downstream return-map regression.
    """

    if section_dimension not in trajectories.dimension_names:
        raise KeyError(f"Unknown section_dimension {section_dimension!r}")
    if not np.isfinite(section_value):
        raise ValueError("section_value must be finite")
    if direction not in {"positive", "negative", "both"}:
        raise ValueError("direction must be 'positive', 'negative', or 'both'")

    curve_index = _curve_index(trajectories, curve)
    section_index = trajectories.dimension_names.index(section_dimension)
    if state_dimensions is None:
        raise ValueError("state_dimensions must be supplied explicitly")
    state_names = tuple(state_dimensions)
    if not state_names:
        raise ValueError(
            "state_dimensions must contain at least one non-section state variable"
        )
    if len(set(state_names)) != len(state_names):
        raise ValueError("state_dimensions must be unique")
    state_indices = []
    for name in state_names:
        if name not in trajectories.dimension_names:
            raise KeyError(f"Unknown state dimension {name!r}")
        state_indices.append(trajectories.dimension_names.index(name))

    values = trajectories.values[curve_index]
    _require_finite(values, context="Poincare crossing detection")
    section = values[:, section_index] - float(section_value)

    crossing_left = []
    fractions = []
    for i in range(trajectories.n_time - 1):
        a = float(section[i])
        b = float(section[i + 1])
        positive = a < 0 <= b
        negative = a > 0 >= b
        if not (
            (direction == "positive" and positive)
            or (direction == "negative" and negative)
            or (direction == "both" and (positive or negative))
        ):
            continue
        denominator = b - a
        if denominator == 0:
            continue
        fraction = -a / denominator
        if 0 <= fraction <= 1:
            crossing_left.append(i)
            fractions.append(fraction)

    if not crossing_left:
        raise ValueError("no crossings satisfy the declared section and direction")
    left = np.asarray(crossing_left, dtype=int)
    frac = np.asarray(fractions, dtype=float)
    states = np.empty((left.size, len(state_indices)), dtype=float)
    times = np.empty(left.size, dtype=float)
    for row, (i, f) in enumerate(zip(left, frac, strict=True)):
        states[row] = values[i, state_indices] + f * (
            values[i + 1, state_indices] - values[i, state_indices]
        )
        times[row] = trajectories.time[i] + f * (
            trajectories.time[i + 1] - trajectories.time[i]
        )

    return PoincareCrossingResult(
        states=states,
        times=times,
        left_indices=left,
        fractions=frac,
        curve_id=trajectories.curve_ids[curve_index],
        section_dimension=section_dimension,
        section_value=float(section_value),
        direction=direction,
        state_dimensions=state_names,
        provenance={
            "operation": "poincare_crossings",
            "source_provenance": dict(trajectories.provenance),
            "interpolation": "linear_between_observed_samples",
            "section_dimension": section_dimension,
            "section_value": float(section_value),
            "direction": direction,
            "state_dimensions": state_names,
            "experimental": True,
        },
    )


def _reference_state(
    states: np.ndarray,
    reference: str | np.ndarray,
) -> tuple[np.ndarray, str]:
    if isinstance(reference, str):
        if reference == "mean":
            return np.mean(states, axis=0), "mean"
        if reference == "median":
            return np.median(states, axis=0), "median"
        raise ValueError("reference string must be 'mean' or 'median'")
    array = np.asarray(reference, dtype=float)
    if array.shape != (states.shape[1],):
        raise ValueError(
            f"reference state must have shape ({states.shape[1]},); got {array.shape}"
        )
    if not np.all(np.isfinite(array)):
        raise ValueError("reference state must be finite")
    return array, "supplied_state"


def fit_local_return_map(
    crossings: PoincareCrossingResult,
    *,
    reference: str | np.ndarray,
    neighborhood_radius: float | None = None,
    n_neighbors: int | None = None,
) -> LocalReturnMapResult:
    """Fit a local affine map from one section crossing to the next.

    Exactly one neighborhood policy must be specified.  The fitted Jacobian is
    empirical and must not be described as a classical monodromy matrix.
    """

    if (neighborhood_radius is None) == (n_neighbors is None):
        raise ValueError("supply exactly one of neighborhood_radius or n_neighbors")
    if crossings.n_crossings < 3:
        raise ValueError("at least three crossings are required to fit a return map")

    x = np.asarray(crossings.states[:-1], dtype=float)
    y = np.asarray(crossings.states[1:], dtype=float)
    reference_state, reference_policy = _reference_state(x, reference)
    distances = np.linalg.norm(x - reference_state, axis=1)

    if neighborhood_radius is not None:
        if not np.isfinite(neighborhood_radius) or neighborhood_radius <= 0:
            raise ValueError("neighborhood_radius must be positive and finite")
        selected = np.where(distances <= float(neighborhood_radius))[0]
        policy = "radius"
        value: float | int = float(neighborhood_radius)
    else:
        if not isinstance(n_neighbors, (int, np.integer)) or n_neighbors < 1:
            raise ValueError("n_neighbors must be a positive integer")
        if int(n_neighbors) > x.shape[0]:
            raise ValueError(
                "n_neighbors exceeds the number of available return-map transitions"
            )
        count = int(n_neighbors)
        selected = np.argsort(distances, kind="mergesort")[:count]
        policy = "n_neighbors"
        value = int(n_neighbors)

    state_dimension = x.shape[1]
    minimum = state_dimension + 1
    if selected.size < minimum:
        raise ValueError(
            f"local affine return map requires at least {minimum} selected transitions; "
            f"got {selected.size}"
        )

    x_centered = x[selected] - reference_state
    y_centered = y[selected] - reference_state
    design = np.column_stack([np.ones(selected.size), x_centered])
    if np.linalg.matrix_rank(design) < design.shape[1]:
        raise ValueError(
            "selected return-map neighborhood is rank deficient; "
            "change the declared section, state variables, reference, or neighborhood"
        )
    coefficient, _, _, _ = np.linalg.lstsq(design, y_centered, rcond=None)
    fitted = design @ coefficient
    residuals = y_centered - fitted
    intercept = coefficient[0]
    jacobian = coefficient[1:].T

    r_squared = np.full(state_dimension, np.nan, dtype=float)
    for d in range(state_dimension):
        target = y_centered[:, d]
        ss_total = float(np.sum((target - target.mean()) ** 2))
        if ss_total > 0:
            ss_residual = float(np.sum(residuals[:, d] ** 2))
            r_squared[d] = 1.0 - ss_residual / ss_total

    return LocalReturnMapResult(
        reference_state=reference_state,
        selected_transition_indices=np.asarray(selected, dtype=int),
        jacobian=jacobian,
        intercept=np.asarray(intercept, dtype=float),
        residuals=residuals,
        r_squared=r_squared,
        neighborhood_policy=policy,
        neighborhood_value=value,
        provenance={
            "operation": "fit_local_return_map",
            "crossing_provenance": dict(crossings.provenance),
            "reference_policy": reference_policy,
            "neighborhood_policy": policy,
            "neighborhood_value": value,
            "n_selected_transitions": int(selected.size),
            "fit": "local_affine_least_squares",
            "experimental": True,
            "interpretation_boundary": (
                "empirical local return-map Jacobian; not a variational-equation "
                "monodromy matrix and not a classical Floquet multiplier calculation"
            ),
        },
    )


def return_map_stability(
    fit: LocalReturnMapResult,
    *,
    tolerance: float = 1e-6,
) -> ReturnMapStabilityResult:
    """Summarize empirical return-map contraction or expansion from eigenvalues."""

    if not np.isfinite(tolerance) or tolerance < 0:
        raise ValueError("tolerance must be non-negative and finite")
    if fit.jacobian.shape[0] != fit.jacobian.shape[1]:
        raise ValueError("return-map Jacobian must be square")
    eigenvalues = np.linalg.eigvals(fit.jacobian)
    spectral_radius = float(np.max(np.abs(eigenvalues)))
    if spectral_radius < 1.0 - tolerance:
        classification = "contracting"
    elif spectral_radius > 1.0 + tolerance:
        classification = "expanding"
    else:
        classification = "near-neutral"

    return ReturnMapStabilityResult(
        eigenvalues=eigenvalues,
        spectral_radius=spectral_radius,
        classification=classification,
        tolerance=float(tolerance),
        provenance={
            "operation": "return_map_stability",
            "fit_provenance": dict(fit.provenance),
            "criterion": "spectral radius of empirical local return-map Jacobian",
            "experimental": True,
            "interpretation_boundary": (
                "describes local empirical cycle-to-cycle contraction/expansion; "
                "does not establish deterministic orbital stability"
            ),
        },
    )
