# W3 R93 — exact observational-equivalence counterexample under near-complete audit return

**Prospectively frozen exact mathematics, 23 October 2026. Research-only.** R93 is deliberately not another simulation, estimator modification or source-level sampling-coverage study. It supplies an **exact binary bounded-outcome submodel** of the broader missing-gaze response problem and proves point nonidentification even with fully known randomized invitation and very high actual completion.

## Scientific construction, conditional originally missing stratum

Within a fixed originally-missing record stratum, let bounded outcome Z∈{0,1} and unknown underlying probability p=P(Z=1). Random invitation I has known, outcome-independent probability g. If invited, the outcome is observed only on successful completion R; response probabilities c0=P(R=1|I=1,Z=0), c1=P(R=1|I=1,Z=1) are unknown. The analyst sees I for everyone and, when I=1, completion status R and Z only if completed. Observed joint probabilities are

- P(I=0)=1−g
- P(I=1,R=1,Z=0)=g(1−p)c0=gq0
- P(I=1,R=1,Z=1)=gpc1=gq1
- P(I=1,R=0)=g(1−q0−q1).

Thus the **entire observed event law** is determined by g,q0,q1 and contains no separate information to decompose q0=(1−p)c0 and q1=pc1 without a response model. All finite i.i.d. observed-data samples have the same likelihood under any pair of mechanisms with equal q0,q1,g.

For a known outcome support Z∈{0,1}, feasible underlying means p satisfy the exact sharp population identification interval **p∈[q1,1−q0]**: each feasible p permits c1=q1/p and c0=q0/(1−p). Width 1−q0−q1 equals the fraction of invited outcomes that did not return. This is a **population observed-law identification region**, not the realized finite-sample worst-case interval from R89/R90, and it is not a frequentist confidence interval.

## Frozen near-complete exact worlds

At overall actual completion 1−δ, choose exact observed masses q0=q1=(1−δ)/2. Construct three latent worlds with exactly the same observed law:

1. **Low mean:** p=(1−δ)/2, c1=1 and c0=(1−δ)/(1+δ).
2. **Uniform completion:** p=1/2, c0=c1=1−δ.
3. **High mean:** p=(1+δ)/2, c0=1 and c1=(1−δ)/(1+δ).

All actual completion probabilities lie in [0,1]. Means of low and high worlds differ by δ, yet every observable probability is identical. The model holds for invitation g=25%, 50%, and **100%**: even inviting everyone does not identify p when some outcomes do not complete.

Freeze δ=0.001,0.01,0.05 (99.9%,99%,95% return), g=0.25,0.50,1.00, three worlds: **27 distinct rational probability parameterizations, forming nine observationally equivalent triples**. Every computed probability uses Python's exact rational Fraction type (not simulated floating-point rates); proof and checksum are archived without source sampling and without invented replication denominators.

The maximum counterexample gap equals δ in this binary setup: a *small* missing fraction creates a *small but nonzero* population mean identified interval, not evidence for large uncertainty or false nominal coverage. This sharp counterexample shows **failure of point identification in the general class containing the binary submodel**. It does not quantify identification width for arbitrary correlated gaze trajectories, continuous bounded outcomes, regression slopes, measurement error, or other strata. It does not rule out identification under additional verified constraints or actual guaranteed completed retrieval.

## Engineering/provenance requirements

Source computes all observable event laws as rationals and rejects any mismatch across latent worlds, any law summing to other than one, any invalid completion probability, incorrect sharp-set endpoints or source-count mismatch. Tests prove product-likelihood equality for every length-three observed event string (and equality of one-record events implies every finite length). Perturbing source values or omitting records must fail.

Require 3 Python-version pytest validations and separate SHA256 original 27-row exact proof-artifact workflow. Before describing R93 as independently reproduced, write a **separate R93-A audit** using independent equations (not importing the original proof module), obtain the original exact artifact, verify the complete 27 parameter worlds and rational observed-law probabilities, and archive a second checked proof. Only then may a docs-only PR publish scientific article/figures; require all 25 PR workflows and a separately successful protected-main Pages deploy. Original and independent research-only scripts must stay draft/unmerged.

Issues [#296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296) (real outcome-dependent observation) and [#289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289) (90% simultaneous functional-band calibration) are unresolved and remain open. No novel measured data, real-MNAR propensity identification, raw missing signal reconstruction, 90% confidence or public production estimator claim; **1.2/GitHub/PyPI release HOLD**.
