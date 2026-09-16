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
    assert '<body class="app"><div class="dash-loading"' in result
    assert '<script data-dash-loading-resource="script">' in result
    assert result.index('class="dash-loading"') < result.index(
        '<script data-dash-loading-resource="script">'
    )
    assert result.count(" data-dash-loading ") == 1
    assert '<span class="dash-loading__spinner" aria-hidden="true"></span>' in result
    assert '<span class="dash-loading__antd-dot">' not in result
    assert 'data-dash-loading-resource="loading-ui"' not in result
    assert '--dash-loading-size:12px' in result
    assert '--dash-loading-stroke:2px' in result
    assert '--dash-loading-loader-color:#000' in result
    assert '--dash-loading-loader-dark-color:#fff' in result
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


def test_browser_runtime_only_waits_for_dash_initial_render():
    script = (
        files("dash_startup_loading_plugin")
        .joinpath("resources", "loading.js")
        .read_text(encoding="utf-8")
    )

    assert 'document.querySelector("#react-entry-point")' in script
    assert 'root.querySelector("._dash-loading")' in script
    assert "sawDashLoading = true" in script
    assert "rootSelector" not in script
    assert "requiredSelectors" not in script
    assert "pendingSelector" not in script
    assert "timeoutMs" not in script
    assert "minimumDisplayMs" not in script
    assert "fadeDurationMs" not in script
    assert "setTimeout" not in script
    assert "requestAnimationFrame" not in script


def test_custom_loader_html_is_intentionally_preserved():
    setup(custom_loader_html='<div class="brand-loader">Please wait</div>')

    result = _inject_overlay("<html><body></body></html>")

    assert '<div class="brand-loader">Please wait</div>' in result


def test_default_spinner_restores_version_1_0_4_animation():
    result = _inject_overlay("<html><body></body></html>")
    css = files("dash_startup_loading_plugin").joinpath("resources", "loading.css").read_text()

    assert get_config().loader == "default"
    assert '<span class="dash-loading__spinner" aria-hidden="true"></span>' in result
    assert "border-top-color: currentcolor;" in css
    assert "animation: dash-loading-spin 0.8s linear infinite;" in css


def test_dash_builtin_loading_message_stays_hidden_after_overlay_removal():
    css = (
        files("dash_startup_loading_plugin")
        .joinpath("resources", "loading.css")
        .read_text(encoding="utf-8")
    )

    assert "._dash-loading {" in css
    assert "display: none !important;" in css
    assert ".dash-loading ~" not in css


def test_antd_spinner_uses_12px_as_its_scaled_visual_baseline():
    setup(loader="antd")
    result = _inject_overlay("<html><body></body></html>")
    css = files("dash_startup_loading_plugin").joinpath("resources", "loading.css").read_text()

    assert '<span class="dash-loading__antd-dot">' in result
    assert '<i></i><i></i><i></i><i></i>' in result
    assert '--dash-loading-size:12px' in result
    assert "transform: scale(1.6666667);" in css
    assert "transform-origin: center;" in css
    assert '--dash-loading-loader-color:#1677ff' in result
    assert '--dash-loading-loader-dark-color:#4096ff' in result

    setup(loader_size=20)
    result = _inject_overlay("<html><body></body></html>")
    assert '--dash-loading-size:20px' in result

    setup(loader_size=32)
    result = _inject_overlay("<html><body></body></html>")
    assert '--dash-loading-size:32px' in result


def test_antd_default_size_override_does_not_affect_other_loaders():
    setup(loader="default")
    result = _inject_overlay("<html><body></body></html>")

    assert '--dash-loading-size:12px' in result
    assert '<span class="dash-loading__antd-spinner"' not in result


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
    assert '--dash-loading-size:12px' in result
    assert result.index('data-dash-loading-resource="loading-ui"') < result.index(
        'data-dash-loading-resource="script"'
    )
    assert '--dash-loading-loader-color:#e91e63' in result
    assert '--dash-loading-loader-dark-color:#ff80ab' in result


