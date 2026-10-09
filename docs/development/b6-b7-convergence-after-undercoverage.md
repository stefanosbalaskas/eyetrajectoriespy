# B6/B7: follow-up to severe 90% credible-interval undercoverage

**Unpublished scientific diagnosis; no automatic inference qualification.**

The source [first empirical wave](first-empirical-calibration-findings.md)
fitted 2,400 B6 and 1,600 B7 actual matched/misspecified models. At
400 independent datasets per scenario, B6 **matched-prior** posterior
population-mean 90% coverage was 70.75% (rank 1), 62.00% (rank 2)
and 62.00% (unequal sparse rank 2). B7's x/y population mean and
cross-covariance coverage was also far below 90%. Source-run
[GitHub evidence #37965949039](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/37965949039).

This requires a fail-closed scientific response, rather than simply
adding methods or authorizing publication.

## Registered next experiment: same data, two chain schedules

`scripts/run_bayesian_convergence_probe.py` calls the **existing prior
and likelihood generator** and **existing learned B6/B7 Gibbs** code.
For each independently seeded prior-generated dataset, it performs:

| Property | Original | New diagnostic |
|---|---:|---:|
| Gibbs chains | 2 | 2 |
| Warmup sweeps | 160 | 1,200 |
| Retained draws per chain | 70 | 600 |
| Thinning | 1 | 1 |
| Rank | 1 or 2 | Same |
| Observation timestamps and participants | Identical | Identical |
| Draw-prior/hyperparameters | Fixed | Identical |

Eight matched prior-generated datasets per combination:
B6 rank-1/rank-2; B7 rank-1 paired/asynchronous and rank-2
paired/asynchronous. Total **96 actual Gibbs model refits**
(48 independently generated datasets × two chain schedules).
This is a **mechanism-diagnostic pilot**, not a replacement for the
400-refit coverage study. All paired observation-data seeds and fit
exceptions are persisted in `cases.csv`, with SHA256 evidence.

## Identifiability and diagnostics

Compare rotation-invariant integrated population means/variances and
joint planar x/y cross-covariance with `ArviZ` R-hat, bulk ESS, and
posterior 90% interval widths on the two schedules. Do not diagnose
mixing from individual sign/rotation-unidentified loading columns.
The B6 helper also evaluates coverage of pointwise mean and
covariance at the prespecified midpoint; the B7 helper evaluates
midpoint x/y means and cross covariance.

The recorded `rhat_max` is a **maximum over the summary variables**
and the recorded bulk ESS is a **minimum**. Missing or nonfinite
diagnostics must not be silently accepted or imputed. Good diagnostics
on these integrated quantities still do not certify every high-
dimensional posterior functional.

Potential findings and decisions:
- If longer chains markedly improve coverage, first improve mixing,
  diagnostics, independent initialization and convergence thresholds.
  Do not simply prescribe a new arbitrary sweep count.
- If R-hat/ESS are poor even for long chains, treat the Gibbs chain as
  inferentially untrustworthy, investigate parameterization and joint
  mixing, and repeat under stronger alternative samplers.
- If R-hat/ESS improve but matched-prior coverage remains poor, audit
  the precision/conditional update algebra, prior/likelihood truth
  match, posterior quantile assembly and parameter functional
  interpretation. An independent reference posterior (e.g. independent
  MCMC implementation in a separate backend) is required to identify
  coding bias versus nonidentification.
- Irrespective of these pilot results, run separate sufficiently
  long-chain SBC ranks and empirical coverage with predeclared
  Monte Carlo precision and independent comparator recovery.

**No 1.2 production release or claim of scientifically calibrated
Bayesian FPCA/MFPCA is authorized.** The source `main` remains
protected, and these procedures stay opt-in research APIs.
