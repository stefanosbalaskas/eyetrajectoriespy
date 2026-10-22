# W3 R91/R91-A — original randomized completed-recovery evidence ledger

**Research provenance, independent-audit gate and interpretation limits.** This evidence concerns a bounded synthetic finite-population mean and an idealized genuinely complete random recovery process, not an installed package estimator.

## Frozen original prospective source study

| Field | Verified original evidence |
|---|---|
| Original R91 research source | [Draft PR #450](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/450) |
| Original 12/12 dedicated scientific jobs | [Actions run #39766521032](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39766521032) |
| Complete original archive, including all source-method records | [Artifact #12420172519](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39766521032/artifacts/12420172519) |
| Original artifact ZIP digest | `sha256:7a503fd7160ee784898a448e50c0df3310fe19273c6265b2c3354b56b321130f` |
| Original source branch head before CI | `bd3c7b25323264432406c499035761129bb8a044` |
| Actual GitHub PR merge checkout archived by science workflow | `eb65592307e1c7bc70d5cd31794bae46996bc656` |
| Independent complete X/Y generating source conditions | 64 |
| Paired MAR/MNAR first-stage masks | 128 |
| Independent primitive source blocks per native design | 32 |
| Known completed-retrieval inclusion probabilities | .10, .25, .50 |
| Conditional randomized retrieval repetitions per source and mechanism | 16 |
| Repeated source-method rows (not independent source observations) | 6,144 |

The archive retains `cases.json`, `summary.json`, `source-commit.txt` and `SHA256SUMS`. Eight separate four-block source shard artifacts retain the entire frozen source experiment. All original source and conditional retrieval records, including unfavorable errors, are preserved. The original source itself is not an independent scientific audit.

## Separate numerical verification requirement

A separate [R91-A draft PR #451](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/451) reconstructs the frozen original experiment **without importing its source generator or HT implementation**. The independent science workflow [#39767059171](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39767059171) must pass three Python-version fixtures and, critically, the mandatory download and replay of artifact #12420172519. It must independently regenerate the original complete X/Y source, selective first-stage and secondary observation masks, all 16 nested Bernoulli completed-retrieval masks, every observed-only HT point and design variance, simulator-only oracle variance and truth, naive estimate, sharp bound width and original fixed-cell summary. It must verify the exact original checkout and every original SHA256 member, and output a distinct independent replay evidence artifact.

**Do not declare the numerical evidence independently replicated until this exact mandatory original-archive replay finishes successfully.** A successful original run or passing independent fixtures without original-archive replay is insufficient.

## Original source-level descriptive errors (await independent numerical gate)

The source simulator yields the following selected results. Each fixed cell has 32 independent complete-source blocks with 16 dependent conditional recovery repetitions per block. The values below are **not** source-independent confidence intervals or calibrated uncertainty statements.

| Native design | Loss law | g | Mean signed HT error | HT RMSE | Naive RMSE | Oracle / estimated design variance |
|---|---|---:|---:|---:|---:|---|
| Curves | MAR | .10 | +.00046 | .04128 | .01122 | .001896 / .001895 |
| Curves | MAR | .25 | +.00153 | .02505 | .00764 | .000632 / .000635 |
| Curves | MAR | .50 | +.00030 | .01495 | .00425 | .000211 / .000211 |
| Curves | MNAR | .10 | +.00019 | .04221 | .00981 | .001925 / .001922 |
| Participants | MAR | .10 | +.00163 | .03486 | .01559 | .001128 / .001131 |
| Participants | MNAR | .10 | +.00199 | .03432 | .01425 | .001167 / .001171 |
| Participants | MNAR | .50 | −.00009 | .01145 | .00486 | .000130 / .000130 |

The HT conditional unbiasedness formula and variance identities are verified analytically by exact two-record Bernoulli enumeration, independent of this simulation. Sixteen finite recovery draws are insufficient to claim exact zero finite-source error. In these original simulated conditions, HT has **larger empirical RMSE than the naive measured-only estimator**, despite smaller signed errors in expectation. This is a legitimate bias-variance trade-off, not an error to delete or a general method qualification.

## Boundaries and publication gate

The only target is the realized finite mean of **clip((Y+1)/2,0,1)** among originally missing synthetic records. An ideal external validator that truly recovers every Bernoulli-selected record with a known positive inclusion probability is assumed. Random audit *assignment* with selective noncompletion is explicitly insufficient. The HT estimate need not lie in [0,1], and no confidence interval or functional-band method is provided.

The [R91 article](../articles/w3-r91-guaranteed-recovery-design-ht.md), [methods companion](../articles/w3-r91-guaranteed-recovery-methods.md) and two actual data SVG figures are documentation-only candidates, not published until independent R91-A original-archive verification and separate exact-head all-CI plus protected-main Pages deployment. Both original and independent scientific PRs remain draft/unmerged.

No claim of field MNAR selection identification, general raw gaze recovery, function-on-scalar slope inference, 90% simultaneous-band coverage or production v1.2 release is authorized. Scientific blockers [#296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296) and [#289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289) stay **OPEN**. Stable public 1.1.0 and API unchanged, **v1.2 GitHub Release/PyPI HOLD**.
