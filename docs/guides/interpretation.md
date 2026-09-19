# Interpretation guidance

## FPC signs are arbitrary

An eigenfunction can be multiplied by `-1` with its scores multiplied by `-1` without changing the model. Interpret the two ends of the component contrast, not the sign itself.

## Variance explained is descriptive

High variance explained does not make a component causal, theoretically important, or predictive.

## Component shapes are estimated

A smooth-looking FPC is not fixed truth. Inspect matched bootstrap stability and, when shape interpretation matters, [descriptive component envelopes](component-uncertainty.md).

When eigenvalues are close, component labels can swap across resamples. Matching similarity should be interpreted before pointwise envelope width.

## Scores inherit preprocessing

A score derived after normalization, registration, smoothing, or coordinate centering represents that transformed process.

## Prefer trajectory language

Good: “Higher FPC1 scores represented earlier rightward evidence-panel excursions followed by return toward the decision region.”

Weak: “FPC1 represented attention.”
