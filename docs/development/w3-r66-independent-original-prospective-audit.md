# W3 R66-A — independent immutable original 128-block prospective matched-detection audit

**Separate research-only, read-only independent verification; at creation, the ORIGINAL R66 simulation is still running. The auditor's contract tests are not evidence that the original archive has been audited.**

## Original experiment targeted

The separately submitted [R66 draft PR #381](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/381) prospectively freezes **128 NEW independent Gaussian generating primitive blocks**, 24 participants per block, and each of their six matched **ordinary/extreme leverage × zero/half/full structural participant random-slope SD** variants. This is **768 repeated source cases, not 768 independent generating blocks**. True structural slope variances are 0, 0.00050625 and 0.002025. Independent source seed `202610186666`, conditional fitted-null H0 Gaussian draw seed `202610186667`. The original fitted-zero H0 and nonnegative H1 Gaussian REML likelihood and nuisance refitting remain unchanged. All **63 conditional H0 Gaussian pseudodraws per source case** must refit both H0 and H1 nuisance parameters. The bootstrap-candidate conditional add-one rank-grid denominator remains **64**, rejection at p≤0.05 requires all original 63 nested fits accepted; the unchanged classical candidate threshold is `2.70554345409542`.

Original predeclared expected workload: 32 shards of four independent generating blocks, **48,384 pseudodraw fits**, **98,304 nested model positions**, **294,912 original optimizer-start records**, complete source/refusal denominators and three-member SHA256 original archive. Original source and sampling run must not be changed or rerun to accommodate this separate audit.

## What the independent auditor verifies

`scripts/audit_w3_r66_original_positive_slope_independent.py` **does not import** the original R66, R64, R63, R57 source generator, REML numerical fitters, or source aggregation. Its likelihood/KKT/NA numerical reconstruction is based on separately implemented code adapted from the previously passed R64-A independent audit. It checks:

1. All three original SHA256 byte hashes and the exact original frozen scientific PR-merge checkout (once available), and 128 original primitive generating block identities with all 768 case rows and consecutive 48,384 63-draw source records. Duplicate or missing slots are a hard failure.
2. Original true structural slope variance labels, within-block recorded full-component slope norms, exact-zero fitted H0 random-slope variance, source-specific nuisance H0 estimates, original six-start fit records, selected physical-coordinate projected KKT, likelihood objective and original nested one-sided LRT calculations, accepted/refused selection and 294,912 start-slot denominator.
3. Each source's independent Gaussian pseudodraw seed identity; complete-refit status, right-tail conditional bootstrap `p=(1+#(T_boot≥T_original))/64`, original fixed 5% candidate classification, unchanged classical candidate threshold, all six strata, Wilson Monte Carlo intervals and numerical refusal-inclusive source bounds.
4. **Original prospectively frozen block-paired inference record**, including intact 128-primitive-block pairing, zero→full ordinary and extreme candidate detection differences, and the frozen **primary extreme-minus-ordinary difference-of-changes**. Its complete 128-element original blockwise contrast vectors, earlier-only and later-only discordance, refusal-inclusive bounds, declared primary label `extreme_minus_ordinary_zero_to_full`, resample seed `202610186668` and **20,000 intact-primitive-block draws** must match independently reconstructed quantities. NumPy is used **only** to reproduce the original frozen PCG64 integer-resampling stream and empirical linear-percentile calculation; the original source simulator, model fitters, and aggregation are never invoked by the auditor. This checks frozen Monte Carlo arithmetic, not independent methodological corroboration of the bootstrap procedure itself.
5. On **any original block with an incomplete six-cell group**, no original prospective bootstrap percentile interval may be reported. Full 128-block refusal bounds remain in the audit instead of silently restricting to completed cases.
6. Release and scientific-qualification flags must remain false: no certified general 5% Type-I control or correctly sized power, no validated 90% fitted-covariance CR2 pointwise/simultaneous bands, no robust MAR/MNAR observation-process validity or release.

Original **native Gaussian latent response innovations and source residuals are not archived**. Passing this audit can certify the stored numerical likelihood, conditional p-value, matched-block bootstrap and SHA256 evidence, **not independently prove that the original source generator drew from its advertised law**.

## Two-stage CI with a hard original-archive boundary

**Stage A, enabled immediately:** deterministic independent integrity, original numerical-start/denominator, checksum-tampering, fake-power/refusal, frozen seed/rank and 20,000-resample matched-contrast fixture contracts run under Python 3.11, 3.12 and 3.13 on the new stacked draft PR. No original R66 archive is read at this stage.

**Stage B, required only after original 32-shard science and aggregate success:** retrieve the **original immutable** GitHub artifact by its known workflow/artifact identifiers, require the archived exact original PR-merge checkout SHA, run the independent numerical audit and record separate R66-A evidence JSON. Do not silently substitute newly generated data for failed source shards, and retain original failing workflow history. **Do not claim independent R66 original-source verification until Stage B actually passes.**

## Scientific use and release boundary

R66's primary leverage contrast is **prospectively selected** before inspecting its new independent source outcomes, which is an advance over R65's retrospective matched-block analysis. Even a nominally nonzero prospective matched bootstrap interval would be **finite-design simulation evidence**, not a general hypothesis about human gaze population leverage, global correctly-sized power, universal nominal 5% calibration, or a statistical repair for #289 (under-covering simultaneous CR2 bands) and #296 (response-dependent gaze observations).

Keep scientific blockers #289 and #296 open, experimental 1.2 inference APIs hidden, protected `main` unchanged, release 1.2 and PyPI unpublished.
