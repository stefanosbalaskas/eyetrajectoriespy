---
title: Integration navigator — choose a Python gaze data source
description: Filter 14 Python gaze ecosystems by task and qualification status, then build a source-aware, no-upload analysis checklist.
---

# Find the right connection for your gaze data

Different tools solve different problems: **recording acquisition**, **event and sample processing**, **file and metadata exchange**, and **functional statistical modelling**. Search across the ecosystem and build a short, explicit data-to-method checklist without uploading anything.

<div class="et-connect-intro" markdown>
**Research-first principle:** a verified parser, a published Python package and a statistically qualified estimator are **three different things**. Status labels here describe their relationship to *this repository*, not a judgment of the external project's quality.
</div>

<div id="et-integration-navigator" class="et-connect">
  <section class="et-connect-panel" aria-labelledby="et-connect-discover">
    <h2 id="et-connect-discover">Explore Python packages and source readers</h2>
    <p>Filter by role, search the library name or research use, and open its integration guidance. Every status is intentionally scoped.</p>
    <div class="et-connect-form">
      <div>
        <label for="et-package-search">Search packages and tasks</label>
        <input id="et-package-search" type="search" placeholder="EyeLink, Neon, pupils, sparse…" autocomplete="off">
      </div>
      <div>
        <label for="et-package-group">Ecosystem role</label>
        <select id="et-package-group">
          <option value="all">Every role</option>
          <option value="acquisition">Acquisition / sample import</option>
          <option value="tables">Tables and schema validation</option>
          <option value="standards">Data standards / metadata</option>
          <option value="functional">Functional-data methods</option>
          <option value="companion">Companion analyses</option>
        </select>
      </div>
      <div>
        <label for="et-package-phase">Status in eyetrajectoriespy</label>
        <select id="et-package-phase">
          <option value="all">All statuses</option>
          <option value="preview">Pinned repository previews</option>
          <option value="example">Other runnable examples</option>
          <option value="optional">Existing optional extras</option>
          <option value="planned">Research candidates</option>
          <option value="comparison">External comparisons</option>
        </select>
      </div>
    </div>
    <div class="et-connect-meta">
      <p id="et-package-count" role="status" aria-live="polite">14 ecosystems indexed · Enable JavaScript for interactive filters</p>
      <button type="button" id="et-package-reset">Clear filters</button>
    </div>
    <div id="et-package-grid" class="et-connect-grid"></div>
    <p id="et-empty-results" class="et-connect-empty" hidden>No matching tools. Clear filters or select a broader research role.</p>
    <div id="et-package-fallback" markdown>
### Plain-text integration index

The same links remain usable with JavaScript disabled.

