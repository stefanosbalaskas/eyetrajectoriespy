"""Research-only information availability audit for longitudinal preprocessing."""
from __future__ import annotations

import numpy as np
import pandas as pd


MODES = {"training_population", "prior_baseline", "online", "retrospective"}


def certify_preprocessing_availability(
    fitted_observations: pd.DataFrame,
    predictions: pd.DataFrame,
    *,
    training_participants,
    mode: str,
) -> pd.DataFrame:
    """Identify source-participant and future-observation leakage.

    fitted_observations: transform_id, source_participant, source_time_s.
    predictions: transform_id, target_participant, prediction_time_s.
    All fitted source rows are assumed USED by the transformation. This
    contract does not inspect opaque estimator internals or identify people.
    The same transformation may have different validity at different times.
    """
    fit_cols = ["transform_id", "source_participant", "source_time_s"]
    pred_cols = ["transform_id", "target_participant", "prediction_time_s"]
    if mode not in MODES:
        raise ValueError("unknown normalization mode")
    if not set(fit_cols).issubset(fitted_observations):
        raise ValueError("missing fitted-observation provenance")
    if not set(pred_cols).issubset(predictions):
        raise ValueError("missing prediction provenance")
    if fitted_observations[fit_cols].isna().any().any() or predictions[pred_cols].isna().any().any():
        raise ValueError("fit and prediction provenance must be complete")
    for col, data in [("source_time_s", fitted_observations),
                      ("prediction_time_s", predictions)]:
        if not np.isfinite(pd.to_numeric(data[col], errors="coerce").to_numpy()).all():
            raise ValueError("time provenance must be finite numeric")
    train = set(training_participants)
    if not train or any(pd.isna(list(train))):
        raise ValueError("training_participants must be nonempty and complete")
    all_fit = fitted_observations.copy()
    all_fit["source_time_s"] = all_fit.source_time_s.astype(float)
    all_pred = predictions.copy()
    all_pred["prediction_time_s"] = all_pred.prediction_time_s.astype(float)
    rows = []
    for transform_id, targets in all_pred.groupby("transform_id", sort=False):
        fitting = all_fit[all_fit.transform_id == transform_id]
        if fitting.empty:
            raise ValueError("transform without any fit observations")
        for participant, group in targets.groupby("target_participant", sort=False):
            first_prediction = float(group.prediction_time_s.min())
            fitted_others = fitting[~fitting.source_participant.isin(
                list(train) + [participant])]
            same = fitting[fitting.source_participant == participant]
            future = 0
            for time in group.prediction_time_s:
                future += int((same.source_time_s >= float(time)).sum())
            nontraining = int(len(fitted_others))
            if mode == "training_population":
                valid = bool(fitting.source_participant.isin(train).all())
            elif mode == "prior_baseline":
                valid = bool((fitting.source_participant == participant).all()
                             and (fitting.source_time_s < first_prediction).all()
                             and participant not in train)
            elif mode == "online":
                valid = bool(nontraining == 0 and future == 0 and participant not in train)
            else:
                valid = False
            rows.append({
                "transform_id": transform_id,
                "target_participant": participant,
                "mode": mode,
                "prediction_rows": len(group),
                "fit_rows": len(fitting),
                "future_target_fit_uses": future,
                "unapproved_other_participant_fit_rows": nontraining,
                "deployment_valid": valid,
                "claim_boundary": (
                    "Declared input provenance only; opaque transformations "
                    "and downstream feature leakage not inspected."),
            })
    if not rows:
        raise ValueError("no prediction rows")
    return pd.DataFrame(rows)
