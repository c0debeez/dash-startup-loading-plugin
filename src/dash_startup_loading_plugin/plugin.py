"""Dash Hooks registration and startup-overlay configuration."""

from __future__ import annotations

import re
from dataclasses import dataclass, fields, replace
from functools import cache
from html import escape
from importlib.metadata import PackageNotFoundError, version
from importlib.resources import files
from threading import RLock
from typing import Any, Literal, NamedTuple, TypedDict, cast, get_args
from weakref import WeakKeyDictionary, ref

from dash import get_app, hooks
from dash.exceptions import AppNotFoundError
from flask import abort, current_app, has_request_context, request
from typing_extensions import Unpack

try:
    __version__ = version("dash-startup-loading-plugin")
except PackageNotFoundError:  # pragma: no cover - source tree fallback
    __version__ = "2.0.1"

_OVERLAY_MARKER = "data-dash-loading"
_BODY_PATTERN = re.compile(r"<body(?:\s[^>]*)?>", flags=re.IGNORECASE)
_HEAD_END_PATTERN = re.compile(r"</head\s*>", flags=re.IGNORECASE)
_START_SCRIPT = "<script>if (window.__dashStartupLoadingStart){window.__dashStartupLoadingStart()}</script>"
_LOADER_CACHE_CONTROL = "public, max-age=31536000, immutable"
_DEFAULT_PATHNAME_PREFIX = "/"
_ANTD_BUNDLE_MARKER = "dash_antd_components"

_CONFIG_LOCK = RLock()
_dash_server: WeakKeyDictionary[Any, list[Any]] = WeakKeyDictionary()
_explicit_options: frozenset[str] = frozenset()

_LOADING_UI_DEFAULT_SIZE = 64
_LOADING_UI_DEFAULT_STROKE_WIDTH = 2
_LOADING_UI_DEFAULT_LOADER = "ring"
_ANTD_SPIN_DEFAULT_SIZE = 20
_LIGHT_LOADER_COLOR = "#1677ff"
_DARK_LOADER_COLOR = "#1668dc"
_LIGHT_TEXT_COLOR = "rgba(0,0,0,0.88)"
_DARK_TEXT_COLOR = "rgba(255,255,255,0.85)"
LoaderName = Literal[
    "default",
    "antd",
    "accordion-loader",
    "analyzing-image",
    "arc",
    "bars",
    "bobbing-dots",
    "bouncing-dots",
    "classic",
    "clock-ring",
    "comet-spinner",
    "concentric-ring",
    "conveyor-loop",
    "dash-ring",
    "diamond",
    "dots",
    "dots-ring",
    "dual-arc",
    "fade-arc",
    "infinity",
    "infinity-square-snake",
    "infinity-track",
    "morphing-infinity",
    "orbit-ring",
    "pulsating-dots",
    "pulse",
    "pulse-dot",
    "quarter-ring",
    "ring",
    "ripple",
    "satellite-ring",
    "skeleton",
    "spiral",
    "spokes",
    "square-accordion",
    "square-grid",
    "square-snake",
    "swirling",
    "symmetric-wave",
    "terminal",
    "text-blink",
    "text-dots",
    "text-shimmer",
    "text-shimmer-wave",
    "triple-dot-spinner",
    "twin-orbit",
    "typing",
    "wandering-eyes",
    "wave",
]
_LOADER_NAMES = frozenset(get_args(LoaderName))
_LOADING_UI_LOADERS = _LOADER_NAMES - {"default", "antd"}
_COLOR_OPTIONS = (
    "loader_color",
    "loader_dark_color",
    "loader_text_color",
    "loader_dark_text_color",
)
_LOADER_ROUTE = "_dash-startup-loading"


@hooks.setup(priority=100)
def _register_dash_app(app: Any) -> None:
    registered = _dash_server.setdefault(app.server, [])
    registered[:] = [app_ref for app_ref in registered if app_ref() is not None]
    registered.append(ref(app))


def _current_app() -> Any:
    """Return the Dash app serving the current request, or ``None`` outside one."""

    if has_request_context():
        server = cast(Any, current_app)._get_current_object()
        apps = [app for app in (app_ref() for app_ref in _dash_server.get(server, ())) if app is not None]
        if apps:
            matches = [app for app in apps if request.path.startswith(app.config.routes_pathname_prefix)]
            return max(matches or apps, key=lambda app: len(app.config.routes_pathname_prefix))
    try:
        return get_app()
    except AppNotFoundError:
        return None


def _requests_pathname_prefix() -> str:
    app = _current_app()
    if app is None:
        return _DEFAULT_PATHNAME_PREFIX
    return app.config.requests_pathname_prefix


class SetupOptions(TypedDict, total=False):
    enabled: bool
    aria_label: str
    z_index: int
    background: str
    dark_background: str
    loader_color: str | None
    loader_dark_color: str | None
    loader_text_color: str | None
    loader_dark_text_color: str | None
    loader: LoaderName
    loader_text: str
    loader_size: int | float | None
    loader_stroke_width: int | float
    custom_loader_html: str | None


