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
