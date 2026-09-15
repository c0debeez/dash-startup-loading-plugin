"""Dash Hooks registration and startup-overlay configuration."""

from __future__ import annotations

import json
import re
from collections.abc import Iterable
from dataclasses import asdict, dataclass, fields, replace
from functools import lru_cache
from html import escape
from importlib.resources import files
from threading import RLock
from typing import Any

from dash import hooks

_OVERLAY_MARKER = "data-dash-loading"
_BODY_PATTERN = re.compile(r"<body(?:\s[^>]*)?>", flags=re.IGNORECASE)
_HEAD_END_PATTERN = re.compile(r"</head\s*>", flags=re.IGNORECASE)
_CONFIG_LOCK = RLock()

_LOADING_UI_LOADERS = frozenset({
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
})


@dataclass(frozen=True)
class StartupLoadingConfig:
    """Configuration serialized into the startup overlay.

    ``custom_loader_html`` is inserted verbatim and must only contain trusted
    HTML supplied by the application author.
    """

    enabled: bool = True
    overlay_id: str = "dash-loading"
    aria_label: str = "Loading"
    root_selector: str = "#react-entry-point"
    required_selectors: tuple[str, ...] = ("#react-entry-point",)
    pending_selector: str | None = None
    timeout_ms: int | None = 6000
    minimum_display_ms: int = 0
    fade_duration_ms: int = 160
    z_index: int = 9999
    background: str = "#ffffff"
    dark_background: str = "#121212"
    color: str | None = None
    dark_color: str | None = None
    loader_color: str | None = None
    loader_dark_color: str | None = None
    theme_mode: str = "auto"
    dash_theme_component_id: str | None = None
    loader: str = "antd"
    spinner_size_px: int | None = 28
    spinner_stroke_px: int = 2
    hide_default_loading: bool = True
    custom_loader_html: str | None = None


_DEFAULT_CONFIG = StartupLoadingConfig()
_config = _DEFAULT_CONFIG


def _selector_tuple(value: Iterable[str] | str) -> tuple[str, ...]:
    if isinstance(value, str):
        raise TypeError("required_selectors must be an iterable of CSS selector strings")
    selectors = tuple(value)
    if not all(isinstance(selector, str) and selector.strip() for selector in selectors):
        raise ValueError("required_selectors must contain non-empty CSS selector strings")
    return selectors


def _validate(config: StartupLoadingConfig) -> StartupLoadingConfig:
    if not isinstance(config.enabled, bool):
        raise TypeError("enabled must be a boolean")
    if not isinstance(config.overlay_id, str) or not config.overlay_id.strip():
        raise ValueError("overlay_id must be a non-empty string")
    if not isinstance(config.root_selector, str) or not config.root_selector.strip():
        raise ValueError("root_selector must be a non-empty CSS selector")
    if config.pending_selector is not None and (
        not isinstance(config.pending_selector, str) or not config.pending_selector.strip()
    ):
        raise ValueError("pending_selector must be None or a non-empty CSS selector")
    if config.timeout_ms is not None and config.timeout_ms < 0:
        raise ValueError("timeout_ms must be None or greater than or equal to zero")
    if config.theme_mode not in {"auto", "light", "dark"}:
        raise ValueError("theme_mode must be 'auto', 'light', or 'dark'")
    if config.loader not in _LOADING_UI_LOADERS | {"antd"}:
        raise ValueError("loader must be a Loading UI loader name or 'antd'")
    for name in ("color", "dark_color", "loader_color", "loader_dark_color"):
        value = getattr(config, name)
        if value is not None and (not isinstance(value, str) or not value.strip()):
            raise ValueError(f"{name} must be None or a non-empty CSS color")
    if config.dash_theme_component_id is not None and (
        not isinstance(config.dash_theme_component_id, str) or not config.dash_theme_component_id.strip()
    ):
        raise ValueError("dash_theme_component_id must be None or a non-empty string")
    if config.spinner_size_px is not None and config.spinner_size_px < 0:
        raise ValueError("spinner_size_px must be greater than or equal to zero")
    for name in ("minimum_display_ms", "fade_duration_ms", "spinner_stroke_px"):
        if getattr(config, name) < 0:
            raise ValueError(f"{name} must be greater than or equal to zero")
    return config


def setup(**changes: Any) -> StartupLoadingConfig:
    """Update the process-wide plugin configuration.

    Call this before creating ``dash.Dash``. The Dash hooks registry is
    process-wide, so one configuration is shared by all apps in the process.
    """

    valid_names = {field.name for field in fields(StartupLoadingConfig)}
    unknown = set(changes).difference(valid_names)
    if unknown:
        names = ", ".join(sorted(unknown))
        raise TypeError(f"Unknown startup loading option(s): {names}")
    if "required_selectors" in changes:
        changes["required_selectors"] = _selector_tuple(changes["required_selectors"])

    global _config
    with _CONFIG_LOCK:
        _config = _validate(replace(_config, **changes))
        return _config


