import json
import shutil
import subprocess
from importlib.resources import files

import pytest


def run_node(script: str) -> dict:
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node.js is unavailable")
    result = subprocess.run(
        [node, "-e", script],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def resource(name: str) -> str:
    return files("dash_startup_loading_plugin").joinpath("resources", name).read_text(encoding="utf-8")


def test_theme_runtime_reads_nested_storage_and_syncs_root_classes():
    source = json.dumps(resource("theme.js"))
    script = f"""
const vm = require("node:vm");
const attributes = new Map();
const classes = new Set(["application-class"]);
const listeners = {{}};
const root = {{
    classList: {{
        contains: (name) => classes.has(name),
        toggle: (name, force) => force ? classes.add(name) : classes.delete(name)
    }},
    style: {{}},
    hasAttribute: (name) => attributes.has(name),
    getAttribute: (name) => attributes.has(name) ? attributes.get(name) : null,
    setAttribute: (name, value) => attributes.set(name, value),
    removeAttribute: (name) => attributes.delete(name)
}};
const media = {{matches: false, addEventListener() {{}}, removeEventListener() {{}}}};
const context = {{
    window: {{
        __dashLoadingThemeConfig: {{
            themeMode: "auto",
            themeStore: ["usage-preferences", "appearance.mode"],
            syncTheme: true
        }},
        matchMedia: () => media,
        addEventListener: (name, callback) => listeners[name] = callback
    }},
    document: {{documentElement: root}},
    localStorage: {{
        length: 1,
        key: () => "usage-preferences",
        getItem: (key) => key === "usage-preferences"
            ? JSON.stringify({{appearance: {{mode: "dark"}}}})
            : null
    }},
    MutationObserver: function () {{ this.observe = () => {{}}; this.disconnect = () => {{}}; }}
}};
vm.runInNewContext({source}, context);
console.log(JSON.stringify({{
    theme: attributes.get("data-dash-loading-theme"),
    classes: Array.from(classes).sort(),
    colorScheme: root.style.colorScheme
}}));
"""

    result = run_node(script)

    assert result == {
        "theme": "dark",
        "classes": ["application-class", "dark"],
        "colorScheme": "dark",
    }


def loading_runtime_script(config: dict, *, release_callbacks: bool, missing_selector: bool = False) -> str:
    source = json.dumps(resource("loading.js"))
    config_json = json.dumps(config)
    selector_result = "null" if missing_selector else "sider"
    release = "state.callbacks = false; mutation();" if release_callbacks else ""
    return f"""
const vm = require("node:vm");
const events = [];
const state = {{loading: true, callbacks: false}};
let mutation = () => {{}};
const element = (width, height) => ({{getBoundingClientRect: () => ({{width, height}})}});
const sider = element(280, 704);
const root = {{
    ...element(1406, 768),
    querySelector: (selector) => selector === "._dash-loading"
        ? (state.loading ? {{}} : null)
        : (selector === "._dash-loading-callback" && state.callbacks ? {{}} : null)
}};
const overlay = {{
    isConnected: true,
    setAttribute() {{}},
    addEventListener() {{}},
    dispatchEvent: (event) => events.push({{type: event.type, detail: event.detail}}),
    remove() {{ this.isConnected = false; }}
}};
const documentElement = element(1406, 768);
documentElement.getAttribute = () => "dark";
const context = {{
    window: {{
        __dashLoadingThemeConfig: {config_json},
        matchMedia: () => ({{matches: false}}),
        setTimeout,
        clearTimeout
    }},
    document: {{
        documentElement,
        fonts: {{ready: Promise.resolve()}},
        querySelector: (selector) => selector === "[data-dash-loading]"
            ? overlay
            : selector === "#react-entry-point"
                ? root
                : selector === "#usage-sider" ? {selector_result} : null
    }},
    MutationObserver: function (callback) {{
        mutation = callback;
        this.observe = () => {{}};
        this.disconnect = () => {{}};
    }},
    ResizeObserver: function () {{ this.observe = () => {{}}; this.disconnect = () => {{}}; }},
    CustomEvent: function (type, options) {{ this.type = type; this.detail = options.detail; }},
    requestAnimationFrame: (callback) => setTimeout(() => callback(Date.now()), 1),
    cancelAnimationFrame: clearTimeout,
    performance: {{now: () => Date.now()}},
    setTimeout,
    clearTimeout
}};
vm.runInNewContext({source}, context);
setTimeout(() => {{ state.loading = false; state.callbacks = true; mutation(); }}, 2);
setTimeout(() => {{
    if (!overlay.isConnected) throw new Error("overlay closed while an initial callback was pending");
    {release}
}}, 20);
setTimeout(() => console.log(JSON.stringify({{connected: overlay.isConnected, events}})), 80);
"""


def test_loading_runtime_waits_for_callbacks_and_stable_layout():
    result = run_node(
        loading_runtime_script(
            {
                "waitFor": ["#usage-sider"],
                "settleFrames": 2,
                "settleMs": 5,
                "timeoutMs": 200,
                "fadeDurationMs": 0,
            },
            release_callbacks=True,
        )
    )

    assert result["connected"] is False
    assert [event["type"] for event in result["events"]] == [
        "dash-loading:before-ready",
        "dash-loading:ready",
    ]
    assert all(event["detail"] == {"reason": "ready", "theme": "dark"} for event in result["events"])


def test_loading_runtime_timeout_releases_missing_stable_selector():
    result = run_node(
        loading_runtime_script(
            {
                "waitFor": ["#missing"],
                "settleFrames": 2,
                "timeoutMs": 30,
                "fadeDurationMs": 0,
            },
            release_callbacks=False,
            missing_selector=True,
        )
    )

    assert result["connected"] is False
    assert result["events"][-1]["detail"]["reason"] == "timeout"
