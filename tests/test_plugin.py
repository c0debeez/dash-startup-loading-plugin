from importlib.resources import files

import pytest
from dash import Dash
from dash import html as dash_html

import dash_startup_loading_plugin as loading_plugin
from dash_startup_loading_plugin import (
    get_config,
    reset_config,
    setup,
)
from dash_startup_loading_plugin.plugin import _inject_overlay


@pytest.fixture(autouse=True)
def restore_defaults():
    reset_config()
    yield
    reset_config()


def startup_runtime() -> str:
    return (
        files("dash_startup_loading_plugin")
        .joinpath("resources/startup-loading.js")
        .read_text(encoding="utf-8")
    )


def loading_ui_runtime(loader: str) -> str:
    return (
        files("dash_startup_loading_plugin")
        .joinpath(f"resources/loading-ui/{loader}.js")
        .read_text(encoding="utf-8")
    )


def test_setup_is_the_public_configuration_entry_point():
    assert hasattr(loading_plugin, "setup")
    assert not hasattr(loading_plugin, "configure")


def test_injects_overlay_after_body_with_custom_attributes():
    index = '<!doctype html><html><head></head><body class="app"><main></main></body></html>'

    result = _inject_overlay(index)

    assert '<script data-dash-loading-resource="startup">' in result
    assert result.index('data-dash-loading-resource="startup"') < result.index(
        "</head>"
    )
    assert '<body class="app"><div class="dash-loading"' in result
    assert (
        "if (window.__dashStartupLoadingStart){window.__dashStartupLoadingStart()}" in result
    )
    assert result.index('class="dash-loading"') < result.rindex(
        "window.__dashStartupLoadingStart"
    )
    assert result.count(" data-dash-loading ") == 1
    assert (
        '<span class="dash-loading__spinner" aria-hidden="true"></span>' not in result
    )
    assert '<span class="dash-loading__antd-dot">' not in result
    assert 'data-dash-loading-resource="loading-ui"' in result
    assert "--dash-loading-size:64px" in result
    assert "--dash-loading-stroke:2px" in result
    assert "--dash-loading-background" not in result
    assert "--dash-loading-dark-background" not in result
    assert "--dash-loading-loader-color:#1677ff" in result
    assert "--dash-loading-loader-dark-color:#1668dc" in result
    assert "--dash-loading-loader-text-color:rgba(0,0,0,0.88)" in result
    assert "--dash-loading-loader-dark-text-color:rgba(255,255,255,0.85)" in result
    assert "data-config=" not in result


def test_injection_is_idempotent_and_can_be_disabled():
    index = "<html><body><main></main></body></html>"
    once = _inject_overlay(index)
    assert _inject_overlay(once) == once

    setup(enabled=False)
    assert _inject_overlay(index) == index


def test_escapes_accessible_label():
    setup(aria_label='Loading "application"')

    result = _inject_overlay("<html><body><main></main></body></html>")

    assert 'aria-label="Loading &quot;application&quot;"' in result


def test_browser_runtime_supports_initial_readiness_gates():
    script = startup_runtime()

    assert 'document.querySelector("#react-entry-point")' in script
    assert 'querySelector("._dash-loading")' in script
    assert "requestAnimationFrame(" in script
    assert "MutationObserver" in script


def test_custom_loader_html_is_intentionally_preserved():
    setup(custom_loader_html='<div class="brand-loader">Please wait</div>')

    result = _inject_overlay("<html><body></body></html>")

    assert '<div class="brand-loader">Please wait</div>' in result


def test_default_loader_uses_the_loading_ui_ring():
    result = _inject_overlay("<html><body></body></html>")

    assert get_config().loader == "default"
    assert 'data-dash-loading-ui="ring"' in result
    assert '<svg class="dash-loading__ring"' not in result
    assert "_dash-startup-loading/ring.js" in result


def test_dash_builtin_loading_message_stays_hidden_after_overlay_removal():
    runtime = startup_runtime()

    assert "._dash-loading{" in runtime
    assert "display:none!important" in runtime
    assert ".dash-loading ~" not in runtime


def test_antd_spinner_uses_12px_as_its_scaled_visual_baseline():
    setup(loader="antd")
    result = _inject_overlay("<html><body></body></html>")
    runtime = startup_runtime()

    assert '<span class="dash-loading__antd-dot">' in result
    assert "<i></i><i></i><i></i><i></i>" in result
    assert "--dash-loading-size:64px" in result
    assert "transform:scale(var(--dash-loading-antd-scale,1))" in runtime
    assert "transform-origin:center" in runtime
    assert "--dash-loading-loader-color:#1677ff" in result
    assert "--dash-loading-loader-dark-color:#1668dc" in result
    assert "--dash-loading-antd-scale:0.3125" in result

    setup(loader_size=20)
    result = _inject_overlay("<html><body></body></html>")
    assert "--dash-loading-size:20px" in result
    assert "--dash-loading-antd-scale:1" in result

    setup(loader_size=32)
    result = _inject_overlay("<html><body></body></html>")
    assert "--dash-loading-size:32px" in result
    assert "--dash-loading-antd-scale:0.625" in result


