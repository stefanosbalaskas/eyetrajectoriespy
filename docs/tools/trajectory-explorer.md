---
title: Interactive synthetic gaze trajectory explorer
description: Explore synthetic planar observations, time curves, descriptive spread and deliberate missingness without claiming empirical validity.
---

# Interactive trajectory explorer

Explore how *one deterministic teaching simulation* looks as a spatial path and a time-indexed coordinate. Move the trial slider or hide sample points. No data are uploaded or sent to a server. All charts are generated locally in the browser.

<div class="et-tool" id="et-trajectory">
  <div class="et-control-grid">
    <div><label for="et-trial">Synthetic example trial <output id="et-trial-value" for="et-trial">1</output></label><input type="range" id="et-trial" min="0" max="5" step="1" value="0"></div>
    <div><label for="et-loss">Illustrative missing samples <output id="et-loss-value" for="et-loss">0%</output></label><input type="range" id="et-loss" min="0" max="50" step="10" value="0"></div>
  </div>
  <p id="et-observed-count" aria-live="polite">61 of 61 synthetic samples displayed.</p>
  <div class="et-chart-grid">
    <div class="et-chart-box"><strong>Planar gaze (x,y)</strong><svg id="et-planar" viewBox="0 0 580 330" role="img" aria-label="Synthetic planar gaze"></svg></div>
    <div class="et-chart-box"><strong>Time-indexed x(t)</strong><svg id="et-timeseries" viewBox="0 0 580 330" role="img" aria-label="Synthetic horizontal gaze over time"></svg></div>
  </div>
  <p class="et-tool-legend">Blue dots = retained synthetic observations; dashed teal = fully known synthetic generating path, displayed only because this is a simulation. Shading = ±1 descriptive SD of six synthetic curves at each time, **not** a confidence or prediction interval. The known synthetic path is not an imputation algorithm.</p>
</div>

<noscript>Live plots require JavaScript. See the static [planar figure](../assets/trajectory-field.svg) and [worked 2-D example](../examples/evidence-inspection.md).</noscript>

## Scientific interpretation

- The same points have different geometric meaning in x/y space and in x(t) time space.
- With missing samples, observed support shrinks. A plotted full generating curve is *unobservable in real datasets* unless separately established.
- Descriptive variation between six illustrative curves is not uncertainty about a fitted population parameter. In particular, it does not resolve W3 whole-function band undercoverage.
- Device-level calibration, missingness, sampling units and AOI definitions must be justified *outside* this interactive toy simulation.

**Continue:** [From data to method](../start/data-to-method.md) · [Real workflow examples](../quickstart.md) · [Scientific contracts](../concepts/contracts.md)
