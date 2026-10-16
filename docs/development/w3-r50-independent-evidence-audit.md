# W3 R50 — independent original-source reporting audit (R50-A)

!!! warning "Audit of a completed artifact, not a statistical qualification"
    This read-only checker is independent of the R50 data generator,
    covariance fitter, Gaussian bootstrap and summary implementation.
    It cannot establish nominal pointwise coverage, correct REML
    optimization or simultaneous functional confidence bands.

## Why this is separate

R50's original source experiment in [PR #352](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/352)
runs three fixed independent Gaussian shards, with 24
independent primitive generating blocks and paired
ordinary/extreme-leverage source conditions.
Its own scientific aggregator checks three shard
SHA256 manifests and source identity.

A second implementation is needed to audit the **final**
original artifact without calling the research simulator
or trusting the source-generated summary.

The independently coded checker is
`scripts/audit_w3_r50_original_evidence_independent.py`.
It accepts the unmodified complete Actions artifact
directory containing `cases.json`, `summary.json`,
`source-commit.txt`, and `SHA256SUMS`.

The checker verifies all three recorded SHA256 digests,
exactly 48 block/support IDs (24 independent blocks),
five method arms and interval slots per original
source case, all 63 bootstrap-refit attempt slots
and both solver-start records per nuisance fit.
Additionally, the read-only checker independently verifies each recorded
original or bootstrap nuisance fit's two fixed optimizer-start identities,
four positive physical variance ratios, objective reconstruction tolerance,
physical projected **KKT ≤ 0.001** and selected **NLL within 0.001** of the
lowest recorded two-start candidate. A recorded accepted fit with no
numerically eligible optimizer start is a reporting-audit failure, even
when the original scientific runner marked its interval as successful.
These numerical checks do **not** prove global REML optimality or
statistical coverage.

It independently reconstructs 90% inclusion decisions,
the 31-versus-63 *absolute studentized-pivot quantile*
using an independently coded linear percentile rule,
full-planned-denominator counts and 95% Wilson
Monte Carlo intervals. It cross-checks the
original source summary's accepted/refused counts,
mean accepted widths, bootstrap-refit status counts,
median critical-value ratios and paired inclusion
disagreements.

Refused and non-attempted intervals are never
reclassified as successes or excluded from the
24-original-block denominator. The Gaussian source
truth appears only in read-only source-ledger checks.

## Reproduce after the R50 original aggregate is complete

Download the final R50 GitHub Actions artifact
`w3-r50-original-checksummed-independent-source-evidence`
from the original scientific workflow, without altering it.
Then:

```bash
python scripts/audit_w3_r50_original_evidence_independent.py \
  --original-artifact-dir /path/to/unpacked-original-R50-artifact
```

Before the original aggregate is available, the
unit tests validate the auditor on artificial
complete-ledger fixtures, including checksum tampering,
duplicate source IDs and inconsistencies between
case records and the source summary. **Passing
these fixture tests must not be reported as an
original R50 outcome verification.**

## Reporting boundary

A completed and independently audited R50
aggregate may describe interval inclusion
in the 24 original independent blocks per
leverage stratum, quantile sensitivity and
numeric refusal rates. **24 blocks cannot
qualify nominal 90% pointwise inference**.
The wrong-family fit is a prespecified
sensitivity comparison, not an automatic
model-selection outcome.

Keep blockers
[#289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289)
and [#296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296)
open; no public API, release tag, protected-main
merge, PyPI upload or simultaneous-band claim.
