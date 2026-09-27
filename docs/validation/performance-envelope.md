# Performance envelope

Version 0.56 introduced a reproducible **single-package performance envelope**. Version 0.57 requalified it after release hardening, 0.9.0rc1 qualified the prerelease, and 0.9.0 independently requalifies the same declared CI-sized workloads under the exact final version. It is
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

The current 0.9.0 final reference snapshot was measured from source commit
`09850da2f79bb32c94ee09d0436826b8a7399289` in GitHub Actions run
`36303746820` on Linux/Python 3.12.14, an AMD EPYC 7763 runner with four
logical CPUs visible to the job. NumPy/SciPy/statsmodels numerical thread
limits were fixed to one thread. Dependency versions and the synthetic workflow
scales are retained in `PERFORMANCE_ENVELOPE.json`.

| Workflow | Qualified scale | Median runtime (IQR), s | Peak RSS median / max, MiB |
|---|---|---:|---:|
| FPCA + participant bootstrap | 10 participants × 3 trials × 41 times; q=3; 20 bootstraps | 1.973 (1.968–2.536) | 223.50 / 227.94 |
| Full-refit mixed-effects bootstrap | 12 × 3 × 6; q=2; 20 bootstraps | 2.955 (2.951–2.966) | 226.81 / 227.03 |
| Nested participant/trial mixed fit | 8 × 3 × 5; q=2 | 2.688 (2.683–2.689) | 226.32 / 226.48 |
| Exposure-adjusted GEE + bootstrap | 8 × 2 × 5; q=2; 100 bootstraps | 2.259 (2.248–2.270) | 225.48 / 225.70 |
| Recurrence + RQA | 1 trajectory; 800 times | 2.153 (2.145–2.163) | 227.68 / 228.29 |
| RQA sensitivity grid | 1 trajectory; 300 times; 16 specifications | 2.296 (2.284–2.306) | 222.73 / 222.99 |

These measurements describe only this CI-sized workload and runner. The ledger
retains every repetition and reports an interval rather than only a fastest
timing. Qualified 0.56, 0.57 and 0.9.0rc1 snapshots remain archived under
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

No runtime threshold is used as a scientific pass/fail criterion in 0.9.0.
Execution failure is a qualification failure; speed is an observed property to
document, not a target to game.
