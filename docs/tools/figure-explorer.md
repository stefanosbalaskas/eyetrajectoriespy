---
title: Filterable scientific figure atlas
description: Filter illustrative gaze, inference stress tests and missing-gaze research figures by topic and evidence class.
---

# Filterable scientific figure atlas

Browse a **curated subset of existing, source-linked figures**. These are *not* fresh numerical results. Figures labeled research evidence must be read with their original data-generating law, independent-unit denominators and limitations.

<div class="et-tool" data-et-collection>
  <div class="et-filter-grid">
    <div><label for="et-figure-topic">Topic</label><select id="et-figure-topic" data-et-filter="topic"><option value="all">All topics</option><option value="representation">Representation</option><option value="inference">Inference stress</option><option value="missingness">Missing gaze</option><option value="identification">Identified sets</option></select></div>
    <div><label for="et-figure-status">Evidence class</label><select id="et-figure-status" data-et-filter="status"><option value="all">All evidence classes</option><option value="teaching">Synthetic teaching</option><option value="research">Research artifact</option></select></div>
    <div><label for="et-figure-search">Search figures</label><input id="et-figure-search" data-et-search type="search" placeholder="Search figure title or study"></div>
  </div>
  <p data-et-count aria-live="polite">8 of 8 entries shown</p>
  <div class="et-entry-grid">
    <article class="et-entry" data-et-entry data-topic="representation" data-status="teaching"><img src="../../assets/trajectory-field.svg" alt="Conceptual synthetic planar gaze curves"><h3>Planar functional representation</h3><p class="et-meta">Synthetic teaching figure · time-indexed x/y</p><p><a href="../../concepts/representations/">Representation contract</a></p></article>
    <article class="et-entry" data-et-entry data-topic="representation" data-status="teaching"><img src="../../assets/gallery/sparse-mfpca-covariance-blocks.svg" alt="Synthetic paired planar covariance blocks"><h3>Sparse planar covariance</h3><p class="et-meta">Synthetic method illustration · paired coordinates</p><p><a href="../../guides/sparse-multivariate-fpca/">Sparse MFPCA guide</a></p></article>
    <article class="et-entry" data-et-entry data-topic="inference" data-status="research"><img src="../../assets/research/w3-r78-ar1-whole-band-coverage.svg" alt="R78 temporal dependence inference diagnostic"><h3>R78: temporal covariance</h3><p class="et-meta">Research stress experiment · not general calibration</p><p><a href="../../articles/w3-temporal-covariance-robustness-r78/">Evidence and limitations</a></p></article>
    <article class="et-entry" data-et-entry data-topic="inference" data-status="research"><img src="../../assets/research/w3-r80-student-t5-whole-band-coverage.svg" alt="R80 heavy-tail functional inference diagnostic"><h3>R80: heavy-tailed units</h3><p class="et-meta">Research stress experiment · source-defined conditions</p><p><a href="../../articles/w3-student-t5-heavy-tail-inference-r80/">Evidence and limitations</a></p></article>
    <article class="et-entry" data-et-entry data-topic="missingness" data-status="research"><img src="../../assets/research/w3-r82-missingness-retention-and-grid-refusal.svg" alt="R82 observed gaze retention and independent-support refusal"><h3>R82: observation support</h3><p class="et-meta">Source-backed selective missingness simulation</p><p><a href="../../articles/w3-response-dependent-gaze-loss-r82/">Evidence and limitations</a></p></article>
    <article class="et-entry" data-et-entry data-topic="identification" data-status="research"><img src="../../assets/w3-r93-sharp-binary-mean-sets.svg" alt="R93 exact binary identified sets"><h3>R93: exact observable law</h3><p class="et-meta">Conditional population identified sets, not confidence bands</p><p><a href="../../articles/w3-r93-exact-observed-law-nonidentification/">Read R93</a></p></article>
    <article class="et-entry" data-et-entry data-topic="identification" data-status="research"><img src="../../assets/w3-r94-sharp-interval-assumption-ladder.svg" alt="R94 externally assumed completion floor bounds"><h3>R94: completion guarantees</h3><p class="et-meta">Assumption-dependent exact set, not field ascertainment</p><p><a href="../../articles/w3-r94-external-audit-completion-bounds/">Read R94</a></p></article>
    <article class="et-entry" data-et-entry data-topic="identification" data-status="research"><img src="../../assets/w3-r95-monotone-direction-sharp-sets.svg" alt="R95 externally assumed monotone response direction bounds"><h3>R95: return-direction assumptions</h3><p class="et-meta">Conditional sharp population sets, not empirically known return direction</p><p><a href="../../articles/w3-r95-monotone-audit-return-identification/">Read R95</a></p></article>
  </div>
</div>

<noscript>Filtering requires JavaScript; all figures and source links remain visible without it.</noscript>

[Full figure atlas](../figures/index.md) · [Complete generated visualization library](../methods/visual-gallery.md) · [Original research ledgers](../development/research-original-figures.md)
