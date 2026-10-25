---
title: Local gaze CSV readiness inspector
description: Inspect time support, coordinate observations and clustering in browser without uploading gaze files or fitting any statistical model.
---

# Check the structure of your gaze data

Before choosing a method, examine a **long-format gaze CSV in your own browser**. The inspector flags structural issues such as duplicated timestamps, nonnumeric coordinates, missing observations and repeated trials. It does **not** upload data, convert timestamps, infer missingness mechanisms, run the package, or claim valid statistical uncertainty.

<div class="et-tool" id="et-data-audit">
  <form>
    <div class="et-control-grid">
      <div>
        <label for="et-csv-file">Choose a local CSV file (optional)</label>
        <input type="file" id="et-csv-file" accept=".csv,text/csv" aria-describedby="et-local-notice">
      </div>
      <div>
        <label for="et-time-unit">Recorded time unit</label>
        <select id="et-time-unit">
          <option value="undeclared">Not declared</option>
          <option value="seconds">Seconds</option>
          <option value="milliseconds">Milliseconds</option>
          <option value="normalized">Normalized 0–1 time</option>
        </select>
      </div>
      <div>
        <label for="et-coordinate-unit">Recorded coordinate system</label>
        <select id="et-coordinate-unit">
          <option value="undeclared">Not declared</option>
          <option value="normalized">Normalized screen position [0,1]</option>
          <option value="pixels">Pixels</option>
          <option value="degrees">Visual degrees</option>
        </select>
      </div>
    </div>
    <label for="et-csv-paste">Or paste a small long-format CSV</label>
    <textarea id="et-csv-paste" rows="7" spellcheck="false" placeholder="participant_id,trial_id,time_s,x,y&#10;P01,T01,0.0,0.3,0.4"></textarea>
    <div class="et-tool-actions">
      <button type="button" id="et-use-sample">Load invented sample</button>
      <button type="submit" class="et-primary-action">Inspect CSV locally</button>
      <button type="button" id="et-export-audit" disabled>Export summary JSON</button>
    </div>
  </form>
  <p class="et-tool-legend" id="et-local-notice">Files are read only in your browser. Nothing is transmitted or uploaded. The exported JSON contains counts and diagnostics, not raw gaze rows. Maximum: 12,000 data rows and 1.2 million CSV characters. A subset check does not qualify an entire recording.</p>
  <p id="et-audit-status" role="status" aria-live="polite">Choose a file, paste a CSV, or load the invented example.</p>
  <div id="et-audit-report" class="et-result" aria-label="Structural audit results"></div>
</div>

<noscript>JavaScript is needed for local inspection. Use the [input schema checklist](../guides/input-schemas.md) and [data-to-method guide](../start/data-to-method.md) instead.</noscript>

## Accepted columns and assumptions

Required literal headers: <code>participant_id</code>, <code>trial_id</code>, <code>time_s</code>, <code>x</code>, <code>y</code>. A <code>condition</code> column may be retained. Coordinates may be absent as empty CSV cells, never interpreted as zero. Time and coordinate units must be declared explicitly; no conversion is performed.

A consistent grid is only structurally compatible with dense analysis, not proof that the curve is scientifically meaningful. Native unequal support may require sparse methods. Coordinate-specific missingness is not, by itself, evidence of a device's asynchronous acquisition. Repeated trials must retain participant clustering.

!!! warning "Structural readiness is not method or inference validation"
    This inspector does not assess equipment calibration, drift, fixation/saccade classification, AOI labels, missing-data identification, statistical power or confidence-band calibration. Research issues [#289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289) and [#296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296) remain open.

**Next:** [Input schemas](../guides/input-schemas.md) · [Method selector](method-selector.md) · [Run synthetic starter](../tutorials/reproducible-starter.md)