def test_antd_default_size_override_does_not_affect_other_loaders():
    setup(loader="default")
    result = _inject_overlay("<html><body></body></html>")

    assert "--dash-loading-size:64px" in result
    assert '<span class="dash-loading__antd-spinner"' not in result


def test_invalid_loader_is_rejected():
    with pytest.raises(ValueError, match="loader"):
        setup(loader="unknown")


@pytest.mark.parametrize(
    "name", ["spokes", "classic", "dots-ring", "spiral", "wave", "text-shimmer"]
)
def test_loading_ui_loader_is_mounted_before_dash_runtime(name):
    setup(loader=name, loader_color="#e91e63", loader_dark_color="#ff80ab")

    result = _inject_overlay("<html><head></head><body></body></html>")

    assert f'data-dash-loading-ui="{name}"' in result
    assert '<svg class="dash-loading__ring"' not in result
    assert '<div class="dash-loading__spinner-region">' in result
    assert "--dash-loading-size:64px" in result
    assert 'data-dash-loading-resource="startup"' in result
    assert "--dash-loading-loader-color:#e91e63" in result
    assert "--dash-loading-loader-dark-color:#ff80ab" in result


def test_loading_ui_uses_official_component_geometry_and_border_box():
    setup(loader="dual-arc")

    result = _inject_overlay("<html><body></body></html>")
    runtime = loading_ui_runtime("dual-arc")
    core_runtime = startup_runtime()

    assert ".dash-loading__loading-ui" in core_runtime
    assert 'width:"3.5rem",height:"3.5rem"' in runtime
    assert "display:inline-flex;width:auto;height:auto" in runtime
    assert "box-sizing:border-box" in runtime
    assert "border-width:var(--dash-loading-ui-stroke,2px)!important" in runtime
    assert "stroke-width:var(--dash-loading-ui-stroke,2px)!important" in runtime
    assert "--dash-loading-size:64px" in result
    assert "--dash-loading-scale:1" in result
    assert "--dash-loading-ui-stroke:2px" in result

    assert 'width:"180px",height:"5rem"' in loading_ui_runtime("wandering-eyes")
    assert 'fontSize:"1.25rem"' in loading_ui_runtime("text-blink")

    setup(loader="wave", loader_size=40)
    result = _inject_overlay("<html><body></body></html>")
    assert "--dash-loading-size:40px" in result
    assert "--dash-loading-scale:0.625" in result
    assert "--dash-loading-ui-stroke:3.2px" in result

    setup(loader="wave", loader_size=0)
    result = _inject_overlay("<html><body></body></html>")
    assert "--dash-loading-scale:0" in result
    assert "--dash-loading-ui-display:none" in result


def test_loading_ui_uses_ant_design_token_default_colors():
    setup(loader="wave")
    result = _inject_overlay("<html><body></body></html>")
    assert "--dash-loading-loader-color:#1677ff" in result
    assert "--dash-loading-loader-dark-color:#1668dc" in result


def test_loader_color_is_reused_in_dark_mode_when_not_explicitly_set():
    setup(loader_color="#e91e63")

    result = _inject_overlay("<html><body></body></html>")

    assert "--dash-loading-loader-color:#e91e63" in result
    assert "--dash-loading-loader-dark-color:#e91e63" in result


def test_text_loader_colors_use_plugin_defaults_and_allow_overrides():
    result = _inject_overlay("<html><body></body></html>")
    assert "--dash-loading-loader-text-color:rgba(0,0,0,0.88)" in result
    assert "--dash-loading-loader-dark-text-color:rgba(255,255,255,0.85)" in result

    setup(loader_text_color="#333333")
    result = _inject_overlay("<html><body></body></html>")
    assert "--dash-loading-loader-text-color:#333333" in result
    assert "--dash-loading-loader-dark-text-color:#333333" in result


def test_text_loader_supports_custom_text_and_escapes_the_attribute():
    setup(loader="text-shimmer", loader_text='正在加载 "报表"')

    result = _inject_overlay("<html><body></body></html>")
    renderer = loading_ui_runtime("text-shimmer")

    assert 'data-dash-loading-text="正在加载 &quot;报表&quot;"' in result
    assert ".dataset.dashLoadingText" in renderer


