"""Dash Ant Design theme persistence demonstration."""

from dash import Dash, Input, Output, clientside_callback, html

from ..plugin import setup
from .cli import DemoDependencyError
from .shared import (
    DEMO_ACTION_TEXT,
    DEMO_DESCRIPTION,
    DEMO_READY_TEXT,
    DEMO_READY_TITLE,
    DEMO_TITLE,
    MAIN_STYLE,
    PANEL_STYLE,
    THEME_OPTIONS,
)


def create_app() -> Dash:
    """Create the Dash Ant Design example application."""

    try:
        import dash_antd_components as dac
    except ModuleNotFoundError as error:
        if error.name != "dash_antd_components":
            raise
        raise DemoDependencyError(
            "Failed to import dash_antd_components. "
            "Install it with: pip install dash-ant-design"
        ) from error

    setup(
        required_selectors=["#antd-app-ready"],
        minimum_display_ms=250,
        fade_duration_ms=180,
    )

    app = Dash(__name__)
    app.layout = dac.ConfigProvider(
        html.Main(
            [
                html.H1(DEMO_TITLE),
                html.P(DEMO_DESCRIPTION),
                dac.Segmented(
                    id="theme-mode",
                    options=THEME_OPTIONS,
                    value="system",
                    block=True,
                    persistence=True,
                    persisted_props=["value"],
                    persistence_type="local",
                ),
                html.Section(
                    [
                        html.H2(DEMO_READY_TITLE),
                        html.P(DEMO_READY_TEXT),
                        html.Button(DEMO_ACTION_TEXT),
                    ],
                    style=PANEL_STYLE,
                ),
            ],
            id="antd-app-ready",
            style=MAIN_STYLE,
        ),
        id="theme-provider",
        theme={"algorithm": "default"},
    )

    clientside_callback(
        """function(mode) {
            const selected = mode || "system";
            const media = window.matchMedia("(prefers-color-scheme: dark)");

            try {
                localStorage.setItem("theme", JSON.stringify(selected));
            } catch (_) {}

            function applyDocumentScheme(dark) {
                document.documentElement.style.colorScheme = dark ? "dark" : "light";
            }

            const dark = selected === "dark"
                || (selected === "system" && media.matches);
            applyDocumentScheme(dark);

            if (!window.__dashLoadingAntdThemeListener) {
                window.__dashLoadingAntdThemeListener = function(event) {
                    let current = "system";
                    try {
                        current = JSON.parse(localStorage.getItem("theme")) || "system";
                    } catch (_) {}
                    if (current !== "system") return;
                    applyDocumentScheme(event.matches);
                    dash_clientside.set_props("theme-provider", {
                        theme: {algorithm: event.matches ? "dark" : "default"}
                    });
                };
                media.addEventListener(
                    "change",
                    window.__dashLoadingAntdThemeListener
                );
            }

            return {algorithm: dark ? "dark" : "default"};
        }""",
        Output("theme-provider", "theme"),
        Input("theme-mode", "value"),
    )
    return app
