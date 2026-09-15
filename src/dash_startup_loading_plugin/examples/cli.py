"""Command-line entry point for the bundled demonstration applications."""

from __future__ import annotations

import argparse
import os
from collections.abc import Sequence
from importlib import import_module
from typing import Any

_DEMO_ALIASES = {
    "examples.dash": "dash",
    "examples.dash-ant-design": "dash-ant-design",
    "dash": "dash",
    "basic": "dash",
    "dash-ant-design": "dash-ant-design",
    "dash-antd-components": "dash-ant-design",
    "antd": "dash-ant-design",
}
_CLI_EXAMPLES = (
    "examples.dash",
    "examples.dash-ant-design",
)
_DEMO_MODULES = {
    "dash": ".basic",
    "dash-ant-design": ".antd",
}


class DemoDependencyError(RuntimeError):
    """Raised when a selected demo's component library cannot be imported."""


def create_demo_app(framework: str = "dash") -> Any:
    """Create a bundled demo app for the requested component framework."""

    normalized = framework.strip().lower()
    try:
        demo_name = _DEMO_ALIASES[normalized]
    except KeyError as error:
        choices = ", ".join(_DEMO_MODULES)
        raise ValueError(f"Unknown demo framework {framework!r}. Choose one of: {choices}.") from error

    module = import_module(_DEMO_MODULES[demo_name], package=__package__)
    return module.create_app()


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dash-startup-loading-plugin",
        description="Run an installed dash-startup-loading-plugin example.",
    )
    parser.add_argument(
        "example",
        choices=_CLI_EXAMPLES,
        help="packaged example application to run",
    )
    parser.add_argument("--host", default=os.environ.get("HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8050")))
    parser.add_argument(
        "--debug",
        action=argparse.BooleanOptionalAction,
        default=os.environ.get("DASH_DEBUG", "1") == "1",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the selected bundled demonstration application."""

    parser = _parser()
    args = parser.parse_args(argv)
    try:
        app = create_demo_app(args.example)
    except DemoDependencyError as error:
        parser.error(str(error))
    app.run(host=args.host, port=args.port, debug=args.debug)
    return 0
