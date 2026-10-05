# Native sparse multilevel FPCA

`fit_sparse_multilevel_fpca()` is the 1.1 development route for **irregular univariate trials nested within participants** when repeated trials should be decomposed into stable participant-level and within-participant/trial functional variation without first interpolating each raw trial onto a common grid.

The initial model is

$$
Y_{ij}(t)=\mu(t)+U_i(t)+V_{ij}(t)+\epsilon_{ij}(t),
$$

where $U_i$ is participant-level variation, $V_{ij}$ is exchangeable trial-level variation within participant, and $\epsilon_{ij}$ is measurement error.

This sparse hierarchy follows the covariance logic of Di, Crainiceanu, and Jank (2014), *Multilevel sparse functional principal component analysis*, Statistics 3(1), 126–143, DOI `10.1002/sta4.50`. The package implementation is intentionally narrower than that literature in several places described below.

## When should I use this?

Use this capability when:

- each participant contributes one or more irregular/sparse trial trajectories;
- at least three participants contribute repeated trials, so between-participant covariance is identifiable from cross-trial products;
- the scientific target is separation of stable participant-level functional variation from residual trial-level variation;
- repeated trials can reasonably be treated as exchangeable after any scientifically required task/condition/visit effects have been removed or stratified upstream.

For complete common-grid repeated trials, use the stable dense `fit_multilevel_fpca()` workflow. For a single sparse level without participant/trial decomposition, use `fit_sparse_fpca()`.

## What this first tranche does not model

B1 does **not** estimate trial-condition, task, visit-order, treatment, or other fixed functional effects. If those are part of the scientific design, do not ask the random two-level decomposition to absorb them. Stratify the analysis or remove/model those effects upstream before using this capability.

The first tranche also supports only `weighting="observation"`. Mean smoothing pools retained native observations; covariance smoothing pools raw covariance products. Participants with more retained observations or more repeated-trial covariance pairs can therefore contribute more local information. This is **not** equal-participant weighting.

## Sparse covariance identities

After subtracting the fitted grand mean, the latent total covariance is

$$
K_T(s,t)=K_B(s,t)+K_W(s,t),
$$

where $K_B$ is between-participant covariance and $K_W$ is within-participant/trial covariance.

### Total covariance

`K_T` is estimated from within-trial off-diagonal residual products. Same-sample diagonal products are excluded so measurement-error variance is not silently absorbed into the latent covariance smoother.

### Between-participant covariance

`K_B` is estimated from residual products drawn from **different trials belonging to the same participant**. Products from different participants never enter this smoother. A participant with only one retained trial contributes no between-level covariance pairs.

### Within-participant covariance

Before PSD handling,

$$
\widehat K_W=\widehat K_T-\widehat K_B.
$$

The result retains the directly smoothed total/between/within surfaces. Between and within operators then receive separate declared PSD audits. Their repaired versions are the covariance operators used for eigendecomposition and scoring.

Because level-specific PSD projection can alter the decomposition slightly, the result also reports the discrepancy between the direct smoothed total covariance and the post-PSD sum of repaired between + within covariance.

## Joint hierarchical BLUP scores

For one participant, all retained trial observations are stacked in deterministic trial/native-time order. The full observation covariance is assembled blockwise:

$$
\Sigma_{i,jj}=K_B(T_{ij},T_{ij})+K_W(T_{ij},T_{ij})+\sigma^2I,
$$

and for distinct trials $j\ne l$,

$$
\Sigma_{i,jl}=K_B(T_{ij},T_{il}).
$$

An optional declared score ridge is added to the final observation covariance system and is recorded separately from measurement error.

The BLUP solve uses the **full repaired between and within covariance surfaces**. Retained component counts control only the participant/trial score vectors returned to the user; they do not rank-truncate the observation covariance system.

Participant score cross-covariance spans all of that participant's observations, so repeated trials legitimately contribute information to the stable participant score. A trial-specific score cross-covariance is non-zero only for observations from that trial, although the common inverse covariance solve couples the full participant record through the between-participant covariance.

## Minimal fit

