# FPCA stability and validation

FPCA always returns components. That does **not** mean every component is stable enough to receive a substantive label.

## Why component stability matters

Functional principal components are sample-dependent eigenfunctions. A component that changes shape markedly under reasonable resampling may be a fragile description of this sample rather than a reproducible viewing mode.

## Bootstrap matched components

    stability = bootstrap_fpca_stability(
        gaze,
        n_bootstrap=200,
        n_components=3,
        scaling="dimension_sd",
        resample_unit="participant",
        participant_column="participant_id",
        random_state=2026,
    )

Each bootstrap fit is matched back to the full-sample FPCs by maximum **absolute functional similarity**. Sign is retained separately because FPC orientation is arbitrary.

## Resample the correct unit

For independent curves, curve-level bootstrap may be appropriate.

For repeated trials nested within people, prefer participant-level bootstrap when the target is the stability of population-level viewing modes. It resamples participants as clusters rather than pretending trials are independent.

## Read the stability summary

    summarise_fpca_stability(stability)

Useful descriptors include:

- median absolute matched similarity;
- an empirical interval of bootstrap similarities;
- the fraction of replicates exceeding a pre-specified similarity threshold;
- matched explained-variance distributions.

!!! important
    The fraction of bootstrap replicates above a threshold is a **descriptive robustness measure**, not a posterior probability and not a p-value.

## Reconstruction diagnostics

Variance explained is not the only way to assess dimensional adequacy.

    curve = fpca_reconstruction_curve(fit, gaze)

The reconstruction curve shows how integrated trajectory error changes as components are added. This helps identify situations where a high variance threshold still leaves scientifically important path details poorly reconstructed.

## Recommended workflow

1. Fit the pre-specified FPCA.
2. Inspect component trajectories.
3. Inspect reconstruction error.
4. Run participant-aware bootstrap stability when the design is repeated measures.
5. Label components only after their geometric interpretation and stability are understood.
6. Report unstable modes as unstable rather than silently dropping or renaming them.


## Select dimension with held-out reconstruction

In-sample reconstruction always benefits from additional fitted directions. When
component retention itself is under study, use
`cross_validate_fpca_reconstruction()` so the basis is estimated only from each
training fold.

For repeated trials, use grouped folds at the participant level.

See [Selecting the number of FPCs](component-selection.md).

## Inspect FPC shape uncertainty

Matched bootstrap similarity answers whether a component direction recurs.
`bootstrap_fpca_component_envelopes()` adds a complementary pointwise view of
where the matched, sign-aligned FPC shape varies across resamples.

These are descriptive envelopes rather than confidence bands.

See [FPC shape uncertainty](component-uncertainty.md).
