# W3 R81: independently audited skew-contaminated Student-t5 source and original figure ledger

**Source/plot provenance · 20 October 2026 · research-only**

!!! danger "Numerical reproducibility is not general inference calibration"
    All original data are **fully observed synthetic heavy-tailed Gaussian-conditional sources** with a known centered rare asymmetric Bernoulli shock; no real eye tracker or actual MNAR loss is tested. W3 #289/#296 remain open and version 1.2/PyPI release stays on hold.

## Figure 1 — new generating asymmetric contamination law

![Prespecified centered rare unit-level contamination shock and analytic covariance contribution](../assets/research/w3-r81-analytic-skew-contamination-law.svg)

The original source model adds an independent unit-specific Bernoulli centered event with **p=.08**, amplitude **A=.16**, signed functional profile **(.75+.25t)[1,-.65]**, to the Student-t5 radial × nonseparable Gaussian unit innovations. The contamination shock is constant across the 31×2 trajectory and all three trials of a participant. It increases the source-known variance by **A²p(1−p)H²** and also creates cross-time/cross-coordinate covariance. The R81 source-known reference is therefore **Student-t5 plus asymmetric Bernoulli**, not R80's Student-t5-only oracle.

## Figure 2 — whole 31×2 generating slope truth inclusion

![R81 full-grid truth inclusion for original and regularized methods and known Student-t5 plus skew benchmark](../assets/research/w3-r81-skew-contaminated-whole-band-inclusion.svg)

| Predictor-dependent variance | Curves: 2 extreme units | Curves: 16 extreme units | Participants: 2 extreme units | Participants: 16 extreme units |
|---|---:|---:|---:|---:|
| Original W3 wild-HC1 | 1/32 | 14/32 | 5/32 | 26/32 |
| Baseline estimated HC3 Gaussian | 10/32 | 26/32 | 16/32 | 27/32 |
| Frozen λ=.25 estimated Gaussian | 21/32 | 29/32 | 20/32 | 31/32 |
| Frozen λ=.50 estimated Gaussian | 24/32 | 30/32 | 24/32 | 32/32 |
| **Simulation-known Student-t5 plus skew source** | 29/32 | 31/32 | 29/32 | 30/32 |

Each entry uses the actual independent source-denominator **n=32 newly generated primitive blocks per cell**, NOT 256 factorial-case replications and NOT 999 conditional reference draws. The successful event is **entire 31×2 known generating slope** contained simultaneously. In the primary two-anchor heteroskedastic cell, frozen λ=.50 includes **24/32 (75%)** of curves and participants; this is **not** generally nominal 90% calibrated inference.

Two-anchor **constant-variance** controls: baseline HC3 / λ=.25 / λ=.50 / source-known non-Gaussian law = **23/32, 26/32, 26/32, 28/32 curves** and **24/32, 28/32, 30/32, 30/32 participants**; wild-HC1 **16/32 curves and 18/32 participants**. The original immutable source report preserves all other cells and failed-source accounting.

## Figure 3 — source-specific lower-tail SE ratios and joint criticals

![R81 mean source-specific estimated marginal to true SE lower-tail and estimated Gaussian 90% criticals](../assets/research/w3-r81-skew-se-tail-and-criticals.svg)

| Two-anchor heteroskedastic source mean | Baseline HC3 | Fixed λ=.25 | Fixed λ=.50 |
|---|---:|---:|---:|
| Curves estimated/true SE 10th percentile | 0.505329 | 0.604494 | 0.656213 |
| Participants estimated/true SE 10th percentile | 0.454295 | 0.478274 | 0.497540 |
| Curves Gaussian max-statistic critical | 2.625530 | 2.924467 | 3.042587 |
| Participants Gaussian max-statistic critical | 2.227093 | 2.788894 | 2.992941 |

The **known Student-t5 plus skew simulation law** maximum critical averages **3.179659** for curves and **2.431226** for repeated participants in the adverse cell. Different critical values must not be compared without their accompanying SE scales or joint maximum-statistic distributions. The true SE is known only in synthetic generating-law source evidence.

## Exact scientific source identities and numerical verification

| Evidence item | Independently verified source |
|---|---|
| Preregistered original generating specification | [Research draft R81 PR #417](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/417), including a completed pre-result protocol |
| Original scientific source run | [Workflow #39490888383](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39490888383): **12/12 dedicated scientific jobs successful** |
| Original complete SHA256 evidence | [Artifact #12295607688](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39490888383/artifacts/12295607688) |
| Pinned actual original scientific checkout | 698bf1eb80a9e856bfc2e0b5bdc362f425a75dc1 |
| Independent real original-source reconstruction | [Research draft R81-A PR #418](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/418) |
| Independent mandatory original archive audit | [Workflow #39491187099](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39491187099): **4/4 dedicated audit jobs successful** |
| Independent reconstructed source report | [Artifact #12296301870](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39491187099/artifacts/12296301870) |
| Complete/attempted original source cases | **256/256 complete, zero refusals** |
| True independent primitive source denominator | **32 per design / support / variance cell** |
| Original independently re-created reference values | **256 sources × five references × 999 draws = 1,278,720 numerical maxima** |
| Data-estimated candidates (all unchanged) | Original wild-HC1, original HC3 Gaussian, fixed λ=.25 and fixed λ=.50 HC3 regularized Gaussian references |
| Source-known comparison | **Unit-specific Student-t5 chi-square radial and centered asymmetric Bernoulli mixture**; only simulator knows probability/amplitude/covariance |
| True unit variance | **R80 Gaussian-conditional unit variance + A²p(1−p)H²** |
| Research qualification | **Numerically audited only**; no general nominal-90% inference, no genuine observation-process loss |
| Public release decision | No inference method merge, stable 1.1.0 unchanged, version 1.2/PyPI HOLD, issues #289/#296 OPEN |

The original and independent implementations each reconstruct source X/Y and all five reference arrays; this tests source identities, RNG ordering, covariance formulas, conditional skewed Student-t5 sampling, reference quantiles and numerical correspondence. It does **not** provide new independent field validation. R80 and R81 source blocks were newly and separately generated, so **between-study differences are not source-paired causal effects**.

[Read R81 research article](../articles/w3-skew-unit-contamination-r81.md) · [Read rare unit-shock methods companion](../articles/independent-unit-skew-contamination-and-simultaneous-inference.md) · [Previous R80 heavy-tail evidence](w3-r80-student-t5-evidence-ledger.md)
