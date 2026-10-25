/* Material instant-navigation progress is not consistently named for AT.
   Label the existing element without replacing Material loading behavior. */
(function () {
  "use strict";
  function labelProgress() {
    document.querySelectorAll(".md-progress[role='progressbar']").forEach(function (node) {
      if (!node.hasAttribute("aria-label") && !node.hasAttribute("aria-labelledby")) {
        node.setAttribute("aria-label", "Page loading");
      }
    });
  }
  function init() {
    labelProgress();
    if (document.body && !document.body.dataset.etProgressObserved) {
      document.body.dataset.etProgressObserved = "1";
      new MutationObserver(labelProgress).observe(document.body, { childList: true, subtree: true });
    }
  }
  if (typeof document$ !== "undefined" && document$ && typeof document$.subscribe === "function") {
    document$.subscribe(init);
  } else if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init, { once: true });
  } else {
    init();
  }
})();
