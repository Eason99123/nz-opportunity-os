from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOGS_DIR = PROJECT_ROOT / "logs"

WEEKLY_STATUS_FILE = (
    LOGS_DIR
    / "latest_weekly_automation_status.json"
)

VALIDATION_STATUS_FILE = (
    LOGS_DIR
    / "latest_validation_status.json"
)

LIFECYCLE_STATUS_FILE = (
    LOGS_DIR
    / "latest_archive_status.json"
)

BATCH_STATUS_FILE = (
    LOGS_DIR
    / "latest_batch_status.json"
)

REFRESH_STATUS_FILE = (
    LOGS_DIR
    / "latest_refresh_status.json"
)

HEALTH_JSON = (
    LOGS_DIR
    / "latest_automation_health.json"
)

HEALTH_TXT = (
    LOGS_DIR
    / "latest_automation_health.txt"
)


def load_json(
    path: Path,
) -> dict[str, Any] | None:
    if not path.exists():
        return None

    try:
        return json.loads(
            path.read_text(
                encoding="utf-8-sig"
            )
        )
    except (
        json.JSONDecodeError,
        UnicodeDecodeError,
        OSError,
    ):
        return None


def parse_datetime(
    value: Any,
) -> datetime | None:
    if not value:
        return None

    text = str(value).strip()

    if not text:
        return None

    try:
        return datetime.fromisoformat(
            text.replace(
                "Z",
                "+00:00",
            )
        )
    except ValueError:
        pass

    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y/%m/%d %H:%M:%S",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(
                text,
                fmt,
            )
        except ValueError:
            continue

    return None


def find_timestamp(
    data: dict[str, Any] | None,
) -> datetime | None:
    if not data:
        return None

    candidates = [
        "finished_at",
        "generated_at",
        "updated_at",
        "started_at",
    ]

    for key in candidates:
        parsed = parse_datetime(
            data.get(key)
        )

        if parsed is not None:
            return parsed

    return None


def status_is_success(
    data: dict[str, Any] | None,
) -> bool:
    if not data:
        return False

    status = str(
        data.get(
            "status",
            "",
        )
    ).strip().lower()

    return status == "success"


