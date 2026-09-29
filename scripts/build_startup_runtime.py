"""Bundle startup resources into the distributable browser runtimes."""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE = PROJECT_ROOT / "scripts/runtime"
OUTPUT = PROJECT_ROOT / "src/dash_startup_loading_plugin/resources"


def read(name: str) -> str:
    return (SOURCE / name).read_text(encoding="utf-8").strip()


def main() -> None:
    css_source = (
        read("loading.css")
        .replace("html[data-dash-loading-theme=dark]", "html.dark")
        .replace(
            "transform:scale(1.6666667);transform-origin:center",
            "transform:scale(var(--dash-loading-antd-scale,1));transform-origin:center",
        )
    )
    css_source = re.sub(
        r"html\[data-dash-loading-framework=[^]]+\]\[data-dash-loading-theme=(?:light|dark)\] \.dash-loading\{[^}]+\}",
        "",
        css_source,
    )
    css = json.dumps(
        css_source
        + ".dash-loading__loading-ui[data-dash-loading-ui^=text-]{color:var(--dash-loading-loader-text-color,currentColor)}"
        + "html.dark .dash-loading__loading-ui[data-dash-loading-ui^=text-]{color:var(--dash-loading-loader-dark-text-color,currentColor)}",
        ensure_ascii=False,
        separators=(",", ":"),
    )
    loading = read("loading.js")
    runtime = (
        '!function(){"use strict";var e=document.createElement("style");'
        'e.setAttribute("data-dash-loading-resource","style");'
        f"e.textContent={css};(document.head||document.documentElement).appendChild(e);"
        "window.__dashStartupLoadingStart=function(){"
        f"{loading}"
        "}}();\n"
    )
    OUTPUT.joinpath("startup-loading.js").write_text(runtime, encoding="utf-8")
    loaders = OUTPUT / "loading-ui"
    shutil.rmtree(loaders, ignore_errors=True)
    shutil.copytree(SOURCE / "loading-ui", loaders)


if __name__ == "__main__":
    main()
