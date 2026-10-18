# W3 R64-A — independent original zero/half/full structural random-slope evidence audit

**Read-only research audit; no R64 original archive is yet complete.** Green fixture tests do not establish independent numerical verification of the original experiment.

## Frozen source and inference contract

[R64 draft PR #378](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/378) introduces a new source-matched positive-slope Gaussian detection pilot following [R63-A independently verified true-null numerical evidence](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39120637419). The original R64 study freezes:

- **32 independent primitive Gaussian source blocks** (seed `202610186464`), each n=24 participants, with paired ordinary/extreme leverage and within-block zero/half/full participant random-slope innovation scaling. The same block is shared across all six factorial cells; **192 total cases, 32 independent source units per cell**, not 192 independent trials.
- Structural true random-slope standard-deviation multipliers 0, 0.5, 1, respectively physical variance **0, 0.00050625, 0.002025**.
- **63 fixed H0 nuisance-refitted Gaussian bootstrap responses per source case**, independent draw seed `202610186465`, fully reestimating nuisance covariance under exact-zero H0 and nonnegative H1. The original nonnegative nested likelihood ratio and multistart physical projected-KKT gate are unchanged. Frozen add-one p grid **/64**, nominal p≤.05; unchanged *candidate* asymptotic classical mixture cutoff 2.70554345409542.
- Full original science denominators: 192 source cases, 12,096 pseudoresponses, 24,576 nested H0/H1 fits and 73,728 original optimizer start records, exact source/branch checkout SHA256 evidence, all refusals preserved.

## Independent standard-library-only auditor

New `scripts/audit_w3_r64_original_positive_slope_independent.py` does **not import original source generation, R57/R63/R64 simulation code, covariance optimizers or downstream scientific summary functions**. It independently reconstructs:

1. Original three-file SHA256 integrity, frozen exact original scientific checkout (once published), complete block×support×slope source identities and structural truth variance labels; all original 192 source and 12,096 pseudodraw identities must be present without duplicate, missing or extra cases.
2. Source-matching diagnostic `full_slope_component_L2` consistency and retained-slope L2 scaled exactly by 0/0.5/1 from the archived numerical metadata. The **original raw participant latent Gaussian innovations and native y are not archived**, hence this does not prove source innovation generation or matching from original native data.
3. Full H0/H1 original optimizer-start labels, physical score/bounds/projected-KKT reconstruction, objective reconstruction and best-eligible original NLL checks. All 73,728 original multistart records and source-level numerical refusals remain counted.
4. Exact-zero participant random-slope component in fitted H0 covariance, originally source-fitted other nuisance variances and complete independent per-draw RNG seed identities across block/support/slope/63 draw index.
5. Fully reconstructed nonnegative nested deviance, frozen classical-candidate classification, conditional bootstrap p=(1+#T_boot≥T_original)/64 only if all 63 bootstrap fits accepted, and the six cell-specific candidate detection rates, Wilson 95% Monte Carlo intervals and full-denominator refusal bounds.
6. **Matched source-block detection transitions** for each support, including nonmonotone detection patterns and matched zero-versus-full discordance. Do not mistake repeated leverage/slope settings within a block as new independent Monte Carlo replications.
7. Unchanged qualification and release flags. Any archived claimed **calibrated 5% size**, **validated statistical power**, **fitted CR2 90% intervals or simultaneous bands**, or **release authorization** causes audit refusal.

## Execution stages

**Stage A — initial:** Python 3.11/3.12/3.13 independent auditor integrity, true-variance, full refusal, Wilson and checksum tamper/seed-grid regression tests are run in a new stacked research draft PR. Green Stage A CI does not certify original R64.

**Stage B — mandatory after original source finish:** Once [R64 original science](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/378) completes all eight shards, record its immutable workflow run/artifact ID and exact PR-merge SHA. Update the **separate audit branch only**, add a required CI job retrieving the *original* finished source archive, require exact archived checkout, run this auditor and publish its independent JSON. Retain original source and failed audit workflows unaltered.

## Interpretation

Even a successful independent original-archive audit would establish numerical/provenance integrity, **not** 5% calibrated null testing, properly sized power under alternatives, robust covariance or missingness mechanisms, true fitted-CR2 pointwise/simultaneous 90% functional coverage, or public inference readiness. A positive variance source with a candidate 5% rejection is an exploratory sensitivity outcome because the reference itself is not universally calibrated.

Issues #289 and #296 remain OPEN. Protected main, stable 1.1.0, unreleased 1.2, tags, API and PyPI stay unchanged.
