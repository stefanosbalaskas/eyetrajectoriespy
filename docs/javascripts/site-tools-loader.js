/* Route-aware tool loading for MkDocs Material instant navigation.
 * The documentation shell, search and mathematical renderer remain unchanged.
 * Scientific/interactive tools are only downloaded on pages that use them.
 * Script URLs are rooted at this script's own URL, not the current page path.
 */
(function () {
  "use strict";
  var current = document.currentScript;
  if (!current || !current.src) return;
  var scriptsRoot = new URL(".", current.src);
  var loaded = Object.create(null);

  function ensureScript(filename) {
    if (loaded[filename]) return loaded[filename];
    var task = new Promise(function (resolve, reject) {
      var node = document.createElement("script");
      node.src = new URL(filename, scriptsRoot).href;
      node.async = false;
      node.dataset.etTool = filename;
      node.onload = resolve;
      node.onerror = function () {
        reject(new Error("Could not load website tool " + filename));
      };
      document.head.appendChild(node);
    });
    // A temporary load failure should not permanently block later navigation.
    loaded[filename] = task.catch(function (error) {
      delete loaded[filename];
      throw error;
    });
    return loaded[filename];
  }

  function onPageReady() {
    var needed = [];
    if (document.getElementById("et-integration-navigator"))
      needed.push("integration-navigator.js");
    if (document.getElementById("et-data-audit"))
      needed.push("gaze-data-readiness.js");
    if (document.getElementById("et-method") ||
        document.getElementById("et-trajectory") ||
        document.querySelector("[data-et-collection]"))
      needed.push("interactive-explorers.js");
    // Sharing restores the method choice; bind core selectors first.
    if (document.getElementById("et-method"))
      needed.push("method-sharing.js");
    needed.reduce(function (step, filename) {
      return step.then(function () { return ensureScript(filename); });
    }, Promise.resolve()).catch(function (error) {
      console.warn("Interactive documentation enhancement unavailable:", error);
    });
  }

  if (typeof document$ !== "undefined" && document$ &&
      typeof document$.subscribe === "function")
    document$.subscribe(onPageReady);
  if (document.readyState === "loading")
    document.addEventListener("DOMContentLoaded", onPageReady, { once: true });
  else
    onPageReady();
})();
