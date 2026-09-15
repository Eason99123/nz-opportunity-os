from pathlib import Path


PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)

INDEX_FILE = (
    PROJECT_ROOT
    / "web"
    / "index.html"
)

SCRIPT_FILE = (
    PROJECT_ROOT
    / "web"
    / "script.js"
)

STYLE_FILE = (
    PROJECT_ROOT
    / "web"
    / "style.css"
)


def test_demo_banner_exists():
    html = INDEX_FILE.read_text(
        encoding="utf-8"
    )

    assert "demoModeBanner" in html
    assert "DEMO MODE" in html


def test_demo_mode_logic_exists():
    script = SCRIPT_FILE.read_text(
        encoding="utf-8"
    )

    assert "demo_mode" in script
    assert "demoModeBanner" in script
    assert "dataSourceLabel" in script
    assert "backendDataBanner" in script


def test_demo_banner_style_exists():
    css = STYLE_FILE.read_text(
        encoding="utf-8"
    )

    assert ".demo-mode-banner" in css
    assert ".hidden" in css