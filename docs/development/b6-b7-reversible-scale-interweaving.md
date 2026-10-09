# Experimental Bayesian reversible scale interweaving — not calibrated

This method is a **posterior-preserving computational proposal** for the
unreleased B6/B7 Gaussian functional factor Gibbs samplers. Do not infer
that enabling it provides valid credible intervals, better mixing or an
approved 1.2 API. Exact prior/likelihood simulation produced severe
population undercoverage and poor chain diagnostics even at 1,200 warmup
and 600 retained samples. [Blocker #255](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/255).

## Posterior-invariant transformation

For a single latent factor column $k$, the native observation model is
(y_i=B_i(\mu+Lz_i)+\varepsilon_i), with
(L_{\cdot k}\sim N(0,\tau^2 I_q)), (z_{ik}\sim N(0,1))
and fixed Gaussian observation noise. The planar model has
(L\in\mathbb R^{2q\times K}), shared participant scores and
channel-specific observation noise.

For a symmetric random-walk proposal (a\sim N(0,s^2)), propose

$$
L'_{\cdot k}=e^a L_{\cdot k},\quad z'_{\cdot k}=e^{-a}z_{\cdot k}.
$$

This **leaves all reconstructed latent curves exactly unchanged**.
It does *not* change the likelihood or the true posterior. The complete
Metropolis log-acceptance ratio is

$$
\log R= -\tfrac12(e^{2a}-1)\|L_{\cdot k}\|^2/\tau^2
         -\tfrac12(e^{-2a}-1)\|z_{\cdot k}\|^2
         +(d_L-n)a,
$$

where $d_L=q$ in B6, $d_L=2q$ in B7 and $n$ is the
number of unique participants. The final **Jacobian factor** is
essential for detailed balance. Code tests independently recompute
this ratio from Gaussian densities and verify that applying the
inverse scale move negates the forward log ratio.

Opt in with `scale_interweave_proposal_sd=0.25` when calling
`fit_bayesian_sparse_fpca` or `fit_bayesian_planar_factor`
via the *experimental Bayesian namespace only*. Default
`scale_interweave_proposal_sd=0` is a strict no-op, preserving the
earlier sampler's random-number sequence and published/research
comparison baseline.

The returned evidence reports attempted and accepted scale moves,
proposal SD, and explicitly false inferential-qualification flags.
Sign/rotation unidentifiability is still present; scale moves target
only a continuous coupling ridge. R-hat/ESS for identifiable
functional-population summaries are still required.

## Independent evidence required

The workflow `science-b6-b7-reversible-scale-mh.yml` checks exact
Jacobian/likelihood invariance in Python 3.11–3.13 and runs
**72 actual Gibbs fits** on 36 independent known-truth datasets
(6 per six combinations, each fit twice with and without scale moves).
Both versions receive identical data and model hyperparameters.
The pilot uses 400 warmup sweeps, 200 retained posterior draws per
chain and the source matched priors; it reports invariant R-hat/ESS,
acceptance rates and failures without automatic inferential decisions.

This is a **mechanism test**, not the 400-refit prior SBC or a
definitive Bayesian sampler comparison. If scale moves fail to improve
invariant ESS and R-hat, the kernel should not be advertised as a
scientific solution. Even if improved, independent NUTS references,
chain convergence, rank-based SBC and adequate empirical predictive
coverage remain obligatory before any research-method qualification.

The original expensive 13,600-attempt study is manually triggered
only. The earlier original F5 AR1 comparison artifact is recovered
through `science-f5-recover-original-oracle-artifact.yml` without
replaying its 1,800 fits, and the historical literal `null` label is
preserved. The new F5 method still requires **externally known scalar
AR1 phi**, not in-sample estimated dependence.

No root namespace, stable 1.1.0 functionality, protected main,
production release flags or public deployment are promoted by this
research tranche.
