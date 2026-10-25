---
title: Interactive gaze method selector
description: Research-first guidance among stable 1.2.0 analysis routes, with explicit inference limits.
---

# Interactive method selector

Select the **observed data support**, scientific target, clustering and uncertainty claim. This is a navigation aid, **not a statistical estimator**. Results indicate a suitable *starting point*, not an automatic or unique correct model.

<div class="et-tool" id="et-method">
  <div class="et-control-grid">
    <div><label for="et-data">Observation grid</label><select id="et-data"><option value="dense">Common aligned x/y grid</option><option value="paired">Paired sparse x/y times</option><option value="async">Coordinate-asynchronous x/y</option></select></div>
    <div><label for="et-goal">Research objective</label><select id="et-goal"><option value="variation">Modes of gaze variation</option><option value="effects">Time-varying predictor effects</option><option value="prediction">Predict a partial gaze path</option><option value="categorical">Binary, grouped-binomial or count response</option><option value="recurrence">Recurrence and nonlinear dynamics</option></select></div>
    <div><label for="et-hierarchy">Independent sampling structure</label><select id="et-hierarchy"><option value="independent">Independent curves</option><option value="repeated">Repeated trials within participants</option></select></div>
    <div><label for="et-uncertainty">Claim to evaluate</label><select id="et-uncertainty"><option value="descriptive">Descriptive or exploratory</option><option value="pointwise">Pointwise effect or prediction</option><option value="simultaneous">Nominal whole-function confidence band</option><option value="missing">Mechanism of missing gaze</option></select></div>
  </div>
  <div class="et-result" data-et-recommendation aria-live="polite" aria-atomic="true">
    <strong data-et-method-name>Common-grid functional PCA</strong>
    <p data-et-method-input>Default: aligned common grid, gaze variation.</p>
    <p data-et-method-note>Interpret the fitted components against the recorded units and design.</p>
    <a data-et-method-link href="../../workflows/fpca-exploration/">Read the method and example</a>
  </div>
  <div class="et-share-control">
    <label for="et-share-link">Bookmarkable method selection</label>
    <input id="et-share-link" type="text" readonly aria-describedby="et-share-status" value="">
    <div class="et-tool-actions"><button type="button" id="et-copy-link">Copy selection URL</button></div>
    <p id="et-share-status" role="status" aria-live="polite">Selections are encoded in the browser URL; no settings are uploaded.</p>
  </div>
</div>

<noscript>Interactive guidance requires JavaScript. Use the [fully readable ten-route comparison](../articles/choosing-the-ten-workflows.md) instead.</noscript>

!!! warning "Scientific limitations are not optional"
    A recommended route does not imply calibrated confidence intervals, a causal effect, or identification of an outcome-dependent missing-gaze mechanism. Whole-function W3 inference and field MNAR interpretation remain restricted by issues [#289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289) and [#296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296). For unusual combinations (e.g. repeated binary trajectories on asynchronous coordinates), return to the [method comparison](workflow-comparison.md) rather than forcing a single estimator.

**Next:** [Input schemas](../guides/input-schemas.md) · [Workflow comparison](workflow-comparison.md) · [Runnable tutorials](../quickstart.md)
