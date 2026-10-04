# Performance envelope

`eyetrajectoriespy` maintains a reproducible **single-package performance envelope** for selected expensive workflows. Evidence is versioned and never relabelled across package identities: release candidates and final releases receive separate snapshots when fresh exact-version qualification is required.

The current committed qualification identity is **1.0.0**. Historical envelopes, including `1.0.0rc1` and the 0.12 line, remain archived under `validation/performance/`.

This is not a comparative benchmark and does not claim that eyetrajectoriespy is faster than another package.

The qualification harness is `scripts/run_performance_qualification.py` and the CI workflow is `performance-qualification`.

## What is recorded

For every run the harness records:

- participant count;
- trials per participant;
- functional grid length (`n_t`);
- basis/component dimension (`q`) where applicable;
- bootstrap/specification count;
- three or more independent process timings;
- median, first quartile, third quartile, minimum and maximum wall-clock time;
- process peak resident memory on supported Unix runners;
- Python/package/dependency versions;
- operating system, machine/CPU information and logical CPU count;
- Git commit and GitHub Actions run identifiers when available; and
- numerical thread-limit environment.

Each repetition runs in a fresh Python process so process peak memory is attributable to one complete workflow rather than inherited from an earlier benchmark case.

## Qualified workflow set

The qualification harness measures these expensive routes separately:

1. FPCA + participant bootstrap stability;
2. functional mixed-effects full-refit participant bootstrap;
3. nested participant/trial covariance fitting;
4. exposure-adjusted generalized GEE + participant bootstrap;
5. recurrence matrix + RQA; and
6. RQA nonlinear parameter-sensitivity grid.

The committed workload profile is intentionally CI-sized and is a **reference envelope**, not a universal workstation capacity claim.

## Final 1.0.0 qualification snapshot

Final `1.0.0` received a fresh package-wide performance envelope rather than inheriting the immutable `1.0.0rc1` measurements.

The current snapshot was generated from source commit `f62431b33ecb24637896ff9dd263e02241cb351a` in GitHub Actions run `37162388959` under literal package identity `1.0.0`. Raw artifact `11287947605` has digest `sha256:d2b0dcee106d98e4963c63897c7011ad6adb0b8058f0672ffd185330658f4104`.

The run used Linux/Python 3.12.14 on an AMD EPYC 9V45 runner with four logical CPUs visible to the job. Numerical thread limits were fixed to one. The canonical `PERFORMANCE_ENVELOPE.json` records this final-version run and preserves every repeated measurement.

| Workflow | Qualified scale | Median runtime (IQR), s | Peak RSS median / max, MiB |
|---|---|---:|---:|
| FPCA + participant bootstrap | 10 participants × 3 trials × 41 times; q=3; 20 bootstraps | 1.462 (1.424–1.809) | 222.83 / 227.33 |
| Full-refit mixed-effects bootstrap | 12 × 3 × 6; q=2; 20 bootstraps | 1.864 (1.835–1.865) | 230.40 / 230.49 |
| Nested participant/trial mixed fit | 8 × 3 × 5; q=2 | 1.692 (1.688–1.733) | 230.14 / 230.21 |
| Exposure-adjusted GEE + bootstrap | 8 × 2 × 5; q=2; 100 bootstraps | 1.536 (1.529–1.555) | 229.24 / 229.32 |
| Recurrence + RQA | 1 trajectory; 800 times | 1.594 (1.571–1.614) | 229.22 / 229.50 |
| RQA sensitivity grid | 1 trajectory; 300 times; 16 specifications | 1.644 (1.625–1.645) | 224.31 / 224.52 |

These measurements describe only this CI-sized workload and runner. The ledger retains every repetition and reports a distribution rather than only a fastest timing.

## How to interpret the numbers

Use the result as:

> On the recorded hardware/software environment, this declared workflow and scale completed with the recorded repeated runtime distribution and peak memory.

Do not convert it into:

> eyetrajectoriespy is faster than package X.

and do not assume a hosted GitHub runner is equivalent to a research workstation.

The latest committed qualification snapshot is stored in `PERFORMANCE_ENVELOPE.json`; CI also uploads the raw run artifact.

## Practical-envelope guidance

Performance guidance should remain conditional on a recorded scale. A workflow may be described as practical at a scale only when repeated qualification supports that statement on a named reference environment. Optimizer-heavy and bootstrap-heavy operations should not be summarized from a single fastest run.

No runtime threshold is used as a scientific pass/fail criterion in stable `1.0.0`. Execution failure is a qualification failure; speed is an observed property to document, not a target to game.

## Historical snapshots

Earlier exact-version qualification records remain immutable, including:

- `PERFORMANCE_ENVELOPE-1.0.0rc1.json` — release-candidate evidence;
- `PERFORMANCE_ENVELOPE-1.0.0.json` — final 1.0 evidence;
- historical 0.12/0.11/0.10 snapshots retained for their original package identities.

Later maintenance or minor releases must generate fresh evidence when their release contract requires it; existing measurements must not be silently relabelled.
