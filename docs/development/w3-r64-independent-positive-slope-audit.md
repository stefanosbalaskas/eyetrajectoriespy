# W3 R64-A — independent original zero/half/full structural random-slope evidence audit

**Read-only original-archive research audit in progress.** The original R64 source archive is now complete, and the independently built auditor is required to validate it on a separate workflow. Previously green fixture tests alone did not establish original-source integrity.

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

**Stage B now required in CI:** download immutable original R64 [workflow #39121431222](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39121431222), [original archive #12136512850](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39121431222/artifacts/12136512850), pin scientific PR-merge checkout `ebe731c3db6a491f1d6b494d91d05143ecc9ee35`, reconstruct complete original original numerical evidence with the independent standard-library-only auditor and preserve a separate audit JSON artifact. The source study itself is frozen; this job must pass before original R64 may be labeled independently audited.

## Actual immutable original R64 audit — PASSED

Two separate [exact original R64-A audit workflows #39151585083](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39151585083) and [#39151655810](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39151655810) each **passed all 4/4 dedicated jobs**, including the mandatory real original-source archive job and three Python 3.11/3.12/3.13 regression jobs. The original R64 archive came from [original workflow #39121431222](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39121431222), [original artifact #12136512850](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39121431222/artifacts/12136512850), pinned at **original PR-merge checkout `ebe731c3db6a491f1d6b494d91d05143ecc9ee35`**. The separate [independent audit evidence artifact #12145059949](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39151655810/artifacts/12145059949) is not the original science archive.

The standard-library-only independent verifier reproduced all **192 source cases, 12,096 individual bootstrap slots, 24,576 H0/H1 nested fit slots and 73,728 optimizer starts**. It verified **3/3 original aggregate SHA256 members** and the original checkout, true generating structural slope variance labels 0, 0.00050625 and 0.002025, recorded matched innovation norms, original nested REML NLL/KKT and source p-rank gate, the six candidate rejection counts and all Wilson intervals. Maximum selected projected physical-coordinate KKT residual **0.0006914718118027805**, below frozen 0.001. **All 192 source cases and 12,096 bootstrap fits accepted**, with zero numerical refusals.

The independently reconstructed **within-block** zero-versus-full candidate rejection discordance was ordinary **1 full-only, 0 zero-only**, with 3 blocks rejecting at both zero and full; extreme **7 full-only, 1 zero-only**, with 1 block rejecting at both zero and full. Across all three slope strengths **0 ordinary blocks and 2 extreme blocks** had nonmonotone original detection classification. These are post-hoc descriptive contrasts on paired source blocks, not six independent samples, a prespecified test of interaction, or statistical power.

**The independent archived numerical-evidence gate is therefore COMPLETE.** The original latent generating Gaussian source arrays were not retained in the aggregate, so this does *not* independently prove original source-generation law, general Gaussian model validity, a calibrated 5% test or 90% fitted-CR2 pointwise/simultaneous coverage.

## Interpretation

Even a successful independent original-archive audit would establish numerical/provenance integrity, **not** 5% calibrated null testing, properly sized power under alternatives, robust covariance or missingness mechanisms, true fitted-CR2 pointwise/simultaneous 90% functional coverage, or public inference readiness. A positive variance source with a candidate 5% rejection is an exploratory sensitivity outcome because the reference itself is not universally calibrated.

Issues #289 and #296 remain OPEN. Protected main, stable 1.1.0, unreleased 1.2, tags, API and PyPI stay unchanged.