def test_dash_antd_bundle_uses_the_plugin_default_loader_without_setup():
    index = (
        '<html><head><script src="/_dash-component-suites/'
        'dash_antd_components/bundle.js"></script></head><body></body></html>'
    )

    result = _inject_overlay(index)

    assert '<span class="dash-loading__antd-dot">' in result
    assert 'data-dash-loading-resource="startup"' in result
    assert "--dash-loading-loader-color:#1677ff" in result
    assert "--dash-loading-loader-dark-color:#1668dc" in result
    assert "--dash-loading-antd-scale:0.3125" in result


def test_dash_antd_bundle_does_not_read_config_provider_tokens():
    index = (
        '<html><head><script src="/_dash-component-suites/'
        'dash_antd_components/bundle.js"></script></head><body></body></html>'
    )

    result = _inject_overlay(index)

    assert "--dash-loading-background" not in result
    assert "--dash-loading-loader-color:#1677ff" in result
    assert "--dash-loading-loader-text-color:rgba(0,0,0,0.88)" in result


def test_dash_antd_dark_algorithm_does_not_change_plugin_defaults():
    index = (
        '<html><head><script src="/_dash-component-suites/'
        'dash_antd_components/bundle.js"></script></head><body></body></html>'
    )

    result = _inject_overlay(index)

    assert "--dash-loading-background" not in result
    assert "--dash-loading-loader-color:#1677ff" in result
    assert "--dash-loading-loader-text-color:rgba(0,0,0,0.88)" in result


def test_explicit_loader_applies_with_a_dash_antd_bundle():
    setup(loader="wave")
    index = (
        '<html><head><script src="/_dash-component-suites/'
        'dash_antd_components/bundle.js"></script></head><body></body></html>'
    )

    result = _inject_overlay(index)

    assert 'data-dash-loading-ui="wave"' in result
    assert 'data-dash-loading-resource="startup"' in result
    assert "--dash-loading-loader-color:#1677ff" in result
    assert "--dash-loading-loader-dark-color:#1668dc" in result


def test_explicit_default_loader_keeps_loading_ui_ring_with_dash_antd_bundle():
    setup(loader="default")
    index = (
        '<html><head><script src="/_dash-component-suites/'
        'dash_antd_components/bundle.js"></script></head><body></body></html>'
    )

    result = _inject_overlay(index)

    assert 'data-dash-loading-ui="ring"' in result
    assert '<span class="dash-loading__antd-dot">' not in result


def test_explicit_colors_apply_with_the_default_loader_and_dash_antd_bundle():
    setup(loader_color="#e91e63", loader_dark_color="#ff80ab")
    index = (
        '<html><head><script src="/_dash-component-suites/'
        'dash_antd_components/bundle.js"></script></head><body></body></html>'
    )

    result = _inject_overlay(index)

    assert '<span class="dash-loading__antd-dot">' in result
    assert "--dash-loading-antd-scale:0.3125" in result
    assert "--dash-loading-loader-color:#e91e63" in result
    assert "--dash-loading-loader-dark-color:#ff80ab" in result


def test_loading_ui_ring_uses_responsive_region_and_accepts_fixed_size():
    setup(loader="ring")
    result = _inject_overlay("<html><body></body></html>")
    assert (
        '<div class="dash-loading__spinner-region"><span class="dash-loading__loading-ui" data-dash-loading-ui="ring"'
        in result
    )
    assert "--dash-loading-size:64px" in result
    assert "--dash-loading-loader-color:#1677ff" in result

    setup(loader_size=36)
    result = _inject_overlay("<html><body></body></html>")
    assert "--dash-loading-size:36px" in result

    setup(loader_size=None)
    result = _inject_overlay("<html><body></body></html>")
    assert "--dash-loading-size:64px" in result
    assert "--dash-loading-scale:1" in result


def test_explicit_colors_override_loader_defaults():
    setup(loader_color="#222222", loader_dark_color="#eeeeee")
    result = _inject_overlay("<html><body></body></html>")
    assert "--dash-loading-loader-color:#222222" in result
    assert "--dash-loading-loader-dark-color:#eeeeee" in result


def test_custom_html_skips_loading_ui_runtime():
    setup(loader="spiral", custom_loader_html="<span>Custom</span>")
    result = _inject_overlay("<html><body></body></html>")
    assert "<span>Custom</span>" in result
    assert 'data-dash-loading-resource="startup"' in result


