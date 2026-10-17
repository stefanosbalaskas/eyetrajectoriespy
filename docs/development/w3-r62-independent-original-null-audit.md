# W3 R62-A — independent immutable Gaussian null-bootstrap evidence audit

!!! warning "Numerical audit only; neither a calibrated 5% test nor power"
    This auditor checks the original R62 numerical evidence **without
    importing the simulation or REML fitting implementation**. Even
    perfect agreement with R62's original 32-block study is not a
    proof of valid Type-I error control, Gaussian model adequacy,
    covariance identification, or random-effect variance boundary calibration.

## Frozen source and audit scope

Original R62 research [PR #374](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/374)
prespecifies 32 new independent structural-zero Gaussian source
blocks, paired ordinary and extreme participant leverage, and 63
null-bootstrap refits per leverage condition. The expected full
archive is the `w3-r62-original-32-independent-block-null-refit-results`
artifact from [original run #39069680983](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39069680983).

This separate research tranche supplies
`scripts/audit_w3_r62_original_null_independent.py`.
It verifies the exact three-file original SHA256 archive,
the original 40-character checkout identity, 64 distinct
source/support records from **32 independent blocks**, 4,032
Gaussian pseudo-draw slots, 8,192 nested H0/H1 fit slots and
24,576 individual optimizer-start records.

For each observed and pseudo-source REML comparison, independently
recalculate the physical-coordinate projected KKT score from
archived start ratios and component scores; reconstruct negative
log-likelihood and near-best-start gates; preserve refusal
status and verify that the null includes EXACTLY zero slope
variance. For accepted comparisons, independently reconstruct
the nested likelihood ratio and its nonnegative statistic.

For each source with **63 accepted** pseudo-draws, calculate
the original finite-B add-one right-tail p-value and
predeclared p ≤ .05 decision. Verify all Gaussian draw seed
identities and original classical cutoff decisions.
No missing/refused draw is silently replaced or treated
as an accepted interval/test.

Recalculate ordinary and extreme source-level rejection counts,
Wilson 95% Monte Carlo intervals, refusal-inclusive
lower/upper bounds and the paired 2×2 rejection breakdown
without counting paired leverage cases as independent draws.
Verify numerical and statistical boundary fields remained false.

## Cross-platform engineering correction

The general Windows pytest suite originally failed three R60/R61/R62
**synthetic-artifact fixture** checks because their SHA256 value was
computed from explicit UTF-8/LF `raw.encode()`, but the data were
written with platform-default text newline conversion.
Writing those **same exact original UTF-8 bytes** directly
restores the cross-platform byte-integrity fixture.
This changes **no scientific estimator, original source
generator, original GitHub Actions artifact, threshold or
observed result**. The initial failures remain visible.

## Execution and limits

The dedicated cross-Python matrix validates positive and
negative fixture contracts before an original archive
exists. **Passing fixture tests must not be reported as
original R62 outcome validation.** Once the complete R62
aggregate is published, run the original-source check
against that original archive; the dedicated workflow
also offers a dispatch-only original audit job.

```bash
python scripts/audit_w3_r62_original_null_independent.py \
  --original /path/to/original-complete-R62-archive \
  --out build/r62-independent-audit.json
```

Both scientific blockers
[#289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289)
and [#296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296)
remain OPEN. The original R59/R60/R61/R62 findings stay
unaltered. This is a draft stacked research audit only;
stable 1.1.0, unreleased 1.2 development, protected main,
public API, release tag and PyPI remain untouched.
