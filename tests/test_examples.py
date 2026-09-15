import sys
from importlib.resources import files
from types import SimpleNamespace

import pytest

from dash_startup_loading_plugin import get_config, reset_config
from dash_startup_loading_plugin.examples import DemoDependencyError, create_demo_app
from dash_startup_loading_plugin.examples import cli
from dash_startup_loading_plugin.examples.shared import (
    DEMO_ACTION_TEXT,
    DEMO_DESCRIPTION,
    DEMO_READY_TEXT,
    DEMO_READY_TITLE,
    DEMO_TITLE,
)


@pytest.fixture(autouse=True)
def restore_defaults():
    reset_config()
    yield
    reset_config()


@pytest.mark.parametrize(
    ("name", "ready_id"),
    [
        ("examples.dash", "dash-app-ready"),
        ("dash", "dash-app-ready"),
        ("basic", "dash-app-ready"),
    ],
)
def test_bundled_demo_aliases_create_runnable_apps(name, ready_id):
    app = create_demo_app(name)

    response = app.server.test_client().get("/")
    layout = app.server.test_client().get("/_dash-layout").get_data(as_text=True)

    assert response.status_code == 200
    assert "data-dash-loading" in response.get_data(as_text=True)
    assert ready_id in layout


def test_dash_demo_prefers_light_mode():
    app = create_demo_app("examples.dash")
    layout = app.layout.to_plotly_json()
    index = app.server.test_client().get("/").get_data(as_text=True)

    assert get_config().theme_mode == "light"
    assert layout["props"]["style"]["background"] == "#ffffff"
    assert layout["props"]["style"]["colorScheme"] == "light"
    assert 'window.__dashLoadingThemeConfig={"themeMode":"light"' in index


def test_all_examples_use_the_shared_display_copy():
    example_resources = files("dash_startup_loading_plugin.examples")
    shared_names = {
        "DEMO_TITLE",
        "DEMO_DESCRIPTION",
        "DEMO_READY_TITLE",
        "DEMO_READY_TEXT",
        "DEMO_ACTION_TEXT",
    }

    for name in ("basic.py", "antd.py"):
        source = example_resources.joinpath(name).read_text(encoding="utf-8")
        assert all(shared_name in source for shared_name in shared_names)

    app = create_demo_app("examples.dash")
    layout = app.server.test_client().get("/_dash-layout").get_data(as_text=True)
    for text in (
        DEMO_TITLE,
        DEMO_DESCRIPTION,
        DEMO_READY_TITLE,
        DEMO_READY_TEXT,
        DEMO_ACTION_TEXT,
    ):
        assert text in layout


def test_unknown_demo_framework_has_actionable_error():
    with pytest.raises(ValueError, match="Unknown demo framework"):
        create_demo_app("unknown-components")


def test_antd_demo_reports_its_missing_dependency(monkeypatch):
    monkeypatch.setitem(sys.modules, "dash_antd_components", None)

    with pytest.raises(
        DemoDependencyError,
        match="Failed to import dash_antd_components",
    ):
        create_demo_app("dash-ant-design")


def test_demo_cli_runs_selected_app_with_server_options(monkeypatch):
    calls = []
    fake_app = SimpleNamespace(run=lambda **options: calls.append(options))
    monkeypatch.setattr(cli, "create_demo_app", lambda framework: fake_app)

    result = cli.main(
        [
            "examples.dash",
            "--host",
            "0.0.0.0",
            "--port",
            "9000",
            "--no-debug",
        ]
    )

    assert result == 0
    assert calls == [{"host": "0.0.0.0", "port": 9000, "debug": False}]
