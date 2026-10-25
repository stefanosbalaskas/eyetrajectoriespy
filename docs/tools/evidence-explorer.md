---
title: Searchable research evidence explorer
description: Filter R76–R95 W3 research by scientific question and evidence type without confusing research with stable software.
---

# Research evidence explorer

This curated research map links to **existing original and independently audited documentation**; filtering changes navigation only. No pooled coverage estimate or calibration judgment is recomputed in the browser.

!!! warning "Evidence status"
    General nominal-90% whole-function W3 calibration and field missing-gaze MNAR identification **remain unqualified**. Stable Python 1.2.0 package release status does not change these statistical limits ([#289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289), [#296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296)).

<div class="et-tool" data-et-collection>
  <div class="et-filter-grid">
    <div><label for="et-evidence-family">Scientific topic</label><select id="et-evidence-family" data-et-filter="topic"><option value="all">All topics</option><option value="coverage">Functional inference</option><option value="missingness">Observed missingness</option><option value="audit">External audit</option><option value="bounds">Exact identified sets</option></select></div>
    <div><label for="et-evidence-era">Research period</label><select id="et-evidence-era" data-et-filter="era"><option value="all">All series</option><option value="early">R76–R83</option><option value="middle">R84–R92</option><option value="late">R93–R95</option></select></div>
    <div><label for="et-evidence-search">Search studies</label><input id="et-evidence-search" data-et-search type="search" placeholder="e.g., leverage or selective return"></div>
  </div>
  <p data-et-count aria-live="polite">9 of 9 entries shown</p>
  <div class="et-entry-grid">
    <article class="et-entry" data-et-entry data-topic="coverage" data-era="early"><h3>R76 · Independent leverage support</h3><p>Functional-band inclusion under leverage stress; participant support and whole-function inference remain separate questions.</p><p><a href="../../articles/how-independent-leverage-support-affects-coverage/">Study interpretation</a></p></article>
    <article class="et-entry" data-et-entry data-topic="coverage" data-era="early"><h3>R78 · Temporal covariance</h3><p>Generator-specific time dependence and uncertainty behavior; not global 90% coverage qualification.</p><p><a href="../../articles/w3-temporal-covariance-robustness-r78/">Study interpretation</a></p></article>
    <article class="et-entry" data-et-entry data-topic="coverage" data-era="early"><h3>R80 · Heavy-tailed independent units</h3><p>Student-t5 stress design with original source plots and methodological caveats.</p><p><a href="../../articles/w3-student-t5-heavy-tail-inference-r80/">Study interpretation</a></p></article>
    <article class="et-entry" data-et-entry data-topic="missingness" data-era="early"><h3>R82 · Retention versus support</h3><p>High sample retention need not imply adequate independent-unit evidence.</p><p><a href="../../articles/w3-response-dependent-gaze-loss-r82/">Study interpretation</a></p></article>
    <article class="et-entry" data-et-entry data-topic="audit" data-era="middle"><h3>R84 · Independent external validation</h3><p>What separately recovered missing outcomes can identify under an explicitly defined ascertainment design.</p><p><a href="../../articles/w3-external-validation-mnar-identification-r84/">Study interpretation</a></p></article>
    <article class="et-entry" data-et-entry data-topic="audit" data-era="middle"><h3>R88 · Selective audit return</h3><p>Assumed return-process sensitivity; randomized invitation alone does not guarantee outcome recovery.</p><p><a href="../../articles/w3-r88-return-audit-sensitivity/">Study interpretation</a></p></article>
    <article class="et-entry" data-et-entry data-topic="bounds" data-era="late"><h3>R93 · Exact observational equivalence</h3><p>Distinct latent populations may induce the same observed law; invitation rates are not complete identification.</p><p><a href="../../articles/w3-r93-exact-observed-law-nonidentification/">Study interpretation</a></p></article>
    <article class="et-entry" data-et-entry data-topic="bounds" data-era="late"><h3>R94 · Externally assumed completion floor</h3><p>Conditional sharp sets given a real-world completion guarantee, not an estimated return rate.</p><p><a href="../../articles/w3-r94-external-audit-completion-bounds/">Study interpretation</a></p></article>
    <article class="et-entry" data-et-entry data-topic="bounds" data-era="late"><h3>R95 · Return direction</h3><p>Monotone response-direction assumptions can narrow a conditional population identified set without revealing the true mechanism.</p><p><a href="../../articles/w3-r95-monotone-audit-return-identification/">Study interpretation</a></p></article>
  </div>
</div>

<noscript>Filtering requires JavaScript, but all study summaries and citations are available without scripting.</noscript>

[Full R76–R95 chronology](../research/studies.md) · [Source archive](../development/research-development-hub.md) · [Evidence vs qualification](../articles/evidence-vs-qualification.md)