@dataclass(frozen=True)
class StartupLoadingConfig:
    """Configuration serialized into the startup overlay.

    ``custom_loader_html`` is inserted verbatim and must only contain trusted
    HTML supplied by the application author.
    """

    enabled: bool = True
    aria_label: str = "Loading"
    z_index: int = 9999
    background: str = "#f5f5f5"
    dark_background: str = "#000"
    loader_color: str | None = None
    loader_dark_color: str | None = None
    loader_text_color: str | None = None
    loader_dark_text_color: str | None = None
    loader: LoaderName = "default"
    loader_text: str = "Loading"
    loader_size: int | float | None = _LOADING_UI_DEFAULT_SIZE
    loader_stroke_width: int | float = _LOADING_UI_DEFAULT_STROKE_WIDTH
    custom_loader_html: str | None = None


_DEFAULT_CONFIG = StartupLoadingConfig()
_config = _DEFAULT_CONFIG


def _validate_color(name: str, value: str | None) -> None:
    if value is not None and (not isinstance(value, str) or not value.strip()):
        raise ValueError(f"{name} must be None or a non-empty CSS color")


def _validate_length(name: str, value: float) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be an int or float")
    if value < 0:
        raise ValueError(f"{name} must be greater than or equal to zero")


def _validate(config: StartupLoadingConfig) -> StartupLoadingConfig:
    if not isinstance(config.enabled, bool):
        raise TypeError("enabled must be a boolean")
    if config.loader not in _LOADER_NAMES:
        raise ValueError("loader must be a Loading UI loader name, 'default', or 'antd'")
    if not isinstance(config.loader_text, str) or not config.loader_text.strip():
        raise ValueError("loader_text must be a non-empty string")
    for name in ("background", "dark_background"):
        value = getattr(config, name)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{name} must be a non-empty CSS color")
    for name in _COLOR_OPTIONS:
        _validate_color(name, getattr(config, name))
    if config.loader_size is not None:
        _validate_length("loader_size", config.loader_size)
    _validate_length("loader_stroke_width", config.loader_stroke_width)
    return config


def setup(**changes: Unpack[SetupOptions]) -> StartupLoadingConfig:
    """Update the process-wide plugin configuration.

    Call this before creating ``dash.Dash``. The Dash hooks registry is
    process-wide, so one configuration is shared by all apps in the process.
    """

    valid_names = {field.name for field in fields(StartupLoadingConfig)}
    unknown = set(changes).difference(valid_names)
    if unknown:
        names = ", ".join(sorted(unknown))
        raise TypeError(f"Unknown startup loading option(s): {names}")
    global _config, _explicit_options
    with _CONFIG_LOCK:
        _config = _validate(replace(_config, **changes))
        _explicit_options = _explicit_options.union(changes)
        return _config


def get_config() -> StartupLoadingConfig:
    """Return the active immutable configuration."""

    with _CONFIG_LOCK:
        return _config


def _configuration_state() -> tuple[StartupLoadingConfig, frozenset[str]]:
    with _CONFIG_LOCK:
        return _config, _explicit_options


def reset_config() -> StartupLoadingConfig:
    """Restore the default configuration, primarily for tests."""

    global _config, _explicit_options
    with _CONFIG_LOCK:
        _config = _DEFAULT_CONFIG
        _explicit_options = frozenset()
        return _config


class _Visuals(NamedTuple):
    loader_color: str
    loader_dark_color: str
    text_color: str
    dark_text_color: str


def _resolved_visuals(config: StartupLoadingConfig) -> _Visuals:
    return _Visuals(
        loader_color=config.loader_color or _LIGHT_LOADER_COLOR,
        loader_dark_color=config.loader_dark_color or config.loader_color or _DARK_LOADER_COLOR,
        text_color=config.loader_text_color or _LIGHT_TEXT_COLOR,
        dark_text_color=config.loader_dark_text_color or config.loader_text_color or _DARK_TEXT_COLOR,
    )


def _overlay_styles(config: StartupLoadingConfig, loader: str) -> dict[str, str]:
    visuals = _resolved_visuals(config)
    size = _LOADING_UI_DEFAULT_SIZE if config.loader_size is None else config.loader_size
    scale = size / _LOADING_UI_DEFAULT_SIZE
    # Loading UI draws at its own baseline, so the stroke is pre-divided by the scale.
    loading_ui_stroke = config.loader_stroke_width / scale if scale > 0 else config.loader_stroke_width
    styles = {
        "--dash-loading-background": config.background,
        "--dash-loading-dark-background": config.dark_background,
        "--dash-loading-loader-color": visuals.loader_color,
        "--dash-loading-loader-dark-color": visuals.loader_dark_color,
        "--dash-loading-loader-text-color": visuals.text_color,
        "--dash-loading-loader-dark-text-color": visuals.dark_text_color,
        "--dash-loading-size": f"{size}px",
        "--dash-loading-scale": f"{scale:g}",
        "--dash-loading-ui-display": "none" if scale == 0 else "inline-flex",
        "--dash-loading-stroke": f"{config.loader_stroke_width}px",
        "--dash-loading-ui-stroke": f"{loading_ui_stroke:g}px",
        "--dash-loading-z-index": str(config.z_index),
        "--dash-loading-fade-duration": "0ms",
    }
    if loader == "antd":
        styles["--dash-loading-antd-scale"] = (
            f"{_ANTD_SPIN_DEFAULT_SIZE / config.loader_size:g}" if config.loader_size else "1"
        )
    return styles


