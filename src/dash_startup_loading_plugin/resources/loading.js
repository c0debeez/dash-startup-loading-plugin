(function () {
    "use strict";

    var overlay = document.querySelector("[data-dash-loading]");
    if (!overlay) {
        return;
    }

    var config = window.__dashLoadingThemeConfig || {};
    var observer = null;
    var resizeObserver = null;
    var animationFrame = 0;
    var readyTimeout = 0;
    var fadeTimeout = 0;
    var sawDashLoading = false;
    var dashFinished = false;
    var advancedReadiness = Boolean(config.waitFor);
    var fontsReady = !advancedReadiness || !document.fonts || !document.fonts.ready;
    var quietSince = 0;
    var stableFrames = 0;
    var previousSizes = null;
    var observedElements = [];
    var leaving = false;
    var finished = false;
    var stabilizeSelectors = Array.isArray(config.waitFor) ? config.waitFor : [];

    function cleanup() {
        if (observer) observer.disconnect();
        if (resizeObserver) resizeObserver.disconnect();
        if (animationFrame) cancelAnimationFrame(animationFrame);
        if (readyTimeout) clearTimeout(readyTimeout);
        if (fadeTimeout) clearTimeout(fadeTimeout);
    }

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

    function dispatch(name, reason) {
        overlay.dispatchEvent(new CustomEvent(name, {
            bubbles: true,
            detail: {
                reason: reason,
                theme: document.documentElement.getAttribute("data-dash-loading-theme")
            }
        }));
    }

    function remove(reason) {
        if (finished) return;
        finished = true;
        cleanup();
        if (overlay.isConnected) {
            dispatch("dash-loading:ready", reason);
            overlay.remove();
        }
    }

    function finish(reason) {
        if (finished || leaving) return;
        leaving = true;
        dispatch("dash-loading:before-ready", reason);
        overlay.setAttribute("data-state", "leaving");
        var duration = Number(config.fadeDurationMs) || 0;
        if (!duration || window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
            remove(reason);
            return;
        }
        overlay.addEventListener("transitionend", function (event) {
            if (event.target === overlay && event.propertyName === "opacity") remove(reason);
        }, { once: true });
        fadeTimeout = window.setTimeout(function () { remove(reason); }, duration + 50);
    }

    function pendingCallbacks(root) {
        return Boolean(advancedReadiness && root.querySelector("._dash-loading-callback"));
    }

    function measuredElements(root) {
        var selectors = ["#react-entry-point"].concat(stabilizeSelectors);
        var elements = selectors.map(function (selector) {
            return selector === "#react-entry-point" ? root : document.querySelector(selector);
        });
        if (resizeObserver) {
            elements.forEach(function (element) {
                if (element && observedElements.indexOf(element) === -1) {
                    observedElements.push(element);
                    resizeObserver.observe(element);
                }
            });
        }
        return elements;
    }

    function sizes(elements) {
        return elements.map(function (element) {
            if (!element) return null;
            var rect = element.getBoundingClientRect();
            return [rect.width, rect.height];
        });
    }

    function equalSizes(left, right) {
        return Boolean(left && right && left.length === right.length && left.every(function (size, index) {
            return size && right[index] && size[0] === right[index][0] && size[1] === right[index][1];
        }));
    }

    function resetSettlement() {
        quietSince = 0;
        stableFrames = 0;
        previousSizes = null;
    }

    function settle() {
        if (finished || !dashFinished) return;
        var root = document.querySelector("#react-entry-point");
        if (!root || pendingCallbacks(root) || !fontsReady) {
            resetSettlement();
            animationFrame = requestAnimationFrame(settle);
            return;
        }
        var now = performance.now();
        if (!quietSince) quietSince = now;
        if (now - quietSince < (Number(config.settleMs) || 0)) {
            animationFrame = requestAnimationFrame(settle);
            return;
        }
        var elements = measuredElements(root);
        if (elements.some(function (element) { return !element; })) {
            resetSettlement();
            animationFrame = requestAnimationFrame(settle);
            return;
        }
        var nextSizes = sizes(elements);
        stableFrames = equalSizes(previousSizes, nextSizes) ? stableFrames + 1 : 1;
        previousSizes = nextSizes;
        if (stableFrames >= Math.max(1, Number(config.settleFrames) || 1)) {
            finish("ready");
            return;
        }
        animationFrame = requestAnimationFrame(settle);
    }

    function check() {
        if (!overlay.isConnected) {
            finished = true;
            cleanup();
            return;
        }
        if (dashHasFinishedLoading()) {
            dashFinished = true;
            if (!advancedReadiness) {
                finish("ready");
            } else if (!animationFrame) {
                animationFrame = requestAnimationFrame(settle);
            }
        } else if (dashFinished) {
            resetSettlement();
        }
    }

    observer = new MutationObserver(check);
    observer.observe(document.documentElement, { childList: true, subtree: true });
    if (advancedReadiness && typeof ResizeObserver === "function") {
        resizeObserver = new ResizeObserver(resetSettlement);
        resizeObserver.observe(document.documentElement);
    }
    if (!fontsReady) {
        document.fonts.ready.then(function () {
            fontsReady = true;
            resetSettlement();
        }, function () {
            fontsReady = true;
        });
    }
    if (Number(config.timeoutMs) > 0) {
        readyTimeout = window.setTimeout(function () { finish("timeout"); }, Number(config.timeoutMs));
    }
    check();
}());