def get_config() -> StartupLoadingConfig:
    """Return the active immutable configuration."""

    with _CONFIG_LOCK:
        return _config


def reset_config() -> StartupLoadingConfig:
    """Restore the default configuration, primarily for tests."""

    global _config
    with _CONFIG_LOCK:
        _config = _DEFAULT_CONFIG
        return _config


def _client_config(config: StartupLoadingConfig) -> dict[str, Any]:
    values = asdict(config)
    return {
        "rootSelector": values["root_selector"],
        "requiredSelectors": list(values["required_selectors"]),
        "pendingSelector": values["pending_selector"],
        "timeoutMs": values["timeout_ms"],
        "minimumDisplayMs": values["minimum_display_ms"],
        "fadeDurationMs": values["fade_duration_ms"],
    }


def _theme_config(config: StartupLoadingConfig) -> dict[str, Any]:
    return {
        "themeMode": config.theme_mode,
        "dashThemeComponentId": config.dash_theme_component_id,
    }


def _resolved_loader_colors(config: StartupLoadingConfig) -> tuple[str, str]:
    defaults = ("#1677ff", "#4096ff")
    return (
        config.loader_color or config.color or defaults[0],
        config.loader_dark_color or config.dark_color or defaults[1],
    )


def _overlay_html(config: StartupLoadingConfig) -> str:
    client_config = escape(
        json.dumps(_client_config(config), ensure_ascii=False, separators=(",", ":")),
        quote=True,
    )
    overlay_id = escape(config.overlay_id, quote=True)
    aria_label = escape(config.aria_label, quote=True)
    classes = ["dash-loading"]
    if config.hide_default_loading:
        classes.append("dash-loading--hide-default")
    class_name = " ".join(classes)
    light_color, dark_color = _resolved_loader_colors(config)
    if config.spinner_size_px is not None:
        spinner_size = f"{config.spinner_size_px}px"
    else:
        spinner_size = "28px"
    styles = {
        "--dash-loading-background": config.background,
        "--dash-loading-dark-background": config.dark_background,
        "--dash-loading-color": light_color,
        "--dash-loading-dark-color": dark_color,
        "--dash-loading-loader-color": light_color,
        "--dash-loading-loader-dark-color": dark_color,
        "--dash-loading-size": spinner_size,
        "--dash-loading-stroke": f"{config.spinner_stroke_px}px",
        "--dash-loading-fade-duration": f"{config.fade_duration_ms}ms",
        "--dash-loading-z-index": str(config.z_index),
    }
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
    loader = config.custom_loader_html
    if loader is None:
        if config.loader == "antd":
            loader = (
                '<span class="dash-loading__antd-spinner" aria-hidden="true">'
                '<span class="dash-loading__antd-dot">'
                '<i></i><i></i><i></i><i></i>'
                '</span></span>'
            )
        elif config.loader == "ring":
            loader = ring
        else:
            name = escape(config.loader, quote=True)
            loader = (
                f'<span class="dash-loading__loading-ui" data-dash-loading-ui="{name}" '
                'aria-hidden="true"></span>'
            )

    content_class = "dash-loading__content"
    if config.custom_loader_html is None and config.loader in _LOADING_UI_LOADERS:
        content_class += " dash-loading__content--loading-ui"
        loader = f'<div class="dash-loading__spinner-region">{loader}</div>'

    return (
        f'<div id="{overlay_id}" class="{class_name}" {_OVERLAY_MARKER} '
        f'data-config="{client_config}" role="status" aria-live="polite" '
        f'aria-label="{aria_label}" aria-busy="true" style="{style}">'
        f'<div class="{content_class}">{loader}</div>'
        "</div>"
    )


@lru_cache(maxsize=4)
def _resource_text(name: str) -> str:
    return files("dash_startup_loading_plugin").joinpath("resources", name).read_text(encoding="utf-8").strip()


def _inline_head_resources(app_index: str, config: StartupLoadingConfig) -> str:
    theme_config = json.dumps(_theme_config(config), ensure_ascii=False, separators=(",", ":"))
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


def _inject_overlay(app_index: str) -> str:
    config = get_config()
    if not config.enabled or _OVERLAY_MARKER in app_index:
        return app_index

    body_match = _BODY_PATTERN.search(app_index)
    if body_match is None:
        return app_index
    app_index = _inline_head_resources(app_index, config)
    body_match = _BODY_PATTERN.search(app_index)
    assert body_match is not None
    position = body_match.end()
    scripts = ""
    if config.custom_loader_html is None and config.loader not in {"ring", "antd"}:
        scripts += (
            '<script data-dash-loading-resource="loading-ui">'
            f'{_resource_text("loading-ui.js")}'
            '</script>'
        )
    scripts += f'<script data-dash-loading-resource="script">{_resource_text("loading.js")}</script>'
    return app_index[:position] + _overlay_html(config) + scripts + app_index[position:]


@hooks.index(priority=100)
def inject_startup_loading(app_index: str) -> str:
    """Inject the pre-React overlay into the final HTML document."""

    return _inject_overlay(app_index)
