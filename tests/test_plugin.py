import html
import json
import re
from importlib.resources import files

import pytest
from dash import Dash
from dash import html as dash_html

import dash_startup_loading_plugin as loading_plugin
from dash_startup_loading_plugin import (
    setup,
    get_config,
    reset_config,
)
from dash_startup_loading_plugin.plugin import _inject_overlay


@pytest.fixture(autouse=True)
def restore_defaults():
    reset_config()
    yield
    reset_config()


def _data_config(index: str) -> dict:
    match = re.search(r'data-config="([^"]+)"', index)
    assert match is not None
    return json.loads(html.unescape(match.group(1)))


def test_setup_is_the_public_configuration_entry_point():
    assert hasattr(loading_plugin, "setup")
    assert not hasattr(loading_plugin, "configure")


def test_injects_overlay_after_body_with_custom_attributes():
    index = '<!doctype html><html><head></head><body class="app"><main></main></body></html>'

    result = _inject_overlay(index)

    assert '<style data-dash-loading-resource="style">' in result
    assert result.index("<style") < result.index("</head>")
    assert '<script data-dash-loading-resource="theme">' in result
    assert result.index('data-dash-loading-resource="theme"') < result.index("</head>")
    assert '<body class="app"><div id="dash-loading"' in result
    assert '<script data-dash-loading-resource="script">' in result
    assert result.index('id="dash-loading"') < result.index(
        '<script data-dash-loading-resource="script">'
    )
    assert result.count(" data-dash-loading ") == 1
    assert '<span class="dash-loading__antd-dot">' in result
    assert 'data-dash-loading-resource="loading-ui"' not in result
    assert '--dash-loading-size:28px' in result
    assert '--dash-loading-loader-color:#1677ff' in result
    assert '--dash-loading-loader-dark-color:#4096ff' in result
    assert _data_config(result)["requiredSelectors"] == ["#react-entry-point"]
    assert _data_config(result)["pendingSelector"] is None


def test_waiting_for_async_components_is_opt_in():
    setup(pending_selector="[data-async-placeholder]")

    result = _inject_overlay("<html><body><main></main></body></html>")

    assert _data_config(result)["pendingSelector"] == "[data-async-placeholder]"


def test_injection_is_idempotent_and_can_be_disabled():
    index = "<html><body><main></main></body></html>"
    once = _inject_overlay(index)
    assert _inject_overlay(once) == once

    setup(enabled=False)
    assert _inject_overlay(index) == index


def test_serializes_readiness_configuration_and_escapes_attributes():
    setup(
        overlay_id='loader"safe',
        aria_label='Loading "application"',
        required_selectors=["#header", "#menu"],
        pending_selector="[data-lazy-placeholder]",
        timeout_ms=None,
        minimum_display_ms=250,
        fade_duration_ms=90,
    )

    result = _inject_overlay("<html><body><main></main></body></html>")
    config = _data_config(result)

    assert 'id="loader&quot;safe"' in result
    assert 'aria-label="Loading &quot;application&quot;"' in result
    assert config == {
        "rootSelector": "#react-entry-point",
        "requiredSelectors": ["#header", "#menu"],
        "pendingSelector": "[data-lazy-placeholder]",
        "timeoutMs": None,
        "minimumDisplayMs": 250,
        "fadeDurationMs": 90,
    }


def test_custom_loader_html_is_intentionally_preserved():
    setup(custom_loader_html='<div class="brand-loader">Please wait</div>')

    result = _inject_overlay("<html><body></body></html>")

    assert '<div class="brand-loader">Please wait</div>' in result


def test_antd_spinner_matches_default_indicator_and_allows_size_override():
    setup(loader="antd")
    result = _inject_overlay("<html><body></body></html>")
    assert '<span class="dash-loading__antd-dot">' in result
    assert '<i></i><i></i><i></i><i></i>' in result
    assert '--dash-loading-size:28px' in result
    assert '--dash-loading-loader-color:#1677ff' in result
    assert '--dash-loading-loader-dark-color:#4096ff' in result

    setup(spinner_size_px=32)
    result = _inject_overlay("<html><body></body></html>")
    assert '--dash-loading-size:32px' in result


def test_invalid_loader_is_rejected():
    with pytest.raises(ValueError, match="loader"):
        setup(loader="unknown")


@pytest.mark.parametrize("name", ["spokes", "classic", "dots-ring", "spiral", "wave", "text-shimmer"])
def test_loading_ui_loader_is_mounted_before_dash_runtime(name):
    setup(loader=name, loader_color="#e91e63", loader_dark_color="#ff80ab")

    result = _inject_overlay("<html><head></head><body></body></html>")

    assert f'data-dash-loading-ui="{name}"' in result
    assert '<svg class="dash-loading__ring"' not in result
    assert '<div class="dash-loading__spinner-region">' in result
    assert '--dash-loading-size:28px' in result
    assert result.index('data-dash-loading-resource="loading-ui"') < result.index(
        'data-dash-loading-resource="script"'
    )
    assert '--dash-loading-loader-color:#e91e63' in result
    assert '--dash-loading-loader-dark-color:#ff80ab' in result