def test_loading_ui_uses_official_component_geometry_and_border_box():
    setup(loader="dual-arc")

    result = _inject_overlay("<html><body></body></html>")
    css = files("dash_startup_loading_plugin").joinpath("resources").joinpath("loading.css").read_text()
    renderer = files("dash_startup_loading_plugin").joinpath("resources").joinpath("loading-ui.js").read_text()

    assert ".dash-loading__loading-ui" in css
    assert '"accordion-loader"' in renderer
    assert '"analyzing-image":{width:"4rem",height:"4rem"}' in renderer
    assert 'bars:{width:"4rem",height:"3rem"}' in renderer
    assert '"dual-arc":{width:"3.5rem",height:"3.5rem"}' in renderer
    assert '"wandering-eyes":{width:"180px",height:"5rem"}' in renderer
    assert 'wave:{width:"6rem",height:"3rem"}' in renderer
    assert 'display:inline-flex;width:auto;height:auto' in renderer
    assert 'fontSize:"1.25rem"' in renderer
    assert "box-sizing:border-box" in renderer
    assert 'border-width:var(--dash-loading-ui-stroke,2px)!important' in renderer
    assert 'stroke-width:var(--dash-loading-ui-stroke,2px)!important' in renderer
    assert 'borderStyle:"solid"' in renderer
    assert 'borderStyle:"var(--tw-border-style)"' not in renderer
    assert '--dash-loading-size:12px' in result
    assert '--dash-loading-scale:0.6' in result
    assert '--dash-loading-ui-stroke:3.33333px' in result

    setup(loader="wave", loader_size=40)
    result = _inject_overlay("<html><body></body></html>")
    assert '--dash-loading-size:40px' in result
    assert '--dash-loading-scale:2' in result
    assert '--dash-loading-ui-stroke:1px' in result

    setup(loader="wave", loader_size=0)
    result = _inject_overlay("<html><body></body></html>")
    assert '--dash-loading-scale:0' in result
    assert '--dash-loading-ui-display:none' in result


def test_loading_ui_uses_its_neutral_default_colors():
    setup(loader="wave")
    result = _inject_overlay("<html><body></body></html>")
    assert '--dash-loading-loader-color:#000' in result
    assert '--dash-loading-loader-dark-color:#fff' in result


def test_text_loader_supports_custom_text_and_escapes_the_attribute():
    setup(loader="text-shimmer", loader_text='正在加载 "报表"')

    result = _inject_overlay("<html><body></body></html>")
    renderer = files("dash_startup_loading_plugin").joinpath("resources").joinpath("loading-ui.js").read_text()

    assert 'data-dash-loading-text="正在加载 &quot;报表&quot;"' in result
    assert ".dataset.dashLoadingText" in renderer


def test_dash_antd_bundle_selects_antd_defaults_without_setup():
    index = (
        '<html><head><script src="/_dash-component-suites/'
        'dash_antd_components/bundle.js"></script></head><body></body></html>'
    )

    result = _inject_overlay(index)

    assert '<span class="dash-loading__antd-dot">' in result
    assert 'data-dash-loading-resource="loading-ui"' not in result
    assert '--dash-loading-loader-color:#1677ff' in result
    assert '--dash-loading-loader-dark-color:#4096ff' in result


def test_explicit_loader_overrides_dash_antd_automatic_default():
    setup(loader="wave")
    index = (
        '<html><head><script src="/_dash-component-suites/'
        'dash_antd_components/bundle.js"></script></head><body></body></html>'
    )

    result = _inject_overlay(index)

    assert 'data-dash-loading-ui="wave"' in result
    assert 'data-dash-loading-resource="loading-ui"' in result
    assert '--dash-loading-loader-color:#000' in result
    assert '--dash-loading-loader-dark-color:#fff' in result


def test_explicit_colors_override_dash_antd_automatic_colors():
    setup(loader_color="#e91e63", loader_dark_color="#ff80ab")
    index = (
        '<html><head><script src="/_dash-component-suites/'
        'dash_antd_components/bundle.js"></script></head><body></body></html>'
    )

    result = _inject_overlay(index)

    assert '<span class="dash-loading__antd-dot">' in result
    assert '--dash-loading-loader-color:#e91e63' in result
    assert '--dash-loading-loader-dark-color:#ff80ab' in result


def test_loading_ui_ring_uses_responsive_region_and_accepts_fixed_size():
    setup(loader="ring")
    result = _inject_overlay("<html><body></body></html>")
    assert '<div class="dash-loading__spinner-region"><svg class="dash-loading__ring"' in result
    assert '--dash-loading-size:12px' in result
    assert '--dash-loading-loader-color:#000' in result

    setup(loader_size=36)
    result = _inject_overlay("<html><body></body></html>")
    assert '--dash-loading-size:36px' in result

    setup(loader_size=None)
    result = _inject_overlay("<html><body></body></html>")
    assert '--dash-loading-size:20px' in result
    assert '--dash-loading-scale:1' in result


def test_explicit_colors_override_loader_defaults():
    setup(loader_color="#222222", loader_dark_color="#eeeeee")
    result = _inject_overlay("<html><body></body></html>")
    assert '--dash-loading-loader-color:#222222' in result
    assert '--dash-loading-loader-dark-color:#eeeeee' in result


def test_custom_html_skips_loading_ui_runtime():
    setup(loader="spiral", custom_loader_html='<span>Custom</span>')
    result = _inject_overlay("<html><body></body></html>")
    assert '<span>Custom</span>' in result
    assert 'data-dash-loading-resource="loading-ui"' not in result


