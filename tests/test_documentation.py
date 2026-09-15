from pathlib import Path
import tomllib


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_pypi_description_uses_english_readme():
    pyproject = tomllib.loads(
        (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )

    assert pyproject["project"]["readme"] == "README.md"
    assert "An installable" in (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")


def test_readmes_use_current_selector_and_installation_examples():
    english = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    chinese = (PROJECT_ROOT / "README.zh-CN.md").read_text(encoding="utf-8")

    for readme in (english, chinese):
        assert "#header" in readme
        assert "#sidebar-menu" in readme
        assert "pending_selector" in readme
        assert "pip install dash-ant-design" in readme
        assert "usage-header" not in readme
        assert "usage-sidebar-menu" not in readme
        assert "dash-ant-design  # Python 3.10+" not in readme
        assert 'theme_mode="auto"' in readme
        assert 'theme_mode="light"' in readme
        assert "dash_theme_component_id" in readme
        assert "setup(loader=\"antd\")" in readme


def test_readmes_link_to_each_other():
    english = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    chinese = (PROJECT_ROOT / "README.zh-CN.md").read_text(encoding="utf-8")

    chinese_link = (
        "[简体中文](https://github.com/C0deBeez/"
        "dash-startup-loading-plugin/blob/master/README.zh-CN.md)"
    )
    english_link = (
        "[English](https://github.com/C0deBeez/"
        "dash-startup-loading-plugin/blob/master/README.md)"
    )

    for readme in (english, chinese):
        assert chinese_link in readme
        assert english_link in readme


def test_packaged_chinese_readme_matches_project_readme():
    project_readme = (PROJECT_ROOT / "README.zh-CN.md").read_text(encoding="utf-8")
    packaged_readme = (
        PROJECT_ROOT
        / "src"
        / "dash_startup_loading_plugin"
        / "README.zh-CN.md"
    ).read_text(encoding="utf-8")

    assert packaged_readme == project_readme


def test_packaged_english_readme_matches_project_readme():
    project_readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    packaged_readme = (
        PROJECT_ROOT
        / "src"
        / "dash_startup_loading_plugin"
        / "README.md"
    ).read_text(encoding="utf-8")

    assert packaged_readme == project_readme
