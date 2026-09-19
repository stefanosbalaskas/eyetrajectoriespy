# FPC shape uncertainty

Functional principal components are **estimated functions**. Their apparent shape in one fitted sample should not be treated as fixed.

Two issues matter immediately:

1. FPC signs are arbitrary.
2. bootstrap components can swap order when eigenvalues are close.

A raw pointwise bootstrap of "component 1" without alignment can therefore average incompatible directions.

## Matched, sign-aligned bootstrap envelopes

`bootstrap_fpca_component_envelopes()` fits a full-sample reference FPCA and then repeatedly:

1. resamples curves or participants;
2. refits FPCA;
3. matches bootstrap FPCs to reference FPCs by maximum absolute functional similarity;
4. sign-aligns each matched function to the reference;
5. forms pointwise empirical quantiles.

```python
envelopes = bootstrap_fpca_component_envelopes(
    gaze,
    n_bootstrap=500,
    n_components=3,
    scaling="dimension_sd",
    resample_unit="participant",
    participant_column="participant_id",
    level=0.95,
    random_state=2026,
)
```

For repeated-trial designs, participant-level resampling is usually the relevant default because it preserves the clustered sampling unit.

## These are descriptive envelopes, not confidence bands

The returned lower and upper functions are **pointwise descriptive bootstrap envelopes**.

They are deliberately not called confidence intervals or simultaneous confidence bands. The implementation does not claim calibrated pointwise or family-wise coverage.

This distinction matters because formal uncertainty for FPCA decompositions is affected by eigenvalue spacing, decomposition uncertainty, and the inferential target.

## Inspect matching quality

The result retains absolute matched component similarities for every bootstrap replicate.

Low or highly variable similarity can indicate:

- weakly separated eigenvalues;
- component swapping;
- insufficient sample size;
- influential participants;
- heterogeneous viewing strategies;
- sensitivity to preprocessing or registration.

An envelope is difficult to interpret when component identity itself is unstable. Inspect bootstrap similarity alongside the envelope.

## Plot one dimension of one FPC

```python
plot_fpca_component_envelope(
    envelopes,
    component=0,
    dimension="x",
)
```

The plot overlays:

- the full-sample reference FPC;
- the sign-aligned bootstrap median;
- the pointwise descriptive envelope.

For MFPCA, inspect all scientifically relevant dimensions rather than interpreting only x(t) or only y(t).

## Relation to stability analysis

`bootstrap_fpca_stability()` asks whether matched component directions recur under resampling.

`bootstrap_fpca_component_envelopes()` asks where the matched component functions vary pointwise after component identity has been aligned.

Use both when component-shape interpretation is central.

## What wide envelopes can mean

Wide regions can arise from several mechanisms:

- genuine sampling uncertainty;
- near-tied eigenvalues;
- phase variation that has not been modeled;
- local trajectory heterogeneity;
- influential participants;
- noisy derivatives or overly flexible preprocessing.

Do not automatically smooth the envelope or remove influential observations to make it narrower.

## Reporting example

> FPC shape sensitivity was summarized using 500 participant-level bootstrap replicates. Bootstrap FPCs were matched to full-sample components by maximum absolute functional similarity and sign-aligned before pointwise 2.5th and 97.5th percentiles were calculated. These envelopes were treated as descriptive resampling summaries rather than simultaneous confidence bands. Median matched similarity was reported for each component to quantify component identity stability.

Use `fpca_component_envelope_reporting_text()` for compact descriptive wording.

## API links

- `bootstrap_fpca_component_envelopes()`
- `plot_fpca_component_envelope()`
- `fpca_component_envelope_reporting_text()`
- `bootstrap_fpca_stability()`
- `match_fpca_components()`

## Methodological context

Hall and Hosseini-Nasab (2006) show that eigenvalue spacing directly affects eigenfunction estimation behavior. Goldsmith, Greven, and Crainiceanu (2013) explicitly address uncertainty from FPC decompositions when constructing formal confidence bands. The envelopes implemented here are intentionally more modest: they expose matched-bootstrap shape variability without claiming the formal coverage properties of those methods.

- Hall P, Hosseini-Nasab M. *On properties of functional principal components analysis*. Journal of the Royal Statistical Society: Series B. 2006;68(1):109–126. doi:10.1111/j.1467-9868.2005.00535.x.
- Goldsmith J, Greven S, Crainiceanu C. *Corrected Confidence Bands for Functional Data Using Principal Components*. Biometrics. 2013;69(1):41–51. doi:10.1111/j.1541-0420.2012.01808.x.


## Near-tied component blocks

Pointwise component envelopes assume that a bootstrap component can be meaningfully matched to a reference axis. When adjacent eigenvalues are close and axes rotate, inspect the corresponding [FPC subspace](subspace-stability.md) as well.

High subspace stability with low individual matching similarity is evidence to interpret the functional span more confidently than the orientation of each FPC inside it.
