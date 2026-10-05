# Sparse partial-prediction validation

This page records the first known-truth qualification for the 1.1 sparse partial-trajectory prediction tranche. It separates **model-based conditional Gaussian prediction** from **participant-aware split-conformal finite-grid prediction**.

The evidence does not claim continuous-domain conformal coverage, latent-function conformal coverage, or propagation of population-estimation uncertainty.

## Qualified implementation

The development surface is contained in dedicated modules:

- `eyetrajectoriespy.sparse_partial_prediction`
- `eyetrajectoriespy.sparse_partial_conformal`

The frozen 1.0 root namespace and `fit_sparse_fpca()` defaults are unchanged.

## Oracle-population conditional prediction

The first qualification component supplies the predictor with known population mean, covariance surface and measurement-error variance. This isolates the conditional-Gaussian calculation from smoothing and population-estimation error.

The simulation uses a three-mode Gaussian functional process, fixed future target grid `(0.75, 0.85, 0.95)`, and native history observations before either cutoff `0.30` or `0.60`. Four deterministic scenarios cross:

- history length: 6 versus 12 observations; and
- measurement-noise SD: 0.05 versus 0.20.

Each scenario contains 400 independent target curves.

### Results

| Noise SD | Cutoff | History n | Latent RMSE | Mean latent conditional variance | Latent standardized-error SD | Latent 95% coverage | Observed standardized-error SD | Observed 95% coverage |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.05 | 0.30 | 6 | 0.2828 | 0.07568 | 1.0329 | 0.9358 | 1.0372 | 0.9417 |
| 0.05 | 0.60 | 12 | 0.03590 | 0.001205 | 1.0344 | 0.9408 | 1.0052 | 0.9458 |
| 0.20 | 0.30 | 6 | 0.5837 | 0.3543 | 0.9860 | 0.9500 | 0.9911 | 0.9467 |
| 0.20 | 0.60 | 12 | 0.1350 | 0.01763 | 1.0149 | 0.9400 | 1.0168 | 0.9425 |

The standardized-error SDs remain close to one and the nominal pointwise 95% intervals show coverage near 0.95 under oracle population truth.

Increasing observed history substantially reduces conditional uncertainty in both noise regimes:

- low noise: mean latent conditional variance `0.07568 -> 0.001205`;
- higher noise: `0.3543 -> 0.01763`.

These are qualification results for the declared simulator, not a universal performance guarantee.

## Participant-aware split conformal qualification

The conformal experiment deliberately includes repeated trials.

- calibration: 60 participants × 2 trials = 120 curves;
- targets: 180 participants × 2 trials = 360 curves;
- within-participant latent-score correlation is introduced through shared participant effects;
- future target grid has three points;
- `alpha = 0.10`;
- calibration unit is `participant_id`;
- each participant score is the maximum trial-level nonconformity;
- each trial-level nonconformity is the maximum standardized absolute future residual across all three target-grid points.

The conformal critical value was **2.32564**.

### Coverage result

Participant-level simultaneous success requires **both target trials and every future target-grid point** to lie within their bands.

- participant-level simultaneous coverage: **0.90556**;
- curve-level simultaneous coverage: **0.95278**.

The participant-level result is the claim-matched metric because participant is the declared exchangeability/calibration unit in this repeated-trial design.

## Guarded failure evidence

Two failure cases are retained in the qualification artifact:

1. replacing one required calibration target timestamp `0.85` with `0.86` causes `calibration_future_grid_observation_missing` rather than interpolation;
2. deliberate proper-training/calibration curve-ID overlap fails explicitly with `ValueError`.

Deterministic replay of the conformal scenario passed.

## Scope boundaries

The qualification supports the following statements:

- the base predictor uses the full fitted covariance and native sparse history to produce conditional future means and latent covariance;
- model-based conditional variances are calibrated under the known Gaussian population used in the oracle simulation;
- more history reduces conditional uncertainty in the qualified scenarios;
- participant-aware split conformal calibration can produce finite-grid simultaneous prediction bands for future observed measurements under the declared exchangeability design;
- repeated trials are not treated as independent calibration units when a group column is supplied;
- calibration future responses are not interpolated.

It does **not** support claims of:

- continuous-domain conformal coverage between target points;
- conformal coverage for the latent noise-free function;
- automatic validity under informative missingness or covariate shift;
- population-estimation uncertainty propagation;
- universal optimality of the chosen cutoff, grid or simulator;
- planar/asynchronous prediction; or
- multilevel functional prediction.

## Reproducibility record

The first completed qualification run on the feature branch was:

- workflow: `sparse-partial-prediction-validation`;
- run: `37356266298`;
- artifact: `11365360297`;
- artifact digest: `sha256:0418eb4a676e883f1cfb6fb25ed20aed64df9fc52d31d76b2a4976ea7db254fc`.

The final merge decision requires a fresh exact-head run after documentation is complete; the record above is retained as the first completed scientific qualification rather than being presented as the eventual final-head release evidence.
