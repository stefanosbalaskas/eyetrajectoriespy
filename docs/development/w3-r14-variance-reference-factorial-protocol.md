# W3 R14 — paired variance-source × critical-value decomposition

!!! danger "Research-only diagnostic; neither pointwise nor simultaneous calibration qualified"
    R13 compared participant CR1 **with t(47)** against a known conditional
    Gaussian source covariance **with normal critical values**. Changing both
    ingredients simultaneously cannot attribute the observed difference to
    covariance estimation alone. R14 changes one element at a time on exactly
    the same historical and fresh R13 datasets, without adding a new estimator.

## Source identity and independent units

The original [R13 evidence](w3-r13-exact-r11-conditional-variance-results.md)
uses 96 historical and 96 independently generated matched-R11-process blocks.
Within each block the two fixed bases, Legendre-5 and cubic spline-13, share
the underlying 48 independent participants and genuinely asynchronous,
complete 1–3 recorded trials/person. They are **paired model fits**, not new
independent replicates. R14 regenerates and checks the same 384 fitted
model/source cases against the unmodified R13 implementation. It adds **zero
new independent source datasets**.

The original R13 historical counts (80/96 Legendre-5 and 77/96 spline CR1/t)
are required *only* as a source-reproduction contract. The fresh cohort's
counts and all crossed comparisons are retained without coverage-success
filters. Previously reported R13 calibration limitations remain intact.

## Predeclared 2 × 2 numerical comparison

Each cell uses the *identical fitted midpoint slope* from R13, changing only
the scalar interval half-width. All intervals are nominal 90% **pointwise**
for the first-dimensional condition slope at time 0.5.

| Covariance source | Student t(47) | Standard normal |
|---|---|---|
| Estimated participant CR1 | Original R13 comparator | New controlled critical-only comparison |
| Simulation-known conditional Gaussian | New controlled critical-only comparison | Original R13 oracle comparator |

The source covariance is conditionally known only in simulation; it cannot
be treated as an estimator available to a researcher analysing human gaze.
R14 must reproduce both R13 diagonal methods exactly, including inclusion
decisions and interval widths. It also retains the source WLS/QR/participant
score numerical contracts, missingness-free inputs, and the real W3 public
workflow's rejection of unsupported irregular observations.

Within each **generating block**, compute indicator differences for: t versus
normal holding CR1 fixed; t versus normal holding oracle covariance fixed;
oracle versus CR1 holding t fixed; oracle versus CR1 holding normal fixed.
Report the interaction (difference of those two critical-value contrasts) as
a descriptive factorial comparison on the coverage-indicator scale, with
source-block bootstrap uncertainty. Do not interpret it as a causal
effect of the observation schedule or as calibrated sampling probabilities.

## Reproducibility and falsification

- Retain all 384 attempted original source cases, including failures.
- Independently preserve 384 crossed case records, with no disappearing
  failed fits and exactly four interval decisions per successful case.
- Preserve original R13 source ledger, R13 audit, crossed ledger, R14 audit,
  deterministic Matplotlib SVG, GitHub checkout SHA, and six SHA256 checksums.
- Run positive and negative numerical contracts under Python 3.11–3.13.
- No convergence, inference or release readiness claim may depend on
  matching an expected rate in newly generated data.
- If original source reconciliation fails, the scientific job fails **after**
  archiving the complete negative evidence.

```bash
python -m pip install -e ".[dev]"
python scripts/run_w3_r14_variance_reference_factorial.py --out build/w3-r14-original
```

### Scientific boundaries

This deliberately controlled numerical decomposition is not an independent
new Monte Carlo replication, a fitted hierarchical likelihood, a new
bootstrap method, a corrected MNAR mechanism, a p-value procedure,
or a simultaneous 90% confidence-band test. Leave scientific blockers
[#289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289)
and [#296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296)
open. Version remains unpublished `1.2.0rc2.dev0`;
`production_release_ready=false`. No change to stable 1.1.0, root API,
release candidate, tag or PyPI.
