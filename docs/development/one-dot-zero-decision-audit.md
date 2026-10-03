# 1.0 decision audit

The post-0.12 programme asked a narrower question than “what should version
0.13 contain?”:

> After observing the package as a product, is there a demonstrated scientific
> omission that should prevent the project from entering 1.0 stabilization?

The evidence-based answer is **no**.

This is not a 1.0 release announcement and it does not activate a blanket
compatibility guarantee. It means the completed evidence does not justify
adding another estimator merely to make the package feel more complete.

## Programme state

$$
\boxed{
0.12.0\ \text{scientific release closed}
\rightarrow
\text{documentation modernization closed}
\rightarrow
\text{public-surface audit}
\rightarrow
\text{real-use observation}
\rightarrow
\text{reproducibility evidence}
\rightarrow
\text{1.0 stabilization decision}
}
$$

The machine-readable decision is `ONE_DOT_ZERO_DECISION.json`.

## Evidence considered

### Public surface

The post-0.12 API audit inventories the installed public namespace rather than
assuming that old code is automatically stable. At the decision point it
contains **458 public exports** and **77 public `plot_*` APIs**. The plotting
surface remains exactly covered by the deterministic documentation gallery.

The audit deliberately authorized **no deprecations and no removals**. Public
objects were assigned review postures rather than automatically receiving a 1.0
promise. Native and compatibility sparse-FPCA routes, and common-grid versus
native sparse MFPCA routes, remain scientifically distinct rather than being
classified as duplicates merely because their names are related.

### Dense/common-grid product observation

The dense route started from a realistic deterministic long-format gaze
surrogate and used top-level public APIs only:

```text
long data
  -> from_long_dataframe()
  -> fit_mfpca()
  -> fpca_score_frame()
  -> fpca_reporting_text()
  -> plot_fpca_component()
  -> export_portable_result()
  -> load_portable_result()
```

The observation covered 56 curves on 81 common time points and retained three
components. A deliberately corrupted curve no longer sharing the declared
common grid failed explicitly with a `ValueError`; the package did not silently
interpolate it.

The portable snapshot also exposed an important boundary correctly: the dense
`FPCAResult` backend model is listed as `result.model` in
`nonportable_fields`. Scientific portability therefore does not pretend that
an opaque backend object was serialized.

### Native sparse planar product observation

The sparse route likewise began from long-format paired x/y samples and used
only public APIs:

```text
native sparse paired x/y data
  -> from_irregular_long_dataframe_native()
  -> fit_sparse_mfpca()
  -> sparse_mfpca_score_frame()
  -> sparse_mfpca_reporting_text()
  -> plot_sparse_mfpca_*()
  -> export_portable_result()
  -> load_portable_result()
```

It covered 36 curves with 9–14 native observations per curve. All 36 joint-PACE
systems reported `ok`, all retained scores were finite, raw sparse samples were
not pre-interpolated, and the observed `SparseMFPCAResult` had no nonportable
fields.

### Reproducibility case study

The sparse-planar observation was then frozen as the canonical
`case_studies/sparse_mfpca_0_12` reproducibility object. It records the exact
input SHA-256, reference environment, product-observation workflow provenance,
public commands, expected scientific invariants, reporting text and three
manuscript-oriented figures.

The case study verifies scientific invariants rather than brittle byte identity
for floating-point outputs. Reference eigenvalues use declared tolerances; SVG
existence is checked without treating SVG bytes as a numerical oracle.

## Decision

The observed evidence supports all of the following conclusions:

1. **No new estimator is currently required before 1.0.** The dense/common-grid
   and native sparse-planar flagship paths both work end to end through public
   interfaces, diagnostics, reporting, figures and portable-result handling.
2. **Sparse hierarchical participant/trial FDA remains a future research
   candidate, not a demonstrated blocker.** It should enter the package only if
   a real scientific use case establishes a distinct estimand and a recovery /
   validation programme strong enough to justify expanding the stable surface.
3. **API stability is now the main 1.0 problem.** The namespace is large enough
   that a stability promise must be explicit. Test coverage, age and naming
   symmetry are not substitutes for deciding what the project is willing to
   preserve.
4. **The plotting rule remains one-way.** Every public plotting API must have a
   deterministic documented figure. Nothing in the 1.0 programme requires a
   plot for every result object.

Accordingly, the project is ready to **begin 1.0 stabilization**, but it is not
yet ready to publish 1.0.

## What remains before a literal 1.0 release

Before a production 1.0 publication, the project should:

- define and freeze the explicit stability boundary, including treatment of
  experimental and compatibility APIs;
- resolve only those deprecations that are deliberately selected, with a
  documented migration window;
- qualify a release candidate under a literal 1.0 version identity rather than
  relabelling earlier 0.12 evidence;
- install and exercise that candidate outside the repository checkout; and
- use the existing fail-closed release-governance process for final promotion.

Those are stabilization and release-governance tasks. They are not a mandate
for another methodology tranche.

## Limitation of the current product observation

Both end-to-end product observations use deterministic realistic synthetic gaze
surrogates. That makes the evidence fully redistributable and reproducible, but
it is not evidence about a particular empirical human population and it does
not reproduce every form of instrument/export irregularity found in field
data.

An independently licensed empirical dataset would therefore be a useful
**non-blocking** follow-up observation when redistribution and consent terms
permit. It should be used to discover product friction, not as a reason to
delay 1.0 automatically if the scientific/API contract is otherwise ready.
