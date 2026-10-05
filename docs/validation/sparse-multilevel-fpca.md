# Native sparse multilevel FPCA qualification

This page documents deterministic known-truth qualification for the 1.1 development capability `fit_sparse_multilevel_fpca()`.

## Qualified target

The estimator targets the exchangeable two-level sparse functional model

$$
Y_{ij}(t)=\mu(t)+U_i(t)+V_{ij}(t)+\epsilon_{ij}(t),
$$

with participant-level covariance $K_B$, trial-within-participant covariance $K_W$, and independent measurement error.

The implementation estimates:

1. the grand mean from pooled retained native observations;
2. latent total covariance from within-trial off-diagonal residual products;
3. between-participant covariance from distinct-trial residual products within the same participant;
4. within-participant covariance as smoothed total minus smoothed between covariance before level-specific PSD handling;
5. participant and trial scores jointly by Gaussian BLUP using the full repaired covariance surfaces.

Raw sparse trajectories are never interpolated onto a common grid.

## Methodological reference

The hierarchical covariance structure follows the sparse multilevel functional PCA framework of Di, Crainiceanu, and Jank (2014), *Multilevel sparse functional principal component analysis*, Statistics 3(1), 126–143, DOI `10.1002/sta4.50`.

The current package tranche is narrower: it is univariate, two-level, exchangeable across repeated trials after any required fixed condition effects are handled upstream, and uses observation/raw-pair weighting only.

## Known truth

The qualification simulator uses one known participant mode and one known trial mode:

$$
\phi_B(t)=\sqrt{2}\sin(\pi t),
\qquad \lambda_B=1,
$$

and

$$
\phi_W(t)=\sqrt{2}\sin(2\pi t),
\qquad \lambda_W=0.45.
$$

Each participant receives an independent participant score. Each retained trial receives an independent within-participant score. Native observation times are irregular and differ across trials.

## Qualified scenarios

### Balanced denser / low noise

- 48 participants;
- 3 trials per participant, 144 trials total;
- 11–15 native observations per trial;
- measurement-noise SD 0.08.

Observed qualification metrics:

- between covariance relative RMSE: **0.2815**;
- within covariance relative RMSE: **0.3389**;
- between eigenfunction similarity: **0.9963**;
- within eigenfunction similarity: **0.9736**;
- participant-score absolute correlation: **0.9993**;
- trial-score absolute correlation: **0.9956**;
- failed participant BLUP systems: **0**.

The between operator required a PSD projection with relative weighted-operator correction **0.0369**; the within operator correction was **0.0287**.

### Unequal sparse / higher noise

- 54 participants;
- 122 trials total;
- 7–10 native observations per trial;
- measurement-noise SD 0.16;
- 9 participants had a single retained trial;
- 45 participants contributed repeated trials to between-covariance estimation.

Observed qualification metrics:

- between covariance relative RMSE: **0.5553**;
- within covariance relative RMSE: **0.4886**;
- between eigenfunction similarity: **0.9844**;
- within eigenfunction similarity: **0.9709**;
- participant-score absolute correlation: **0.9712**;
- trial-score absolute correlation: **0.9602**;
- failed participant BLUP systems: **0**.

The between operator required a PSD projection with relative weighted-operator correction **0.0683**; the within operator correction was **0.0106**.

The nine single-trial participants remained in the analysis and could be scored after the population hierarchy had been identified by repeated participants. Their between-covariance pair counts remain zero by construction.

## Explicit non-identifiability check

A third deterministic dataset retains six participants but only two with repeated trials. The fitter is required to stop before smoothing between covariance. The qualification observed the declared failure:

```text
insufficient_repeated_participants
```

This check prevents an underidentified hierarchy from being silently converted to a single-level model or from manufacturing between-participant covariance from cross-participant products.

## Score-system contract

Qualification records confirm:

- `rank_k_covariance_used_for_scoring=False`;
- the participant observation covariance uses the full repaired between + within covariance surfaces plus declared measurement error;
- participant scores borrow information across that participant's repeated trials;
- each trial score's cross-covariance is confined to that trial's observation block;
- deterministic replay reproduces the same scenario summary exactly;
- `raw_sparse_trajectory_interpolation_performed=False`;
- `weighting="observation"`;
- `trial_fixed_effects_estimated=False`.

The BLUP calculations are conditional on fitted population quantities. The qualification does not imply that population-estimation or bandwidth uncertainty has been propagated into score uncertainty.

## Evidence identity

First completed B1 qualification on implementation head `b654dcb184205097182248b0343b94767ba9dc44`:

- workflow run: `37295044677`;
- artifact: `11338301279`;
- artifact digest: `sha256:59a0cbe5119ea9239dfc8071a081aca7f3cea35feba2d747ab4256b0f0d4f774`.

A later documentation-only or corrective head must rerun this workflow before merge; the final PR evidence should point to the final qualified head.

## Interpretation boundary

This evidence supports the implementation claim for the declared deterministic sparse two-level designs. It does **not** establish:

- universal recovery across all sparse sampling mechanisms;
- validity under unmodeled task/visit fixed effects;
- robustness to informative observation processes beyond separately diagnosed missingness assumptions;
- equal-participant weighting;
- full inferential coverage after estimating covariance surfaces/eigenfunctions;
- multivariate or asynchronous sparse multilevel FPCA.

Those require separate estimands and qualification programmes.