```python
import numpy as np
from eyetrajectoriespy.sparse_multilevel import fit_sparse_multilevel_fpca

fit = fit_sparse_multilevel_fpca(
    irregular_trials,
    dimension="x",
    participant_column="participant_id",
    participant_components=2,
    trial_components=2,
    evaluation_grid=np.linspace(0.05, 0.95, 31),
    mean_bandwidth=0.25,
    total_covariance_bandwidth=0.35,
    between_covariance_bandwidth=0.40,
    analysis_support_action="restrict",
    weighting="observation",
    noise_variance_method="fixed",
    measurement_error_variance=0.01,
    psd_action="project",
    score_failure_action="retain_nan",
)
```

Selected bandwidths remain explicit inputs. B1 does not add automatic multilevel bandwidth selection.

## Result object

`SparseMultilevelFPCAResult` retains:

- fitted grand mean;
- directly smoothed total, between, and within covariance surfaces;
- repaired between/within covariance operators and their post-PSD sum used for scoring;
- participant- and trial-level eigenvalues/eigenfunctions;
- participant and trial score tables;
- participant-level BLUP conditioning/failure diagnostics;
- measurement-error variance;
- mean/covariance support counts;
- trial/sample/pair counts by participant, including single-trial participants;
- separate PSD audit trails;
- complete scientific provenance.

## Failure semantics

The fitter fails explicitly when the population hierarchy is not identifiable or the numerical support is inadequate. Important examples include:

- fewer than three participants overall;
- fewer than three participants with repeated trials;
- missing participant metadata;
- a trial with no retained observations after an explicit support restriction;
- insufficient local mean or covariance support;
- insufficient positive components at either hierarchy level;
- invalid diagonal-difference noise variance;
- non-positive-definite or excessively ill-conditioned participant BLUP systems.

`score_failure_action="retain_nan"` preserves failed participant/trial scores and diagnostics rather than silently dropping them.

## Single-trial participants

Single-trial participants are not automatically discarded. After a valid population fit has been identified by other repeated participants, a single-trial participant may contribute to mean/total covariance estimation and may receive participant/trial BLUP scores. Its between-covariance pair count remains exactly zero and is visible in `support_diagnostics`.

## Reporting

```python
from eyetrajectoriespy.sparse_multilevel import (
    sparse_multilevel_fpca_reporting_text,
)

print(sparse_multilevel_fpca_reporting_text(fit))
```

Report at minimum:

- participant/trial counts and unequal trial structure;
- native sparse sampling and analysis support;
- mean, total-covariance, and between-covariance bandwidths;
- observation/raw-pair weighting;
- measurement-error model;
- level-specific PSD policy/corrections;
- participant/trial retained components;
- BLUP ridge, conditioning threshold, and failures;
- whether task/visit fixed effects were removed or stratified upstream.

## Qualification evidence

The dedicated [`sparse-multilevel-validation`](../validation/sparse-multilevel-fpca.md) workflow uses known between/within population truth. In its first completed run:

| Scenario | Between cov relRMSE | Within cov relRMSE | Between mode similarity | Within mode similarity | Participant score | Trial score |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Balanced, denser, low noise | 0.281 | 0.339 | 0.996 | 0.974 | 0.999 | 0.996 |
| Unequal, sparse, higher noise | 0.555 | 0.489 | 0.984 | 0.971 | 0.971 | 0.960 |

The harder scenario retained nine single-trial participants and had zero failed participant BLUP systems. The qualification also verifies deterministic replay, no rank-K score covariance, no raw sparse interpolation, and explicit failure of a hierarchy with only two repeated participants.

These are qualification observations for the declared deterministic designs, not universal recovery guarantees.

## Limitations

B1 does not provide:

- trial-condition or visit-specific fixed functional effects;
- equal-participant or equal-curve weighting;
- automatic bandwidth selection;
- uncertainty propagation from estimated mean/covariance/eigensystems into downstream models;
- multivariate/asynchronous x/y hierarchy;
- more than two nested random functional levels;
- causal interpretation of participant/trial components.

Those are separate estimands and should be added only with dedicated methodological and validation contracts.
