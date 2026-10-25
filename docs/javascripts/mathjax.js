/* Load MathJax 3 only when the current page contains an equation.
 * The old global external <script> cost every route, including the home page.
 * Works with MkDocs Material instant navigation; no math means no MathJax download.
 * Remote URL/version and TeX rendering semantics are otherwise unchanged.
 */
(function () {
  "use strict";
  var upstream = "https://unpkg.com/mathjax@3/es5/tex-mml-chtml.js";
  var bootPromise = null;
  var sequence = 0;

  window.MathJax = {
    tex: {
      inlineMath: [["\\(", "\\)"], ["$", "$"]],
      displayMath: [["\\[", "\\]"], ["$$", "$$"]],
      processEscapes: true,
      processEnvironments: true
    },
    options: {
      ignoreHtmlClass: ".*|",
      processHtmlClass: "arithmatex"
    },
    startup: { typeset: false }
  };

  function needMath() {
    return document.querySelector(".md-content .arithmatex") !== null;
  }

  function ensureMathJax() {
    if (bootPromise) return bootPromise;
    bootPromise = new Promise(function (resolve, reject) {
      var script = document.createElement("script");
      script.src = upstream;
      script.async = true;
      script.dataset.etMathjax = "conditional";
      script.onload = function () {
        if (!window.MathJax || !window.MathJax.startup || !window.MathJax.startup.promise) {
          reject(new Error("MathJax loaded but startup promise is unavailable"));
          return;
        }
        window.MathJax.startup.promise.then(resolve, reject);
      };
      script.onerror = function () {
        reject(new Error("MathJax could not be loaded from the configured source"));
      };
      document.head.appendChild(script);
    });
    return bootPromise;
  }

  function onPageReady() {
    var current = ++sequence;
    if (!needMath()) return;
    ensureMathJax().then(function () {
      if (current !== sequence || !needMath()) return;
      var mathNodes = document.querySelectorAll(".md-content .arithmatex");
      if (window.MathJax.typesetClear) window.MathJax.typesetClear();
      if (window.MathJax.texReset) window.MathJax.texReset();
      return window.MathJax.typesetPromise(Array.prototype.slice.call(mathNodes));
    }).catch(function (error) {
      // Render no altered/incorrect formulas; raw source stays inspectable.
      console.warn("MathJax rendering unavailable:", error);
    });
  }

  if (typeof document$ !== "undefined" && document$ && typeof document$.subscribe === "function") {
    document$.subscribe(onPageReady);
  } else if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", onPageReady, { once: true });
  } else {
    onPageReady();
  }
})();
