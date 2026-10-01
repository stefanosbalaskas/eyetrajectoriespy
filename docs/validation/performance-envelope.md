# Performance envelope

Version 0.56 introduced a reproducible **single-package performance envelope**. Version 0.57 requalified it after release hardening, 0.9.0rc1 qualified the prerelease, 0.9.0 qualified the first stable pre-1.0 release, 0.9.1.dev0 qualified the maintenance line, 0.10.0.dev0 requalified the integrated native sparse-FPCA/PACE development line, and 0.10.0rc1 independently qualified the first release candidate. `0.10.0rc2` received its own fresh qualified envelope, final `0.10.0` was independently requalified, and the reconciled `0.11.0.dev0` stabilization line received its own fresh envelope. `0.11.0rc1` and final `0.11.0` were qualified separately. The `0.12.0rc1` sparse-MFPCA/joint-PACE release candidate likewise received its own exact-version envelope and that snapshot is archived immutably. Final `0.12.0` now has a separate fresh exact-version envelope generated under the literal final package identity; no RC measurements were relabeled. Evidence is never relabeled across package versions.

This is not a comparative benchmark and does not claim that eyetrajectoriespy is faster than another package.

The qualification harness is `scripts/run_performance_qualification.py` and the CI workflow is `performance-qualification`.

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

Each repetition runs in a fresh Python process so process peak memory is attributable to one complete workflow rather than inherited from an earlier benchmark case.

## Qualified workflow set

The qualification harness measures these expensive routes separately:

1. FPCA + participant bootstrap stability;
2. functional mixed-effects full-refit participant bootstrap;
3. nested participant/trial covariance fitting;
4. exposure-adjusted generalized GEE + participant bootstrap;
5. recurrence matrix + RQA;
6. RQA nonlinear parameter-sensitivity grid.

The committed workload profile is intentionally CI-sized and is a **reference envelope**, not a universal workstation capacity claim.

## Final 0.12.0 qualification snapshot

The immutable `0.12.0rc1` snapshot remains archived under `validation/performance/PERFORMANCE_ENVELOPE-0.12.0rc1.json`. The fresh final `0.12.0` snapshot was generated from PR-head source commit `eabb28029184c44190d1f3630d3d61df37bd3601` in GitHub Actions run `36914769585` under literal package identity `0.12.0`. The raw workflow artifact is `11189676740` with digest `sha256:823b2473006096ccf51eec83ec8da8056bb54e2d8d142ea0a354debe4a320f43`.

The run used Linux/Python 3.12.14 on an AMD EPYC 9V45 runner with four logical CPUs visible to the job. Numerical thread limits were fixed to one. The canonical `PERFORMANCE_ENVELOPE.json` records this final-version run and preserves all repeated measurements.

| Workflow | Qualified scale | Median runtime (IQR), s | Peak RSS median / max, MiB |
|---|---|---:|---:|
| FPCA + participant bootstrap | 10 participants × 3 trials × 41 times; q=3; 20 bootstraps | 1.218 (1.194–1.515) | 222.96 / 227.36 |
| Full-refit mixed-effects bootstrap | 12 × 3 × 6; q=2; 20 bootstraps | 1.601 (1.567–1.607) | 230.65 / 230.77 |
| Nested participant/trial mixed fit | 8 × 3 × 5; q=2 | 1.485 (1.479–1.488) | 230.06 / 230.29 |
| Exposure-adjusted GEE + bootstrap | 8 × 2 × 5; q=2; 100 bootstraps | 1.267 (1.264–1.285) | 229.44 / 229.44 |
| Recurrence + RQA | 1 trajectory; 800 times | 1.258 (1.252–1.268) | 229.02 / 229.31 |
| RQA sensitivity grid | 1 trajectory; 300 times; 16 specifications | 1.402 (1.380–1.404) | 224.31 / 224.56 |

These measurements describe only this CI-sized workload and runner. The ledger retains every repetition and reports an interval rather than only a fastest timing. Earlier qualified snapshots remain under `validation/performance/` when archived; in particular the `0.12.0rc1` archive is retained rather than overwritten or silently relabeled.

## How to interpret the numbers

Use the result as:

> On the recorded hardware/software environment, this declared workflow and scale completed with the recorded repeated runtime distribution and peak memory.

Do not convert it into:

> eyetrajectoriespy is faster than package X.

and do not assume a hosted GitHub runner is equivalent to a research workstation.

The latest committed qualification snapshot is stored in `PERFORMANCE_ENVELOPE.json`; CI also uploads the raw run artifact.

## Practical-envelope guidance

Performance guidance should remain conditional on a recorded scale. A workflow may be described as practical at a scale only when repeated qualification supports that statement on a named reference environment. Optimizer-heavy and bootstrap-heavy operations should not be summarized from a single fastest run.

No runtime threshold is used as a scientific pass/fail criterion in final `0.12.0`. Execution failure is a qualification failure; speed is an observed property to document, not a target to game.

For the fresh final-version run, median runtimes were 1.218 s (FPCA bootstrap), 1.601 s (mixed full-refit bootstrap), 1.485 s (nested mixed fit), 1.267 s (generalized GEE bootstrap), 1.258 s (recurrence/RQA), and 1.402 s (nonlinear sensitivity). Median process peak RSS ranged from 222.96 to 230.65 MiB across these synthetic workloads. These values describe only the recorded GitHub-hosted environment.