def main() -> int:
    weekly = load_json(
        WEEKLY_STATUS_FILE
    )

    validation = load_json(
        VALIDATION_STATUS_FILE
    )

    lifecycle = load_json(
        LIFECYCLE_STATUS_FILE
    )

    batch = load_json(
        BATCH_STATUS_FILE
    )

    refresh = load_json(
        REFRESH_STATUS_FILE
    )

    checks: list[
        dict[str, Any]
    ] = []

    issues: list[str] = []

    # --------------------------------------------------------
    # Weekly automation
    # --------------------------------------------------------

    weekly_ok = status_is_success(
        weekly
    )

    checks.append(
        {
            "name": "weekly_automation",
            "ok": weekly_ok,
            "timestamp": (
                find_timestamp(
                    weekly
                ).isoformat()
                if find_timestamp(
                    weekly
                )
                else None
            ),
        }
    )

    if not weekly_ok:
        issues.append(
            "Latest weekly automation did not report success."
        )

    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    validation_ok = status_is_success(
        validation
    )

    checks.append(
        {
            "name": "validation",
            "ok": validation_ok,
            "timestamp": (
                find_timestamp(
                    validation
                ).isoformat()
                if find_timestamp(
                    validation
                )
                else None
            ),
        }
    )

    if not validation_ok:
        issues.append(
            "Latest validation status is unavailable or failed."
        )

    # --------------------------------------------------------
    # Lifecycle
    # --------------------------------------------------------

    lifecycle_ok = status_is_success(
        lifecycle
    )

    checks.append(
        {
            "name": "lifecycle",
            "ok": lifecycle_ok,
            "timestamp": (
                find_timestamp(
                    lifecycle
                ).isoformat()
                if find_timestamp(
                    lifecycle
                )
                else None
            ),
        }
    )

    if not lifecycle_ok:
        issues.append(
            "Latest lifecycle status is unavailable or failed."
        )

    # --------------------------------------------------------
    # Refresh
    # --------------------------------------------------------

    refresh_ok = status_is_success(
        refresh
    )

    checks.append(
        {
            "name": "refresh",
            "ok": refresh_ok,
            "timestamp": (
                find_timestamp(
                    refresh
                ).isoformat()
                if find_timestamp(
                    refresh
                )
                else None
            ),
        }
    )

    if not refresh_ok:
        issues.append(
            "Latest refresh status is unavailable or failed."
        )

    # --------------------------------------------------------
    # Batch
    # --------------------------------------------------------

    batch_exists = False
    batch_count = None

    if batch:
        batch_exists = bool(
            batch.get(
                "exists",
                False,
            )
        )

        batch_count = batch.get(
            "entry_count"
        )

    batch_ok = (
        batch is not None
        and batch_exists
        and isinstance(
            batch_count,
            int,
        )
        and batch_count >= 0
    )

    checks.append(
        {
            "name": "production_batch",
            "ok": batch_ok,
            "entry_count": batch_count,
            "timestamp": (
                find_timestamp(
                    batch
                ).isoformat()
                if find_timestamp(
                    batch
                )
                else None
            ),
        }
    )

    if not batch_ok:
        issues.append(
            "Production batch status is invalid or unavailable."
        )

    # --------------------------------------------------------
    # Cross-check lifecycle and batch
    # --------------------------------------------------------

    lifecycle_active = None

    if lifecycle:
        lifecycle_active = lifecycle.get(
            "active"
        )

    if (
        isinstance(
            lifecycle_active,
            int,
        )
        and isinstance(
            batch_count,
            int,
        )
        and lifecycle_active != batch_count
    ):
        issues.append(
            (
                "Lifecycle active count does not match "
                "production batch count."
            )
        )

    # --------------------------------------------------------
    # Cross-check weekly embedded lifecycle
    # --------------------------------------------------------

    if weekly:
        weekly_lifecycle = weekly.get(
            "lifecycle"
        )

        if isinstance(
            weekly_lifecycle,
            dict,
        ):
            embedded_active = (
                weekly_lifecycle.get(
                    "active"
                )
            )

            if (
                isinstance(
                    embedded_active,
                    int,
                )
                and isinstance(
                    batch_count,
                    int,
                )
                and embedded_active
                != batch_count
            ):
                issues.append(
                    (
                        "Weekly lifecycle active count "
                        "does not match production batch."
                    )
                )

    # --------------------------------------------------------
    # Overall state
    # --------------------------------------------------------

    if not issues:
        overall_status = "healthy"

    elif weekly_ok and batch_ok:
        overall_status = "warning"

    else:
        overall_status = "unhealthy"

    generated_at = datetime.now()

    result = {
        "status": overall_status,
        "generated_at": generated_at.isoformat(
            timespec="seconds"
        ),
        "issues": issues,
        "checks": checks,
        "summary": {
            "production_entries": batch_count,
            "lifecycle_active": lifecycle_active,
            "issue_count": len(
                issues
            ),
        },
    }

    HEALTH_JSON.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    HEALTH_JSON.write_text(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    lines = [
        "NZ Opportunity OS Automation Health",
        "",
        f"Status: {overall_status}",
        (
            "Generated at: "
            + generated_at.isoformat(
                timespec="seconds"
            )
        ),
        (
            "Production entries: "
            + str(
                batch_count
            )
        ),
        (
            "Lifecycle active: "
            + str(
                lifecycle_active
            )
        ),
        (
            "Issues: "
            + str(
                len(issues)
            )
        ),
        "",
    ]

    if issues:
        lines.append(
            "Health Issues:"
        )

        for issue in issues:
            lines.append(
                f"* {issue}"
            )
    else:
        lines.append(
            "All monitored components are healthy."
        )

    HEALTH_TXT.write_text(
        "\n".join(
            lines
        ),
        encoding="utf-8",
    )

    print(
        "\n".join(
            lines
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )