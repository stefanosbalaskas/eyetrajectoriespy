# W3 R5: use native observed time support without inventing missing gaze

!!! danger "Prespecified research comparison—not an irregular-data estimator for production"
    The existing W3 function-on-scalar workflow requires complete finite
    common-grid trajectories. This standalone research study explores
    source-supported least squares using **only genuinely recorded gaze
    samples at exactly observed timestamps**; it does not interpolate
    missing coordinates, imply validity of conventional confidence bands,
    or add a new public regression API.

## Research question and independence accounting

The earlier [W3 R4 source study](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/295)
used fully observed generating trajectories, then compared explicit
whole-unit deletion under MCAR and latent-response-dependent recording
gaps. The current R5 study asks a different question: **can an analyst
retain valid observed data outside missing intervals, rather than
discarding an entire incomplete curve?** It does not claim that doing
so identifies unobserved outcomes.

The study uses **128 independently seeded original generating blocks**,
each with **96 independent curves**, 31 common source times and two
response dimensions. The three missingness mechanisms share **the exact
same original complete trajectory values, condition assignments and
underlying dropout uniforms within block**:

| Mechanism | Dropout probability | Identifiability boundary |
|---|---|---|
| MCAR | 0.35 for every curve | Known and constant only because it is simulated |
| MAR depending on observed condition | logistic(−0.62 + 1.30 × x) | Known condition and generating probabilities; real probabilities are not supplied by W3 |
| Outcome-dependent MNAR | logistic(−0.62 + 1.30 × x + 2.70 × hidden midpoint residual / 0.105) | The generating dropout probability depends on an unobserved outcome; unavailable to a real analyst |

A selected curve loses one contiguous **8-time-point interval** in the
middle of the original series. Observed curve-specific time stamps
and coordinates are kept in a native `IrregularTrajectorySet`.
All observation times are exact sub-support of the generating grid;
**this pilot does not address genuinely asynchronous or jittered
sampling times**.

There are **384 planned mechanism-fit cases but only 128 independent
generating blocks**. All mechanism contrasts are paired within
generating block. There are no repeated participant trials in R5;
extension to participant-level multitrial models needs a new,
independently validated design.

## Four deliberately distinct numerical references

Each research case records these known-truth slope-function RMSEs:

1. **Full source OLS:** numerical reference fitted to all genuinely
   generated source values. These complete values are hidden from
   the observed-data analyses in real settings.
2. **Explicit complete-curve deletion:** analyst deliberately removes
   every curve with any recording gap, then estimates the function
   at all original grid points. The unchanged supported dense W3
   fit is independently checked against NumPy OLS.
3. **Native observed-time OLS:** at each specified target time
   location, use **only independent curves that actually possess
   an observed coordinate at that exact time**. No attempt is
   made to replace missing measurements. If support/rank is
   inadequate, that coefficient remains missing and the
   case is not silently completed.
4. **Known-probability oracle IPW:** for MCAR and x-dependent MAR
   only, multiply genuinely observed values **at the missing
   interval** by inverse *known generating* probability of being
   observed, then solve a weighted regression. At fully observed
   times, weights are 1. Under latent-MNAR this comparator is
   deliberately **unavailable**, rather than passing an
   unobservable true dropout mechanism to a supposedly
   feasible empirical estimator.

The available-time OLS has a clear mathematical limitation:
**outside the recording gap**, all 96 independent source curves
are present, so it must reproduce the complete-source OLS exactly.
**Inside the gap**, the observed source curves are precisely those
without a recording gap, so available-time OLS and the explicit
complete-curve OLS are *identical* there. The method therefore
recovers statistical efficiency outside the gap but **cannot
repair MNAR selection within it**.

No data-dependent smoothing, time-grid interpolation, trial
exclusion, hidden preprocessing, or model replacement is applied.
The original native coordinates and time vectors must remain
unchanged. The complete-grid W3 workflow must still reject native
irregular data.

## Source evidence and falsification

Per generating block and mechanism preserve:

- Native time-support counts at **all 31** original target locations
  and exact observed source-value conservation.
- Missing-curve fraction, independent curve count and minimum
  time-specific analysis support.
- Complete-source, explicit deletion, available-time, and
  available-oracle-IPW slope RMSE against known generating truth.
- Paired signed estimate differences at the masked midpoint
  and independent NumPy/package OLS agreement.
- Monte Carlo summaries using **128 independent blocks** within
  each mechanism, with 2000 block-level bootstrap replicates.
- Complete 384-case JSON ledger, original source SVG,
  SHA256 checksums, original checkout SHA and all failures
  and missing source cases.

The study will not select a winning statistical architecture or
make coverage, interval width or desired bias into a CI pass gate.
A lower RMSE in this pilot is not a guarantee about gaze-device
sampling errors, biological time warping, eye blinks, location-
dependent dropout or unobserved source conditions.

### Reproduction

```bash
python -m pip install -e ".[dev]"
python scripts/run_w3_r5_native_observed_support.py \
  --out build/w3-native-observed-support-r5
```

This is **exploratory research only**. Retain [observation-loss
scientific issue #296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296)
and the separate [90% W3 simultaneous-inference
blocker #289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289).
It does not qualify missing-data corrections, native asynchronous
functional regression, HC1 coverage, or inferential Type-I error.

Stable published **1.1.0** remains unchanged; unreleased development
`1.2.0rc2.dev0` remains `production_release_ready=false`.
No RC tag, PyPI publication or stable API change is authorized.
