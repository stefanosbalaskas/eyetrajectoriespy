# Reproducibility bundle checklist

A manuscript or archived analysis should retain enough information to explain
what was analyzed, how it was analyzed and which software contract produced the
reported quantities.

For an eyetrajectoriespy analysis, retain as applicable:

- source-data identifier or immutable data reference;
- preprocessing specification and any exclusions;
- coordinate system and time units;
- participant/trial/stimulus identifiers required by the inferential hierarchy;
- estimator/model specification and all consequential arguments;
- random seed and resampling count for stochastic procedures;
- grouped-binomial denominators or Poisson exposure when used;
- diagnostic/sensitivity specification;
- portable result snapshot (`manifest.json` + `arrays.npz`);
- captured software/environment metadata;
- package version and Git commit when available;
- reporting text or tables actually used in the manuscript;
- independent-reference qualification relevant to the chosen canonical route.

Do not use the portable snapshot as a substitute for retaining the original
data and preprocessing decisions when those inputs are necessary to reproduce
the analysis from first principles.
