# W3 R6: original-source findings for genuinely asynchronous gaze

!!! danger "Successful source numerical fitting is not a validated statistical estimator"
    The experimental degree-five basis fit accepted **native jittered
    asynchronous timestamps** without fabricating observed gaze.
    Its estimated slope functions are **model-based predictions**
    on an illustration grid. The results do not qualify the basis,
    model assumptions, confidence intervals, hypothesis tests,
    a MAR/MNAR correction, or a new public API.

## Original verification

Original [scientific workflow #38220034003](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/38220034003)
retained GitHub Actions artifact **`11733915603`**,
`w3-r6-native-asynchronous-basis-original-evidence`.
It contains **all 288** original case records, summary JSON,
the unmodified original Matplotlib figure
`source-async-basis.svg`, workflow source identity and checksums.
The ZIP was independently downloaded; **4/4 original source
SHA256 entries matched**. Original checkout-source SHA recorded
`3f5798fdcb55a13412bbdb94a7f34d30fc39aac5` (may be
a transient pull-request checkout commit).

The original code and 3.11–3.13 Python reference-contract
tests passed: **288/288 case evaluations completed with zero
numerical/source-integrity exceptions**, 96 per loss mechanism.
Actual observed timestamps and coordinate measurements were
unchanged. The experimental least-squares computations agreed
with a separately derived reduced-QR solve, to the preregistered
numerical tolerance. Current supported W3 common-grid regression
explicitly rejected these native asynchronous inputs in all
original cases.

The design generated **96 independent blocks**, each with
96 independent curves. The loss mechanisms were **paired**
within block, sharing original jittered times, source responses,
condition assignments and loss uniforms: MCAR, condition-dependent
MAR, latent-response-dependent MNAR. All curves have independent
measurement-time jitter; each selected curve loses a contiguous
eight-observation source interval. There are **288 scenarios,
not 288 independent source blocks**.

## Fixed-degree native time-basis regression results

The model was fixed in advance: degree-five Legendre basis for
the intercept and condition slope functions, without automatic
degree selection. Fitted samples were *original recorded
measurements at original native times*. Coefficients predicted
slope functions on the common illustration grid only after
regression fitting.

Mean known-truth **full slope-function RMSE**:

| Recording-loss mechanism | Complete jittered-source model | Observed-data curve-balanced weighting | Observed-data sample-weighted |
|---|---:|---:|---:|
| MCAR | 0.01305 | **0.01377** | 0.01400 |
| MAR on observed condition | 0.01305 | **0.01384** | 0.01397 |
| Latent-response-dependent MNAR | 0.01305 | **0.01386** | 0.01411 |

![W3 R6 original-audit derived full-function slope RMSE under native asynchronous time-basis regressions](../assets/research/w3-r6-asynchronous-basis-mean-rmse-20261012.svg)

*These numbers are source-audited simulated-regression RMSEs in
normalized generated response units, not empirical gaze-device
errors. The original SVG and full source ledger remain in the
GitHub artifact.*

Curve-balanced weighting produced modestly smaller mean slope
RMSE than sample-weighting in each of the three simulated
settings. It ensures **equal total statistical weight per
independent curve** despite unequal recording lengths; the
sample-weighted alternative assigns more total influence to
curves with more observed samples. These are two explicitly
different numerical objectives, not a proof that either is
universally more efficient or less biased.

### Signed midpoint selection and its uncertainty

For the first response dimension, the average predicted slope
difference **versus the same block's full-jittered source
model** was:

| Mechanism | Curve-balanced mean signed difference | 95% independent-block MC interval | Sample-weighted mean signed difference |
|---|---:|---:|---:|
| MCAR | −0.0004 | −0.0016 to +0.0008 | −0.0004 |
| MAR on condition | +0.0006 | −0.0007 to +0.0019 | +0.0007 |
| Latent MNAR | **−0.0051** | **−0.0066 to −0.0037** | **−0.0066** |

Under latent-MNAR selection the sample-weighted model showed
mean difference −0.0066 (95% independent-block interval
**−0.0083 to −0.0050**). Both approaches therefore retained
signed selection effects under this source mechanism.

The MNAR result is not a general claim about missing gaze.
Its data-generating probability depends on the **unobserved
midpoint residual**, which a researcher with only incomplete
recordings cannot recover merely by declaring a smooth basis.
No feasible missingness model, IPW correction or identification
claim was implemented.

Average observed sample counts across all 96 curves were
approximately **2,703.7 (MCAR)**, **2,692.4 (MAR)** and
**2,652.4 (MNAR)** compared with 2,976 source samples without
recording loss. The higher proportion of measured time points
does not by itself validate model assumptions or confidence
intervals.

## Nonqualification boundaries

1. **Model predictions are not observed gaze.** The smooth
   common-grid functions come from a declared Legendre
   expansion, not from deterministic interpolation of
   missing sensor measurements.
2. Degree five was deliberately prespecified; the true
   functions are smooth but need not be exactly represented
   by this degree. Performance can differ with polynomial
   basis misspecification, other temporal dynamics, rapid
   saccades or nonstationary device noise.
3. Only independent-curve input was evaluated. **Repeated
   participant trials, participant random effects, and
   hierarchical dependence were not modelled here.**
4. Original W3 fixed-HC1 simultaneous-band undercoverage
   remains unresolved. This experiment **does not calculate
   or validate new standard errors, simultaneous intervals,
   p-values, Bayesian coverage or model selection**.
5. The fitted model, source dataset, analysis scripts and
   Python cross-version contracts remain on a draft
   research branch. They have not been promoted into
   production `eyetrajectoriespy`.

[Prespecified R6 protocol](w3-r6-native-asynchronous-basis-protocol.md)
· [Missing-gaze observation-process blocker #296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296)
· [Separate W3 uncertainty blocker #289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289).

Stable published **1.1.0** and unreleased
development **`1.2.0rc2.dev0`** remain unchanged, with
`production_release_ready=false`. No package tag, PyPI
publication or statistical-method approval follows.
