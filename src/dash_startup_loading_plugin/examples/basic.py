"""Framework-neutral Dash demonstration."""

from dash import Dash, html

from ..plugin import setup
from .shared import (
    DEMO_ACTION_TEXT,
    DEMO_DESCRIPTION,
    DEMO_READY_TEXT,
    DEMO_READY_TITLE,
    DEMO_TITLE,
    MAIN_STYLE,
    PANEL_STYLE,
)


def create_app() -> Dash:
    """Create the framework-neutral example application."""

    setup(
        required_selectors=["#dash-app-ready"],
        minimum_display_ms=250,
        fade_duration_ms=180,
        theme_mode="light",
    )

    app = Dash(__name__)
    app.layout = html.Main(
        [
            html.H1(DEMO_TITLE),
            html.P(DEMO_DESCRIPTION),
            html.Section(
                [
                    html.H2(DEMO_READY_TITLE),
                    html.P(DEMO_READY_TEXT),
                    html.Button(DEMO_ACTION_TEXT),
                ],
                style=PANEL_STYLE,
            ),
        ],
        id="dash-app-ready",
        style=MAIN_STYLE
        | {
            "color": "#212529",
            "background": "#ffffff",
            "colorScheme": "light",
        },
    )
    return app
