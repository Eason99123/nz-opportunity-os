from __future__ import annotations

import json
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent.parent

SAMPLE_FILE = (
    PROJECT_ROOT
    / "sample_data"
    / "sample_opportunities.txt"
)

BATCH_FILE = (
    PROJECT_ROOT
    / "incoming"
    / "openclaw_batch.txt"
)

LOG_DIR = PROJECT_ROOT / "logs"

WEEKLY_STATUS_FILE = (
    LOG_DIR
    / "latest_weekly_automation_status.json"
)

SUCCESSFUL_RUN_FILE = (
    LOG_DIR
    / "latest_successful_weekly_run.json"
)

VALIDATION_STATUS_FILE = (
    LOG_DIR
    / "latest_validation_status.json"
)

LIFECYCLE_STATUS_FILE = (
    LOG_DIR
    / "latest_archive_status.json"
)

OUTPUT_JSON = (
    PROJECT_ROOT
    / "opportunities"
    / "deduplicated_ranked_output.json"
)


def timestamp() -> str:
    return (
        datetime.now()
        .astimezone()
        .isoformat()
    )


def load_generated_opportunities() -> list[dict[str, Any]]:
    if not OUTPUT_JSON.exists():
        return []

    try:
        data = json.loads(
            OUTPUT_JSON.read_text(
                encoding="utf-8"
            )
        )
    except (
        json.JSONDecodeError,
        UnicodeDecodeError,
        OSError,
    ):
        return []

    if isinstance(data, list):
        return [
            item
            for item in data
            if isinstance(
                item,
                dict,
            )
        ]

    if isinstance(data, dict):
        opportunities = data.get(
            "opportunities",
            [],
        )

        if isinstance(
            opportunities,
            list,
        ):
            return [
                item
                for item in opportunities
                if isinstance(
                    item,
                    dict,
                )
            ]

    return []


def run_python_script(
    relative_path: str,
) -> None:
    script = (
        PROJECT_ROOT
        / relative_path
    )

    if not script.exists():
        raise FileNotFoundError(
            "Required script not found: "
            f"{script}"
        )

    print()
    print(
        f"Running {relative_path}..."
    )

    subprocess.run(
        [
            sys.executable,
            str(script),
        ],
        cwd=PROJECT_ROOT,
        check=True,
    )


