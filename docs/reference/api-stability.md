# API stability and hierarchy

Version 0.55 begins a stabilization line. It does **not** redesign the public
namespace and does not remove existing scientific APIs.

## Public API levels

### Canonical

Recommended default entry points for common scientific questions. The five
canonical routes are declared in `CANONICAL_WORKFLOWS.json` and documented in
the [canonical workflow guide](../workflows/index.md).

### Advanced

Supported and tested APIs for a more specific scientific need after the
canonical route is understood. Examples include sparse PACE FPCA, phase
analysis, full-refit mixed-effects bootstrap and exposure-aware generalized
prediction.

### Diagnostic

Inspection, sensitivity and audit APIs. They expose consequences of declared
choices but must not silently select the preferred model/specification.
Examples include covariance sensitivity, residual diagnostics and RQA
parameter sensitivity.

### Experimental

Supported code with a narrower validation or interpretation boundary. Examples
include empirical return-map stability and transfer-entropy extensions. The
experimental label is not permission to weaken tests; it is an interpretation
warning.

## Naming conventions for new APIs

New public APIs should follow these conventions unless a scientific object
requires a clearer domain name:

- estimators: `fit_*`;
- resampling procedures: `bootstrap_*` when the operation is genuinely a
  bootstrap;
- plotting helpers: `plot_*`;
- tidy/tabular extractors: `*_frame`;
- manuscript wording: `*_reporting_text`;
- stochastic control: `random_state`;
- interval level: `confidence_level`;
- hierarchy identifiers: `participant_column` and `trial_column` where
  those concepts apply;
- result containers: descriptive CamelCase names ending in `Result` when the
  object represents the result of an analysis rather than a data container.

These are forward conventions, not grounds for mass-renaming established APIs.

## 0.55 compatibility decision

No public statistical function is renamed or removed in 0.55. Historical names
that do not perfectly match the conventions above remain available. The
package first establishes canonical routes and documentation hierarchy.

A future rename must:

1. introduce the canonical name before removing the historical name;
2. keep an explicit compatibility alias during the deprecation window where
   technically possible;
3. emit a targeted `DeprecationWarning` that names the replacement;
4. update examples, mathematical contracts and reporting documentation in the
   same change;
5. document the earliest eligible removal release.

## Deprecation window

Before 1.0, a public API scheduled for removal should remain available for at
least **two subsequent minor development releases** after the replacement is
introduced, unless retaining it would cause incorrect scientific results or a
security defect. Scientific-correctness exceptions must be documented
explicitly.

Concrete example: if a replacement is introduced and the historical API is
first deprecated in **0.55**, the deprecated API remains available throughout
**0.56** and **0.57**. The earliest ordinary removal release is therefore
**0.58**. A release counts for this clock when that minor development version
is merged to `main`; patch-only documentation corrections do not advance the
clock.

Deprecation is not an excuse to reinterpret an existing result object silently.
Changes to estimands, units, resampling units, clustering, denominator/exposure
semantics or uncertainty definitions require a new explicit contract.

## Argument consistency

0.55 audits but does not globally reorder historical signatures. New APIs
should keep required scientific objects positional only when their meaning is
unambiguous and place analysis choices behind keyword-only arguments where
possible.

Existing defaults remain unchanged unless a documented correctness issue
requires otherwise.

## Failure semantics

Canonical workflows prefer explicit failure to silent repair. In particular,
the package should not silently:

- interpolate or convert missing values to zero;
- choose a model, family, correlation structure or sensitivity winner;
- infer grouped-binomial denominators or Poisson exposure;
- drop failed bootstrap refits;
- reinterpret participant/trial independence;
- clip scientifically meaningful uncertainty merely to satisfy physical bounds.

The full public surface remains in the [API reference](api.md); the exhaustive
capability list is separate from the recommended entry paths.