@pytest.mark.parametrize(
    "removed_option",
    [
        "root_selector",
        "required_selectors",
        "pending_selector",
        "overlay_id",
        "timeout_ms",
        "minimum_display_ms",
        "spinner_size_px",
        "spinner_stroke_px",
        "color",
        "dark_color",
        "hide_default_loading",
        "dash_theme_component_id",
        "theme_storage_key",
        "theme_storage_path",
        "sync_root_theme_classes",
        "wait_for_initial_callbacks",
        "wait_for_fonts",
        "stabilize_selectors",
        "settle_frames",
        "settle_ms",
        "fade_duration_ms",
        "ready_timeout_ms",
        "background",
        "dark_background",
    ],
)
def test_removed_configuration_options_are_rejected(removed_option):
    with pytest.raises(TypeError, match=removed_option):
        setup(**{removed_option: True})


def test_configuration_validation():
    with pytest.raises(TypeError, match="theme_mode"):
        setup(theme_mode="sepia")
    with pytest.raises(ValueError, match="loader_text"):
        setup(loader_text=" ")
    with pytest.raises(ValueError, match="loader_size"):
        setup(loader_size=-1)
    with pytest.raises(TypeError, match="loader_size"):
        setup(loader_size=True)
    with pytest.raises(ValueError, match="loader_stroke_width"):
        setup(loader_stroke_width=-1)
    with pytest.raises(TypeError, match="loader_stroke_width"):
        setup(loader_stroke_width=True)
    with pytest.raises(TypeError, match="theme_store"):
        setup(theme_store=" ")
    with pytest.raises(TypeError, match="theme_store"):
        setup(theme_store=("preferences", ""))
    with pytest.raises(TypeError, match="wait_for"):
        setup(wait_for=["#ready", ""])
    with pytest.raises(TypeError, match="wait_for"):
        setup(wait_for=1)
    with pytest.raises(TypeError, match="timeout"):
        setup(timeout=0)
    with pytest.raises(TypeError, match="Unknown"):
        setup(unknown=True)


def test_setup_rejects_removed_theme_and_wait_options():
    for name in ("theme_store", "sync_theme", "wait_for", "timeout"):
        with pytest.raises(TypeError, match=name):
            setup(**{name: True})


def test_resolved_theme_controls_overlay_colors():
    runtime = startup_runtime()

    assert "html.dark .dash-loading" in runtime
    assert "background:var(--layout-bg,#111825)" in runtime
    assert "--dash-loading-dark-background" not in runtime


def test_theme_bootstrap_supports_dash_and_tailwind_conventions():
    assert True


def test_theme_bootstrap_defaults_to_light_without_an_app_preference():
    assert True


def test_theme_bootstrap_serializes_explicit_mode():
    with pytest.raises(TypeError, match="theme_mode"):
        setup(theme_mode="dark")


def test_runtime_does_not_include_framework_specific_compatibility():
    runtime = startup_runtime()

    assert "data-dash-loading-framework" not in runtime


def test_resources_contain_only_the_bundled_startup_runtime():
    resources = files("dash_startup_loading_plugin").joinpath("resources")
    resource_names = {
        resource.name for resource in resources.iterdir() if resource.is_file()
    }
    loader_names = {
        resource.name for resource in resources.joinpath("loading-ui").iterdir()
    }
    resource_text = startup_runtime()

    assert resource_names == {"startup-loading.js"}
    assert {"ring.js", "wave.js", "text-shimmer.js"} <= loader_names
    assert "window.__dashStartupLoadingStart" in resource_text
    assert "._dash-loading" in resource_text
    assert 'querySelector("._dash-loading")' in resource_text


def test_only_the_selected_loader_is_requested_by_the_index():
    setup(loader="wave")
    app = Dash(__name__)
    app.layout = dash_html.Div("Ready", id="ready")
    client = app.server.test_client()

    index = client.get("/").get_data(as_text=True)

    assert (
        f'src="/_dash-startup-loading/wave.js?v={loading_plugin.__version__}"' in index
    )
    assert "ring.js" not in index
    for loader in ("spiral", "text-shimmer"):
        assert f"{loader}.js" not in index

    response = client.get("/_dash-startup-loading/wave.js")
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "public, max-age=31536000, immutable"
    assert client.get("/_dash-startup-loading/default.js").status_code == 404
    assert client.get("/_dash-startup-loading/startup-loading.js").status_code == 404


def test_dash_index_contains_overlay_and_inline_resources():
    app = Dash(__name__)
    app.layout = dash_html.Div("Ready", id="ready")

    client = app.server.test_client()
    response = client.get("/")
    index = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "data-dash-loading" in index
    assert '<script data-dash-loading-resource="startup">' in index
    assert "if (window.__dashStartupLoadingStart){window.__dashStartupLoadingStart()}" in index
    assert "resources/startup-loading.js" not in index
    assert '<div class="_dash-loading">' in index
