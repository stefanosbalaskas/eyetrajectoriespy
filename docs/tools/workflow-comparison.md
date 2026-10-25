---
title: Compare ten stable workflows
description: Filter stable module-scoped W1–W4 eyetrajectoriespy 1.2.0 workflows by question, input support and reporting needs.
---

# Compare ten stable workflows

The ten workflow orchestration routes were published with **1.2.0** as module-scoped APIs. A workflow organizes scientific decisions and records; it is not a guarantee of calibrated statistical inference. Select a scientific question to narrow the table. The entire table remains readable with JavaScript disabled.

<div class="et-tool" data-et-collection>
  <div class="et-control-grid">
    <div><label for="et-compare-question">Research need</label><select id="et-compare-question" data-et-filter="question"><option value="all">All ten workflows</option><option value="variation">Functional variation</option><option value="sparse">Sparse observations</option><option value="hierarchy">Repeated trials</option><option value="effects">Predictor effects</option><option value="outcomes">Non-Gaussian responses</option><option value="prediction">Partial-path prediction</option><option value="dynamics">Recurrence / dynamics</option></select></div>
    <div><label for="et-compare-search">Search method</label><input id="et-compare-search" data-et-search type="search" placeholder="e.g., covariance, binomial, paired"></div>
  </div>
  <p data-et-count aria-live="polite">10 of 10 entries shown</p>
  <div class="et-table-wrap">
    <table>
      <thead><tr><th scope="col">Stable entry point</th><th scope="col">Observed data and estimand</th><th scope="col">Required reporting / boundary</th></tr></thead>
      <tbody>
        <tr data-et-entry data-question="sparse variation"><td><code>run_sparse_fpca_workflow()</code></td><td>One sparse functional coordinate; mean/covariance/modes</td><td>Native timestamps, smoothing, noise, PSD and score failures</td></tr>
        <tr data-et-entry data-question="sparse variation"><td><code>run_sparse_mfpca_workflow()</code></td><td>Paired sparse x/y, joint covariance</td><td>Shared observed times and cross-channel covariance; not two separate scalar fits</td></tr>
        <tr data-et-entry data-question="sparse variation"><td><code>run_sparse_mfpca_async_workflow()</code></td><td>Coordinate-asynchronous x/y times</td><td>Separate time support per channel, never invented pairing</td></tr>
        <tr data-et-entry data-question="sparse hierarchy variation"><td><code>run_sparse_multilevel_workflow()</code></td><td>Sparse participant/trial functions</td><td>Cluster IDs, decomposition and independent-unit support</td></tr>
        <tr data-et-entry data-question="sparse prediction"><td><code>run_sparse_prediction_workflow()</code></td><td>Prediction from partially observed trajectories</td><td>Train/calibration separation, horizon and coverage scope</td></tr>
        <tr data-et-entry data-question="variation"><td><code>run_fpca_workflow()</code></td><td>Common-grid continuous trajectories</td><td>Coordinate scaling, rank selection, fit support</td></tr>
        <tr data-et-entry data-question="effects"><td><code>run_function_on_scalar_workflow()</code></td><td>Functional effect of scalar covariates</td><td>Design matrix, independence, inferential target</td></tr>
        <tr data-et-entry data-question="effects hierarchy"><td><code>run_functional_mixed_effects_workflow()</code></td><td>Repeated-trial functional effects</td><td>Random effects, covariance, cluster resampling; W3 limitation #289</td></tr>
        <tr data-et-entry data-question="outcomes effects"><td><code>run_generalized_functional_workflow()</code></td><td>Binary / grouped-binomial / count functions</td><td>Family/link, denominators, exposure and hierarchy</td></tr>
        <tr data-et-entry data-question="dynamics"><td><code>run_recurrence_workflow()</code></td><td>Recurring states and nonlinear structure</td><td>Embedding, delay, radius, Theiler exclusion and RQA limits</td></tr>
      </tbody>
    </table>
  </div>
</div>

<noscript>The filtering controls require JavaScript; the comparison table stays visible without them.</noscript>

The [original ten-workflow article](../articles/choosing-the-ten-workflows.md) gives the exact scientific decision sequence, and the [product qualification report](../validation/one-dot-two-workflow-product-qualification.md) gives the engineering evidence. This table does **not** supersede documented preconditions, exclusions or scientific refusal behavior.
