# W3 independent frequentist uncertainty pilot: protocol

!!! danger "Research evidence, not inferential qualification"
    W3 pointwise HC1 standard errors and wild-bootstrap simultaneous bands
    have not yet been shown to attain nominal 90% coverage across plausible
    eye-tracking designs. This study may document undercoverage or overcoverage.
    Success of fitting or CI does not imply statistical calibration, and this
    work must not automatically promote an inferential API or a release.

## Scientific objective and prior reference

The completed [W3 known-truth numerical study](w3-functional-regression-known-truth-results.md)
established regression-coefficient agreement with an independent least-squares
oracle and exploratory finite-sample recovery in 24 generating blocks.
It **did not** evaluate uncertainty coverage. The next investigation treats
the nominal **90%** interval and simultaneous band as testable hypotheses.

We prespecify 64 fresh independent generating datasets (new seed namespace
`2026101207`; not reusing the 24 earlier blocks). Every block contains
two separately simulated scenarios under the same fixed coefficient truth:

- **Curve-level inference:** 72 independent curves, two dimensions,
  31 time locations, smooth generating intercept and condition slope,
  independent Gaussian errors.
- **Participant-level inference:** 36 independent participants, three
  trials each (108 curves), participant-constant condition, smooth random
  participant intercept and within-trial Gaussian noise. The analysis
  averages trials within participant *before* fitting. The 108 curves
  must never become 108 independent inference units.

A block identifier groups the two scenarios for bookkeeping; the two
scenarios are separately generated. Each scenario receives 64 new datasets.
Their 128 fitted cases are not 128 interchangeable draws from one homogeneous
superpopulation: report each design separately and preserve block-level
pairing if comparing designs.

## Estimands, methods, exact source contracts

Every dataset fits observed-grid function-on-scalar regression via the
typed W3 workflow with one intercept and one condition predictor.
An independent NumPy least-squares oracle computes **all** coefficient
functions. A separate NumPy/sandwich calculation computes the finite-n
HC1 estimator from the unit-level design matrix and residual functions,
using the explicit correction `n/(n - p)`. Both estimates and HC1 SEs
must agree within `2e-10` with the W3 scientific primitive.

The inferential pilot retains three distinct truth-inclusion outcomes:

1. **Pointwise slope normal interval:** nominal 90%, normal critical
   value, HC1 pointwise SEs; report the fraction of the 62 slope
   time-by-dimension cells containing the known truth and the stricter
   indicator that **all** such cells contain truth.
2. **Slope simultaneous band:** nominal 90%, fixed-design wild bootstrap
   with **199 Rademacher draws** per dataset and one random multiplier per
   *independent inference unit*, maximum studentized deviation across
   31 time points × two dimensions for the slope coefficient.
3. **Full coefficient family band:** maximum studentized deviation across
   intercept and slope, all 31 time points and both dimensions.

The critical values are recomputed independently from retained bootstrap
draws and independently calculated standard errors and compared with
the library band output. No automatic optimizer selection or model change.

A complete scientific run saves the original case ledger, attempted and
completed denominators, numerical-oracle discrepancies, per-design coverage,
Wilson 95% Monte Carlo intervals, interval widths, all fit/evidence failures,
source-commit identity, SHA256 checksums and an original SVG figure.

## Interpretation restrictions

**Zero scientific inference gates are automatically promoted by this pilot.**
The 95% Wilson Monte Carlo intervals for a 90% coverage probability remain
relatively wide with only 64 independent datasets per design, and the
199-draw bootstrap produces quantile Monte Carlo discreteness. Report the
observed inclusion rate as an estimate with uncertainty, not a pass/fail
certificate. Even if empirical coverage is close to 90%, the study is
restricted to two idealized generating mechanisms, one effect truth,
fixed sampling support and modest sample sizes. Nonrandom observation
processes, realistic sensor artifacts, autocorrelated errors beyond the
specified design, non-Gaussian tails, unequal participant trial counts,
and misspecified dependence are **not validated**.

Coverage failures must remain in the evidence. The workflow **must pass**
if its original cases, checksums and oracle comparisons are complete,
regardless of observed scientific undercoverage. Do not discard poor
results or widen thresholds after inspecting them.

## Reproducibility

```bash
python -m pip install -e ".[dev]"
python scripts/run_w3_fixed_truth_interval_pilot.py \
  --blocks 64 --out build/w3-interval-pilot
```

Stable eyetrajectoriespy **1.1.0** remains published. The working source
version remains **`1.2.0rc2.dev0`** and publication readiness remains
**false**. Bayesian B6/B7 and F5 dependent-data scientific blockers are
separate and remain open.
