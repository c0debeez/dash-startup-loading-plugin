(function () {
    "use strict";

    var overlays = new Map();

    function warn(message, error) {
        if (window.console && typeof window.console.warn === "function") {
            window.console.warn("[dash-loading] " + message, error || "");
        }
    }

    function parseConfig(overlay) {
        try {
            return JSON.parse(overlay.getAttribute("data-config") || "{}");
        } catch (error) {
            warn("Invalid overlay configuration.", error);
            return {};
        }
    }

    function hasRenderedContent(root) {
        if (!root || root.querySelector("._dash-loading")) {
            return false;
        }
        return Array.prototype.some.call(root.childNodes, function (node) {
            return node.nodeType === 1 || (node.nodeType === 3 && node.textContent.trim());
        });
    }

    function createController(overlay) {
        var config = parseConfig(overlay);
        var startedAt = window.performance && performance.now ? performance.now() : Date.now();
        var observer = null;
        var timeoutId = null;
        var minimumTimerId = null;
        var removalTimerId = null;
        var scheduled = false;
        var finished = false;

        function now() {
            return window.performance && performance.now ? performance.now() : Date.now();
        }

        function isReady() {
            return hasRenderedContent(document.querySelector("#react-entry-point"));
        }

        function cleanup() {
            if (observer) {
                observer.disconnect();
            }
            window.removeEventListener("load", check);
            if (timeoutId !== null) {
                window.clearTimeout(timeoutId);
            }
            if (minimumTimerId !== null) {
                window.clearTimeout(minimumTimerId);
            }
        }

        function finish(reason) {
            if (finished) {
                return;
            }

            var minimumDisplayMs = Math.max(Number(config.minimumDisplayMs) || 0, 0);
            var remaining = minimumDisplayMs - (now() - startedAt);
            if (remaining > 0 && reason !== "timeout") {
                if (minimumTimerId === null) {
                    minimumTimerId = window.setTimeout(function () {
                        minimumTimerId = null;
                        finish(reason);
                    }, remaining);
                }
                return;
            }

            finished = true;
            cleanup();
            overlay.classList.add("is-ready");
            overlay.setAttribute("aria-busy", "false");
            overlay.dispatchEvent(new CustomEvent("dash-loading:ready", {
                bubbles: true,
                detail: { reason: reason || "manual" }
            }));

            var fadeDurationMs = Math.max(Number(config.fadeDurationMs) || 0, 0);
            removalTimerId = window.setTimeout(function () {
                overlays.delete(overlay.id);
                if (overlay.isConnected) {
                    overlay.remove();
                }
            }, fadeDurationMs + 20);
        }

        function check() {
            if (finished || scheduled || !isReady()) {
                return;
            }
            scheduled = true;
            window.requestAnimationFrame(function () {
                window.requestAnimationFrame(function () {
                    scheduled = false;
                    if (isReady()) {
                        finish("ready");
                    }
                });
            });
        }

        observer = new MutationObserver(check);
        observer.observe(document.documentElement, { childList: true, subtree: true });
        window.addEventListener("load", check);
        if (config.timeoutMs !== null && config.timeoutMs !== undefined) {
            timeoutId = window.setTimeout(function () { finish("timeout"); }, Math.max(Number(config.timeoutMs) || 0, 0));
        }
        check();

        return {
            check: check,
            finish: finish,
            destroy: function () {
                cleanup();
                if (removalTimerId !== null) {
                    window.clearTimeout(removalTimerId);
                }
            }
        };
    }

    function boot() {
        document.querySelectorAll("[data-dash-loading]").forEach(function (overlay) {
            if (!overlays.has(overlay.id)) {
                overlays.set(overlay.id, createController(overlay));
            }
        });
    }

    window.dashLoading = {
        check: function (overlayId) {
            var controller = overlays.get(overlayId || "dash-loading");
            if (controller) {
                controller.check();
            }
        },
        finish: function (overlayId) {
            var controller = overlays.get(overlayId || "dash-loading");
            if (controller) {
                controller.finish("manual");
            }
        }
    };

    boot();
}());
