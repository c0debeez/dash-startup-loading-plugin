"""Dash Hooks registration and startup-overlay configuration."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, fields, replace
from functools import lru_cache
from html import escape
from importlib.resources import files
from threading import RLock
from typing import Any, Literal, TypedDict, cast, get_args
from weakref import WeakKeyDictionary, ref

from dash import get_app, hooks
from dash.exceptions import AppNotFoundError
from flask import current_app, has_app_context, request
from typing_extensions import Unpack

_OVERLAY_MARKER = "data-dash-loading"
_BODY_PATTERN = re.compile(r"<body(?:\s[^>]*)?>", flags=re.IGNORECASE)
_HEAD_END_PATTERN = re.compile(r"</head\s*>", flags=re.IGNORECASE)
_CONFIG_LOCK = RLock()
_DASH_APPS_BY_SERVER: WeakKeyDictionary[Any, list[Any]] = WeakKeyDictionary()
_explicit_options: frozenset[str] = frozenset()

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
ThemeMode = Literal["auto", "light", "dark"]
_LOADING_UI_LOADERS = frozenset(get_args(LoaderName)) - {"default", "antd"}


@hooks.setup(priority=100)
def _register_dash_app(app: Any) -> None:
    _DASH_APPS_BY_SERVER.setdefault(app.server, []).append(ref(app))


class SetupOptions(TypedDict, total=False):
    enabled: bool
    aria_label: str
    z_index: int
    background: str
    dark_background: str
    loader_color: str | None
    loader_dark_color: str | None
    theme_mode: ThemeMode
    loader: LoaderName
    loader_text: str
    spinner_size_px: int | None
    spinner_stroke_px: int
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
    background: str = "#ffffff"
    dark_background: str = "#121212"
    loader_color: str | None = None
    loader_dark_color: str | None = None
    theme_mode: ThemeMode = "auto"
    loader: LoaderName = "default"
    loader_text: str = "Loading"
    spinner_size_px: int | None = 12
    spinner_stroke_px: int = 2
    custom_loader_html: str | None = None


_DEFAULT_CONFIG = StartupLoadingConfig()
_config = _DEFAULT_CONFIG


def _validate(config: StartupLoadingConfig) -> StartupLoadingConfig:
    if not isinstance(config.enabled, bool):
        raise TypeError("enabled must be a boolean")
    if config.theme_mode not in {"auto", "light", "dark"}:
        raise ValueError("theme_mode must be 'auto', 'light', or 'dark'")
    if config.loader not in _LOADING_UI_LOADERS | {"default", "antd"}:
        raise ValueError("loader must be a Loading UI loader name, 'default', or 'antd'")
    if not isinstance(config.loader_text, str) or not config.loader_text.strip():
        raise ValueError("loader_text must be a non-empty string")
    for name in ("loader_color", "loader_dark_color"):
        value = getattr(config, name)
        if value is not None and (not isinstance(value, str) or not value.strip()):
            raise ValueError(f"{name} must be None or a non-empty CSS color")
    if config.spinner_size_px is not None and config.spinner_size_px < 0:
        raise ValueError("spinner_size_px must be greater than or equal to zero")
    if config.spinner_stroke_px < 0:
        raise ValueError("spinner_stroke_px must be greater than or equal to zero")
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


def _mantine_forced_color_scheme(layout: Any) -> str | None:
    """Return a static MantineProvider color scheme without rendering the layout."""

    if layout is None or callable(layout):
        return None
    pending = [layout]
    seen: set[int] = set()
    while pending:
        component = pending.pop()
        if component is None or id(component) in seen:
            continue
        seen.add(id(component))
        if (
            getattr(component, "_namespace", None) == "dash_mantine_components"
            and getattr(component, "_type", None) == "MantineProvider"
        ):
            scheme = getattr(component, "forceColorScheme", None)
            if scheme in {"light", "dark"}:
                return scheme
        children = getattr(component, "children", None)
        if isinstance(children, (list, tuple)):
            pending.extend(children)
        elif children is not None:
            pending.append(children)
    return None


def _theme_config(
    config: StartupLoadingConfig,
    app_index: str,
    layout: Any = None,
) -> dict[str, Any]:
    values: dict[str, Any] = {
        "themeMode": config.theme_mode,
        "mantineBundle": "dash_mantine_components" in app_index,
    }
    forced_scheme = _mantine_forced_color_scheme(layout)
    if forced_scheme:
        values["mantineForcedColorScheme"] = forced_scheme
    return values


def _resolved_loader_colors(
    config: StartupLoadingConfig,
    loader: LoaderName,
) -> tuple[str, str]:
    defaults = ("#1677ff", "#4096ff") if loader == "antd" else ("#000", "#fff")
    return (
        config.loader_color or defaults[0],
        config.loader_dark_color or defaults[1],
    )


def _overlay_html(
    config: StartupLoadingConfig,
    loader: LoaderName | None = None,
) -> str:
    aria_label = escape(config.aria_label, quote=True)
    class_name = "dash-loading"
    selected_loader = loader or config.loader
    light_color, dark_color = _resolved_loader_colors(config, selected_loader)
    if config.spinner_size_px is not None:
        spinner_size = f"{config.spinner_size_px}px"
        spinner_scale = config.spinner_size_px / 20
    else:
        spinner_size = "20px"
        spinner_scale = 1
    loading_ui_stroke = (
        config.spinner_stroke_px / spinner_scale
        if spinner_scale > 0
        else config.spinner_stroke_px
    )
    styles = {
        "--dash-loading-background": config.background,
        "--dash-loading-dark-background": config.dark_background,
        "--dash-loading-loader-color": light_color,
        "--dash-loading-loader-dark-color": dark_color,
        "--dash-loading-size": spinner_size,
        "--dash-loading-scale": f"{spinner_scale:g}",
        "--dash-loading-ui-display": "none" if spinner_scale == 0 else "inline-flex",
        "--dash-loading-stroke": f"{config.spinner_stroke_px}px",
        "--dash-loading-ui-stroke": f"{loading_ui_stroke:g}px",
        "--dash-loading-z-index": str(config.z_index),
    }
    if config.background != _DEFAULT_CONFIG.background:
        styles["--dash-loading-mantine-light-background"] = config.background
    if config.dark_background != _DEFAULT_CONFIG.dark_background:
        styles["--dash-loading-mantine-dark-background"] = config.dark_background
    style = escape(";".join(f"{name}:{value}" for name, value in styles.items()), quote=True)
    ring = (
        '<svg class="dash-loading__ring" viewBox="0 0 24 24" fill="none" '
        'aria-hidden="true" xmlns="http://www.w3.org/2000/svg">'
        '<path d="M21 12.0004C20.9999 13.901 20.3981 15.7528 19.2809 17.2904'
        'C18.1637 18.8279 16.5885 19.9723 14.7809 20.5596'
        'C12.9733 21.1469 11.0262 21.1468 9.21864 20.5594'
        'C7.41109 19.9721 5.83588 18.8276 4.71876 17.29'
        'C3.60165 15.7523 2.99999 13.9005 3 11.9999'
        'C3.00001 10.0993 3.60171 8.24755 4.71884 6.70994'
        'C5.83598 5.17233 7.4112 4.02785 9.21877 3.44052'
        'C11.0263 2.85319 12.9734 2.85316 14.781 3.44044" '
        'stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"/>'
        '</svg>'
    )
    loader_html = config.custom_loader_html
    if loader_html is None:
        if selected_loader == "default":
            loader_html = '<span class="dash-loading__spinner" aria-hidden="true"></span>'
        elif selected_loader == "antd":
            antd_size = "20px" if config.spinner_size_px == 12 else spinner_size
            loader_html = (
                '<span class="dash-loading__antd-spinner" aria-hidden="true" '
                f'style="--dash-loading-antd-size:{antd_size}">'
                '<span class="dash-loading__antd-dot">'
                '<i></i><i></i><i></i><i></i>'
                '</span></span>'
            )
        elif selected_loader == "ring":
            loader_html = ring
        else:
            name = escape(selected_loader, quote=True)
            loader_text = escape(config.loader_text, quote=True)
            loader_html = (
                f'<span class="dash-loading__loading-ui" data-dash-loading-ui="{name}" '
                f'data-dash-loading-text="{loader_text}" '
                'aria-hidden="true"></span>'
            )

    content_class = "dash-loading__content"
    if config.custom_loader_html is None and selected_loader in _LOADING_UI_LOADERS:
        content_class += " dash-loading__content--loading-ui"
        loader_html = f'<div class="dash-loading__spinner-region">{loader_html}</div>'

    return (
        f'<div class="{class_name}" {_OVERLAY_MARKER} '
        'role="status" aria-live="polite" '
        f'aria-label="{aria_label}" aria-busy="true" style="{style}">'
        f'<div class="{content_class}">{loader_html}</div>'
        "</div>"
    )


@lru_cache(maxsize=4)
def _resource_text(name: str) -> str:
    return files("dash_startup_loading_plugin").joinpath("resources").joinpath(name).read_text(encoding="utf-8").strip()


def _inline_head_resources(
    app_index: str,
    config: StartupLoadingConfig,
    layout: Any = None,
) -> str:
    theme_config = json.dumps(
        _theme_config(config, app_index, layout),
        ensure_ascii=False,
        separators=(",", ":"),
    )
    resources = (
        '<style data-dash-loading-resource="style">'
        f"{_resource_text('loading.css')}"
        "</style>"
        '<script data-dash-loading-resource="theme">'
        f"window.__dashLoadingThemeConfig={theme_config};"
        f"{_resource_text('theme.js')}"
        "</script>"
    )
    head_end = _HEAD_END_PATTERN.search(app_index)
    if head_end is not None:
        return app_index[: head_end.start()] + resources + app_index[head_end.start() :]
    return resources + app_index


def _inject_overlay(app_index: str, layout: Any = None) -> str:
    config, explicit_options = _configuration_state()
    if not config.enabled or _OVERLAY_MARKER in app_index:
        return app_index

    body_match = _BODY_PATTERN.search(app_index)
    if body_match is None:
        return app_index
    app_index = _inline_head_resources(app_index, config, layout)
    body_match = _BODY_PATTERN.search(app_index)
    assert body_match is not None
    position = body_match.end()
    dash_antd_bundle = "dash_antd_components" in app_index
    loader = (
        "antd"
        if dash_antd_bundle and "loader" not in explicit_options
        else config.loader
    )
    scripts = ""
    if config.custom_loader_html is None and loader in _LOADING_UI_LOADERS - {"ring"}:
        scripts += (
            '<script data-dash-loading-resource="loading-ui">'
            f'{_resource_text("loading-ui.js")}'
            '</script>'
        )
    scripts += f'<script data-dash-loading-resource="script">{_resource_text("loading.js")}</script>'
    return app_index[:position] + _overlay_html(config, loader) + scripts + app_index[position:]


def _current_app_layout() -> Any:
    if has_app_context():
        server = cast(Any, current_app)._get_current_object()
        registered = [app_ref() for app_ref in _DASH_APPS_BY_SERVER.get(server, [])]
        apps = [app for app in registered if app is not None]
        if apps:
            path = request.path
            matches = [
                app
                for app in apps
                if path.startswith(app.config.routes_pathname_prefix)
            ]
            selected = max(
                matches or apps,
                key=lambda app: len(app.config.routes_pathname_prefix),
            )
            return selected.layout
    try:
        return get_app().layout
    except AppNotFoundError:
        return None


@hooks.index(priority=100)
def inject_startup_loading(app_index: str) -> str:
    """Inject the pre-React overlay into the final HTML document."""

    return _inject_overlay(app_index, _current_app_layout())