def write_json(
    path: Path,
    data: dict[str, Any],
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(
            data,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def prepare_demo_batch() -> None:
    if not SAMPLE_FILE.exists():
        raise FileNotFoundError(
            "Sample opportunity file "
            f"not found: {SAMPLE_FILE}"
        )

    BATCH_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    shutil.copyfile(
        SAMPLE_FILE,
        BATCH_FILE,
    )

    print(
        "Created demo production batch:"
    )

    print(
        f"  {BATCH_FILE}"
    )


def write_demo_validation_status(
    entry_count: int,
    generated_at: str,
) -> None:
    status = {
        "status": "success",
        "generated_at": generated_at,
        "demo_mode": True,
        "total_entries": entry_count,
        "approved": entry_count,
        "needs_review": 0,
        "rejected": 0,
        "message": (
            "Demo validation status generated "
            "from safe sample data."
        ),
    }

    write_json(
        VALIDATION_STATUS_FILE,
        status,
    )

    print(
        "Wrote demo validation status:"
    )

    print(
        f"  {VALIDATION_STATUS_FILE}"
    )


def write_demo_lifecycle_status(
    opportunities: list[dict[str, Any]],
    generated_at: str,
) -> None:
    entry_count = len(
        opportunities
    )

    details = []

    for opportunity in opportunities:
        title = (
            opportunity.get(
                "title"
            )
            or opportunity.get(
                "Title"
            )
            or "(untitled)"
        )

        date_deadline = (
            opportunity.get(
                "date_deadline"
            )
            or opportunity.get(
                "Date/Deadline"
            )
            or ""
        )

        details.append(
            {
                "title": title,
                "status": "active",
                "reason": (
                    "Safe demo opportunity "
                    "treated as active."
                ),
                "date_deadline": (
                    date_deadline
                ),
            }
        )

    status = {
        "status": "success",
        "generated_at": generated_at,
        "demo_mode": True,
        "today": (
            datetime.now()
            .date()
            .isoformat()
        ),
        "batch_file": str(
            BATCH_FILE
        ),
        "total_entries": entry_count,
        "active": entry_count,
        "uncertain": 0,
        "expired": 0,
        "active_file": None,
        "uncertain_file": None,
        "archive_file": None,
        "details": details,
        "message": (
            "Demo lifecycle status generated "
            "from safe sample data."
        ),
    }

    write_json(
        LIFECYCLE_STATUS_FILE,
        status,
    )

    print(
        "Wrote demo lifecycle status:"
    )

    print(
        f"  {LIFECYCLE_STATUS_FILE}"
    )


def write_weekly_status(
    entry_count: int,
    started_at: str,
    finished_at: str,
    duration_seconds: float,
) -> None:
    status = {
        "status": "success",
        "message": (
            "Demo environment generated "
            "successfully from safe sample data."
        ),
        "started_at": started_at,
        "finished_at": finished_at,
        "duration_seconds": round(
            duration_seconds,
            2,
        ),
        "failure_stage": "completed",
        "rollback_performed": False,
        "production_modified": True,
        "demo_mode": True,
        "transaction_backup_file": None,
        "lifecycle_backup_file": None,
        "validation": {
            "total_entries": entry_count,
            "approved": entry_count,
            "needs_review": 0,
            "rejected": 0,
        },
        "lifecycle": {
            "total_entries": entry_count,
            "active": entry_count,
            "uncertain": 0,
            "expired": 0,
        },
    }

    write_json(
        WEEKLY_STATUS_FILE,
        status,
    )

    write_json(
        SUCCESSFUL_RUN_FILE,
        status,
    )

    print(
        "Wrote demo weekly status:"
    )

    print(
        f"  {WEEKLY_STATUS_FILE}"
    )

    print(
        "Wrote demo successful-run status:"
    )

    print(
        f"  {SUCCESSFUL_RUN_FILE}"
    )


def main() -> int:
    print(
        "NZ Student Opportunity OS "
        "Demo Setup"
    )

    print("=" * 50)

    started_perf = (
        time.perf_counter()
    )

    started_at = timestamp()

    try:
        prepare_demo_batch()

        run_python_script(
            "src/refresh_from_batch.py"
        )

        run_python_script(
            "src/write_batch_status.py"
        )

        opportunities = (
            load_generated_opportunities()
        )

        entry_count = len(
            opportunities
        )

        if entry_count == 0:
            raise RuntimeError(
                "Demo pipeline produced "
                "zero opportunities."
            )

        generated_at = timestamp()

        write_demo_validation_status(
            entry_count=entry_count,
            generated_at=generated_at,
        )

        write_demo_lifecycle_status(
            opportunities=opportunities,
            generated_at=generated_at,
        )

        finished_at = timestamp()

        duration_seconds = (
            time.perf_counter()
            - started_perf
        )

        write_weekly_status(
            entry_count=entry_count,
            started_at=started_at,
            finished_at=finished_at,
            duration_seconds=duration_seconds,
        )

        run_python_script(
            "src/write_automation_health.py"
        )

        print()
        print("=" * 50)

        print(
            "Demo setup completed successfully."
        )

        print(
            f"Demo opportunities: "
            f"{entry_count}"
        )

        print()

        print(
            "Expected demo health state:"
        )

        print(
            f"  Production entries: "
            f"{entry_count}"
        )

        print(
            f"  Lifecycle active: "
            f"{entry_count}"
        )

        print()

        print(
            "Start the local server and open:"
        )

        print(
            "http://127.0.0.1:8000/"
            "web/index.html"
        )

        return 0

    except subprocess.CalledProcessError as exc:
        print()

        print(
            "Demo setup failed while running "
            "a pipeline component."
        )

        print(
            f"Exit code: "
            f"{exc.returncode}"
        )

        return 1

    except Exception as exc:
        print()

        print(
            f"Demo setup failed: "
            f"{exc}"
        )

        return 1


if __name__ == "__main__":
    raise SystemExit(
        main()
    )