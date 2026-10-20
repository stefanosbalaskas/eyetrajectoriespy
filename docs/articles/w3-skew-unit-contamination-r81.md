---
title: When functional confidence bands encounter skewed, contaminated heavy-tailed units
description: Independently audited R81 Student-t5 and asymmetric Bernoulli unit-contamination stress test
---

# When functional confidence bands encounter skewed, contaminated heavy-tailed units

**Scientific research article · 20 October 2026 · Original R81 and independent R81-A numerical audit**

!!! danger "Research-only, not qualified nominal 90% confidence bands"
    These results concern **fully observed, synthetic, Gaussian-conditional Student-t5 trajectories with a prespecified rare asymmetric unit shock**. They do not derive from actual participant recordings. The candidate implementations remain isolated in [R81 research PR #417](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/417) and [independent numerical audit PR #418](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/418). W3 inference blocker #289 and response-dependent gaze-loss blocker #296 remain open; stable eyetrajectoriespy 1.1.0 is unchanged and 1.2 is unreleased.

## Rationale: covariance and Student-t tails do not exhaust observational failures

The independently audited [R79 study](w3-nonseparable-coordinate-covariance-r79.md) challenged the assumption of independent gaze coordinates by changing the Gaussian spatial-temporal dependence. [R80](w3-student-t5-heavy-tail-inference-r80.md) retained that conditional dependence but introduced shared Student-t5 radial shocks **at the independent participant or curve level**. In both cases, the previously frozen data-estimated HC3 covariance regularizations improved whole-functional-slope inclusion over the original HC3 Gaussian baseline under certain severe leverage designs, while significant undercoverage persisted.

R81 tests a different departure: a small probability of **one-sided, persistent contamination of an entire unit's two-dimensional time series**, in addition to the independent-unit Student-t5 process. Such asymmetry can affect tail behavior and the slope's joint sampling distribution even when its mean is centered at zero and its covariance can be calculated exactly. This is a stylized falsification of the *unchanged* procedures, not a model of any particular eye-tracker's calibration failure or sensor dropout.

## A new, prospectively frozen generating model

The [R81 design](https://github.com/stefanosbalaskas/eyetrajectoriespy/blob/research/w3-r81-new-unit-contamination-skew-stress-20261020/docs/development/w3-r81-prospective-student-t5-skew-contamination.md) was committed before seeing the 32 new generating blocks' outcomes. For independent observational unit i, its measurement error at time t and gaze coordinate d can be written

$$
E_i(t,d)=s_i\left[
R_iG_i(t,d)+A(B_i-p)H(t,d)
\right],
$$

where $G_i$ is the R80 nonseparable, centered Gaussian functional innovation (including shared participant random effects when applicable), $R_i=\sqrt{3/V_i}$ with $V_i\sim\chi^2_5$ is a single positive Student-t5 radial shock **shared by all trials and coordinates of that unit**, and $B_i\sim\mathrm{Bernoulli}(p)$ is an *independent* rare event with **p=.08**. The contamination amplitude is **A=.16**, with fixed signed trajectory shape

$$
H(t,d)=(0.75+0.25t)\begin{bmatrix}1 & -0.65\end{bmatrix}_d,
\qquad 0\leq t\leq1.
$$

The two coordinates have opposing contamination effects; within a source unit, this shock persists across the entire 31 × 2 trajectory and, for participants, all three repeated trials. Centering by p ensures that the original population slope is unchanged. Nevertheless, the innovation distribution is asymmetric: rare positive $B_i-p=0.92$ shocks contrast with the more common negative $B_i-p=-0.08$ shocks.

The Gaussian component retains trial AR(1) correlation **rho=.72**, trial marginal SD $0.04(0.70+0.60t)$ and time-varying cross-coordinate correlation $q(t)=0.15+0.65t$. The repeated-participant design retains a shared latent Gaussian term with coordinate correlation **0.45**. The independent unit scale $s_i$ equals 1 under the constant-variance control or $1+0.75|x_i|$ under predictor-dependent heteroskedasticity. The new Bernoulli shock is independent of the Gaussian innovations and of the Student-t5 radial scales.

![Prespecified centered Bernoulli contamination and its analytic share of source marginal variance](../assets/research/w3-r81-analytic-skew-contamination-law.svg)

*Figure 1.* Analytic depiction of the **generating mechanism**, not a fitted contamination probability for an actual gaze recording. The rare unit shock has a time-varying signed profile, and its additional source-known marginal variance differs by coordinate and independent-unit design.

The known source-unit variance must account for the contamination:

$$
V_i(t,d)/s_i^2=V_G(t,d)+A^2p(1-p)H(t,d)^2,
$$

where $V_G$ is the variance of the R80 Gaussian-conditional Student-t5 unit process, equal to its unconditionally finite Gaussian covariance because $E(R_i^2)=1$. The additional term is a rank-one functional covariance contribution, not merely a change to the Gaussian-conditional correlation parameters.

Each new primitive generating block was evaluated under two observation-unit designs (**72 independent curves**; **36 participants with three complete trials**), two extreme $x=\pm4$ independent-unit support counts (**2 or 16**), and two variance laws (**constant or predictor-dependent**). There are **256 original case-condition datasets**, but only **32 independently generated primitive source blocks in each fixed design/support/variance cell**. Within each primitive block, source innovations are paired across the leverage/variance treatments.

## The correct source-known reference is now a two-part non-Gaussian mixture

A Gaussian covariance reference is not an exact generating-law benchmark for this simulation. R81 instead uses a source-known joint Student-t5 **and skew-contamination** reference. For the fitted source's fixed slope OLS weights $a_i$ and known heteroskedasticity scales $s_i$, each reference draw b independently generates all unit-specific Student-t5 radial factors $R_{ib}$ and Bernoulli indicators $B_{ib}$, then constructs

$$
Q_b=\sqrt{\frac{\sum_i(a_is_iR_{ib})^2}{\sum_i(a_is_i)^2}},
\qquad
S_b=\frac{\sum_i a_is_i(B_{ib}-p)}{\sqrt{\sum_i(a_is_i)^2}}.
$$

A fresh Gaussian process $G_b(t,d)$ with the true unit covariance produces the standardized slope-error function

$$
Z_b(t,d)=
\frac{Q_bG_b(t,d)+AS_bH(t,d)}
{\sqrt{V_G(t,d)+A^2p(1-p)H(t,d)^2}}.
$$

The reference statistic is $\max_{t,d}|Z_b(t,d)|$ over all **62 functional slope positions**. Using a global Student-t radial factor, a symmetric contamination law, the old Gaussian oracle or an SE omitting the Bernoulli variance would represent different models.

The four *data-estimated* candidate methods remain **unchanged**: the original W3 Rademacher wild-HC1 reference; residual HC3 Gaussian; and positive-definite estimated HC3 covariance regularization at **λ=.25 and λ=.50**, each with the original seven-time-point within-coordinate diagonal smoother. Every original dataset archives **999 maximum-statistic values for each of the five references**, higher empirical 90th-percentile criticals and individual source-wise full-function truth-inclusion classifications. Reference draws are not new independent datasets; no tuning or source selection was performed after the outcomes.

## Results: full-function truth inclusion

![Independent source-level 31 by 2 whole-slope inclusion under Student-t5 and centered Bernoulli skew contamination](../assets/research/w3-r81-skew-contaminated-whole-band-inclusion.svg)

*Figure 2.* Each entry counts generating datasets whose **entire 31 × 2 slope function** is included by the nominal-90% band. Denominators are 32 independent new primitive blocks per experimental condition. The source-known mixture is a simulator-only benchmark.

| Predictor-dependent noise | Curves, 2 anchors | Participants, 2 anchors | Curves, 16 anchors | Participants, 16 anchors |
|---|---:|---:|---:|---:|
| Original W3 wild-HC1 | **1/32** | **5/32** | 14/32 | 26/32 |
| Original HC3 Gaussian | **10/32** | **16/32** | 26/32 | 27/32 |
| Frozen regularization λ=.25 | **21/32** | **20/32** | 29/32 | 31/32 |
| Frozen regularization λ=.50 | **24/32** | **24/32** | 30/32 | 32/32 |
| Source-known Student-t5 + skew mixture | 29/32 | 29/32 | 31/32 | 30/32 |

With only **two extreme predictor units** and predictor-dependent source variance, the original HC3 Gaussian reference includes the true full slope in **10/32 independent curves** and **16/32 repeated-participant datasets**. The frozen λ=.50 candidate increases inclusion to **24/32 in both designs**, whereas the source-known Student-t5/skew mixture yields **29/32 in both**.

Thus the fixed λ=.50 candidate still reaches only **75% empirical whole-slope truth inclusion** in either primary adverse cell. This is substantial undercoverage relative to nominal 90%. A finite 29/32 inclusion count for a simulator-known source law does not establish universal calibration either, especially with only 32 primitive source replications. Under 16 independent extreme predictors, results can be higher, including 32/32 participant λ=.50 inclusion; this finite-cell frequency does not certify general 90% coverage and might reflect conservative band widening.

### Prespecified constant-variance controls

The prespecified two-anchor **constant-unit-variance** cells gave the following complete-grid truth counts for baseline HC3, fixed λ=.25, fixed λ=.50 and source-known mixture, respectively: **23/32, 26/32, 26/32, 28/32** for curves, and **24/32, 28/32, 30/32, 30/32** for participants. Original wild-HC1 included **16/32** curves and **18/32** participants. The full 16-anchor constant-variance cells are archived in the independent source report. The design does not justify selecting only the most favorable regularizer or suppressing non-adverse comparison cells.

## Marginal standard errors and joint maximum-statistic thresholds

![Independently audited R81 lower-tail standard-error ratios and estimated simultaneous criticals](../assets/research/w3-r81-skew-se-tail-and-criticals.svg)

*Figure 3.* Adverse two-anchor heteroskedastic condition. The first panel shows the source average of each source's 10th percentile of **estimated/true marginal slope SE** over all 62 functional positions. The second panel shows average data-estimated Gaussian maximum-statistic criticals. Known true SE is only available to the simulator.

| Source-mean diagnostic | Original HC3 | Frozen λ=.25 | Frozen λ=.50 |
|---|---:|---:|---:|
| Curves, estimated/true SE lower-tail ratio | 0.505 | 0.604 | 0.656 |
| Participants, estimated/true SE lower-tail ratio | 0.454 | 0.478 | 0.498 |
| Curves, estimated Gaussian maximum critical | 2.626 | 2.924 | 3.043 |
| Participants, estimated Gaussian maximum critical | 2.227 | 2.789 | 2.993 |

The simulator-known **Student-t5 plus skew** reference's average critical in these same cells is **3.180 for curves** and **2.431 for participants**. These criticals must not be compared without their associated SE scales and joint covariance laws. Changes in full-band inclusion can arise from improvements to estimated marginal variance, larger estimated maximum criticals, or both; undercoverage remains after regularization in the hard cells.

## Independent numerical reconstruction

The original [R81 scientific run #39490888383](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39490888383) passed **12/12 scientific jobs**, including three Python-version source contracts, eight disjoint simulation shards and one exact-checkout SHA256 aggregate. Original [artifact #12295607688](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39490888383/artifacts/12295607688) contains all **256/256 source cases, zero refusals**, pinned to scientific checkout `698bf1eb80a9e856bfc2e0b5bdc362f425a75dc1`.

An independently coded [R81-A actual source replay #39491187099](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39491187099) passed **4/4 audit jobs**, independently reconstructing the **same 256 original X/Y source datasets and all 1,278,720 raw original conditional maximum-statistic values**. The replay checked the correctly ordered unit-specific Student-t radial and Bernoulli draws, known extra contamination variance, true nonlinear maximum references, original package W3 numerical identities, candidate covariance factors, source truth-inclusion classifications and SHA256 original source identity. Separate independent numerical [artifact #12296301870](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39491187099/artifacts/12296301870) preserves the report.

Those workflows establish **numerical reproducibility of the stipulated simulation**, not observed-data coverage calibration. Unlike a controlled source-paired R80-vs-R81 comparison, the programmes use **different freshly generated source blocks**; the independent experiments also change the law. Comparisons cannot be interpreted as source-paired estimates of contamination's causal effect, and the combined Student-t5-plus-Bernoulli law does not separately isolate the effects of heavy tails and skewness.

## Interpretation and release boundary

The R81 result is narrower than evidence for a generally robust estimator. In the specified fully synthetic model with independent-unit Student-t5 radial noise and rare asymmetric unit shocks, fixed λ=.25/.50 regularization again improves empirical full-slope inclusion over baseline HC3 in the adverse source cells, but both methods remain below nominal 90% despite independent numerical reconstruction.

This test does **not** cover genuinely missing gaze samples, irregular observation times, detector-defined AOI uncertainty, actual camera calibration failure, skewness families beyond the one specified, or model selection and covariance learning in field recordings. The next decisive work should investigate **response-dependent observation loss**, not continue claiming estimator calibration from favorable synthetic sources.

**Final R81 decision:** W3 #289 and #296 **remain open**. No experimentally estimated W3 simultaneous-band method is qualified at nominal 90%, no inference API promotion occurs, stable release 1.1.0 remains unchanged and **eyetrajectoriespy 1.2/PyPI remains on release HOLD**.

[Read the R81 independent-unit contamination methods companion](independent-unit-skew-contamination-and-simultaneous-inference.md) · [Full numerical evidence ledger](../development/w3-r81-skewed-unit-evidence-ledger.md)
