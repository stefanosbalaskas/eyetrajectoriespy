# W3 R16 — matched predictor leverage × covariance factorial

!!! danger "Research-only, not calibrated pointwise or simultaneous inference"
    R15 changes both participant leverage and the covariance contribution from a participant random slope multiplied by x. R16 separates these mechanisms and retains all unfavorable scientific outcomes.

## Prespecified experiment

- New master seed `202610131616`; 96 independently generated source blocks; nested 24, 48 and 96 participants within each block. These are 96 independent Monte Carlo units, not 2,304 independent datasets.
- Two fixed bases: Legendre-5 and cubic-spline-13. The first coordinate's fixed midpoint slope at t=.5 is the prespecified contrast.
- Four 2×2 conditions: `ordinary_independent`, `ordinary_dependent`, `extreme_independent`, `extreme_dependent`.
- Ordinary x is Uniform(-.95,.95); extreme x substitutes x=3.0 and x=-2.5 at participants 0 and 1. No other x changes.
- Independently of leverage, the participant random functional slope is multiplied by 1 (predictor-independent covariance) or by x (predictor-dependent covariance). The conditional mean still uses x in every case.
- Within a generating block, preserve participant innovations, trial counts, native asynchronous timestamps, trial and sensor innovations in all four cells. Every native observation remains complete; no interpolation.
- Total planned cases: 96 × 3 × 4 × 2 = **2,304**, fully failure-inclusive; method comparisons are paired within block.

## Source uncertainty

Retain unchanged original participant-weighted WLS, cluster CR1/t, CR1/normal, actual delete-whole-participant centered jackknife/t (**CV3J**), simulation-known Gaussian conditional covariance/t and oracle/normal. Recompute the oracle's participant-slope covariance coefficient as x or 1 to match the generating condition. The oracle is not available to empirical users.

No CR2 is asserted at this stage. A subsequent independently validated CR2 bias-reduced linearization implementation must check the target matrix, WLS cluster-block adjustment, leverage numerics and degrees-of-freedom method before entering a scientific comparison. CR2 and CV3J must not be labeled interchangeable.

## Interpretation

Compare paired CR1/oracle standard-error ratios, observed known-truth inclusion, jackknife/oracle ratios, and the leverage × covariance interaction with participant block as the independent Monte Carlo unit. Report coefficient-specific contrast leverage and influence in the subsequent measurement tranche; R15's maximum cluster block eigenvalue alone cannot identify focal-contrast influence. Neither nominal-coverage attainment nor method ranking is a software CI gate.

The implementation also records participant information-block leverage, independent weighted-QR agreement, independent grouped-score agreement, participant count, complete timestamps, failures, 95% Wilson intervals, paired-block Monte Carlo intervals, source original plot, commit provenance and SHA256 evidence.

## Governance

This first R16 tranche isolates source covariance dependence; CR2, focal contrast leverage and final inference are separate required validation steps. Keep [#289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289), [#296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296) open. No public estimator, public API change, protected-main merge, release tag or PyPI publication. Development stays `1.2.0rc2.dev0`, with `production_release_ready=false`.

```bash
python -m pytest -q tests/test_w3_r16_leverage_covariance_factorial.py
python scripts/run_w3_r16_leverage_covariance_factorial.py --out build/w3-r16-original
```
