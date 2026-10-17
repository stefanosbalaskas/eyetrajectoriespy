# W3 R58 — prospective independent-source boundary-null reference stress test

**Status: research-only candidate reference, NOT inferential qualification.** This document specifies the original design before seeing R58 simulation results. R57 established a genuine nested restricted Gaussian likelihood and strict numerical gates, but did not supply a sampling-law reference or nominal variance-component test.

## Mathematical benchmark: explicitly conditional, not assumed valid

For exactly one variance parameter constrained to the half-line under H0, with all nuisance parameters identifiable and regular in the interior and valid local asymptotics, a classical *candidate* boundary likelihood-ratio law is the 50:50 mixture of a point mass at zero and a chi-square distribution with one degree of freedom. At candidate alpha 0.05 the positive-tail cutoff is `chi2.isf(0.10, 1) = 2.705543454095404`, with **strict** rejection at T > cutoff. The candidate tail mapping is 1 at T=0, otherwise 0.5 times chi-square-one survival.

Primary methodological references:

- Self, S. G., & Liang, K.-Y. (1987). Asymptotic properties of maximum likelihood estimators and likelihood ratio tests under nonstandard conditions. *Journal of the American Statistical Association*, 82(398), 605–610. https://doi.org/10.1080/01621459.1987.10478472
- Crainiceanu, C. M., & Ruppert, D. (2004). Likelihood ratio tests in linear mixed models with one variance component. *Journal of the Royal Statistical Society: Series B*, 66(1), 165–185. https://doi.org/10.1111/j.1467-9868.2004.00438.x

**Critical limitation:** the second reference specifically cautions that ordinary chi-square-mixture approximations can be inaccurate for finite-sample restricted likelihood ratios in linear mixed models. R58 neither proves the required asymptotic regime for the irregular repeated-trial designs nor claims that nuisance variance parameters are interior everywhere. The candidate mapping is therefore a **benchmark calibration hypothesis**, not a validated p-value or a portable supported testing procedure. Selected nuisance estimates and all numerical refusals must not be silently discarded.

## Completely new independent null and positive generators

Freeze **24 NEW independent Gaussian primitive generating blocks**, source seed **202610175858**, each with 24 participants and original native irregular repeated trials. This seed and its 24-block source plan are different from R57's seed 202610175757 and eight-block design.

Within each generating block, make two predictor-dependent leverage variants, ordinary and extreme, using the same source primitive innovations. Within each support, make two matched generating slope states, true-zero and true-positive. Exact source zero is constructed by subtracting *only* the participant-slope Gaussian contribution from the same positive native response, following R57. Generating positive random-slope variance is 0.002025 and generating null variance is exactly zero. Source information is not handed to the nested estimator.

**Independent denominator is 24 primitive blocks per leverage-specific marginal sampling estimate, not 48 or 96 independent replicates.** The planned complete original evidence is **24 blocks × 2 paired predictor supports × 2 matched slope states = 96 case records**, with 192 H0/H1 fitted-model slots and **576 independent optimizer-start record slots**. Paired supports/states are to be reported in separate cells; they are not extra independent information.

R58 reuses the numerically audited *R57* exact-zero H0 and nonnegative H1 Gaussian REML objectives, frozen initializations, strict physical score/KKT<=0.001, near-observed-best NLL<=0.001, reconstruction<=1e-6, and nested monotonicity tolerance. A source or fit that cannot pass these unchanged gates is a **refusal**, not a boundary-null rejection or success.

## Prospective estimation and Monte Carlo reporting

For each accepted true-zero Gaussian source, report the R57 nested deviance with both raw signed and accepted nonnegative versions, the fitted structural-zero frequency, and whether its value exceeds candidate 2.705543454095404. For each support independently, report:

- original 24 planned source blocks, source failures, H0 failures, H1 failures, and accepted deviance count;
- count and fraction above the candidate threshold **among numerically accepted sources**, explicitly conditional on numerical acceptance;
- Wilson 95% binomial interval using **only** the accepted block count, with its actual denominator, plus the binomial plug-in Monte Carlo standard error;
- two explicit *sensitivity bounds* over all 24 planned blocks, assigning refused sources first all nonrejections and then all rejections. These are missing-outcome identification extremes, not confidence intervals;
- observed proportion where H1 selected exactly zero variance and median accepted deviance.

Use the same descriptive numerical reports on the paired **positive** generating states, but do not call the observed positive-source rejection fraction a qualified power estimate: the cutoff is unvalidated and the 24 independent blocks produce broad Monte Carlo intervals. No pooling across leverage conditions to artificially double the independent source count. Do not interpret positive and zero source states as independent.

With 24 true-null sources per support, even **zero** observed candidate exceedances permits a Wilson 95% upper bound around **13.8%**, so this stage is explicitly underpowered to establish a true 5% reference. It can falsify gross calibration and diagnose failures; it cannot prove accurate Type-I error, alternative power, or validity under varied sample sizes and nuisance designs. Prespecify subsequent independent, larger-source finite-null simulation or a mathematically justified design-specific restricted-likelihood reference if this initial gate supports progression.

## Original archive and no-release boundary

Six disjoint four-block shards [0,4), [4,8), [8,12), [12,16), [16,20), [20,24) run on an identical exact GitHub PR merge checkout. Each shard writes all eight paired source variants per four blocks, including numerical refusals, and a source SHA256/seed/checkout manifest. Only an aggregate containing all six same-checkout SHA256-verified shards and **exactly all** 96 distinct source identities can compute the final stratified report. The final immutable original archive contains `cases.json`, `summary.json`, `source-commit.txt`, and `SHA256SUMS`.

Passing Python tests, GitHub CI, numerical optimization and archive checks alone is **engineering evidence**, not confirmation of a reference distribution. R58 is separate from CR2 fitted covariance estimation and does not validate 90% pointwise coefficient intervals or simultaneous whole-function bands. It does not identify MNAR point loss or latent whole-participant selection. Research issues #289 and #296 stay OPEN, protected `main` unchanged, no public stable inference API promotion, no 1.2 tag, and no PyPI publishing.