def test_loading_ui_uses_antd_blue_by_default():
    setup(loader="wave")
    result = _inject_overlay("<html><body></body></html>")
    assert '--dash-loading-loader-color:#1677ff' in result
    assert '--dash-loading-loader-dark-color:#4096ff' in result


def test_loading_ui_ring_uses_responsive_region_and_accepts_fixed_size():
    setup(loader="ring")
    result = _inject_overlay("<html><body></body></html>")
    assert '<div class="dash-loading__spinner-region"><svg class="dash-loading__ring"' in result
    assert '--dash-loading-size:28px' in result
    assert '--dash-loading-loader-color:#1677ff' in result

    setup(spinner_size_px=36)
    result = _inject_overlay("<html><body></body></html>")
    assert '--dash-loading-size:36px' in result


def test_explicit_colors_override_loader_defaults():
    setup(color="#111111", dark_color="#eeeeee", loader_color="#222222")
    result = _inject_overlay("<html><body></body></html>")
    assert '--dash-loading-loader-color:#222222' in result
    assert '--dash-loading-loader-dark-color:#eeeeee' in result


def test_custom_html_skips_loading_ui_runtime():
    setup(loader="spiral", custom_loader_html='<span>Custom</span>')
    result = _inject_overlay("<html><body></body></html>")
    assert '<span>Custom</span>' in result
    assert 'data-dash-loading-resource="loading-ui"' not in result


def test_configuration_validation():
    with pytest.raises(TypeError, match="required_selectors"):
        setup(required_selectors="#header")
    with pytest.raises(ValueError, match="timeout_ms"):
        setup(timeout_ms=-1)
    with pytest.raises(ValueError, match="theme_mode"):
        setup(theme_mode="sepia")
    with pytest.raises(ValueError, match="dash_theme_component_id"):
        setup(dash_theme_component_id="")
    with pytest.raises(TypeError, match="Unknown"):
        setup(unknown=True)
    assert get_config().required_selectors == ("#react-entry-point",)


def test_setup_uses_shared_background_defaults_and_allows_overrides():
    assert get_config().background == "#ffffff"
    assert get_config().dark_background == "#121212"

    config = setup(background="#f5f5f5", dark_background="#202020")
    assert config.background == "#f5f5f5"
    assert config.dark_background == "#202020"


def test_resolved_theme_controls_overlay_colors():
    css = (
        files("dash_startup_loading_plugin")
        .joinpath("resources/loading.css")
        .read_text(encoding="utf-8")
    )

    assert 'html[data-dash-loading-theme="light"] .dash-loading' in css
    assert 'html[data-dash-loading-theme="dark"] .dash-loading' in css


def test_theme_bootstrap_supports_dash_and_tailwind_conventions():
    script = (
        files("dash_startup_loading_plugin")
        .joinpath("resources/theme.js")
        .read_text(encoding="utf-8")
    )

    assert "_dash_persistence." in script
    assert 'classList.contains("dark")' in script
    assert 'data-color-scheme' in script
    assert 'data-dash-loading-theme' in script
    assert 'name === "system" || name === "auto"' in script


def test_theme_bootstrap_defaults_to_light_without_an_app_preference():
    script = (
        files("dash_startup_loading_plugin")
        .joinpath("resources/theme.js")
        .read_text(encoding="utf-8")
    )

    assert (
        'rootTheme() || dashPersistenceTheme() || conventionalStoredTheme() || "light"'
        in script
    )
    assert 'conventionalStoredTheme() || "system"' not in script
    assert 'theme === "system"' in script
    assert 'matchMedia("(prefers-color-scheme: dark)")' in script


def test_theme_bootstrap_serializes_component_id_and_explicit_mode():
    setup(theme_mode="dark", dash_theme_component_id="theme-provider")

    result = _inject_overlay("<html><head></head><body></body></html>")

    assert (
        'window.__dashLoadingThemeConfig={"themeMode":"dark",'
        '"dashThemeComponentId":"theme-provider"};'
    ) in result


def test_resource_names_drop_startup_and_preserve_dash_default_loading_selector():
    resources = files("dash_startup_loading_plugin").joinpath("resources")
    resource_names = {resource.name for resource in resources.iterdir() if resource.is_file()}
    resource_text = "\n".join(
        resources.joinpath(name).read_text(encoding="utf-8")
        for name in ("loading.css", "loading.js", "theme.js")
    )

    assert resource_names == {
        "loading.css", "loading.js", "loading-ui.js", "theme.js",
        "LOADING-UI-LICENSE.md",
    }
    assert "startup" not in resource_text.lower()
    assert "._dash-loading" in resource_text
    assert "window.dashLoading" in resource_text
    assert "dash-loading:ready" in resource_text


def test_dash_index_contains_overlay_and_inline_resources():
    app = Dash(__name__)
    app.layout = dash_html.Div("Ready", id="ready")

    client = app.server.test_client()
    response = client.get("/")
    index = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "data-dash-loading" in index
    assert '<style data-dash-loading-resource="style">' in index
    assert '<script data-dash-loading-resource="theme">' in index
    assert '<script data-dash-loading-resource="script">' in index
    assert "resources/loading.css" not in index
    assert "resources/loading.js" not in index
    assert '<div class="_dash-loading">' in index
