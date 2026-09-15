(function () {
    "use strict";

    var root = document.documentElement;
    var config = window.__dashLoadingThemeConfig || {};
    var persistencePrefix = "_dash_persistence.";

    function parseStored(value) {
        if (value === null || value === undefined) {
            return null;
        }
        try {
            return JSON.parse(value);
        } catch (_) {
            return value;
        }
    }

    function normalize(value) {
        if (Array.isArray(value)) {
            value = value[0];
        }
        if (typeof value === "string") {
            var name = value.toLowerCase();
            if (name === "dark") return "dark";
            if (name === "light" || name === "default") return "light";
            if (name === "system" || name === "auto") return "system";
            return null;
        }
        if (!value || typeof value !== "object") {
            return null;
        }

        var explicit = value.mode || value.colorScheme || value.color_scheme;
        var normalized = normalize(explicit);
        if (normalized) return normalized;

        var algorithms = Array.isArray(value.algorithm) ? value.algorithm : [value.algorithm];
        if (algorithms.some(function (algorithm) { return algorithm === "dark"; })) return "dark";
        if (algorithms.some(function (algorithm) { return algorithm === "default"; })) return "light";

        return Object.keys(value).length ? "light" : null;
    }

    function rootTheme() {
        if (root.classList.contains("dark")) return "dark";
        if (root.classList.contains("light")) return "light";
        return normalize(
            root.getAttribute("data-theme")
            || root.getAttribute("data-color-scheme")
        );
    }

    function dashPersistenceTheme() {
        var id = config.dashThemeComponentId;
        var exactPrefix = id ? persistencePrefix + id + ".theme." : null;
        var fallback = null;
        try {
            for (var index = 0; index < localStorage.length; index += 1) {
                var key = localStorage.key(index);
                if (!key || key.indexOf(persistencePrefix) !== 0 || key.indexOf(".theme.") < 0) {
                    continue;
                }
                var theme = normalize(parseStored(localStorage.getItem(key)));
                if (!theme) continue;
                if (exactPrefix && key.indexOf(exactPrefix) === 0) return theme;
                if (!fallback) fallback = theme;
            }
        } catch (_) {
            return null;
        }
        return fallback;
    }

    function conventionalStoredTheme() {
        var keys = ["theme", "color-theme", "color-scheme"];
        try {
            for (var index = 0; index < keys.length; index += 1) {
                var theme = normalize(parseStored(localStorage.getItem(keys[index])));
                if (theme) return theme;
            }
        } catch (_) {
            return null;
        }
        return null;
    }

    var configuredTheme = normalize(config.themeMode);
    var theme = configuredTheme === "light" || configuredTheme === "dark" ? configuredTheme : null;
    if (!theme && config.dashThemeComponentId) {
        theme = dashPersistenceTheme();
    }
    if (!theme) {
        theme = rootTheme() || dashPersistenceTheme() || conventionalStoredTheme() || "light";
    }
    if (theme === "system") {
        theme = window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    }

    root.setAttribute("data-dash-loading-theme", theme);
}());
