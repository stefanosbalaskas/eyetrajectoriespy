# B6/B7 exact partially collapsed Gaussian population mean Gibbs

**Unpublished 1.2 research. No inference qualification, stable API promotion, protected-main merge or release authorization.**

The B6/B7 first 400-refit prior-truth study showed substantial
undercoverage of nominal 90% population intervals. A 96-fit longer-chain
study (1,200 warmup/600 retained draws) still had many
**R-hat ≈ 1.2–1.6 and minimum ESS around 3–6**, even for identifiable
population summaries. An exact reversible MH factor-scale proposal
subsequently proved mathematically valid but showed **no consistent mixing
improvement** in 72 real paired fits. See scientific blocker
[#255](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/255).

## Mathematical rationale: eliminate mean/score conditional coupling

For sparse B6 participant observations:

$$
y_i=B_i\mu+B_iLz_i+\epsilon_i,\qquad
z_i\sim N(0,I_k),\quad \epsilon_i\sim N(0,\sigma^2I).
$$

The exact conditional distribution of the mean **after integrating all
participant scores** is

$$
\mu\mid L,y\sim N(P^{-1}b,P^{-1}),\qquad
P=\tau_\mu^{-2}I+\sum_iB_i^\top V_i^{-1}B_i,\quad
b=\sum_iB_i^\top V_i^{-1}y_i,\quad
V_i=\sigma^2I+B_iLL^\top B_i^\top.
$$

This is still the **same model and prior posterior**. Rather than
inverting an observation-sized matrix, Woodbury gives these terms using
the existing raw-observation Gram matrices and their cross products:

$$
T_i=I_k+\sigma^{-2}L^\top G_iL,\quad
H_i=\sigma^{-2}G_iL,\quad
P=\tau_\mu^{-2}I+\sum_i(\sigma^{-2}G_i-H_iT_i^{-1}H_i^\top).
$$

For B7, the mean is a joint **2q-dimensional** vector in x-then-y
channel order. Each participant's shared latent score creates
nonzero **cross-channel precision blocks** after integration:

$$
T_i=I_k+\sum_{d\in\{x,y\}}\sigma_d^{-2}L_d^\top G_{di}L_d,\qquad
H_i=\begin{bmatrix}\sigma_x^{-2}G_{xi}L_x\\
                    \sigma_y^{-2}G_{yi}L_y\end{bmatrix}.
$$

The joint precision subtracts $H_iT_i^{-1}H_i^\top$ from the
two-channel block-diagonal observation precision. Thus B7 does
**not** approximate x/y as independent or interpolate disjoint
observation timestamps.

## Valid Gibbs update order

The opt-in sampler now applies these conditionals in a valid
partially-collapsed sequence: **loadings given old mean and scores,
mean given loadings with scores integrated out, then participant
scores given the newly sampled mean and loadings**.

This ordering matters; casually inserting a collapsed step before
the old conditional loadings would not be the same Gibbs transition
and could fail to preserve the joint posterior.

New optional argument:
`collapsed_population_mean_update=True` in the *experimental*
B6/B7 fitter only. Its default remains **False**; explicitly False
and omission must yield bit-identical original posterior draws.
Factor ranks, priors, fixed observation noise and observation models
remain unchanged. Every evidence object exposes
`collapsed_mean_inferential_qualification=False`.

## Independent math proof checks and empirical study

`tests/test_bayesian_partially_collapsed_mean.py` compares the
Woodbury precision and right-hand side to independently formed
**dense marginal Gaussian likelihoods**, including B7 with
different x/y observation counts, cross-channel precision,
and real native asynchronous refits.

A dedicated study, executed once on the draft PR's initial
opening, runs **72 real paired full Gibbs fits** on **36 new
matched-prior independent datasets**, six per six scenario combinations,
each with and without the collapsed-mean update.
The pilot uses 400 warmup sweeps, 200 retained draws/chain,
and reports invariant R-hat/ESS, failures and scalar posterior
coverage without promoting a result. Same participant observations,
noise, rank and priors are used for the two samplers, and new independent
master seed `20261126` is separate from prior study seeds.

**Scientific interpretation boundary:** correct conditional posterior
algebra is necessary but not sufficient for full posterior mixing.
If this trial improves diagnostics, further independent NUTS,
rank-based SBC and hundreds of longer-chain posterior coverage
refits are still required. If it fails, document the negative evidence,
do not advertise the opt-in route as an inference fix, and retain the
original blocker. All statistical and 1.2 release flags remain false.


## Actual first paired posterior experiment: qualified algebra, better mixing in some cases

![Actual 72-fit original versus exact collapsed mean Gibbs Rhat diagnostic, with scientific warning](../assets/research/b6-b7-collapsed-mixing.svg)



[Workflow #37978244822](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/37978244822)
completed **72/72** actual Gibbs refits, six independent prior-generated
datasets per each of six B6/B7 scenarios, each refitted under original
and collapsed-mean kernels (36 independent dataset pairs). All three
Python 3.11/3.12/3.13 independent dense Gaussian marginal algebra
jobs passed, and all real Gibbs fits completed with **zero failures**.
Retained source artifact: `11639857546`.

Median **worst monitored R-hat** (lower is better) and median
**minimum bulk ESS** (higher is better) from identifiable population
summaries were:

| Scenario | Worst R-hat original → collapsed | Minimum bulk ESS original → collapsed |
|---|---|---|
| B6 rank 1 | 1.114 → 1.142 | 12.68 → 13.43 |
| B6 rank 2 | 1.670 → 1.272 | 3.46 → 6.29 |
| B7 rank 1 paired | 1.964 → 1.496 | 2.90 → 4.03 |
| B7 rank 1 asynchronous | 1.470 → 1.067 | 4.07 → 15.35 |
| B7 rank 2 paired | 1.937 → 1.537 | 2.92 → 3.81 |
| B7 rank 2 asynchronous | 1.668 → 1.470 | 3.42 → 4.19 |

The exact partially collapsed procedure substantially improves
several difficult scenarios, especially the rank-1 asynchronous
planar population mean. This is a **genuine computational finding**,
but most rank-2 and paired settings retain very poor R-hat/ESS;
the proposed new Gibbs route remains scientifically unqualified.
The collapsed route is opt-in and the legacy/default sampler
remains unchanged.

Empirical 90% coverage in this pilot has only **six dataset replicates
per regime** and cannot justify a population-coverage conclusion.
In particular, even a median R-hat close to 1.07 does not certify
convergence of all the high-dimensional covariance functionals.
A separate independent posterior NUTS implementation/reference,
parameter-mixing study, rank-based SBC and hundreds of longer-chain
coverage refits are still required. The scientific blocker
[#255](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/255)
remains open and **no 1.2 release is authorized**.
