from pathlib import Path

from src import setup_demo


def test_sample_demo_file_exists():
    assert setup_demo.SAMPLE_FILE.exists()


def test_demo_paths_are_inside_project():
    project_root = (
        setup_demo.PROJECT_ROOT.resolve()
    )

    paths = [
        setup_demo.SAMPLE_FILE,
        setup_demo.BATCH_FILE,
        setup_demo.LOG_DIR,
        setup_demo.WEEKLY_STATUS_FILE,
        setup_demo.SUCCESSFUL_RUN_FILE,
        setup_demo.OUTPUT_JSON,
    ]

    for path in paths:
        assert (
            project_root
            in path.resolve().parents
            or path.resolve() == project_root
        )


def test_demo_sample_contains_opportunities():
    text = setup_demo.SAMPLE_FILE.read_text(
        encoding="utf-8"
    )

    assert "Title:" in text
    assert "Source link:" in text


def test_demo_does_not_require_absolute_user_path():
    source = Path(
        setup_demo.__file__
    ).read_text(
        encoding="utf-8"
    )

    assert "C:\\Users\\" not in source