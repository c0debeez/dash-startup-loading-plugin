"""Rebuild the bundled Loading UI renderer from the pinned MIT-licensed source."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

UPSTREAM = "https://github.com/turbostarter/loading-ui.git"
COMMIT = "0ba63f89430d21c445edc6a771039288733462a9"
PACKAGES = (
    "react@19.3.0",
    "react-dom@19.3.0",
    "motion@12.43.0",
    "clsx@2.1.1",
    "tailwind-merge@3.7.0",
    "esbuild@0.28.2",
    "tailwindcss@4.3.3",
    "@tailwindcss/cli@4.3.3",
    "@babel/parser@7.29.8",
    "@babel/traverse@7.29.8",
    "@babel/generator@7.29.8",
    "@babel/types@7.29.8",
    "postcss@8.5.28",
    "postcss-selector-parser@7.1.6",
)
OUTPUT = Path(__file__).resolve().parents[1] / "src/dash_startup_loading_plugin/resources"


def run(*args: str) -> None:
    subprocess.run(args, check=True)


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="dash-loading-ui-build-") as temp:
        root = Path(temp)
        source = root / "loading-ui"
        build = root / "build"
        build.mkdir()
        run("git", "clone", "--filter=blob:none", UPSTREAM, str(source))
        run("git", "-C", str(source), "checkout", COMMIT)
        (build / "package.json").write_text('{"private":true}', encoding="utf-8")
        run("npm", "install", "--prefix", str(build), "--no-audit", "--no-fund", *PACKAGES)
        (source / "node_modules").symlink_to(build / "node_modules", target_is_directory=True)

        components = source / "registry/components/loading-ui"
        component_files = sorted(components.glob("*.tsx"))
        lines = [
            'import React from "react";',
            'import { createRoot } from "react-dom/client";',
            'import css from "./loading-ui.css";',
        ]
        symbols = {}
        for path in component_files:
            symbol = "InfinityLoop" if path.stem == "infinity" else "".join(
                part.title() for part in path.stem.split("-")
            )
            symbols[path.stem] = symbol
            lines.append(f'import {{ {symbol} }} from "{path}";')
        lines.append("const components: Record<string, React.ComponentType<any>> = {")
        lines.extend(f'  "{name}": {symbol},' for name, symbol in symbols.items())
        lines.extend([
            "};",
            'const host = document.querySelector("[data-dash-loading-ui]") as HTMLElement | null;',
            "if (host) {",
            '  const selected = host.dataset.dashLoadingUi || "ring";',
            "  const Component = components[selected];",
            "  if (Component) {",
            '    const shadow = host.attachShadow({mode:"open"});',
            '    const style = document.createElement("style");',
            '    style.textContent = ":host{display:inline-block;width:100%;height:100%;color:inherit} .sr-only{position:absolute!important;width:1px!important;height:1px!important;padding:0!important;margin:-1px!important;overflow:hidden!important;clip:rect(0,0,0,0)!important;white-space:nowrap!important;border:0!important}" + css;',
            "    shadow.appendChild(style);",
            '    const mount = document.createElement("span");',
            '    mount.style.cssText = selected.startsWith("text-") ? "display:inline-block;width:auto;height:auto;min-width:6em" : "display:inline-block;width:var(--dash-loading-size,28px);height:var(--dash-loading-size,28px)";',
            "    shadow.appendChild(mount);",
            '    const text = selected.startsWith("text-") ? "Loading" : undefined;',
            '    const svgWithForwardedProps = ["diamond", "morphing-infinity", "swirling"].includes(selected);',
            '    const props = svgWithForwardedProps ? {style: {width: "100%", height: "100%"}} : {className: text ? "inline-block" : "size-full", children: text};',
            '    createRoot(mount).render(React.createElement(Component, props));',
            "  }",
            "}",
        ])
        (build / "entry.tsx").write_text("\n".join(lines) + "\n", encoding="utf-8")
        (build / "input.css").write_text(
            '@import "tailwindcss/utilities";\n'
            '@theme { --color-muted: currentColor; --radius-md: 4px; '
            '--spacing: 0.25rem; --shadow-sm: 0 1px 3px rgb(0 0 0 / 0.1); }\n'
            f'@source "{components}";\n',
            encoding="utf-8",
        )
        run(str(build / "node_modules/.bin/tailwindcss"), "-i", str(build / "input.css"),
            "-o", str(build / "loading-ui.css"), "--minify")
        transformer = build / "inline_loading_ui_classes.cjs"
        shutil.copyfile(Path(__file__).with_name("inline_loading_ui_classes.cjs"), transformer)
        run("node", str(transformer), str(components), str(build / "loading-ui.css"),
            str(build / "loader-class-styles.ts"))
        run(str(build / "node_modules/.bin/esbuild"), str(build / "entry.tsx"),
            "--bundle", "--minify", "--format=iife", "--platform=browser",
            f"--alias:@/lib/utils={source / 'registry/lib/utils.ts'}", "--loader:.css=text",
            f"--outfile={OUTPUT / 'loading-ui.js'}")
        shutil.copyfile(source / "LICENSE.md", OUTPUT / "LOADING-UI-LICENSE.md")


if __name__ == "__main__":
    main()
