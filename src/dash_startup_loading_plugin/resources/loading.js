(function () {
    "use strict";

    var overlay = document.querySelector("[data-dash-loading]");
    if (!overlay) {
        return;
    }

    var observer = null;
    var sawDashLoading = false;

    function dashHasFinishedLoading() {
        var root = document.querySelector("#react-entry-point");
        if (!root) {
            return false;
        }
        if (root.querySelector("._dash-loading")) {
            sawDashLoading = true;
            return false;
        }
        return sawDashLoading;
    }

    function finish() {
        if (observer) {
            observer.disconnect();
        }
        if (overlay.isConnected) {
            overlay.dispatchEvent(new CustomEvent("dash-loading:ready", {
                bubbles: true
            }));
            overlay.remove();
        }
    }

    function check() {
        if (dashHasFinishedLoading()) {
            finish();
        }
    }

    observer = new MutationObserver(check);
    observer.observe(document.documentElement, { childList: true, subtree: true });
    check();
}());
