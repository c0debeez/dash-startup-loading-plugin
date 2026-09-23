"""Rebuild the bundled Loading UI renderers from the pinned MIT-licensed source.

One self-contained IIFE bundle is emitted per loader so that a Dash index only
ever inlines the renderer it actually uses.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
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
PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUNTIME = PROJECT_ROOT / "scripts/runtime"
OUTPUT = RUNTIME / "loading-ui"

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

# Loaders whose root element is sized through ``style`` rather than a class.
FORWARDS_STYLE = frozenset({"diamond", "morphing-infinity", "swirling"})

TAILWIND_THEME = (
    '@import "tailwindcss/utilities";\n'
    "@theme { --color-muted: currentColor; --radius-md: 4px; "
    "--spacing: 0.25rem; --shadow-sm: 0 1px 3px rgb(0 0 0 / 0.1); "
    "--font-mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "
    '"Liberation Mono", "Courier New", monospace; '
    "--text-xl: 1.25rem; --text-xl--line-height: 1.75rem; }\n"
)


def run(*args: str) -> None:
    subprocess.run(args, check=True)


def component_symbol(stem: str) -> str:
    """Return the React symbol exported by a loader source file."""

    if stem == "infinity":
        return "InfinityLoop"
    return "".join(part.title() for part in stem.split("-"))


def entry_source(name: str, component: Path, mount_module: Path) -> str:
    symbol = component_symbol(name)
    return (
        f'import {{ {symbol} }} from "{component}";\n'
        f'import {{ mount }} from "{mount_module}";\n'
        'import css from "./loading-ui.css";\n'
        "mount({\n"
        f"  component: {symbol},\n"
        "  css,\n"
        f"  geometry: {json.dumps(COMPONENT_STYLES.get(name, {}), separators=(',', ':'))},\n"
        f"  usesText: {json.dumps(name.startswith('text-'))},\n"
        f"  forwardsStyle: {json.dumps(name in FORWARDS_STYLE)},\n"
        "});\n"
    )


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="dash-loading-ui-build-") as temp:
        root = Path(temp)
        source = root / "loading-ui"
        build = root / "build"
        build.mkdir()
        run("git", "clone", "--filter=blob:none", UPSTREAM, str(source))
        run("git", "-C", str(source), "checkout", COMMIT)
        (build / "package.json").write_text('{"private":true}', encoding="utf-8")
        run(
            "npm",
            "install",
            "--prefix",
            str(build),
            "--no-audit",
            "--no-fund",
            *PACKAGES,
        )
        (source / "node_modules").symlink_to(
            build / "node_modules", target_is_directory=True
        )

        components = source / "registry/components/loading-ui"
        stylesheet = build / "loading-ui.css"
        (build / "input.css").write_text(
            f'{TAILWIND_THEME}@source "{components}";\n', encoding="utf-8"
        )
        run(
            str(build / "node_modules/.bin/tailwindcss"),
            "-i",
            str(build / "input.css"),
            "-o",
            str(stylesheet),
            "--minify",
        )

        transformer = build / "inline_loading_ui_classes.cjs"
        shutil.copyfile(
            Path(__file__).with_name("inline_loading_ui_classes.cjs"), transformer
        )
        run(
            "node",
            str(transformer),
            str(components),
            str(stylesheet),
            str(build / "loader-class-styles.ts"),
        )

        mount_module = build / "mount.ts"
        shutil.copyfile(RUNTIME / "mount.ts", mount_module)
        entries = build / "entries"
        entries.mkdir()
        shutil.copyfile(stylesheet, entries / "loading-ui.css")
        names = sorted(path.stem for path in components.glob("*.tsx"))
        for name in names:
            (entries / f"{name}.tsx").write_text(
                entry_source(name, components / f"{name}.tsx", mount_module),
                encoding="utf-8",
            )

        shutil.rmtree(OUTPUT, ignore_errors=True)
        OUTPUT.mkdir(parents=True)
        run(
            str(build / "node_modules/.bin/esbuild"),
            *(str(entries / f"{name}.tsx") for name in names),
            "--bundle",
            "--minify",
            "--legal-comments=none",
            "--format=iife",
            "--platform=browser",
            f"--alias:@/lib/utils={source / 'registry/lib/utils.ts'}",
            "--loader:.css=text",
            f"--outdir={OUTPUT}",
        )

    subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "scripts/build_startup_runtime.py")],
        check=True,
    )


if __name__ == "__main__":
    main()