def _loader_markup(config: StartupLoadingConfig, loader: str) -> str:
    if loader == "antd":
        return (
            '<span class="dash-loading__antd-spinner" aria-hidden="true">'
            '<span class="dash-loading__antd-dot">'
            "<i></i><i></i><i></i><i></i>"
            "</span></span>"
        )
    return (
        f'<span class="dash-loading__loading-ui" data-dash-loading-ui="{escape(loader, quote=True)}" '
        f'data-dash-loading-text="{escape(config.loader_text, quote=True)}" '
        'aria-hidden="true"></span>'
    )


def _overlay_html(config: StartupLoadingConfig, loader: str) -> str:
    styles = _overlay_styles(config, loader)
    style = escape(";".join(f"{name}:{value}" for name, value in styles.items()), quote=True)
    content_class = "dash-loading__content"
    if config.custom_loader_html is not None:
        loader_html = config.custom_loader_html
    else:
        loader_html = _loader_markup(config, loader)
        if loader in _LOADING_UI_LOADERS:
            content_class += " dash-loading__content--loading-ui"
            loader_html = f'<div class="dash-loading__spinner-region">{loader_html}</div>'
    return (
        f'<div class="dash-loading" {_OVERLAY_MARKER} '
        'role="status" aria-live="polite" '
        f'aria-label="{escape(config.aria_label, quote=True)}" aria-busy="true" style="{style}">'
        f'<div class="{content_class}">{loader_html}</div>'
        "</div>"
    )


@cache
def _resource_text(name: str) -> str:
    return files(__package__).joinpath(f"resources/{name}").read_text(encoding="utf-8").strip()


@hooks.route(name=f"{_LOADER_ROUTE}/{{loader}}.js", priority=100)
@hooks.route(name=f"{_LOADER_ROUTE}/<loader>.js", priority=100)
def serve_loading_ui(loader: str = ""):
    """Serve a single Loading UI renderer as a long-lived cacheable resource."""

    if loader not in _LOADING_UI_LOADERS:
        abort(404)

    app = _current_app()
    backend = app.backend if app is not None else None
    if backend is not None:
        response = backend.make_response(
            _resource_text(f"loading-ui/{loader}.js"),
            mimetype="text/javascript",
        )
        response.headers["Cache-Control"] = _LOADER_CACHE_CONTROL
        return response

    return current_app.response_class(
        _resource_text(f"loading-ui/{loader}.js"),
        mimetype="text/javascript",
        headers={"Cache-Control": _LOADER_CACHE_CONTROL},
    )


def _loading_ui_script(loader: str) -> str:
    """Reference the selected renderer instead of inlining every loader in the index."""

    source = f"{_requests_pathname_prefix()}{_LOADER_ROUTE}/{loader}.js?v={__version__}"
    return f'<script data-dash-loading-resource="loading-ui" src="{escape(source, quote=True)}" async></script>'


def _with_startup_runtime(head: str) -> str:
    runtime = f'<script data-dash-loading-resource="startup">{_resource_text("startup-loading.js")}</script>'
    head_end = _HEAD_END_PATTERN.search(head)
    if head_end is None:
        return runtime + head
    return head[: head_end.start()] + runtime + head[head_end.start() :]


def _selected_loader(config: StartupLoadingConfig, explicit_options: frozenset[str], app_index: str) -> str:
    """Resolve the configured loader, defaulting to Ant Design's when its bundle is present."""

    if _ANTD_BUNDLE_MARKER in app_index and "loader" not in explicit_options:
        return "antd"
    return _LOADING_UI_DEFAULT_LOADER if config.loader == "default" else config.loader


def _inject_overlay(app_index: str) -> str:
    config, explicit_options = _configuration_state()
    if not config.enabled or _OVERLAY_MARKER in app_index:
        return app_index
    body = _BODY_PATTERN.search(app_index)
    if body is None:
        return app_index

    loader = _selected_loader(config, explicit_options, app_index)
    scripts = ""
    if config.custom_loader_html is None and loader in _LOADING_UI_LOADERS:
        scripts = _loading_ui_script(loader)
    return (
        _with_startup_runtime(app_index[: body.end()])
        + _overlay_html(config, loader)
        + scripts
        + _START_SCRIPT
        + app_index[body.end() :]
    )


@hooks.index(priority=100)
def inject_startup_loading(app_index: str) -> str:
    """Inject the pre-React overlay into the final HTML document."""

    return _inject_overlay(app_index)
