---
title: Visual methods explorer — gaze, FPCA, inference and nonlinear dynamics
description: Explore 12 source-linked deterministic eyetrajectoriespy visualizations grouped by scientific question, with guardrails for interpreting figures.
---

# Explore methods through figures

A researcher should be able to **recognize what a method shows before copying code**. This visual explorer collects 12 images already produced by the existing deterministic documentation scripts. These are **not new data or independently calibrated claims**.

[Start with an analysis path](../start/first-analysis.md){ .md-button .md-button--primary }
[Complete generated figure gallery](../methods/visual-gallery.md){ .md-button }
[Method selector](method-selector.md){ .md-button }

<div class="et-story-intro" markdown>
**Read the figure together with its assumptions.** *Synthetic teaching* images illustrate API behavior. *Diagnostic* images expose sensitivity or fit characteristics; neither category by itself proves instrument validity, statistical coverage, or missingness identification.
</div>

<div class="et-tool et-story-filter" data-et-collection>
  <div class="et-filter-grid">
    <div>
      <label for="et-story-topic">Scientific question</label>
      <select id="et-story-topic" data-et-filter="topic">
        <option value="all">All figure topics</option>
        <option value="representation">Represent and align gaze</option>
        <option value="fpca">FPCA modes and variance</option>
        <option value="sparse">Sparse covariance and scoring</option>
        <option value="inference">Regression and uncertainty</option>
        <option value="dynamics">Geometry and nonlinear analysis</option>
      </select>
    </div>
    <div>
      <label for="et-story-status">Figure purpose</label>
      <select id="et-story-status" data-et-filter="status">
        <option value="all">Both teaching and diagnostics</option>
        <option value="teaching">Synthetic teaching</option>
        <option value="diagnostic">Numerical / model diagnostics</option>
      </select>
    </div>
    <div>
      <label for="et-story-search">Find an analysis</label>
      <input id="et-story-search" type="search" data-et-search placeholder="FPCA, residual, surrogate, band">
    </div>
  </div>
  <p data-et-count aria-live="polite">12 of 12 figures shown</p>
  <div class="et-story-grid">
    <article class="et-story-card et-entry" data-et-entry data-topic="representation" data-status="teaching">
      <a class="et-story-image" href="../../assets/gallery/planar-trajectories.svg" aria-label="View Planar gaze trajectories SVG"><img loading="lazy" decoding="async" src="../../assets/gallery/planar-trajectories.svg" alt="Planar gaze trajectories — deterministic synthetic documentation figure"></a>
      <div class="et-story-copy">
        <p class="et-story-eyebrow">Whole-path spatial structure · Synthetic teaching</p>
        <h3>Planar gaze trajectories</h3>
        <p>Displays the recorded 2-D path concept; it cannot diagnose psychological attention or event quality.</p>
        <p class="et-story-actions"><a href="../../methods/visual-gallery/">Guide</a> · <a href="../../examples/evidence-inspection/">Method or evidence</a></p>
      </div>
    </article>
    <article class="et-story-card et-entry" data-et-entry data-topic="representation" data-status="teaching">
      <a class="et-story-image" href="../../assets/gallery/functional-simulation-truth-audit.svg" aria-label="View Observed support versus latent truth SVG"><img loading="lazy" decoding="async" src="../../assets/gallery/functional-simulation-truth-audit.svg" alt="Observed support versus latent truth — deterministic synthetic documentation figure"></a>
      <div class="et-story-copy">
        <p class="et-story-eyebrow">Missingness and known simulation truth · Synthetic teaching</p>
        <h3>Observed support versus latent truth</h3>
        <p>Illustrates how a simulator retains ground truth; real recordings do not expose their latent truth.</p>
        <p class="et-story-actions"><a href="../../examples/functional-simulation/">Guide</a> · <a href="../../guides/functional-simulation/">Method or evidence</a></p>
      </div>
    </article>
    <article class="et-story-card et-entry" data-et-entry data-topic="fpca" data-status="teaching">
      <a class="et-story-image" href="../../assets/gallery/fpca-component.svg" aria-label="View Functional principal-component shapes SVG"><img loading="lazy" decoding="async" src="../../assets/gallery/fpca-component.svg" alt="Functional principal-component shapes — deterministic synthetic documentation figure"></a>
      <div class="et-story-copy">
        <p class="et-story-eyebrow">FPCA modes of variation · Synthetic teaching</p>
        <h3>Functional principal-component shapes</h3>
        <p>Component perturbations summarize variation, not a latent cognitive mechanism.</p>
        <p class="et-story-actions"><a href="../../guides/fpca/">Guide</a> · <a href="../../methods/mathematical-reference/">Method or evidence</a></p>
      </div>
    </article>
    <article class="et-story-card et-entry" data-et-entry data-topic="fpca" data-status="teaching">
      <a class="et-story-image" href="../../assets/gallery/fpca-variance.svg" aria-label="View Cumulative explained functional variance SVG"><img loading="lazy" decoding="async" src="../../assets/gallery/fpca-variance.svg" alt="Cumulative explained functional variance — deterministic synthetic documentation figure"></a>
      <div class="et-story-copy">
        <p class="et-story-eyebrow">Variance explained across components · Synthetic teaching</p>
        <h3>Cumulative explained functional variance</h3>
        <p>Retained variance helps describe a fitted representation; it does not choose a confirmatory model automatically.</p>
        <p class="et-story-actions"><a href="../../guides/fpca/">Guide</a> · <a href="../../reference/function-equation-index/">Method or evidence</a></p>
      </div>
    </article>
    <article class="et-story-card et-entry" data-et-entry data-topic="sparse" data-status="teaching">
      <a class="et-story-image" href="../../assets/gallery/sparse-fpca-covariance.svg" aria-label="View Sparse latent covariance surface SVG"><img loading="lazy" decoding="async" src="../../assets/gallery/sparse-fpca-covariance.svg" alt="Sparse latent covariance surface — deterministic synthetic documentation figure"></a>
      <div class="et-story-copy">
        <p class="et-story-eyebrow">Sparse FPCA covariance · Synthetic teaching</p>
        <h3>Sparse latent covariance surface</h3>
        <p>Smoothing and PSD decisions affect the estimated covariance and must be reported.</p>
        <p class="et-story-actions"><a href="../../guides/sparse-irregular-fpca/">Guide</a> · <a href="../../validation/sparse-fpca-validation/">Method or evidence</a></p>
      </div>
    </article>
    <article class="et-story-card et-entry" data-et-entry data-topic="sparse" data-status="diagnostic">
      <a class="et-story-image" href="../../assets/gallery/sparse-fpca-score-conditioning.svg" aria-label="View Sparse score conditioning SVG"><img loading="lazy" decoding="async" src="../../assets/gallery/sparse-fpca-score-conditioning.svg" alt="Sparse score conditioning — deterministic synthetic documentation figure"></a>
      <div class="et-story-copy">
        <p class="et-story-eyebrow">Conditional covariance numerical behavior · Diagnostic</p>
        <h3>Sparse score conditioning</h3>
        <p>Condition numbers signal sensitivity, not certified uncertainty coverage.</p>
        <p class="et-story-actions"><a href="../../guides/sparse-irregular-fpca/">Guide</a> · <a href="../../validation/sparse-fpca-validation/">Method or evidence</a></p>
      </div>
    </article>
    <article class="et-story-card et-entry" data-et-entry data-topic="representation" data-status="teaching">
      <a class="et-story-image" href="../../assets/gallery/registration-warping.svg" aria-label="View Registration phase displacement SVG"><img loading="lazy" decoding="async" src="../../assets/gallery/registration-warping.svg" alt="Registration phase displacement — deterministic synthetic documentation figure"></a>
      <div class="et-story-copy">
        <p class="et-story-eyebrow">Temporal warping / alignment · Synthetic teaching</p>
        <h3>Registration phase displacement</h3>
        <p>Phase displacement should be reported rather than hidden in preprocessing.</p>
        <p class="et-story-actions"><a href="../../guides/registration/">Guide</a> · <a href="../../methods/mathematical-reference/">Method or evidence</a></p>
      </div>
    </article>
    <article class="et-story-card et-entry" data-et-entry data-topic="dynamics" data-status="teaching">
      <a class="et-story-image" href="../../assets/gallery/trajectory-curvature.svg" aria-label="View Continuous planar curvature SVG"><img loading="lazy" decoding="async" src="../../assets/gallery/trajectory-curvature.svg" alt="Continuous planar curvature — deterministic synthetic documentation figure"></a>
      <div class="et-story-copy">
        <p class="et-story-eyebrow">Signed local geometry · Synthetic teaching</p>
        <h3>Continuous planar curvature</h3>
        <p>Curvature is derived geometry and is sensitive to acquisition noise and smoothing choices.</p>
        <p class="et-story-actions"><a href="../../examples/trajectory-geometry/">Guide</a> · <a href="../../guides/trajectory-geometry/">Method or evidence</a></p>
      </div>
    </article>
    <article class="et-story-card et-entry" data-et-entry data-topic="inference" data-status="teaching">
      <a class="et-story-image" href="../../assets/gallery/function-on-scalar-coefficient.svg" aria-label="View Time-varying predictor coefficient SVG"><img loading="lazy" decoding="async" src="../../assets/gallery/function-on-scalar-coefficient.svg" alt="Time-varying predictor coefficient — deterministic synthetic documentation figure"></a>
      <div class="et-story-copy">
        <p class="et-story-eyebrow">Functional regression and bands · Synthetic teaching</p>
        <h3>Time-varying predictor coefficient</h3>
        <p>A displayed band is method- and design-conditional, not universally calibrated.</p>
        <p class="et-story-actions"><a href="../../examples/function-on-scalar/">Guide</a> · <a href="../../guides/function-on-scalar/">Method or evidence</a></p>
      </div>
    </article>
    <article class="et-story-card et-entry" data-et-entry data-topic="inference" data-status="diagnostic">
      <a class="et-story-image" href="../../assets/gallery/functional-mixed-effects-residual-acf.svg" aria-label="View Repeated-trial residual autocorrelation SVG"><img loading="lazy" decoding="async" src="../../assets/gallery/functional-mixed-effects-residual-acf.svg" alt="Repeated-trial residual autocorrelation — deterministic synthetic documentation figure"></a>
      <div class="et-story-copy">
        <p class="et-story-eyebrow">Within-participant dependence · Diagnostic</p>
        <h3>Repeated-trial residual autocorrelation</h3>
        <p>Residual structure is a diagnostic; it does not select a covariance family without a declared rule.</p>
        <p class="et-story-actions"><a href="../../examples/functional-mixed-effects-residual-diagnostics/">Guide</a> · <a href="../../methods/functional-mixed-effects-residual-diagnostics/">Method or evidence</a></p>
      </div>
    </article>
    <article class="et-story-card et-entry" data-et-entry data-topic="dynamics" data-status="diagnostic">
      <a class="et-story-image" href="../../assets/gallery/multivariate-iaaft-diagnostics.svg" aria-label="View Multichannel surrogate diagnostics SVG"><img loading="lazy" decoding="async" src="../../assets/gallery/multivariate-iaaft-diagnostics.svg" alt="Multichannel surrogate diagnostics — deterministic synthetic documentation figure"></a>
      <div class="et-story-copy">
        <p class="et-story-eyebrow">Cross-channel spectrum preservation · Diagnostic</p>
        <h3>Multichannel surrogate diagnostics</h3>
        <p>Surrogate diagnostics describe a declared null and algorithmic mismatch, not all nonlinear structure.</p>
        <p class="et-story-actions"><a href="../../examples/multivariate-surrogates/">Guide</a> · <a href="../../methods/multivariate-surrogates/">Method or evidence</a></p>
      </div>
    </article>
    <article class="et-story-card et-entry" data-et-entry data-topic="inference" data-status="teaching">
      <a class="et-story-image" href="../../assets/gallery/wild-bootstrap-family-test.svg" aria-label="View Fixed-family wild-bootstrap tests SVG"><img loading="lazy" decoding="async" src="../../assets/gallery/wild-bootstrap-family-test.svg" alt="Fixed-family wild-bootstrap tests — deterministic synthetic documentation figure"></a>
      <div class="et-story-copy">
        <p class="et-story-eyebrow">Adjusted p-values for declared target families · Synthetic teaching</p>
        <h3>Fixed-family wild-bootstrap tests</h3>
        <p>Studentization and family definition govern interpretation; testing many targets post hoc is different.</p>
        <p class="et-story-actions"><a href="../../examples/fpcr-wild-bootstrap-family-tests/">Guide</a> · <a href="../../methods/mathematical-reference/">Method or evidence</a></p>
      </div>
    </article>
  </div>
</div>

<noscript>JavaScript is only needed for filtering. All twelve figure images, captions, and source links remain visible without it.</noscript>

## How to use a figure as research evidence

1. **Start with actual observations.** Declare sampling support, units, time origins and participant/trial identifiers. See [input schemas](../guides/input-schemas.md).
2. **Read the fitted estimand.** A component, predictor coefficient, covariance surface and adjusted p-value answer different questions. See [mathematical reference](../methods/mathematical-reference.md).
3. **Check failure-inclusive evidence.** Simulation figures are designed for teaching; independent tests and [research exclusions](../methods/limitations.md) govern stronger claims.
4. **Reproduce the figure.** The [full generated gallery](../methods/visual-gallery.md) is rebuilt in documentation CI, rather than being hand-drawn or manually altered for this explorer.

The existing [research evidence figure atlas](figure-explorer.md) remains separately labelled; its experimental results must not be mixed with these API teaching figures.

[Full figure atlas](../figures/index.md) · [Reproducible workflows](../articles/reproducible-workflow-bundles.md) · [Research evidence](../research/index.md)
