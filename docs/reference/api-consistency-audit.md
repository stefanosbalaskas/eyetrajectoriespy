# Post-0.12 public API consistency audit

!!! note "Historical stabilization evidence"
    This page records the conservative audit that preceded the frozen 1.0 compatibility boundary. Final `1.0.0` is now published; the active compatibility policy is the [API stability and hierarchy](api-stability.md) page.

This audit was the first tranche of the **post-0.12 product-observation and 1.0-readiness programme**: inventory first, real-use evidence second, and only then a decision about what deserved a 1.0 stability promise.

The published `0.12.0` scientific release remained immutable throughout that work. The audit did **not** imply a `0.13` estimator programme and did not authorize namespace surgery. Its results fed the later frozen 1.0 contract and final `1.0.0` release.

## Machine-checked inventory

`PUBLIC_API_1_0_AUDIT.json` records the review policy. The exhaustive installed inventory is generated from the exact package `__all__` surface with:

```bash
python scripts/audit_public_api_surface.py \
  --output build/public-api-1.0-audit.json
```

The audit fails closed when:

- `__all__` contains duplicate names;
- a public reporting helper violates the `*_reporting_text` convention;
- a public `_frame` name does not use the `*_frame` suffix;
- an explicit stability override refers to a non-public symbol; or
- the deterministic gallery manifest differs from the callable public `plot_*` surface.

The generated JSON contains every public export, its naming family, its review posture, workflow roles, exact callable/class identity aliases, and summary counts. At the time of this audit, a review posture was intentionally not yet a stability guarantee.

## Review postures used by the audit

The audit distinguished:

- **canonical candidate** — recommended workflow entry points and their canonical bootstrap/reporting companions;
- **supported candidate** — supported public functionality still awaiting a deliberate 1.0 decision;
- **diagnostic candidate** — sensitivity, audit, recovery, validation, or diagnostic functionality that must not become a silent model-selection oracle;
- **experimental** — supported with a narrower interpretation/validation boundary and no 1.0 promise;
- **compatibility** — an intentionally retained backend-specific or migration route rather than an accidental duplicate;
- **reproducibility** — environment and portable-result infrastructure; and
- **result-object candidate** — a public `*Result` schema assessed before promising long-term compatibility.

Unclassified public APIs defaulted to **supported candidate**, not stable. This was intentional: 1.0 stability was something the project opted into only after product observation rather than something inferred from age or test coverage.

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

Historical descriptive APIs such as `recurrence_matrix()`, `rqa_metrics()`, `dynamic_time_warping_distance()`, `register_to_landmarks()` and `summarise_fpca()` were not renamed merely to force prefix uniformity.

## Parallel routes are not automatically duplicates

The audit explicitly recorded two scientifically meaningful pairs:

1. `fit_sparse_fpca()` versus `fit_sparse_fpca_fdapy()` — native sparse PACE versus the explicit FDApy compatibility backend;
2. `fit_mfpca()` versus `fit_sparse_mfpca()` — common-grid multivariate FDA versus native paired sparse/irregular planar FDA.

Neither pair became a deprecation candidate simply because both routes exist. Exact Python-object aliases are nevertheless reported in the generated audit so accidental compatibility names can be reviewed rather than guessed.

## Result objects and serialization

Public result objects were part of the 1.0 review surface. Their long-term contract is wider than field names: units, array orientation, identifiers, diagnostics, failure/status fields and provenance all matter.

Portable serialization remains intentionally distinct from pickling. The portable-result layer stores scientific arrays, identifiers, specifications, units, diagnostics and provenance in an explicit JSON + NPZ bundle. Opaque backend-native fields are disclosed through `nonportable_fields`; the project must not silently pretend they were serialized.

The later real-use tranche tested whether dense and sparse-planar result objects survived the actual path from fitted analysis through frames, reporting, figures and portable export/load without repository-only knowledge. That evidence contributed to the final 1.0 freeze.

## Failure semantics

The candidate 1.0 rule was **explicit failure or explicit status rather than silent scientific repair**. That rule remains part of the stable 1.x policy. In particular, public workflows should not silently:

- interpolate raw sparse trajectories merely to satisfy a common-grid method;
- replace missing observations with zero;
- choose a model, family, covariance structure or sensitivity winner;
- infer grouped-binomial denominators or Poisson exposure;
- discard failed bootstrap refits;
- reinterpret participant/trial independence; or
- hide nonportable scientific state during serialization.

## Plotting policy

The documentation contract remains one-way:

$$
\text{public plot API}
\Rightarrow
\text{one deterministic documented gallery case}.
$$

The converse is **not** a requirement. A result object does not acquire a new plotting helper merely to make the namespace visually symmetric. This prevents stability work from becoming another source of API inflation.

## Deprecation and removal outcome

The audit authorized:

- **deprecation candidates: none**;
- **removal candidates: none**.

Subsequent product observation, reproducibility work and explicit contract generation supported a stable 1.0 boundary of 455 stable exports plus three explicitly experimental exports. Final `1.0.0` activated that compatibility promise.

Any future inconsistency selected for correction requires an individual migration record containing the current public name/signature, replacement, warning/alias behavior, first deprecated version, earliest removal version and affected docs/examples/tests.

## Outcome

The inventory was intentionally not the final decision. It was followed by external-researcher-style product observation, reproducibility evidence, the machine-readable 1.0 contract, literal `1.0.0rc1` qualification/production observation, and final `1.0.0` qualification/publication.

The current policy is therefore no longer “observe before promising stability”; it is **preserve the stable 1.0 boundary and require explicit governance for any change to it**.
