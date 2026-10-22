# W3 R94/R94-A — original and independent exact floor sensitivity evidence

**Study boundary:** binary bounded originally missing stratum, exact observable masses, known randomized audit invitation, hypothesized EXTERNAL lower response-probability guarantees. Neither an empirical study nor an estimator qualifying real MNAR gaze or whole-grid 90% bands.

## Original exact proof (research DRAFT; not merged)

| Field | Immutable source |
|---|---|
| Original research PR | [#459](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/459) |
| Source head SHA | 142d63a551d0e61d776f3b604b5d3cd865b0c2e7 |
| Original GitHub Actions science | [#39863137968](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39863137968), 4/4 jobs PASS |
| Original immutable archive | [Artifact #12461918445](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39863137968/artifacts/12461918445), name: w3-r94-exact-floors-54-record-original-archive |
| Original archived members | r94_exact_evidence.json; SHA256SUMS |
| Dataset size | 54 **mathematical cases** = 3 nonreturn rates × 3 known invitation probabilities × 6 hypothetical floor assumptions |
| Identified set | For $p=P(Z=1)$, $L=\max\{q_1,1-q_0/\ell_0\}$, $U=\min\{1-q_0,q_1/\ell_1\}$; ratio terms omitted at zero floor |
| Status | Research-only; production_release_ready=false; no package public API, tag, or PyPI change |

Original source contracts explicitly reject missing/tampered factorial evidence and demonstrate exact endpoint models at all feasible intervals. The original archive includes all 9 incompatible cells rather than silently excluding them.

## Independent exact rederivation (research DRAFT; not merged)

| Field | Immutable audit evidence |
|---|---|
| Separate auditor PR | [#460](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/460), stacked on #459 |
| Audit source SHA | ff6d8ec2a77452e79a1c6f041e3609996a9be908 |
| Dedicated R94-A workflow | [#39863696029](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39863696029), 4/4 jobs PASS |
| Independent archive | [Artifact #12462204809](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39863696029/artifacts/12462204809), name: w3-r94-A-independent-original-54-case-audit |
| Dependency gate | Three separate Python version contract jobs plus mandatory download and full replay of the **actual original source archive**, validating original SHA256SUMS |
| Independent mathematics | Allocate unreturned binary $Z=1$ mass $t$ and $Z=0$ mass $\delta-t$; derive bounds on $t$ without importing original R94 code |
| Complete replay | 54/54 original archived cell records, 45 feasible endpoint-witness sets and 9 incompatible external assumptions |
| Status | Independent mathematical/source verification, not empirical calibration |

The auditor independently reconstructs every original denominator, exact rational lower/upper, endpoint completion law, boolean guardrail and nonreturn count. It refuses incomplete archives, duplicates, noncanonical fractions, invalid hashes, unexpected fields and missing case combinations.

## Figure-to-source ledger

| Documentation figure | Source evidence | Denominator |
|---|---|---|
| [Exact 99% return assumption ladder](../assets/w3-r94-sharp-interval-assumption-ladder.svg) | δ=1/100, six prespecified floors and exact sharp bounds, R94 original verified by R94-A | Six deterministic assumption regimes; no simulation |
| [Width by return fraction](../assets/w3-r94-sharp-widths-by-return.svg) | δ=1/1000,1/100,1/20 and exact common/moderate/asymmetric/strong widths | Three fixed δ values × four illustrated floor assumptions; not independent replications |

The SVGs display exact-source-derived sharp population sets/widths with rounded labels for readability. They are **not** 90% intervals, Monte Carlo uncertainty bars or estimates of real eye-tracker quality.

## Scientific limitations and release restrictions

The crucial external lower completion floors are hypothetically imposed: they are not identified by random invitation alone and must not be passed off as measured return propensities. A strong floor equal to the observed overall return probability forces uniform completion *in this symmetric binary special case*, not in arbitrary field data.

No claim is made for arbitrary functional response mechanisms, real raw-missing gaze recovery, point estimation without those assumptions, finite-sample confidence regions, 90% function-wide W3 slope bands, empirical statistical calibration, public API qualification or v1.2 release.

Keep research PRs #459 and #460 draft/unmerged; issues [#289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289) and [#296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296) OPEN. Stable 1.1.0 and no GitHub/PyPI release unchanged. Publication of these **documentation-only** pages is gated on full exact-head CI and a separately successful protected-main Pages build/deploy.
