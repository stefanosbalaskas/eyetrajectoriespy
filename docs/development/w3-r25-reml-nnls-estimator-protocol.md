# R25 — experimental covariance-component estimation alternatives

**Research-only numerical preflight, not estimator superiority or confidence-interval calibration.** R24 documented that the original leverage-adjusted NNLS residual-moment operator is correct at its exact Gaussian expectation, while finite-sample noise often drives positive generating slope/trial variances to the zero boundary. Its eight fixed-design Gaussian tests share only two original generating blocks. This result supports investigating a statistically distinct estimator, **not** changing the original R20–R24 results or relaxing CR2 numerical refusal policy.

## Declared comparison and data access

The baseline is the original R20 leverage-adjusted, nonnegative four-component residual-moment estimator, including its disclosed numerical sensor floor. The alternative is a new **Gaussian restricted maximum likelihood (REML)** estimator for exactly the same specified covariance family, independently implemented using participant-block Cholesky factorization, generalized least-squares mean profiling and the restricted likelihood penalty `log|Zᵀ V⁻¹ Z|`.

The Gaussian REML objective, with `Z=sqrt(W)X`, `y_w=sqrt(W)y`, participant covariance `V_i(theta)=sum_k theta_k K_ik`, is

`0.5 * [sum_i logdet V_i + logdet(sum_i Z_iᵀ V_i⁻¹ Z_i) + y_wᵀ P(theta)y_w]`.

The analytic variance-component score is `0.5 [tr(P K_k) - y_wᵀ P K_k P y_w]`, converted to log-variance-parameter derivatives by multiplication by `theta_k`. This independently specifies a statistically motivated alternative to fitting many noisy residual outer products. Tests must verify the analytic gradient against finite differences and invariance of the restricted likelihood to fixed-mean shifts. Both methods see **only native observed trajectories, times, labels, predictors, weights and their own fitted residuals**—no generating covariance or primitive innovations.

REML optimizes **strictly positive bounded log-variance ratios** (limits −13.8 to 7 relative to the observed-data residual-variance reference), with 125 iterations maximum. It cannot yield literal zeros; estimates below `1e−4` of the observed residual-variance reference, or touching the lower optimization bound, are separately reported as *near-boundary*, not silently regarded as accurate positive recovery. All nonconvergence, fit errors and estimation refusals remain observed results. Initial values may come from observed-only NNLS, never from generator truth.

## Frozen fresh four-block numerical comparison

New master seed **202610153525** distinct from R20–R24. Four independent generating blocks; n=24/48; ordinary/extreme predictor leverage crossed with predictor-independent/dependent covariance mechanisms; one fixed Legendre-5 mean basis and **both separately fitted prespecified** shared/predictor-scaled covariance candidate structures. **64 paired model-family source cases**, only **4 independent source blocks**. Both estimators fit *identical* native source observations in each case. The four-component true generating variance values and matched/mismatched structure are annotated *after estimation*, exclusively to assess matched-family component recovery; mismatched-family estimates cannot be scored against structurally incompatible true parameters.

Report estimator fit/nonconvergence, near-zero/boundary component frequencies, sensor-floor frequency for NNLS, optimizer diagnostics for REML and median absolute relative component errors for matching nuisance families. Report each cell with **four independent generating blocks** denominator and transparent Monte Carlo uncertainty; no method-winner decision from this four-block pilot.

## Strict limits

Neither restricted Gaussian likelihood nor improved component point estimation proves a working covariance family appropriate for actual irregular gaze recordings; both use a parametric structure close to the simulation source. A likelihood model depends on Gaussian innovations and correct within-person covariance assumptions. Estimated working covariance in CR2/Satterthwaite also makes nuisance-estimation uncertainty relevant, currently unaccounted for. No nominal pointwise coverage, simultaneous functional band or empirical method selection is tested here. To qualify an alternative, subsequently require larger independently seeded samples, frequentist component recovery and numerical refusal accounting, nuisance-estimation-aware inference comparisons and real-source stress tests.

Original R20 41/256 failures and R22 32 numerical refusals remain unchanged; scientific blockers #289 and #296 open. No protected-main merge, public API promotion, version 1.2 tag or PyPI upload.
