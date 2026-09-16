"""Rebuild the bundled Loading UI renderer from the pinned MIT-licensed source."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
import json
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

# Default geometry used by each component's official demo. Components omitted
# here calculate their own intrinsic ch/em dimensions from their default props.
COMPONENT_STYLES = {
    "analyzing-image": {"width": "4rem", "height": "4rem"},
    "arc": {"width": "3.5rem", "height": "3.5rem"},
    "bars": {"width": "4rem", "height": "3rem"},
    "bobbing-dots": {"width": "4rem"},
    "bouncing-dots": {"width": "4rem"},
    "classic": {"width": "4rem", "height": "4rem"},
    "clock-ring": {"width": "3.5rem", "height": "3.5rem"},
    "comet-spinner": {"width": "3rem", "height": "3rem"},
    "concentric-ring": {"width": "3.5rem", "height": "3.5rem"},
    "dash-ring": {"width": "3.5rem", "height": "3.5rem"},
    "diamond": {"width": "2.5rem", "height": "2.5rem"},
    "dots-ring": {"width": "4rem", "height": "4rem"},
    "dots": {"width": "4.5rem"},
    "dual-arc": {"width": "3.5rem", "height": "3.5rem"},
    "fade-arc": {"width": "3.75rem", "height": "3.75rem"},
    "infinity": {"width": "5rem", "height": "4rem"},
    "morphing-infinity": {"width": "6rem", "height": "6rem"},
    "orbit-ring": {"width": "3.5rem", "height": "3.5rem"},
    "pulsating-dots": {"width": "4.5rem"},
    "pulse-dot": {"width": "0.75rem", "height": "0.75rem"},
    "pulse": {"width": "3.5rem", "height": "3.5rem"},
    "quarter-ring": {"width": "3.5rem", "height": "3.5rem"},
    "ring": {"width": "4rem", "height": "4rem"},
    "ripple": {"width": "3.5rem", "height": "3.5rem"},
    "satellite-ring": {"width": "3.5rem", "height": "3.5rem"},
    "skeleton": {"width": "4rem", "height": "4rem"},
    "spiral": {"width": "4.5rem", "height": "4.5rem"},
    "spokes": {"width": "4rem", "height": "4rem"},
    "swirling": {"width": "6rem", "height": "6rem"},
    "terminal": {"fontSize": "1.25rem"},
    "text-blink": {"fontSize": "1.25rem"},
    "text-dots": {"fontSize": "1.25rem", "fontWeight": "500"},
    "text-shimmer-wave": {"fontSize": "1.25rem", "fontWeight": "500"},
    "text-shimmer": {"fontSize": "1.25rem", "fontWeight": "500"},
    "triple-dot-spinner": {"width": "0.875rem", "height": "0.875rem"},
    "twin-orbit": {"width": "1.125rem", "height": "1.125rem"},
    "typing": {"width": "4rem"},
    "wandering-eyes": {"width": "180px", "height": "5rem"},
    "wave": {"width": "6rem", "height": "3rem"},
}


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
            f"const componentStyles = {json.dumps(COMPONENT_STYLES, separators=(',', ':'))};",
            'const host = document.querySelector("[data-dash-loading-ui]") as HTMLElement | null;',
            "if (host) {",
            '  const selected = host.dataset.dashLoadingUi || "ring";',
            "  const Component = components[selected];",
            "  if (Component) {",
            '    const shadow = host.attachShadow({mode:"open"});',
            '    const style = document.createElement("style");',
            '    style.textContent = ":host{display:inline-block;width:100%;height:100%;color:inherit} *,*::before,*::after{box-sizing:border-box;border-width:var(--dash-loading-ui-stroke,2px)!important} svg,svg *{stroke-width:var(--dash-loading-ui-stroke,2px)!important} .sr-only{position:absolute!important;width:1px!important;height:1px!important;padding:0!important;margin:-1px!important;overflow:hidden!important;clip:rect(0,0,0,0)!important;white-space:nowrap!important;border:0!important}" + css;',
            "    shadow.appendChild(style);",
            '    const mount = document.createElement("span");',
            '    mount.style.cssText = "display:inline-flex;width:auto;height:auto";',
            '    const componentStyle = componentStyles[selected] || {};',
            '    Object.assign(mount.style, componentStyle);',
            "    shadow.appendChild(mount);",
            '    const text = selected.startsWith("text-") ? (host.dataset.dashLoadingText || "Loading") : undefined;',
            '    const fillsMount = Boolean(componentStyle.width || componentStyle.height);',
            '    const forwardsStyle = ["diamond", "morphing-infinity", "swirling"].includes(selected);',
            '    const props = forwardsStyle && fillsMount',
            '      ? {style: {width: "100%", height: "100%"}, children: text}',
            '      : {className: fillsMount ? "size-full" : undefined, children: text};',
            '    createRoot(mount).render(React.createElement(Component, props));',
            "  }",
            "}",
        ])
        (build / "entry.tsx").write_text("\n".join(lines) + "\n", encoding="utf-8")
        (build / "input.css").write_text(
            '@import "tailwindcss/utilities";\n'
            '@theme { --color-muted: currentColor; --radius-md: 4px; '
            '--spacing: 0.25rem; --shadow-sm: 0 1px 3px rgb(0 0 0 / 0.1); '
            '--font-mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, '
            '"Liberation Mono", "Courier New", monospace; '
            '--text-xl: 1.25rem; --text-xl--line-height: 1.75rem; }\n'
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
        shutil.copyfile(source / "LICENSE.md", OUTPUT / "LOADING-UI-LICENSE")


if __name__ == "__main__":
    main()
