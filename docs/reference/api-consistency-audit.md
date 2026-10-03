# Post-0.12 public API consistency audit

This audit is the first tranche of the **post-0.12 product-observation and
1.0-readiness programme**. It is deliberately conservative: inventory first,
real-use evidence second, and only then a decision about what deserves a 1.0
stability promise.

The published `0.12.0` scientific release is closed. The active source line is
`0.12.1.dev0`; this page does **not** imply a `0.13` estimator programme and it
does not authorize namespace surgery.

## Machine-checked inventory

`PUBLIC_API_1_0_AUDIT.json` records the review policy. The exhaustive installed
inventory is generated from the exact package `__all__` surface with:

```bash
python scripts/audit_public_api_surface.py \
  --output build/public-api-1.0-audit.json
```

The audit fails closed when:

- `__all__` contains duplicate names;
- a public reporting helper violates the `*_reporting_text` convention;
- a public `_frame` name does not use the `*_frame` suffix;
- an explicit stability override refers to a non-public symbol; or
- the deterministic gallery manifest differs from the callable public
  `plot_*` surface.

The generated JSON contains every public export, its naming family, its current
**review posture**, workflow roles, exact callable/class identity aliases, and
summary counts. A review posture is not a stability guarantee.

## Review postures

The current audit distinguishes:

- **canonical candidate** — recommended workflow entry points and their
  canonical bootstrap/reporting companions;
- **supported candidate** — supported public functionality that still needs a
  deliberate 1.0 decision;
- **diagnostic candidate** — sensitivity, audit, recovery, validation, or
  diagnostic functionality that must not become a silent model-selection
  oracle;
- **experimental** — supported with a narrower interpretation/validation
  boundary and no 1.0 promise yet;
- **compatibility** — an intentionally retained backend-specific or migration
  route rather than an accidental duplicate;
- **reproducibility** — environment and portable-result infrastructure; and
- **result-object candidate** — a public `*Result` schema that must be assessed
  before promising long-term compatibility.

Unclassified public APIs default to **supported candidate**, not stable. This
is intentional: 1.0 stability is something the project will opt into after
product observation, not something inferred from age or test coverage.

## Naming conventions under review

The forward conventions remain:

| Scientific role | Convention |
|---|---|
| estimator | `fit_*` |
| genuine bootstrap | `bootstrap_*` |
| plotting helper | `plot_*` |
| tidy/tabular extractor | `*_frame` |
| manuscript wording | `*_reporting_text` |
| stochastic control | `random_state` |
| interval level | `confidence_level` |
| analysis result container | descriptive `*Result` class |

Historical descriptive APIs such as `recurrence_matrix()`, `rqa_metrics()`,
`dynamic_time_warping_distance()`, `register_to_landmarks()` and
`summarise_fpca()` are not renamed merely to force prefix uniformity.

## Parallel routes are not automatically duplicates

The audit explicitly records two scientifically meaningful pairs:

1. `fit_sparse_fpca()` versus `fit_sparse_fpca_fdapy()` — native sparse PACE
   versus the explicit FDApy compatibility backend;
2. `fit_mfpca()` versus `fit_sparse_mfpca()` — common-grid multivariate FDA
   versus native paired sparse/irregular planar FDA.

Neither pair is a deprecation candidate simply because both routes exist.
Exact Python-object aliases are nevertheless reported in the generated audit
so accidental compatibility names can be reviewed rather than guessed.

## Result objects and serialization

Public result objects are part of the 1.0 review surface. Their long-term
contract is wider than field names: units, array orientation, identifiers,
diagnostics, failure/status fields and provenance all matter.

Portable serialization remains intentionally distinct from pickling. The
portable-result layer stores scientific arrays, identifiers, specifications,
units, diagnostics and provenance in an explicit JSON + NPZ bundle. Opaque
backend-native fields are disclosed through `nonportable_fields`; the project
must not silently pretend they were serialized.

The real-use tranche will test whether the dense and sparse-planar result
objects survive the actual path from fitted analysis through frames, reporting,
figures and portable export/load without repository-only knowledge.

## Failure semantics

The candidate 1.0 rule remains **explicit failure or explicit status rather
than silent scientific repair**. In particular, public workflows should not
silently:

- interpolate raw sparse trajectories merely to satisfy a common-grid method;
- replace missing observations with zero;
- choose a model, family, covariance structure or sensitivity winner;
- infer grouped-binomial denominators or Poisson exposure;
- discard failed bootstrap refits;
- reinterpret participant/trial independence; or
- hide nonportable scientific state during serialization.

Whether every existing API obeys this consistently is an observation target,
not assumed by this document.

## Plotting policy

The documentation contract is one-way:

$$
\text{public plot API}
\Rightarrow
\text{one deterministic documented gallery case}.
$$

The converse is **not** a requirement. A result object does not acquire a new
plotting helper merely to make the namespace visually symmetric. This prevents
1.0-readiness work from becoming another source of API inflation.

## Deprecation and removal decision

At this tranche:

- **deprecation candidates: none authorized**;
- **removal candidates: none authorized**;
- **1.0 compatibility promise: not yet active**.

Any later inconsistency selected for correction requires an individual
migration record containing the current public name/signature, replacement,
warning/alias behavior, first deprecated version, earliest removal version and
affected docs/examples/tests.

## What comes next

This inventory is intentionally not the final decision. The next evidence is
external-researcher-style use of both the dense/common-grid and sparse planar
paths. Friction found there may justify targeted corrections. Absence of
friction is evidence for stability. Either outcome is more informative than
renaming APIs from a static namespace inspection alone.
