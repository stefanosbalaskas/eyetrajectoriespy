# W3 R63 — prospectively frozen 128-independent-source fitted-null Gaussian replication

**Research only. R63 is an independent source-level null-size replication, NOT a qualified 5% boundary test, inferential power study, empirical gaze-data model, 90% pointwise interval or simultaneous-band qualification.**

## R62 evidence and scientific motivation

The original R62 complete fitted-H0 Gaussian null bootstrap at
[PR #374](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/374)
passed **10/10 original dedicated scientific jobs**. All 32 independent
primitive blocks, 64 paired source cases, 4,032 bootstrap H0/H1 refits
and 24,576 optimizer starts were present and numerically accepted.
For ordinary and extreme leverage, the frozen conditional
bootstrap test rejected **2/32 = 6.25%** each, with very broad 95%
Wilson Monte Carlo intervals **1.73–20.15%**. The unchanged
classical candidate rejected **3/32 = 9.375%** each. Paired
bootstrap rejection counts were ordinary-only 2, extreme-only 2,
both 0, neither 28. Neither method is thereby calibrated.

Crucially, [R62-A independent audit PR #375](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/375)
passed **all four independent audit workflow jobs**, including
actual original-archive reconstruction, at
[GitHub Actions run #39093391808](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39093391808).
All three archived SHA256 entries and 64 source/4032 bootstrap/8192
nested fit/24576 start identities were reconstructed independently.
The largest selected physical projected KKT was ~0.000639,
below the original prespecified 0.001 numerical threshold.
This validates provenance and numerical reporting, not a true-null
probability law.

R63 independently increases the outer source count **fourfold**
without changing the method after observing the R62 outcomes.
Its *newly seeded independent data* constitute another exploratory
simulation replication, rather than retesting the archived R62
source blocks.

## Frozen generating and inferential design

- **128 NEW independent structural-zero Gaussian primitive generating
  blocks**, source seed `202610186363`, bootstrap-draw seed
  `202610186364`, both disjoint from R57–R62. Each block contains
  **24 participants** and two **paired** ordinary/extreme
  predictor-leverage source conditions, both with the original
  dependent covariance generator. The 256 source/support cases
  represent 128 independent units per leverage condition—not
  256 independent Bernoulli draws.
- Identical R57 **exact-zero H0** versus nested **nonnegative H1**
  Gaussian REML working family and prespecified optimization gates:
  two original H0 and four H1 starts per nested comparison; no
  post-study threshold changes; positive physical component bounds,
  original physical projected KKT ≤0.001, within-start likelihood
  reconstruction ≤1e−6 and original near-best objective tolerance ≤0.001.
  Failed fits are permanent, recorded refusals.
- For each accepted observed original H0/H1 comparison, generate
  **63 independent fitted-H0 Gaussian responses from observed-only
  nuisance estimates and GLS mean** on the unchanged native
  irregular X, positive weights, participant groups, trials
  and timestamps. Refitting H0 and H1 and their nuisance
  covariance on every draw is mandatory.
- Prespecified conditional bootstrap rank p-value
  `(1 + count(bootstrap_LRT >= observed_LRT))/64`,
  only if **all 63** nested bootstrap fits are accepted.
  At nominal 5%, only p values ≤ 3/64 = 0.046875 reject.
  Retain the unchanged classical 50:50 mixture candidate,
  `T > 2.70554345409542`, for a **paired descriptive**
  benchmark, with no post-R62 tuning or model selection.
- **No other effects/samples**: there are no positive-variance
  generating scenarios, independent-null validation beyond
  this Gaussian source, real participants, missingness/MNAR
  corrections, physiological errors, or simultaneous bands.

## Frozen denominators and computability gate

| Item | Prespecified total |
|---|---:|
| Genuinely independent Gaussian primitive blocks | **128** |
| Paired source/support cases | **256** |
| Gaussian null-bootstrap refit attempts | **16,128** |
| Nested H0/H1 model-fit positions (observed + bootstrap) | **32,768** |
| Individual optimizer start positions | **98,304** |
| Independent deterministic shards | **32** (four primitive blocks per shard) |

The source runner writes **all** original and attempted/failed
bootstrap records. The whole-case numerical ledger retains
full 63-draw source completeness and reports every refusal.
Each shard has a source checkout SHA and SHA256 case digest.
The aggregator **fails closed** on any missing, wrong, duplicate,
tampered or mixed-checkout shard. A structurally complete
failure-inclusive original source ledger is distinct from
numerically successful fits.

Report ordinary and extreme rejection numerators, **128-block
source-level** Wilson 95% Monte Carlo intervals (complete-source
conditional and all-source refusal-inclusive bounds),
classical-candidate rejection counts, the paired rejection
2×2 table and any refusal/floor/numerical KKT diagnostics.
Use no sequential efficacy or significance stopping rule and
no Monte Carlo estimates from partial shards.

## Qualification boundaries

Under a 5% true-null rate, the binomial Monte Carlo standard
error from 128 outer blocks is approximately 1.93 percentage
points; its two-sided 95% uncertainty remains several
percentage points wide. The second replication materially
improves R62 precision but still **cannot certify a universal
5% test or rule out modest size distortions**.

Fitted-null Gaussian generation, nested REML convergence and
a valid p-value under estimated covariance are distinct
scientific properties. The simulation tests one prespecified
Gaussian design at n24, with original complete observations,
and no positive-variance power. Future validation would need
other sample sizes, covariance misspecification, boundary
component regimes, larger independent-source Monte Carlo
precision and separate real-data applicability studies.

Keep scientific blockers
[#289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289)
and [#296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296)
OPEN. No supported public inference API, protected-main
merge, stable 1.2 tag, PyPI/TestPyPI, or release approval.

**Frozen before any original R63 outcomes are available.**
