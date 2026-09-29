!function(){"use strict";var e=document.createElement("style");e.setAttribute("data-dash-loading-resource","style");e.textContent=".dash-loading{position:fixed;inset:0;z-index:var(--dash-loading-z-index,9999);display:grid;place-items:center;overflow:hidden;background:var(--dash-loading-background,#f5f5f5);opacity:1;transition:opacity var(--dash-loading-fade-duration, 0ms) ease-out}.dash-loading[data-state=leaving]{opacity:0;pointer-events:none}.dash-loading__content{display:grid;place-items:center;color:var(--dash-loading-loader-color,#1677ff);width:var(--dash-loading-size,12px);height:var(--dash-loading-size,12px)}.dash-loading__content--loading-ui{width:100%;height:auto}.dash-loading__spinner{box-sizing:border-box;display:block;width:var(--dash-loading-size,12px);height:var(--dash-loading-size,12px);border:var(--dash-loading-stroke,2px) solid transparent;border-top-color:currentcolor;border-radius:50%;animation:dash-loading-spin .8s linear infinite}.dash-loading__spinner-region{position:relative;display:grid;place-items:center;width:100%;max-width:100%;aspect-ratio:4/3;flex:0 0 auto;container-type:inline-size}@media (min-width:640px){.dash-loading__spinner-region{width:calc((100% - 1px)/ 2)}}@media (min-width:768px){.dash-loading__spinner-region{width:calc((100% - 2px)/ 3)}}@media (min-width:1024px){.dash-loading__spinner-region{width:calc((100% - 3px)/ 4)}}html.dark .dash-loading__content{color:var(--dash-loading-loader-dark-color,#4096ff)}.dash-loading__ring{display:inline-block;width:var(--dash-loading-size,12px);height:var(--dash-loading-size,12px)}.dash-loading__loading-ui{display:var(--dash-loading-ui-display,inline-flex);width:auto;height:auto;zoom:var(--dash-loading-scale,1)}.dash-loading__ring{stroke-width:var(--dash-loading-stroke,2px);animation:dash-loading-ui-ring-spin 1s linear infinite}.dash-loading__antd-dot,.dash-loading__antd-spinner{position:relative;display:inline-block;width:var(--dash-loading-size,12px);height:var(--dash-loading-size,12px)}.dash-loading__antd-spinner{transform:scale(var(--dash-loading-antd-scale,1));transform-origin:center}.dash-loading__antd-dot{transform:rotate(45deg);animation:dash-loading-antd-rotate 1.2s linear infinite}.dash-loading__antd-dot i{position:absolute;display:block;width:calc((var(--dash-loading-size,12px) - 2px)/ 2);height:calc((var(--dash-loading-size,12px) - 2px)/ 2);background:currentcolor;border-radius:100%;transform:scale(.75);opacity:.3;animation:dash-loading-antd-move 1s linear infinite alternate}.dash-loading__antd-dot i:first-child{top:0;left:0;animation-delay:0s}.dash-loading__antd-dot i:nth-child(2){top:0;right:0;animation-delay:.4s}.dash-loading__antd-dot i:nth-child(3){right:0;bottom:0;animation-delay:.8s}.dash-loading__antd-dot i:nth-child(4){bottom:0;left:0;animation-delay:1.2s}._dash-loading{display:none!important}html[data-dash-loading-theme=light] .dash-loading{background:var(--dash-loading-background,#f5f5f5)}html.dark .dash-loading{background:var(--dash-loading-dark-background,#000)}@media (prefers-reduced-motion:reduce){.dash-loading{transition-duration:0s}.dash-loading__ring{animation-duration:1.6s}.dash-loading__spinner{animation-duration:1.6s}.dash-loading__antd-dot,.dash-loading__antd-dot i{animation-duration:1.6s}}@keyframes dash-loading-ui-ring-spin{to{transform:rotate(360deg)}}@keyframes dash-loading-spin{to{transform:rotate(360deg)}}@keyframes dash-loading-antd-rotate{to{transform:rotate(405deg)}}@keyframes dash-loading-antd-move{to{opacity:1}}.dash-loading__loading-ui[data-dash-loading-ui^=text-]{color:var(--dash-loading-loader-text-color,currentColor)}html.dark .dash-loading__loading-ui[data-dash-loading-ui^=text-]{color:var(--dash-loading-loader-dark-text-color,currentColor)}";(document.head||document.documentElement).appendChild(e);window.__dashStartupLoadingStart=function(){!(function () {
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
})();}}();
