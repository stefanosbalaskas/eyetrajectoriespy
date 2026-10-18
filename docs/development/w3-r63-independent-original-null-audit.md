# W3 R63-A — independent original 128-block fitted-H0 null-bootstrap audit

**Draft research-only, read-only original-evidence verification. The original R63 source archive is not yet complete at protocol creation.** Do not describe R63-A contract tests as independent certification of the original data. This audit must operate on the separately completed original R63 artifact, never source data generated or changed on this branch.

## Frozen target

[Original R63 draft PR #376](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/376) studies **128 new genuinely independent Gaussian structural-zero primitive blocks** with 24 participants per block, paired ordinary/extreme leverage. There are **256 paired cases**, not 256 independent Monte Carlo replications per stratum, **63 fitted-null Gaussian pseudoresponse draws per case** (16,128 draw slots), **32,768 nested H0/H1 model-fit positions** and **98,304 optimization-start records**. The source seed is `202610186363`; the separate bootstrap seed is `202610186364`. The add-one conditional candidate 5% decision uses p=(1+#(T_boot≥T_original))/64, requiring all 63 numerical fits accepted. The unchanged classical candidate mixture cutoff is T>2.70554345409542.

All original cases, draw indices, missing fits and numerical refusals belong in the fixed denominator. The original source experiment consists of 32 shards of four independent primitive blocks each. The exact source checkout SHA and immutable full artifact ID **cannot be frozen until the original R63 workflow completes**; this audit must separately pin the real original PR merge checkout SHA in its required original-data job before claiming original verification.

## Independent archive audit

The new `scripts/audit_w3_r63_original_null_independent.py` imports only the Python standard library, **not** R63/R62/R57 model estimators, source generators or likelihood optimizers. It independently checks:

1. SHA256 bytes of the complete original `cases.json`, `summary.json`, `source-commit.txt` evidence, 40-character lowercase commit identity and optionally the frozen exact original scientific merge checkout.
2. The complete set of 128 distinct primitive block IDs, ordinary/extreme paired case IDs, 256 case records, 16,128 consecutive source-owned pseudodraw records and original start labels; no absent or duplicated source/sample positions.
3. Original physical-coordinate projected KKT gradients, ratio bounds, selected and reconstructed REML negative log likelihoods, near-best multistart gate, and raw/clipped nested H0–H1 likelihood-ratio differences. All 98,304 original start positions are retained for the source-level denominator.
4. Exact original fitted H0 covariance-component decomposition with **zero slope variance**; per-draw seed identity and the candidate classical reference exceedance. Fully recomputed conditional (1+#(T_boot≥T_observed))/64 p-values **only** for source cases with all 63 bootstrap nested models accepted.
5. Full per-stratum acceptance/refusal denominators, source-level Wilson 95% intervals, conservative full-denominator refusal bounds and **paired** ordinary/extreme bootstrap rejection classification table.
6. All original release/CR2/nonqualification flags. Any false source-ID, seed, physical numerical fit, likelihood, SHA256, or inferred p-value is a hard audit failure.

## CI execution stages

**Stage A:** The independent auditor and SHA256/cutoff/Wilson/tamper/regression contracts run on Python 3.11, 3.12 and 3.13 on its own stacked draft PR, without original R63 data. Three green contracts alone are *not* validation of source evidence.

**Stage B (required before any source-audit claim):** Once the original R63 source workflow uploads its final complete aggregated artifact, record the exact original scientific PR-merge checkout; update this separate audit workflow to download its pinned artifact ID and require that exact checkout, run the independent audit and preserve uploaded independent JSON evidence. Preserve prior CI attempts and any failures. Leave the original R63 source runner and immutable original experiment untouched.

## Scientific limits

Even successful original R63-A mathematical reconstruction will only independently certify *archived numerical and reporting integrity* under the original designs. R63 would be stronger independent Monte Carlo size evidence than the original [R62 32-block study](w3-r62-original-32block-null-results.md), which had **2/32 (6.25%)** bootstrap candidate exceedances in each paired leverage stratum (Wilson 95% 1.73–20.15%) and **3/32 (9.38%)** classical candidates each. R63 cannot by itself prove a generally calibrated nominal 5% variance-component test, asymptotic-reference superiority, statistical power or correct 90% fitted-covariance CR2 pointwise/simultaneous function-wide bands. Missing-observation MAR/MNAR and real gaze data remain outside this experiment.

**Keep issues #289 and #296 OPEN. Protected main, stable API, release tag, version 1.2 and PyPI remain unchanged.**
