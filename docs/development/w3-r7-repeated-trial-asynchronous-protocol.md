# W3 R7: native asynchronous repeated trials, participant-level weighting

!!! danger "Prespecified research only—no hierarchical-inference qualification"
    The supported W3 observed-grid function-on-scalar workflow
    rejects irregular sources. This pilot preserves actual recorded
    native timestamps, repeated trials and independent participant
    identities while fitting a fixed time-basis **research**
    regression. It does not estimate mixed-effects covariance,
    qualified standard errors, MNAR corrections or confidence bands.

## New scientific question

The earlier [R6 study](w3-r6-native-asynchronous-basis-results.md)
used independent curves with genuinely jittered source times.
However, many experiments collect **multiple trials from each
participant**, and the number of recorded trials or gaze samples
can differ between participants. Treating all trials or gaze
points as independent people would exaggerate sampling information
and can inadvertently reweight the scientific estimand.

The R7 study generates **64 independent source blocks**, each
comprising **48 genuinely independent participants**, each with
up to three source trials. Each participant has a fixed experimental
condition and smooth shared *random intercept and random slope*
components, together with trial-specific noise and independently
jittered trial timestamps. The source population condition slope
is known on the common **evaluation grid** of 31 time locations
and two response dimensions.

Four matched generating scenarios are formed within *each* block
rather than generating four independent samples:

| Trial support | Recording-loss scenario | Important constraint |
|---|---|---|
| Balanced 3 trials/participant | MCAR recording gaps | Three source trials for every participant |
| Balanced 3 trials/participant | Latent-response-dependent gaps | Same participant/trial sources and dropout uniforms as MCAR |
| Unbalanced 1–3 trials/participant | MCAR gaps | Pre-generated trial-allocation uniforms determine supported source trials |
| Unbalanced 1–3 trials/participant | Latent-response-dependent gaps | Reuses same original source as the paired MCAR case |

The recording gap is a contiguous eight-source-observation
interval; source records for retained trials are never
interpolated, zero-filled or regridded. In the MNAR scenario
loss is generated using the otherwise hidden midpoint residual
and the observed condition; **the real analyst does not know
that conditional loss mechanism**.

The study therefore has **256 source evaluations but only
64 independently seeded blocks of 48 participants**. It is not
a participant-random-effects estimator and does not consider the
repeated gaze points or repeated trials independent Monte Carlo
replications.

## Explicit fixed-model fitting contrasts

All analyses use the **same fixed degree-five Legendre time basis**
specified before source simulation results are read, and fit
the model using only each trial's genuinely recorded timestamps.
Estimated functions shown on the common reference grid are
**model-based predictions**, not observed or recovered eye coordinates.

The source contrasts use three transparent least-squares objectives:

- **Per-sample weighting:** every genuinely observed trial/time
  record gets equal numerical weight; longer or more frequently
  observed participants contribute more in total.
- **Per-trial weighting:** each recorded trial gets equal total
  weight, by assigning a weight of `1/n_ij` to its observations.
  Participants with more trials therefore contribute more.
- **Per-participant weighting:** each participant gets equal
  total numerical weight, assigning each observation a
  weight of `1/(k_i n_ij)`, where k_i is that participant's
  number of source trials and n_ij the actual observations in
  trial j. This does **not** by itself implement statistical
  cluster-robust inference.

The known-source numerical benchmark uses the **same
participant-balanced objective** on the complete pre-gap
native recordings, with exactly the same prespecified
trial-support scenario. That isolates the recording-loss
change within a trial allocation instead of silently mixing
different generating samples.

Fit coefficients must independently agree with a reduced-QR
triangular-solve numerical oracle to tolerance 2e−8.
Every source participant is retained in each scenario,
and each original native time/coordinate record is conserved.
The unchanged supported W3 common-grid estimator must refuse
the native irregular input.

With exactly three trials per participant, trial-balanced and
participant-balanced objectives differ only by one common
scalar and must produce **identical regression coefficients**.
Under unequal trial counts those objectives can differ.
This invariance is a scientific contract, not an empirical
performance optimization.

## Original evidence and limits

For every source block and paired scenario, retain:
- The exact original trial count and observed native point count
  and number of gapped trials/participants.
- Known-true slope-function RMSE and signed midpoint change for
  each weighting objective.
- Original complete-source participant-balanced reference slope
  RMSE, plus numerical-oracle discrepancies.
- Exactly 64 independent generating-block resampling units for
  **2000-resample Monte Carlo intervals** per scenario; never
  treat trials or time samples as independent sources.
- Failure-inclusive original **256-case JSON ledger**, source
  figure, workflow SHA and verified original SHA256 evidence
  hashes, including all fitting/source failures.

No preferred weighting, desired significance or anticipated
bias direction is made a CI pass criterion. This study does
not qualify a novel hierarchical method or population-level
inference. It does not assess functional mixed-model random
slopes, unequal participant recruitment, event-locked
resampling, or variance estimators under repeated trials.

```bash
python -m pip install -e ".[dev]"
python scripts/run_w3_r7_async_repeated_trials.py --out build/w3-r7-original
```

Research remains separate from [missing-observation
issue #296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296)
and [W3 simultaneous-band inference issue #289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289).
Stable 1.1.0 is published; development is **`1.2.0rc2.dev0`**
and `production_release_ready=false`. No new public API, tag,
RC or PyPI publication is authorized.