@pytest.mark.parametrize(
    "removed_option",
    [
        "root_selector",
        "required_selectors",
        "pending_selector",
        "overlay_id",
        "timeout_ms",
        "minimum_display_ms",
        "fade_duration_ms",
        "spinner_size_px",
        "spinner_stroke_px",
        "color",
        "dark_color",
        "hide_default_loading",
        "dash_theme_component_id",
    ],
)
def test_removed_configuration_options_are_rejected(removed_option):
    with pytest.raises(TypeError, match=removed_option):
        setup(**{removed_option: True})


def test_configuration_validation():
    with pytest.raises(ValueError, match="theme_mode"):
        setup(theme_mode="sepia")
    with pytest.raises(ValueError, match="loader_text"):
        setup(loader_text=" ")
    with pytest.raises(ValueError, match="loader_size"):
        setup(loader_size=-1)
    with pytest.raises(ValueError, match="loader_stroke_width"):
        setup(loader_stroke_width=-1)
    with pytest.raises(TypeError, match="Unknown"):
        setup(unknown=True)


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
    assert 'data-dash-loading-framework="mantine"' in css
    assert 'var(--mantine-color-body, #fff)' in css
    assert 'var(--mantine-color-body, #242424)' in css


def test_explicit_backgrounds_override_mantine_body_color():
    setup(background="#f5f5f5", dark_background="#202020")

    result = _inject_overlay("<html><body></body></html>")

    assert '--dash-loading-mantine-light-background:#f5f5f5' in result
    assert '--dash-loading-mantine-dark-background:#202020' in result


def test_theme_bootstrap_supports_dash_and_tailwind_conventions():
    script = (
        files("dash_startup_loading_plugin")
        .joinpath("resources/theme.js")
        .read_text(encoding="utf-8")
    )

    assert "_dash_persistence." in script
    assert "mantine-color-scheme-value" in script
    assert 'data-mantine-color-scheme' in script
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

    assert "rootTheme()" in script
    assert "mantineStored" in script
    assert 'conventionalStoredTheme()' in script
    assert '|| "light"' in script
    assert 'conventionalStoredTheme() || "system"' not in script
    assert 'theme === "system"' in script
    assert 'matchMedia("(prefers-color-scheme: dark)")' in script


def test_theme_bootstrap_serializes_explicit_mode():
    setup(theme_mode="dark")

    result = _inject_overlay("<html><head></head><body></body></html>")

    assert 'window.__dashLoadingThemeConfig={"themeMode":"dark","mantineBundle":false};' in result


def test_mantine_bundle_is_detected_without_setup():
    index = (
        '<html><head><script src="/_dash-component-suites/'
        'dash_mantine_components/bundle.js"></script></head><body></body></html>'
    )

    result = _inject_overlay(index)

    assert 'window.__dashLoadingThemeConfig={"themeMode":"auto","mantineBundle":true};' in result
    assert '<span class="dash-loading__spinner" aria-hidden="true"></span>' in result


def test_mantine_app_works_with_default_plugin_configuration():
    dmc = pytest.importorskip("dash_mantine_components")
    app = Dash(__name__)
    app.layout = dmc.MantineProvider(dmc.Text("Ready"))

    index = app.server.test_client().get("/").get_data(as_text=True)

    assert get_config().theme_mode == "auto"
    assert 'window.__dashLoadingThemeConfig={"themeMode":"auto","mantineBundle":true};' in index
    assert '<span class="dash-loading__spinner" aria-hidden="true"></span>' in index


def test_mantine_force_color_scheme_is_applied_before_first_render():
    dmc = pytest.importorskip("dash_mantine_components")
    app = Dash(__name__)
    app.layout = dmc.MantineProvider(
        dmc.Text("Ready"),
        forceColorScheme="dark",
    )

    index = app.server.test_client().get("/").get_data(as_text=True)

    assert (
        'window.__dashLoadingThemeConfig={"themeMode":"auto",'
        '"mantineBundle":true,"mantineForcedColorScheme":"dark"};'
    ) in index


def test_resource_names_drop_startup_and_preserve_dash_default_loading_selector():
    resources = files("dash_startup_loading_plugin").joinpath("resources")
    resource_names = {resource.name for resource in resources.iterdir() if resource.is_file()}
    resource_text = "\n".join(
        resources.joinpath(name).read_text(encoding="utf-8")
        for name in ("loading.css", "loading.js", "theme.js")
    )

    assert resource_names == {
        "loading.css", "loading.js", "loading-ui.js", "theme.js",
        "LOADING-UI-LICENSE",
    }
    assert "startup" not in resource_text.lower()
    assert "._dash-loading" in resource_text
    assert "window.dashLoading" not in resource_text
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
