---
title: External reference implementation policy
---

# External reference implementation policy

External scientific libraries are valuable to eyetrajectoriespy as
**independent validation references**. They are not automatically appropriate
runtime dependencies.

## Principle

$$
\text{study concepts and architecture}
\neq
\text{depend on an external implementation}.
$$

A mature library may motivate an algorithm, diagnostic, simulation design, or
validation target. The eyetrajectoriespy implementation must still be specified
from the scientific method and independently tested.

## FDApy

FDApy currently has two roles:

1. a public, explicitly backend-named sparse/PACE compatibility path through
   `fit_sparse_fpca_fdapy()`;
2. an external numerical reference/sensitivity comparator for the native 0.10 sparse
   FPCA/PACE implementation.

It is **not** a core dependency. The canonical 0.10 estimator does not call
FDApy internally.

The existing optional wrapper is retained during the transition because it is
already public and qualified. Removal or deprecation can happen only after the
native path is validated and the normal deprecation window is satisfied.

## bayesFPCA

`bayesFPCA` is used only as a **post-1.1 external scientific comparator** for
sparse/irregular univariate and multivariate FPCA. The dedicated validation
workflow pins the exact upstream Git commit and exchanges only neutral
CSV/JSON fixtures and evidence files.

`bayesFPCA` is GPL >= 3. It is therefore not copied, translated, vendored,
imported by the Python package, or added as a runtime backend/dependency.
Any future native Bayesian method would require an independently specified
mathematical and software contract rather than a source-code port.

The comparator is especially useful because its variational latent-basis
architecture differs from the native covariance/PACE route. Comparisons use
known truth, invariant functional/score subspaces and reconstruction targets;
they do not assume coefficient-level numerical equivalence or choose an
architecture winner automatically.

## What counts as independent validation?

A reference comparison should document:

- the external package and exact version;
- the scientific quantity being compared;
- matched preprocessing and observation support;
- matched smoothing/model specifications where possible;
- component sign/order alignment rules;
- numerical tolerances and their justification;
- known non-equivalences between the two implementations.

Agreement is not assumed merely because two functions share a method name.

## Evidence hierarchy

Reference-library agreement is one evidence type, not the final authority.
Validation should combine:

1. analytical or controlled truth;
2. simulation recovery;
3. independent implementation equivalence;
4. domain-specific failure-case tests.

When evidence conflicts, the discrepancy is investigated rather than resolved
by automatically preferring the external library.

## Runtime dependency boundary

General-purpose scientific libraries may remain optional interoperability
layers when they provide a distinct specialist capability. They should not
enter the core dependency list merely because they are convenient development
references.

For FDApy specifically, the target direction is:

```text
optional runtime compatibility today
        ↓
independent development/validation comparator
        ↓
no requirement for canonical native sparse FPCA/PACE
```

This policy does not require immediate removal of the current `sparse` extra.
