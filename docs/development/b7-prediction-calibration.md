# B7/B9: predictive uncertainty for an independent future participant

**Experimental research API, not a stable release or calibrated prediction method.**
This research continuation extends the [learned B7 Gaussian planar factor](b7-learned-planar-model.md)
rather than the fixed-population B7 conditional-score benchmark.

Use `eyetrajectoriespy.bayesian.predict_bayesian_planar_new_participant()`
with the returned `BayesianPlanarFactorFit`, exact evaluation-grid
indices and two declared coordinate-specific noise scales:

```python
from eyetrajectoriespy.bayesian import (
    fit_bayesian_planar_factor,
    predict_bayesian_planar_new_participant,
)

posterior = fit_bayesian_planar_factor(
    gaze,  # unique participant_id; x/y NaN means intentionally unobserved
    evaluation_grid=grid,
    observation_noise_sd=(0.04, 0.06),
    n_components=2,
    n_basis=5,
    n_chains=2,
    n_draws=60,
    warmup=90,
)
future = predict_bayesian_planar_new_participant(
    posterior,
    evaluation_indices_x=[3, 8, 12, 18],
    evaluation_indices_y=[5, 9, 14, 20],
    observation_noise_sd=(0.04, 0.06),
    random_state=100,
)
pointwise = future.summary_frame()
```

The call does **not** use the fitted training participant scores. For
each stored Gibbs iteration it draws a *new* shared participant factor
`z_new ~ N(0,I_K)` and combines it with the same iteration's learned
population mean and both channel loading functions. It then adds
independent Gaussian observation noise using supplied coordinate scales.
Using a common `z_new` propagates temporal and x/y dependence rather
than drawing each coordinate independently.

Predictions intentionally require exact integer positions in the fitted
evaluation grid. Coordinates can have different observed index subsets.
Nothing silently interpolates x/y onto a common observed clock, and
there is no hidden time-unit conversion. This grid restriction is an
explicit implementation boundary, not a universal limitation of Gaussian
functional models.

The returned `latent_draws` and `observed_draws` arrays have shape
`(chain, population_posterior_draw, requested_channel_time_rows)`.
`row_frame` records the source coordinate, time and index for each row.
`summary_frame()` gives pointwise 5th/95th predictive quantiles; it does
**not** construct simultaneous 90% prediction regions or certify 90%
frequentist coverage.

## Known-truth predictive check

The B7 refit pilot now additionally draws one completely new participant
per simulation from the same prior/likelihood generating population,
including a new latent factor and coordinate-specific observation noise.
That participant is never part of the population posterior fit. For each
participant it tests eight withheld coordinate-time outcomes (four x,
four y), reports the *mean within-participant pointwise inclusion
fraction*, and records whether all eight marginal bands happened to
contain their outcomes.

The eight outcomes are strongly dependent. They must not be used as
eight independent binomial simulation replications. An all-eight event
is **not** itself a jointly calibrated functional 90% prediction band.
Such a region and calibration remains new methodological work.

Engineering CI evaluates two prior-generated datasets per paired/async
and rank-1/rank-2 combination. It is a smoke test, not a sample adequate
to claim nominal predictive coverage.

## Unresolved

Population noise, prior and rank learning; rich observation-process and
missingness mechanisms; full posterior-convergence qualification;
near-tied eigenspace sensitivity; conditional prediction after observing
part of a new participant's trajectory; simultaneous x/y functional
predictive bands; independent external benchmarks; and honest
real-participant holdout studies. Existing scientific and release gates
remain false. Development remains stacked and unpublished.
