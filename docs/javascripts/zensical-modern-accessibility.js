/* Zensical Modern: restore keyboard scrolling to generated API content.
 * Mkdocstrings wraps wide API tables in nonfocusable scroll containers.
 * A focusable region allows arrow/shift+wheel/keyboard users to reach content.
 * Run after initial render and after instant-navigation DOM replacements.
 */
(() => {
  let pending = false;
  const update = () => {
    pending = false;
    document.querySelectorAll(".md-typeset__scrollwrap").forEach((element) => {
      if (element.hasAttribute("tabindex")) return;
      const x = element.scrollWidth > element.clientWidth + 1;
      const y = element.scrollHeight > element.clientHeight + 1;
      if (!x && !y) return;
      element.setAttribute("tabindex", "0");
      element.setAttribute("role", "region");
      element.setAttribute("aria-label", "Scrollable documentation content");
    });
  };
  const schedule = () => {
    if (pending) return;
    pending = true;
    window.requestAnimationFrame(update);
  };
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", schedule, { once: true });
  } else {
    schedule();
  }
  const observer = new MutationObserver(schedule);
  observer.observe(document.documentElement, { childList: true, subtree: true });
  window.addEventListener("resize", schedule, { passive: true });
})();
