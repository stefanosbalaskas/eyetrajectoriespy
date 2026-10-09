(() => {
  function boot() {
    const root = document.getElementById("et-research-selector");
    if (!root || root.dataset.bound === "yes") return;
    root.dataset.bound = "yes";
    const layout = root.querySelector("#et-layout"), design = root.querySelector("#et-design");
    const target = root.querySelector("#et-target"), inference = root.querySelector("#et-inference"), out = root.querySelector("#et-method-outcome");
    const link = root.querySelector("#et-method-link");
    if (!layout || !design || !target || !inference || !out || !link) return;
    function update() {
      let title, caveat, href = "../research-method-api/";
      if (inference.value === "bayesian") {
        title = "Unpublished B5–B10 Bayesian research methods";
        caveat = "B5 posterior tools and fixed-population B6/B7, fixed-noise B8, conditional B9 baselines are experimental. Full learned Bayesian FPCA, repeated-participant hierarchies and B10 models are not yet qualified. No production recommendation.";
        href = "../bayesian-research-programme/";
      } else if (target.value === "quality" || layout.value === "bids") {
        title = "Experimental target/BIDS evidence route";
        caveat = "Explicit metadata and target validation required; no clock alignment or full standards certificate.";
      } else if (target.value === "reliability") {
        title = "Experimental balanced functional repeatability";
        caveat = "Requires registered equal-repeat participant trajectories and homogeneous condition.";
      } else if (target.value === "power") {
        title = "Experimental native sparse-F1 power pilot";
        caveat = "Runs the actual unqualified F1 test; does not recommend an adequate sample size.";
      } else if (target.value === "contrast" && design.value === "paired") {
        title = "Experimental participant-paired whole-curve contrast";
        caveat = "Symmetric paired-null assumption; no order/carryover adjustment.";
      } else if (target.value === "contrast" && layout.value === "sparse" && design.value === "independent") {
        title = "Experimental F1 pooled-PACE unit permutation";
        caveat = "Not Koner–Luo; null calibration and covariance sensitivity pending.";
      } else if (target.value === "contrast") {
        title = "No automatic validated contrast selector";
        caveat = "Use a declared regression/mixed design with proper experimental dependence.";
        href = "../../workflows/experimental-functional-regression/";
      } else if (layout.value === "sparse") {
        title = "Documented sparse MFPCA exploration";
        caveat = "Preserve irregular observation density and declare error/covariance fitting.";
        href = "../../guides/sparse-multivariate-fpca/";
      } else {
        title = "Documented common-grid FPCA exploration";
        caveat = "Inspect registration and component uncertainty before interpretation.";
        href = "../../workflows/fpca-exploration/";
      }
      out.textContent = title + ". " + caveat;
      link.textContent = "Read: " + title;
      link.href = href;
    }
    for (const element of [layout, design, target, inference]) element.addEventListener("change", update);
    update();
  }
  if (typeof document$ !== "undefined" && document$.subscribe) document$.subscribe(boot);
  else document.addEventListener("DOMContentLoaded", boot);
})();