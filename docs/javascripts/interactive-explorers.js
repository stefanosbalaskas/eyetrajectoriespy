/* Progressive enhancements for MkDocs Material instant navigation.
   All visuals are explicitly synthetic teaching illustrations, not empirical data. */
(function () {
  "use strict";
  const ns = "http://www.w3.org/2000/svg";
  function one(root, selector) { return root.querySelector(selector); }
  function svgNode(tag, attrs, label) {
    const el = document.createElementNS(ns, tag);
    Object.keys(attrs || {}).forEach(function (key) { el.setAttribute(key, String(attrs[key])); });
    if (label !== undefined) el.textContent = label;
    return el;
  }
  function pathFor(points) {
    return points.map(function (p, i) { return (i ? "L" : "M") + p[0].toFixed(2) + " " + p[1].toFixed(2); }).join(" ");
  }
  const routes = {
    fpca: ["Common-grid functional PCA", "../../workflows/fpca-exploration/", "Declare scaling, time grid and independence; component patterns are not psychological constructs."],
    sparse: ["Paired sparse planar MFPCA", "../../guides/sparse-multivariate-fpca/", "Keep both coordinates on their actual shared observation times; smoothing choices and score uncertainty must be reported."],
    async: ["Asynchronous sparse MFPCA", "../../guides/irregular-trajectories/", "Preserve channel-specific timestamps. Do not invent synchronized observations."],
    multilevel: ["Sparse multilevel workflow", "../../articles/choosing-the-ten-workflows/", "Participant/trial nesting changes the independent unit; verify support and model assumptions."],
    prediction: ["Sparse partial-trajectory prediction", "../../articles/choosing-the-ten-workflows/", "Separate training and prediction support; do not present illustrative prediction as guaranteed coverage."],
    regression: ["Function-on-scalar regression", "../../workflows/experimental-functional-regression/", "Declare design and independent unit; fitted coefficients alone do not justify simultaneous inferential claims."],
    mixed: ["Functional mixed-effects regression", "../../workflows/repeated-trial-mixed-effects/", "Declare random effects, dependence and cluster-level resampling; W3 general whole-function calibration remains open."],
    generalized: ["Generalized functional response", "../../workflows/generalized-responses/", "Specify the response family, denominator/exposure and participant dependence."],
    recurrence: ["Recurrence / nonlinear workflow", "../../workflows/nonlinear-recurrence/", "Declare embedding, time delay, radius and Theiler window before inspecting the result."]
  };
  function initMethod() {
    const root = document.getElementById("et-method");
    if (!root || root.dataset.ready) return;
    root.dataset.ready = "1";
    const output = one(root, "[data-et-recommendation]");
    function update() {
      const data = one(root, "#et-data").value;
      const goal = one(root, "#et-goal").value;
      const hierarchy = one(root, "#et-hierarchy").value;
      const uncertainty = one(root, "#et-uncertainty").value;
      let key;
      if (goal === "recurrence") key = "recurrence";
      else if (goal === "categorical") key = "generalized";
      else if (goal === "prediction" && data !== "dense") key = "prediction";
      else if (data === "async") key = "async";
      else if (data === "paired") key = hierarchy === "repeated" ? "multilevel" : "sparse";
      else if (hierarchy === "repeated" && goal === "effects") key = "mixed";
      else if (goal === "effects") key = "regression";
      else key = "fpca";
      const route = routes[key];
      one(output, "[data-et-method-name]").textContent = route[0];
      const link = one(output, "[data-et-method-link]");
      link.href = route[1];
      link.textContent = "Read the method and example";
      const note = route[2] + (uncertainty === "simultaneous" ? " IMPORTANT: General W3 nominal simultaneous whole-function coverage is NOT qualified (#289)." : "") + (uncertainty === "missing" ? " Missing gaze cannot be assumed MAR/MCAR, nor is field MNAR identified (#296)." : "");
      one(output, "[data-et-method-note]").textContent = note;
      one(output, "[data-et-method-input]").textContent = "Selection: " + data.replace("-", " ") + ", " + goal + ", " + hierarchy + ", " + uncertainty + ".";
    }
    root.querySelectorAll("select").forEach(function (el) { el.addEventListener("change", update); });
    update();
  }
  function drawTrajectory(svg, pts, observed, spread, view) {
    if (!svg) return;
    while (svg.firstChild) svg.removeChild(svg.firstChild);
    svg.setAttribute("viewBox", "0 0 580 330");
    svg.setAttribute("role", "img");
    svg.setAttribute("aria-label", view === "space" ? "Synthetic gaze position in normalized screen space with observed sample markers" : "Synthetic time-indexed horizontal gaze trajectory and descriptive between-curve spread");
    const title = svgNode("title", {}, view === "space" ? "Synthetic planar gaze path" : "Synthetic horizontal gaze over time");
    svg.appendChild(title);
    const plot = { x: 55, y: 23, w: 480, h: 245 };
    for (let i = 0; i <= 4; i++) {
      const y = plot.y + (i * plot.h / 4);
      svg.appendChild(svgNode("line", { x1: plot.x, y1: y, x2: plot.x + plot.w, y2: y, class: "et-grid-line" }));
    }
    svg.appendChild(svgNode("rect", { x: plot.x, y: plot.y, width: plot.w, height: plot.h, fill: "none", class: "et-chart-axis" }));
    function p(t, v) { return [plot.x + t * plot.w, plot.y + (1 - v) * plot.h]; }
    const full = pts.map(function (v) { return view === "space" ? p(v.x, v.y) : p(v.t, v.x); });
    if (view === "time" && spread.length) {
      const top = spread.map(function (s) { return p(s.t, Math.min(1, s.mean + s.sd)); });
      const bot = spread.slice().reverse().map(function (s) { return p(s.t, Math.max(0, s.mean - s.sd)); });
      svg.appendChild(svgNode("path", { d: pathFor(top.concat(bot)) + " Z", class: "et-spread-band" }));
    }
    svg.appendChild(svgNode("path", { d: pathFor(full), class: "et-latent-path" }));
    observed.forEach(function (v) {
      const q = view === "space" ? p(v.x, v.y) : p(v.t, v.x);
      svg.appendChild(svgNode("circle", { cx: q[0], cy: q[1], r: 2.5, class: "et-observed-point" }));
    });
    svg.appendChild(svgNode("text", { x: plot.x, y: 305, class: "et-axis-label" }, view === "space" ? "Horizontal position (normalized)" : "Trial time (normalized 0–1)"));
    svg.appendChild(svgNode("text", { x: 11, y: 18, class: "et-axis-label" }, view === "space" ? "Vertical" : "Horizontal"));
  }
  function syntheticCurve(k) {
    return Array.from({ length: 61 }, function (_, i) {
      const t = i / 60;
      return { t: t, x: Math.max(0.02, Math.min(0.98, 0.5 + 0.23 * Math.sin(2 * Math.PI * (t + 0.08 * k)) + 0.034 * Math.cos(6 * Math.PI * t + k))),
        y: Math.max(0.02, Math.min(0.98, 0.49 + 0.2 * Math.cos(2 * Math.PI * (t + 0.05 * k)) + 0.04 * Math.sin(4 * Math.PI * t + k))) };
    });
  }
  function initTrajectory() {
    const root = document.getElementById("et-trajectory");
    if (!root || root.dataset.ready) return;
    root.dataset.ready = "1";
    const trial = one(root, "#et-trial");
    const loss = one(root, "#et-loss");
    function update() {
      const k = Number(trial.value), missing = Number(loss.value);
      const pts = syntheticCurve(k);
      const observed = pts.filter(function (_, i) { return ((i * 37 + k * 19) % 100) >= missing; });
      const curves = Array.from({ length: 6 }, function (_, n) { return syntheticCurve(n); });
      const spread = pts.map(function (_, i) {
        const xs = curves.map(function (c) { return c[i].x; });
        const mean = xs.reduce(function (a, b) { return a + b; }, 0) / xs.length;
        const sd = Math.sqrt(xs.reduce(function (a, b) { return a + Math.pow(b - mean, 2); }, 0) / (xs.length - 1));
        return { t: i / 60, mean: mean, sd: sd };
      });
      one(root, "#et-trial-value").textContent = String(k + 1);
      one(root, "#et-loss-value").textContent = String(missing) + "%";
      one(root, "#et-observed-count").textContent = String(observed.length) + " of 61 synthetic samples displayed. Unobserved samples are not imputed.";
      drawTrajectory(one(root, "#et-planar"), pts, observed, spread, "space");
      drawTrajectory(one(root, "#et-timeseries"), pts, observed, spread, "time");
      const body = one(root, "#et-sample-table");
      if (body) {
        const retained = new Set(observed.map(function (p) { return p.t; }));
        const rows = document.createDocumentFragment();
        pts.forEach(function (p) {
          const tr = document.createElement("tr");
          const yes = retained.has(p.t);
          [p.t.toFixed(3), yes ? p.x.toFixed(4) : "", yes ? p.y.toFixed(4) : "", yes ? "Observed" : "Not observed"].forEach(function (value) {
            const td = document.createElement("td");
            td.textContent = value;
            tr.appendChild(td);
          });
          rows.appendChild(tr);
        });
        body.replaceChildren(rows);
      }
    }
    const save = one(root, "#et-save-observed");
    if (save) save.addEventListener("click", function () {
      const k = Number(trial.value), missing = Number(loss.value);
      const observed = syntheticCurve(k).filter(function (_, i) { return ((i * 37 + k * 19) % 100) >= missing; });
      const csv = ["trial,time_normalized,x_normalized,y_normalized"]
        .concat(observed.map(function (p) { return [k + 1, p.t.toFixed(6), p.x.toFixed(6), p.y.toFixed(6)].join(","); })).join("\n") + "\n";
      const url = URL.createObjectURL(new Blob([csv], { type: "text/csv" }));
      const a = document.createElement("a");
      a.href = url; a.download = "synthetic-visible-gaze.csv";
      document.body.appendChild(a); a.click(); a.remove();
      setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
    });
    trial.addEventListener("input", update);
    loss.addEventListener("input", update);
    update();
  }
  function initFilters() {
    document.querySelectorAll("[data-et-collection]").forEach(function (root) {
      if (root.dataset.ready) return;
      root.dataset.ready = "1";
      const cards = Array.from(root.querySelectorAll("[data-et-entry]"));
      const controls = Array.from(root.querySelectorAll("[data-et-filter]"));
      const search = one(root, "[data-et-search]");
      const count = one(root, "[data-et-count]");
      function update() {
        let total = 0;
        cards.forEach(function (card) {
          const matches = controls.every(function (control) {
            return control.value === "all" || (card.getAttribute("data-" + control.dataset.etFilter) || "").split(/\s+/).includes(control.value);
          });
          const q = search ? search.value.trim().toLocaleLowerCase() : "";
          const visible = matches && (!q || card.textContent.toLocaleLowerCase().includes(q));
          card.hidden = !visible;
          if (visible) total += 1;
        });
        if (count) count.textContent = total + " of " + cards.length + " entries shown";
      }
      controls.forEach(function (control) { control.addEventListener("change", update); });
      if (search) search.addEventListener("input", update);
      update();
    });
  }
  function init() { initMethod(); initTrajectory(); initFilters(); }
  if (typeof document$ !== "undefined" && document$ && typeof document$.subscribe === "function") {
    document$.subscribe(init);
  }
  // Mount immediately when this bundle is injected after a page transition.
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else { init(); }
})();
