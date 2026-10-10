# Rank-two PyMC log-posterior and automatic-differentiation study R2

**Research only.** This study follows rank-two dense-Gaussian versus Woodbury
mathematical identity validation in [PR #273](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/273),
but does not assume that independently correct numerical algebra implies a
correct PyMC/PyTensor posterior graph.

Four predeclared cases (paired/asynchronous × matched-Gaussian/near-tied)
instantiate an **actual PyMC** rank-two normal-prior model with a low-rank
score-marginal likelihood Potential. Its compiled full log posterior, including
all normal-prior normalization constants, is compared to a separately
implemented full dense observation-space Gaussian log likelihood plus normal
priors. Its PyTensor automatic derivatives are checked against independent
two-sided finite differences of the dense reference for all 30 parameters.
Loading rotation invariance is independently checked for the full posterior
under isotropic Gaussian loading priors and for population covariance.

Near-tied equal-eigenvalue configurations are explicitly **outside the
matched loading-generating prior** and constitute mathematical stress, not
SBC or posterior-coverage evidence. Each configuration retains its log-value
discrepancy, scaled-gradient discrepancy, covariance and rotational checks,
fit exceptions, and SHA256 source artifacts. Predeclared tolerances are
absolute log posterior <5e-6 and maximum scaled gradient discrepancy <3e-3.

**No rank-two NUTS sampling occurs in this stage.** Passing a differentiable
graph contract only unlocks independent four-chain computational reference
experiments. It cannot establish rank-two posterior convergence, rank-SBC
uniformity, nominal 90% interval coverage, or release qualification.
Scientific blocker #255 and every publication/production gate remain open.
