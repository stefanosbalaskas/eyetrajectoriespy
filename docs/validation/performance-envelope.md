# Performance envelope

Version 0.56 introduced a reproducible **single-package performance envelope**. Version 0.57 requalified it after release hardening, 0.9.0rc1 qualified the prerelease, 0.9.0 qualified the first stable pre-1.0 release, 0.9.1.dev0 qualified the maintenance line, 0.10.0.dev0 requalified the integrated native sparse-FPCA/PACE development line, and 0.10.0rc1 independently qualified the first release candidate. `0.10.0rc2` received its own fresh qualified envelope and that snapshot is archived immutably. Final `0.10.0` requires another fresh envelope under the exact final version; rc2 evidence is not relabeled. It is
not a comparative benchmark and does not claim that eyetrajectoriespy is faster
than another package.

The qualification harness is
`scripts/run_performance_qualification.py` and the CI workflow is
`performance-qualification`.

## What is recorded

For every run the harness records:

- participant count;
- trials per participant;
- functional grid length (n_t);
- basis/component dimension (q) where applicable;
- bootstrap/specification count;
- three or more independent process timings;
- median, first quartile, third quartile, minimum and maximum wall-clock time;
- process peak resident memory on supported Unix runners;
- Python/package/dependency versions;
- operating system, machine/CPU information and logical CPU count;
- Git commit and GitHub Actions run identifiers when available;
- numerical thread-limit environment.

Each repetition runs in a fresh Python process so process peak memory is
attributable to one complete workflow rather than inherited from an earlier
benchmark case.

## Qualified workflow set

The qualification harness measures these expensive routes separately:

1. FPCA + participant bootstrap stability;
2. functional mixed-effects full-refit participant bootstrap;
3. nested participant/trial covariance fitting;
4. exposure-adjusted generalized GEE + participant bootstrap;
5. recurrence matrix + RQA;
6. RQA nonlinear parameter-sensitivity grid.

The committed workload profile is intentionally CI-sized and is a **reference
envelope**, not a universal workstation capacity claim.

The current 0.10.0rc2 release-candidate reference snapshot was measured from
source commit `3b73acce83e34da65d5255dd01af23a08055038e` in GitHub Actions run
`36511144199` on Linux/Python 3.12.14, an AMD EPYC 9V74 runner with four
logical CPUs visible to the job. NumPy/SciPy/statsmodels numerical thread
limits were fixed to one thread. Dependency versions and the synthetic workflow
scales are retained in `PERFORMANCE_ENVELOPE.json`.

| Workflow | Qualified scale | Median runtime (IQR), s | Peak RSS median / max, MiB |
|---|---|---:|---:|
| FPCA + participant bootstrap | 10 participants × 3 trials × 41 times; q=3; 20 bootstraps | 1.964 (1.962–2.468) | 223.58 / 227.92 |
| Full-refit mixed-effects bootstrap | 12 × 3 × 6; q=2; 20 bootstraps | 2.801 (2.775–2.803) | 227.14 / 227.26 |
| Nested participant/trial mixed fit | 8 × 3 × 5; q=2 | 2.482 (2.473–2.488) | 226.72 / 226.91 |
| Exposure-adjusted GEE + bootstrap | 8 × 2 × 5; q=2; 100 bootstraps | 2.221 (2.210–2.236) | 225.85 / 225.98 |
| Recurrence + RQA | 1 trajectory; 800 times | 2.148 (2.140–2.156) | 228.38 / 228.82 |
| RQA sensitivity grid | 1 trajectory; 300 times; 16 specifications | 2.300 (2.287–2.305) | 223.00 / 223.13 |

These measurements describe only this CI-sized workload and runner. The ledger
retains every repetition and reports an interval rather than only a fastest
timing. Qualified 0.56, 0.57, 0.9.0rc1, 0.9.0, 0.9.1.dev0, 0.10.0.dev0, and 0.10.0rc1 snapshots remain archived
under `validation/performance/` rather than being overwritten or silently
relabeled.


## How to interpret the numbers

Use the result as:

> On the recorded hardware/software environment, this declared workflow and
> scale completed with the recorded repeated runtime distribution and peak
> memory.

Do not convert it into:

> eyetrajectoriespy is faster than package X.

and do not assume a hosted GitHub runner is equivalent to a research
workstation.

The latest committed qualification snapshot is stored in
`PERFORMANCE_ENVELOPE.json`; CI also uploads the raw run artifact.

## Practical-envelope guidance

Performance guidance should remain conditional on a recorded scale. A workflow
may be described as practical at a scale only when repeated qualification
supports that statement on a named reference environment. Optimizer-heavy and
bootstrap-heavy operations should not be summarized from a single fastest run.

No runtime threshold is used as a scientific pass/fail criterion in 0.10.0rc2. Execution failure is a qualification failure; speed is an observed property to document, not a target to game.
Execution failure is a qualification failure; speed is an observed property to
document, not a target to game.
