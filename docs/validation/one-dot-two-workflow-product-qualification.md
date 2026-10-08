# 1.2 workflow product qualification

The 1.2 workflow release is qualified as an orchestration/product layer rather
than as a new estimator programme. Scientific estimators composed by the
workflows retain their earlier recovery, calibration, comparator and
method-specific validation evidence.

## Qualification design

The workflow programme is gated in four tranches:

1. **W1 — infrastructure:** immutable configuration/result contracts, ordered
   step records, decision provenance, strict serialization and portable bundle
   export.
2. **W2 — sparse workflows:** sparse FPCA, paired/asynchronous sparse MFPCA,
   sparse multilevel decomposition and sparse prediction.
3. **W3 — dense/regression workflows:** common-grid FPCA, function-on-scalar,
   functional mixed effects and generalized functional regression.
4. **W4 — product qualification:** recurrence orchestration, explicit workflow
   plotting, documentation/gallery integration, installed-wheel product
   analyses, performance envelope and final workflow API audit.

Each tranche must qualify on its pull-request head and then again on the exact
protected-`main` merge commit before the next tranche begins.

## Installed-package evidence

`scripts/run_one_dot_two_workflow_product_qualification.py` runs from an
installed wheel outside the source checkout and exercises all ten workflow
entry points on deterministic realistic synthetic eye-tracking fixtures.

The fixtures are **not empirical human observations** and are not used as
known-truth recovery simulators. Their purpose is product integration: input →
typed workflow → primitive result → audit records → reporting/tables → figures
and reproducibility bundles.

The retained evidence includes:

- a summary for every workflow contract;
- decision and ordered-step tables;
- generic workflow reporting;
- representative dense, sparse and recurrence reproducibility bundles;
- canonical workflow-generated figures;
- runtime measurements;
- a friction ledger with release-blocking status.

## Performance envelope

The CI envelope is deliberately broad. It guards against accidental product
regressions rather than claiming benchmark performance:

- all ten workflows together must complete within 120 seconds on the
  qualification runner;
- no single workflow route may exceed 60 seconds.

Dedicated estimator/performance workflows remain authoritative for
method-specific computational claims.

## API audit

`WORKFLOW_API_AUDIT.json` freezes the candidate 1.2 module surface and
scientific policies. `scripts/validate_workflow_api_audit.py` requires exact
agreement with `eyetrajectoriespy.workflows.__all__` and rejects accidental
root-namespace promotion.

The 1.2 candidate therefore keeps workflow APIs under
`eyetrajectoriespy.workflows`; the established package root is not expanded by
this release.

## Release interpretation

Passing this qualification means that the supported workflows can be executed
from an installed distribution with their declared scientific decisions,
primitive outputs, reporting and provenance intact. It does not establish that
one estimator architecture is superior to another and it does not relax any
method-specific uncertainty or interpretation limitation.
