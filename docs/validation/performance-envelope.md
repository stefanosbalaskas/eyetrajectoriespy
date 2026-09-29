# Performance envelope

Version 0.56 introduced a reproducible **single-package performance envelope**. Version 0.57 requalified it after release hardening, 0.9.0rc1 qualified the prerelease, 0.9.0 qualified the first stable pre-1.0 release, 0.9.1.dev0 qualified the maintenance line, 0.10.0.dev0 requalified the integrated native sparse-FPCA/PACE development line, and 0.10.0rc1 independently qualified the first release candidate. `0.10.0rc2` received its own fresh qualified envelope, final `0.10.0` was independently requalified and archived, and the reconciled `0.11.0.dev0` stabilization line received its own fresh envelope. That development snapshot is now archived. `0.11.0rc1` requires a new exact-version envelope and is not allowed to relabel development evidence. Evidence is never relabeled across package versions. It is
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

The archived `0.11.0.dev0` stabilization snapshot was measured from source commit `9d191c6975e8a4fc31d2434266d9b34801426c17` in GitHub Actions run `36555745875` on Linux/Python 3.12.14, an AMD EPYC 7763 runner with four logical CPUs visible to the job. `0.11.0rc1` qualification must replace the canonical ledger only with a fresh workflow-generated rc1 snapshot while preserving that development snapshot under `validation/performance/`.

| Workflow | Qualified scale | Median runtime (IQR), s | Peak RSS median / max, MiB |
|---|---|---:|---:|
| FPCA + participant bootstrap | 10 participants × 3 trials × 41 times; q=3; 20 bootstraps | 1.930 (1.922–2.429) | 224.07 / 228.73 |
| Full-refit mixed-effects bootstrap | 12 × 3 × 6; q=2; 20 bootstraps | 2.859 (2.840–2.875) | 227.68 / 227.75 |
| Nested participant/trial mixed fit | 8 × 3 × 5; q=2 | 2.557 (2.543–2.570) | 226.94 / 227.35 |
| Exposure-adjusted GEE + bootstrap | 8 × 2 × 5; q=2; 100 bootstraps | 2.160 (2.149–2.161) | 226.12 / 226.52 |
| Recurrence + RQA | 1 trajectory; 800 times | 2.014 (2.008–2.016) | 228.71 / 228.81 |
| RQA sensitivity grid | 1 trajectory; 300 times; 16 specifications | 2.174 (2.170–2.184) | 223.86 / 223.89 |

These measurements describe only this CI-sized workload and runner. The ledger
retains every repetition and reports an interval rather than only a fastest
timing. Qualified 0.56, 0.57, 0.9.0rc1, 0.9.0, 0.9.1.dev0, 0.10.0.dev0, 0.10.0rc1, 0.10.0rc2, final 0.10.0, and 0.11.0.dev0 snapshots remain archived
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

No runtime threshold is used as a scientific pass/fail criterion in 0.11.0rc1. Execution failure is a qualification failure; speed is an observed property to document, not a target to game.
Execution failure is a qualification failure; speed is an observed property to
document, not a target to game.
