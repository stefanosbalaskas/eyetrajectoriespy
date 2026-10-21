# W3 R88 / R88-A — original and independent source evidence ledger

**Scope:** research-only conditional sensitivity of fitted selection coefficients under selectively returned randomized gaze audits. No released package changes, no general MNAR identification, and no 90%-band calibration claim.

## Frozen original evidence

| Property | Verified source |
|---|---|
| Original prospective research | [Draft PR #441](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/441) |
| Original exact-head scientific Actions run | [#39672709750](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39672709750) |
| Dedicated source/contract/aggregation CI | **12/12 successful** |
| Immutable original full 32-block archive | [Artifact #12381046538](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39672709750/artifacts/12381046538) |
| GitHub artifact ZIP digest (not the internal members) | `sha256:7d0078299e0bb39788af29bc52c541ffa6b38969dcbd94774cf6bdc22592da38` |
| Frozen original GitHub PR science checkout | `194d00a14ac35b85cf25864ed5e099d0c7ffb02c` |
| Original source conditions | 64 independent complete X/Y conditions |
| Missingness conditions | 128 source MAR/MNAR masks |
| Repeated source × method records | 1,024 |
| Original source artifact members | `cases.json`, `summary.json`, `source-commit.txt`, `SHA256SUMS` |

Eight four-block simulation shards and the three Python-version source contracts were mandatory predecessors of the original final SHA256 aggregate. Zero rows were dropped to produce the reported group means. R88 does not report cluster-valid uncertainty intervals or a formally estimated identified set.

## Frozen independent numerical audit

| Property | Verified source |
|---|---|
| Independent reconstruction research | [Draft PR #442](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/442) |
| Independent scientific workflow | [#39674304705](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39674304705) |
| Three-version contracts and actual original archive replay | **4/4 successful** |
| Separate R88-A audit evidence | [Artifact #12380982844](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39674304705/artifacts/12380982844) |
| Independent artifact ZIP digest | `sha256:7e3b277016f4e8d48e4a7164e5904161969e76fb7b859322ab44c0b8e6e6e387` |

The independent script imports neither original R87/R88 source estimators nor the production package. It recreates the frozen source X/Y, covariance and repeated-trial process, first-stage observation masks, secondary-recovery and third-stage randomization/return, and all recorded original 1,024 coefficients and refusals. It re-estimates the secondary selection model using SciPy score roots and the first-stage δ by a separate Newton solver. It recomputes original cell summaries and strictly verifies original SHA256 members and fixed checkout.

The first R88-A test attempt failed solely because an inherited error message said R87-A; the failure was retained and the label/fixture was corrected before the successful exact-head 4/4 replay. This is a transparently recorded engineering correction, not a scientific estimator change.

## Original evidence contrasts (25% audit fraction)

| First-stage mechanism | Native source | Assumed γ=0 | γ=0.675 | γ=1.35 | γ=2.025 | True δ |
|---|---|---:|---:|---:|---:|---:|
| MAR | Curves | +0.2859 | +0.1563 | +0.0066 | −0.1890 | 0 |
| MAR | Participants | +0.3207 | +0.1837 | +0.0225 | −0.1991 | 0 |
| MNAR | Curves | +1.2174 | +1.1092 | +1.0147 | +0.9155 | 1.1 |
| MNAR | Participants | +1.2117 | +1.0924 | +0.9892 | +0.8759 | 1.1 |

Every displayed estimate is an unweighted arithmetic average of 32 source-level fitted δ values, **not** an individual gaze-record mean or formal coverage estimate. The four γ scenarios reweight the same observed returns; they do not represent four independent synthetic source cohorts. The true γ=1.35 is privileged *simulation knowledge*.

## Figures and publication gate

The documentation-only website branch contains two source-derived SVG visualizations, [R88 selection sensitivity](../assets/w3-r88-assumed-gamma-sensitivity.svg) and [actual audit yield](../assets/w3-r88-audit-return-yield.svg). The [research article](../articles/w3-r88-return-audit-sensitivity.md) and [methods companion](../articles/reading-assumed-audit-return-sensitivity.md) preserve the design's scope.

The original research source PRs remain draft. Documentation publication requires its own strict exact-head docs and general checks, followed by a successful protected-main GitHub Pages deployment; source code/release remains excluded. Independently implemented numerical reconstruction does **not** establish historical gaze recovery, identifiable outcome-dependent return coefficients, 90% simultaneous-band coverage, or release readiness.

Keep [#289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289) and [#296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296) OPEN. Public 1.1.0 and API are unchanged. **Version 1.2 / GitHub Release / PyPI = HOLD.**
