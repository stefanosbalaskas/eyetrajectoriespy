# Performance envelope

Version 0.56 introduced a reproducible **single-package performance envelope**. Version 0.57 requalified it after release hardening, and 0.9.0rc1 requalifies the same declared CI-sized workloads under the exact prerelease version. It is
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

The current 0.9.0rc1 reference snapshot was measured from source commit
`ecd73e96deda07d1a64949ab0ce85999079a4b56` in GitHub Actions run
`36275419531` on Linux/Python 3.12.14, an AMD EPYC 7763 runner with four
logical CPUs visible to the job. NumPy/SciPy/statsmodels numerical thread
limits were fixed to one thread. Dependency versions and the synthetic workflow
scales are retained in `PERFORMANCE_ENVELOPE.json`.

| Workflow | Qualified scale | Median runtime (IQR), s | Peak RSS median / max, MiB |
|---|---|---:|---:|
| FPCA + participant bootstrap | 10 participants × 3 trials × 41 times; q=3; 20 bootstraps | 1.998 (1.981–2.474) | 223.45 / 227.62 |
| Full-refit mixed-effects bootstrap | 12 × 3 × 6; q=2; 20 bootstraps | 2.937 (2.912–2.954) | 226.74 / 227.16 |
| Nested participant/trial mixed fit | 8 × 3 × 5; q=2 | 2.608 (2.605–2.619) | 226.53 / 226.57 |
| Exposure-adjusted GEE + bootstrap | 8 × 2 × 5; q=2; 100 bootstraps | 2.184 (2.178–2.193) | 225.75 / 225.77 |
| Recurrence + RQA | 1 trajectory; 800 times | 2.063 (2.059–2.066) | 227.94 / 228.33 |
| RQA sensitivity grid | 1 trajectory; 300 times; 16 specifications | 2.218 (2.216–2.227) | 222.72 / 222.96 |

These measurements describe only this CI-sized workload and runner. The ledger
retains every repetition and reports an interval rather than only a fastest
timing. Qualified 0.56 and 0.57 snapshots remain archived under
`validation/performance/` rather than being overwritten or silently relabeled.


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

No runtime threshold is used as a scientific pass/fail criterion in 0.9.0rc1.
Execution failure is a qualification failure; speed is an observed property to
document, not a target to game.
