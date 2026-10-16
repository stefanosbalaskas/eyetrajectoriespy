# W3 R51 — independent, read-only original Gaussian mechanism evidence audit

**This checker does not alter the R51 Gaussian source, nuisance estimator, reference distribution or inferential interval. It supplies a separate numerical/reporting verification, not validation of nominal 90% confidence-interval coverage.**

## Immutable original scientific source

The original prospective [R51 research PR #354](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/354) completed its [original workflow #38952364476](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/38952364476) with all four dedicated jobs successful. [Original artifact #12070401587](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/38952364476/artifacts/12070401587) contains the Gaussian primitive source cases, every fixed/refitted and fitted/oracle-generation bootstrap draw, original variance nuisance starts and pointwise intervals, summary, recorded PR-merge checkout and SHA256 digests.

The read-only audit independently retrieves that original immutable GitHub Actions artifact using the original run ID (rather than any subsequent PR-branch regenerated simulation). It checks recorded original checkout **`03a38611a2eeb585a1139863d1f3010fffb918ea`**. The SHA256 manifest must match the actual original byte content for `cases.json`, `summary.json` and `source-commit.txt`.

## What is independently recalculated

The dedicated checker `scripts/audit_w3_r51_original_mechanism_independent.py` does **not import the original R51 simulation or optimizer implementation**. It verifies the complete set of eight independent primitive block IDs and two paired leverage source cases, **16 complete original source cases, 80 original method intervals, 2,016 Gaussian draws/refits and 4,064 individual two-start optimizer records**. It does not conflate the paired leverage variants with independent simulation replications.

For all original and simulated four-component Gaussian nuisance covariance fits, the audit separately verifies both frozen start identities, physically positive variance ratios, optimizer flags, objective reconstruction within **1e-6**, projected physical KKT threshold **0.001**, near-best observed negative restricted likelihood gap **0.001**, and an eligible selected optimizer outcome. It distinguishes **optimizer-success** from **physical KKT success**, and refuses a reported successful Gaussian refit if neither recorded start satisfies the physical first-order/NLL gates. These checks alone do not certify a global Gaussian REML optimum.

It independently recomputes Gaussian generation-pair seed alignment (source block, leverage support, replicate index), all absolute 63-draw **90th percentile studentized bootstrap critical values**, the common original fitted-CR2 SE and resulting interval half-widths, true-generating-coefficient inclusion decisions, 95% Wilson Monte Carlo intervals with **eight original independent primitive blocks** per leverage stratum, and the paired critical-value ratios. The oracle-generation reference remains explicitly **nonimplementable** on empirical gaze datasets.

The original evidence contains **one numerically unsuccessful individual KKT start** (block 3, extreme support, fitted-generation replicate 25, `interior` projected KKT **0.0019989066**), yet its alternate `spread` start has KKT **3.3071×10⁻¹¹** at the same best observed likelihood. The paired nuisance fit passes the original predetermined gate, so the original source records show **2,032/2,032 accepted nuisance fits and zero numerical refusal**. Do not claim all **4,064** starts individually passed strict projected KKT.

## Scientific status

The original R51 fixed/refit versus fitted/oracle Gaussian generation study is now documented in the [original results article](w3-r51-bootstrap-narrowing-mechanism-results.md). The independent verifier is an engineering and reproducible scientific-source audit, **not a rerun of the original experiment, a proof that the bootstrap-t model is correctly calibrated, or a new Gaussian inferential procedure**. It cannot establish exact 90% pointwise or whole-function simultaneous coverage, MNAR/latent whole-participant selection identification, covariance kernel robustness, or random-slope boundary null Type-I/power calibration.

Keep issues [#289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289) and [#296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296) OPEN, and no protected-main merge, supported inference API, release tag or PyPI publication.
