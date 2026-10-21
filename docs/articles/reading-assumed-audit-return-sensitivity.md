# How to read assumed audit-return sensitivity without claiming MNAR identification

*R88/R88-A methods companion · Independently replayed simulation evidence only*

## Four different probabilities

A valid interpretation separates at least four quantities: (i) the first-stage probability that a gaze observation is missing; (ii) secondary validation success among originally missing outcomes; (iii) the known randomized assignment probability q among outcomes still unmeasured; and (iv) *actual* return completion after assignment. Observing (iii) does not make (iv) known, because assigned outcomes can remain unavailable.

Write the conditional audit-return probability as \(r(Y,X,t)\). R88 examines a family \(r_\gamma(Y,X,t)\) with an assumed γ and a stipulated recorded-predictor/time baseline. The weighting of observed recovered outcomes uses the prespecified assignment fraction times the assumed return probability. **It does not replace unreturned Y, fit the return γ from unobserved Y, or create individual gaze trajectories.**

## Why these coefficients are not identified bounds

The displayed values are point estimates of first-stage selection coefficients under four **externally stipulated** γ values. A list of point estimates across a chosen sensitivity grid is not an empirical confidence region, a sharp identification region, or evidence of complete identification of a latent selection process.

Correctly matching the simulator-known γ=1.35 does not imply that an applied researcher can learn γ from the returned outcome sample. Even when γ is correct, the simulation's first-stage δ can differ from the generating δ because estimation, pilot quality, repeated-trial structure and finite-source sampling remain.

If the recorded baseline is unknown or misspecified, a γ-only sensitivity grid understates the real identification ambiguity. Extending this programme would require explicit, defensible external information about *actual response completion*, rather than choosing the γ whose estimates appear closest to expected truth in simulation.

## Proper independent-unit denominators

The primitive source block is the independent replication for each fixed comparison. There are 32 blocks for the curves design and 32 for the repeated-trial participant design. MAR and MNAR masks, two audit-assignment rates, and four γ assumptions are evaluated repeatedly on matched source blocks. Therefore 1,024 analysis rows are not 1,024 independent draws.

The three trials per participant and the 31 time positions are not independently randomized participants. Source-level summaries average 32 block-level first-stage estimates per fixed cell. Without an explicit source-level inferential analysis, these averages have **no advertised confidence intervals**.

## Why random audit assignment is not sufficient

In a two-stage ideal randomized audit, the analyst must also secure the measurement for assigned outcomes or adequately model any difference between assignment and realized observation. R88's actual audit-return completion depends on a hidden outcome; a model based solely on random assignment and recorded X/time can be distorted. Raising q increases the number assigned, but does not force response completion independent of hidden Y.

Figure 2 in the [main R88 article](w3-r88-return-audit-sensitivity.md) reports descriptive completed/assigned proportions, not an estimated latent-Y selection coefficient. The same completed/assigned rate can arise from different hidden-Y selection laws, so the rate alone cannot identify γ.

## What independent R88-A replay establishes

The independent implementation regenerates all original source streams and recomputes the original coefficients/refusal records with separate SciPy numerical routines. It checks the original source checkout, original archive SHA256 manifest, measured subset counts, source identities and per-method scientific restrictions. All four dedicated R88-A jobs passed, including mandatory actual-archive replay.

This establishes **independent software/numerical agreement** for the specified data generating law and fitted score equations. It is not a statistical coverage experiment or general proof of missing-data identification. Refer to the [evidence ledger](../development/w3-r88-original-independent-evidence-ledger.md) for immutable sources and gates.

## Release boundary

The experimental work stays on draft research branches. [Issue #289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289) (90% simultaneous bands) and [issue #296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296) (response-dependent gaze loss) remain open. Public stable 1.1.0 and its missing-input rejection contract are unchanged; **1.2 release/PyPI HOLD**.
