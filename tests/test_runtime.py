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
        [node, "-"],
        capture_output=True,
        text=True,
        input=script,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def runtime_source() -> str:
    return json.dumps(
        files("dash_startup_loading_plugin")
        .joinpath("resources/startup-loading.js")
        .read_text(encoding="utf-8")
    )


def harness(root_literal: str, epilogue: str) -> str:
    """Run the startup runtime against a fake document and report the overlay state."""

    return f"""
const vm = require("node:vm");
const state = {{loading: true}};
let mutation = () => {{}};
const root = {root_literal};
const overlay = {{isConnected: true, remove() {{ this.isConnected = false; }}}};
const context = {{
  window: {{setTimeout, clearTimeout}},
  document: {{
    documentElement: {{appendChild: () => {{}}}},
    head: {{appendChild: () => {{}}}},
    createElement: () => ({{setAttribute: () => {{}}}}),
    querySelector: (selector) =>
      selector === "[data-dash-loading]" ? overlay : selector === "#react-entry-point" ? root : null
  }},
  MutationObserver: function(callback) {{
    mutation = callback;
    this.observe = () => {{}};
    this.disconnect = () => {{}};
  }},
  requestAnimationFrame: (callback) => setTimeout(callback, 1),
  cancelAnimationFrame: clearTimeout
}};
vm.runInNewContext({runtime_source()}, context);
context.window.__dashStartupLoadingStart();
{epilogue}
"""


def test_loading_runtime_removes_overlay_after_dash_loading_disappears():
    script = harness(
        "{firstElementChild: {}, querySelector: (selector) =>"
        ' selector === "._dash-loading" && state.loading ? {} : null}',
        "setTimeout(() => { state.loading = false; mutation(); }, 5);\n"
        "setTimeout(() => console.log(JSON.stringify({connected: overlay.isConnected})), 30);",
    )

    assert run_node(script) == {"connected": False}


def test_loading_runtime_stays_visible_while_dash_loading_remains():
    script = harness(
        '{firstElementChild: {}, querySelector: (selector) => selector === "._dash-loading" ? {} : null}',
        "setTimeout(() => console.log(JSON.stringify({connected: overlay.isConnected})), 20);",
    )

    assert run_node(script) == {"connected": True}


def test_loading_runtime_stays_visible_while_the_entry_point_is_empty():
    script = harness(
        "{firstElementChild: null, querySelector: () => null}",
        "setTimeout(() => console.log(JSON.stringify({connected: overlay.isConnected})), 20);",
    )

    assert run_node(script) == {"connected": True}