| Ecosystem | Role and integration status | Start here |
| --- | --- | --- |
| pandas / Polars / PyArrow | Tables · Runnable repository example | <a href="/eyetrajectoriespy/integrations/tabular-handoff/">Tabular handoff</a> |
| pymovements | Gaze preprocessing · Pinned 0.28.0 example | [Gaze handoff](pymovements-handoff.md) |
| SyeLink | EyeLink ASC parsing · Pinned 2.0.0 example | [EyeLink handoff](syelink-handoff.md) |
| Eye-Tracking-BIDS | Metadata standard · Narrow read-only preview | [BIDS inspection](bids-metadata-inspector.md) |
| PyNeon | Neon acquisition · Research candidate | [Acquisition guides](acquisition-and-bids.md) |
| eye2bids | Device export · Research candidate | [Acquisition guides](acquisition-and-bids.md) |
| EyeLinkIO | EDF parsing · External comparison | [EyeLink tools](eyelink-ecosystem.md) |
| PyeLink | EyeLink hardware control · External comparison | [EyeLink tools](eyelink-ecosystem.md) |
| Pandera | Schema validation · Research candidate | [Qualification roadmap](roadmap.md) |
| eyekit | Reading/fixation · Companion | [Acquisition guides](acquisition-and-bids.md) |
| PupEyes | Pupillometry · Companion | [Acquisition guides](acquisition-and-bids.md) |
| scikit-fda | Functional FDA · Existing optional extra | [Basis guide](../guides/basis-representations.md) |
| FDApy | Sparse functional FDA · Existing optional extra | [Sparse FPCA guide](../guides/sparse-irregular-fpca.md) |
| fdasrsf | Elastic registration · Existing optional extra | [Elastic guide](../guides/elastic.md) |
    </div>
  </section>
  <section class="et-connect-panel" aria-labelledby="et-connect-plan">
    <h2 id="et-connect-plan">Build a reproducible handoff checklist</h2>
    <p>Choose what supplied your data and what your recorder actually observed. This suggests **documentation to read**, not a model fit or acceptance decision.</p>
    <div class="et-connect-form et-connect-plan-form">
      <div>
        <label for="et-path-source">My original data source</label>
        <select id="et-path-source">
          <option value="table">pandas / Polars / Parquet</option>
          <option value="pymovements">pymovements</option>
          <option value="syelink">SyeLink / EyeLink ASC</option>
          <option value="bids">Eye-Tracking-BIDS</option>
          <option value="pyneon">PyNeon / Neon</option>
          <option value="eye2bids">eye2bids</option>
          <option value="eyelinkio">EyeLinkIO EDF</option>
          <option value="pyelink">PyeLink hardware</option>
          <option value="pandera">Pandera schema validation</option>
          <option value="eyekit">eyekit reading studies</option>
          <option value="pupeyes">PupEyes pupil studies</option>
          <option value="scikit-fda">scikit-fda</option>
          <option value="fdapy">FDApy</option>
          <option value="fdasrsf">fdasrsf</option>
        </select>
      </div>
      <div>
        <label for="et-path-support">Observed trajectory support</label>
        <select id="et-path-support">
          <option value="unknown">Uncertain / needs examination</option>
          <option value="aligned">Complete common time grid</option>
          <option value="sparse">Paired sparse / irregular times</option>
          <option value="async">Asynchronous x and y</option>
          <option value="repeated">Repeated trials / participants</option>
        </select>
      </div>
    </div>
    <div class="et-connect-path" aria-labelledby="et-path-summary">
      <h3 id="et-path-summary">Choose a source and support type</h3>
      <ol id="et-path-steps">
        <li>Preserve original device/export files and upstream parser version.</li>
        <li>Declare participant, trial, clock and coordinate semantics.</li>
        <li>Check the relevant <a href="../../start/data-to-method/">data-to-method guide</a>.</li>
      </ol>
      <p id="et-path-limitation">This planner does not read, upload, convert or validate participant recordings.</p>
      <div class="et-connect-links">
        <a id="et-path-guide" href="/eyetrajectoriespy/integrations/tabular-handoff/">Open source guide</a>
        <a id="et-path-method" href="../../start/data-to-method/">Open method guidance</a>
      </div>
      <div class="et-connect-actions">
        <button id="et-path-copy" type="button">Copy checklist</button>
        <button id="et-path-share" type="button">Copy shareable selection</button>
      </div>
      <textarea id="et-path-copy-text" class="et-connect-copy" hidden readonly aria-label="Selected checklist or link for manual copying"></textarea>
      <p id="et-path-status" role="status" aria-live="polite">Selections remain in your browser. No network request is made.</p>
    </div>
  </section>
</div>

<noscript>Interactive filtering and the checklist need JavaScript. The complete plain-text integration index above remains available, as do the [integration status details](index.md) and [data-to-method guide](../start/data-to-method.md).</noscript>

## What to do after choosing

<ol class="et-connect-journey">
  <li><strong>Acquire &amp; preserve.</strong> Keep device-export originals, conversion settings and library versions.</li>
  <li><strong>Represent observed support.</strong> Declare eye, time origin, pixel/degree geometry, masks and independent units.</li>
  <li><strong>Select the estimand.</strong> Use the <a href="../../start/data-to-method/">research decision guide</a> before method fitting.</li>
  <li><strong>Report limitations.</strong> Cite versioned source/analysis code and the unresolved coverage and missing-gaze boundaries.</li>
</ol>

## Evidence behind the design

This navigator adopts **task-first guides and public-dataset discovery** from [pymovements](https://pymovements.readthedocs.io/en/stable/), **narrative tutorial versus example gallery separation** from [MNE-Python](https://mne.tools/stable/auto_tutorials/index.html), **method-grouped examples** from [scikit-fda](https://fda.readthedocs.io/en/stable/auto_examples/), and **modality-specific tutorials** from [PyNeon](https://ncc-brain.github.io/PyNeon/). Those websites motivate *navigation design*, not claims that our package implements their complete capabilities.

!!! warning "Stable functionality is not established by an external package appearing here"
    The published **eyetrajectoriespy 1.2.0** optional extras and stable workflows are unchanged. The pinned pymovements and SyeLink interfaces, tabular conversion and narrow BIDS inspector are repository-level **examples**, not full real-device validation. The open [simultaneous inference issue #289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289) and [missing-gaze issue #296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296) remain unresolved. No data leave this documentation interface.

[All integration details](index.md) · [Qualification roadmap](roadmap.md) · [Reproducibility checklist](../reproducibility/checklist.md)
