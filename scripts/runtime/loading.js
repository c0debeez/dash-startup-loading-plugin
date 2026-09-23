!(function () {
  "use strict";

  var overlay = document.querySelector("[data-dash-loading]");
  if (!overlay) return;

  var observer = null;
  var checkFrame = 0;
  var finished = false;

  function remove() {
    if (finished) return;
    finished = true;
    if (observer) observer.disconnect();
    if (checkFrame) cancelAnimationFrame(checkFrame);
    if (overlay.isConnected) overlay.remove();
  }

  function check() {
    checkFrame = 0;
    if (finished || !overlay.isConnected) return;
    var root = document.querySelector("#react-entry-point");
    // Dash serves its own loading marker inside the entry point until React renders the layout.
    if (!root || !root.firstElementChild || root.querySelector("._dash-loading")) return;
    remove();
  }

  function scheduleCheck() {
    if (!checkFrame) checkFrame = requestAnimationFrame(check);
  }

  observer = new MutationObserver(scheduleCheck);
  observer.observe(document.documentElement, { childList: true, subtree: true });
  check();
})();
