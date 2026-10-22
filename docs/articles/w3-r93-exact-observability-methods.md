# Exact likelihood equivalence and sharp identified-set derivation

*W3 R93 methods companion · independently audited exact rational calculation · 23 October 2026*

## The observation law and its observational equivalence class

Condition on a fixed originally missing target stratum. Let latent bounded outcome $Z\in\{0,1\}$ have probability $p=P(Z=1)$. A randomized invitation $I$ is independent of $Z$ with known $g=P(I=1)>0$. Completion is an outcome-specific Bernoulli event conditional on invitation, with probabilities $c_z=P(R=1\mid I=1,Z=z)$ for $z=0,1$. The observed data for each record are invitation status, completion status if invited, and $Z$ only after actual completion.

A single record's complete *observable* support consists of four mutually exclusive events: uninvited; invited and returned $Z=0$; invited and returned $Z=1$; and invited but unreturned. Their probabilities are

$$
(1-g,\,g(1-p)c_0,\,gpc_1,\,
 g[(1-p)(1-c_0)+p(1-c_1)]).
$$

Let $q_0=(1-p)c_0$ and $q_1=pc_1$. The entire observed event law is $(1-g,gq_0,gq_1,g(1-q_0-q_1))$. It contains **no independent information** about the factorization of $q_0$ and $q_1$ into the underlying population distribution and outcome-specific completion rates. In the stipulated independent-record binary submodel, for any finite observed sequence of length $n$, its likelihood is the product of these four-event probabilities; identical single-record laws therefore imply identical likelihoods for *every* $n$, not just approximate equality after simulation.

## Proof of sharp identified population mean set

Because $0\le c_1\le1$, $q_1=pc_1\le p$. Similarly $q_0=(1-p)c_0\le1-p$. Hence any feasible underlying mean obeys

$$
q_1\le p\le1-q_0.
$$

Conversely, given $q_0,q_1>0$ and $q_0+q_1\le1$, each $p\in[q_1,1-q_0]$ is realized by the completion probabilities

$$
c_1=\frac{q_1}{p},\qquad
c_0=\frac{q_0}{1-p}.
$$

They are both between zero and one, so *every point* of the interval is observationally feasible. That proves sharpness. The identified-set width is

$$
(1-q_0)-q_1=1-q_0-q_1,
$$

exactly the fraction of **invited** records whose outcomes remain unreturned. This is a *population* partial-identification region under a binary response support. It is distinct from the fixed-realized finite-population bounds of R89–R90 and contains no source-sampling confidence guarantees.

## Exact three-world construction

Fix conditional nonreturn mass $\delta>0$ and $q_0=q_1=(1-\delta)/2$. Three latent worlds instantiate the two sharp endpoints and the midpoint:

$$
\begin{array}{c|ccc}
& p & c_0 & c_1\\
\hline
\mathrm{Low}&(1-\delta)/2&(1-\delta)/(1+\delta)&1\\
\mathrm{Uniform}&1/2&1-\delta&1-\delta\\
\mathrm{High}&(1+\delta)/2&1&(1-\delta)/(1+\delta)
\end{array}
$$

The three underlying population means have sharp total gap $\delta$. Their successful return masses satisfy $(1-p)c_0=pc_1=(1-\delta)/2$ identically, so the observed event law is exactly the same at **every** fixed invitation probability $g\in(0,1]$. Even $g=1$ does not identify missing observations that fail to return.

The prospective exact rational grid contains $\delta\in\{1/1000,1/100,1/20\}$ and $g\in\{1/4,1/2,1\}$. Each of the nine $(\delta,g)$ cells has three different latent world constructions: **27 parameterization records** and **nine complete observational-equivalence comparisons**, with no independent empirical subjects or stochastic estimation errors. The probabilities were evaluated using exact fractions, including zero and one, not rounded finite-precision estimates.

At $\delta=1/1000$, the two extremal latent means are 0.4995 and 0.5005. This is an identification gap of 0.001 in this example, not evidence of dramatic inference failure. Additional verified restrictions on $c_0,c_1$ can shrink the interval.

## What an independent audit verifies

Original [R93 science run #39854975837](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39854975837) passed its three Python-version tests and immutable proof-artifact check, after an initial test-environment import failure had been corrected. Independent [R93-A run #39855518388](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39855518388) passed its independently coded three-version tests and mandatory actual original 27-record proof replay.

The independent script does **not** import the original proof implementation. It independently decomposes the unreturned mass into low, evenly divided or high latent outcome mass, constructs completion probabilities by dividing observed success subprobabilities by latent outcome probabilities, and tests all four observable event probabilities and all nine sharp population mean regions. It also verifies the complete source ledger, canonical rational numerators/denominators and SHA256 archive member integrity. Its likelihood-product tests establish algebraic equality for finite event sequences; the general arbitrary-sample result follows from elementary probability multiplication.

These proofs concern only the stated binary iid population model conditional on a target stratum. Arbitrary continuous trajectories with temporal dependence or multiple covariates are not fitted or analyzed. A binary submodel counterexample disproves unrestricted *universal* point identification; it does not provide exact width for every practical gaze-data model.

## Scientific and engineering release gates

This work does not estimate the true return process from unreturned observations, reconstruct real missing sensor values, validate simultaneous functional bands, construct a frequentist confidence interval or establish a production estimator. Original and independently audited scripts remain draft research PRs, without merges into protected public package code. Only reviewed documentation, figures and provenance may enter protected main after all exact-head CI checks and the GitHub Pages deployment gate. Scientific issues [#296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296) and [#289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289) remain **open**. Stable public 1.1.0 and API unchanged, version 1.2/GitHub/PyPI publication **HOLD**.
