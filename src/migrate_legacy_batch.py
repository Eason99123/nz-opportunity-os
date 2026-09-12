from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from validate_opportunities import (
    parse_entry,
    split_entries,
    validate_entry,
    read_text_with_fallback,
    serialize_entry,
)

from archive_expired_opportunities import (
    classify_lifecycle,
)


PROJECT_ROOT = Path(__file__).resolve().parent.parent

SOURCE_BATCH = (
    PROJECT_ROOT
    / "incoming"
    / "openclaw_batch.txt"
)

MIGRATED_BATCH = (
    PROJECT_ROOT
    / "incoming"
    / "openclaw_batch_migrated.txt"
)

MIGRATION_REVIEW = (
    PROJECT_ROOT
    / "incoming"
    / "legacy_migration_review.txt"
)

MIGRATION_REJECTED = (
    PROJECT_ROOT
    / "incoming"
    / "legacy_migration_rejected.txt"
)

MIGRATION_EXPIRED = (
    PROJECT_ROOT
    / "incoming"
    / "legacy_migration_expired.txt"
)

BACKUP_DIR = (
    PROJECT_ROOT
    / "opportunities"
    / "migration_backups"
)

STATUS_JSON = (
    PROJECT_ROOT
    / "logs"
    / "latest_legacy_migration_status.json"
)

STATUS_TXT = (
    PROJECT_ROOT
    / "logs"
    / "latest_legacy_migration_status.txt"
)


def write_entries(
    path: Path,
    entries: list[dict[str, str]],
    extra_lines: dict[str, list[str]] | None = None,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    blocks = []

    for entry in entries:
        block = serialize_entry(
            entry
        )

        if extra_lines:
            title = entry.get(
                "Title",
                "",
            )

            reasons = extra_lines.get(
                title,
                [],
            )

            if reasons:
                block += (
                    "\nMigration Reasons: "
                    + " | ".join(reasons)
                )

        blocks.append(
            block
        )

    path.write_text(
        "\n\n===OPPORTUNITY===\n\n".join(
            blocks
        ),
        encoding="utf-8",
    )


def backup_source_batch() -> Path:
    BACKUP_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    timestamp = datetime.now().strftime(
        "%Y-%m-%d_%H%M%S"
    )

    backup_path = (
        BACKUP_DIR
        / f"openclaw_batch_before_migration_{timestamp}.txt"
    )

    backup_path.write_bytes(
        SOURCE_BATCH.read_bytes()
    )

    return backup_path


def main() -> int:
    if not SOURCE_BATCH.exists():
        print(
            "Migration failed: source batch does not exist."
        )
        return 1

    text = read_text_with_fallback(
        SOURCE_BATCH
    )

    blocks = split_entries(
        text
    )

    if not blocks:
        print(
            "Migration failed: no entries found."
        )
        return 1

    backup_file = backup_source_batch()

    migrated: list[dict[str, str]] = []
    review: list[dict[str, str]] = []
    rejected: list[dict[str, str]] = []
    expired: list[dict[str, str]] = []

    review_reasons: dict[str, list[str]] = {}
    rejected_reasons: dict[str, list[str]] = {}
    expired_reasons: dict[str, list[str]] = {}

    seen_opportunities: list[
        dict[str, str]
    ] = []

    validation_approved = 0
    validation_review = 0
    validation_rejected = 0

    lifecycle_active = 0
    lifecycle_uncertain = 0
    lifecycle_expired = 0

    today = datetime.now().date()

    details = []

    for block in blocks:
        entry = parse_entry(
            block
        )

        title = entry.get(
            "Title",
            "(untitled)",
        )

        validation = validate_entry(
            entry,
            seen_opportunities,
            check_date_status=False,
        )

        validation_status = validation[
            "status"
        ]

        if validation_status == "approved":
            validation_approved += 1

        elif validation_status == "needs_review":
            validation_review += 1

        else:
            validation_rejected += 1

        # Hard rejection stops here.
        if validation_status == "rejected":
            rejected.append(
                entry
            )

            reasons = (
                validation["reject_reasons"]
                + validation["review_reasons"]
            )

            rejected_reasons[
                title
            ] = reasons

            details.append(
                {
                    "title": title,
                    "validation_status": validation_status,
                    "lifecycle_status": None,
                    "final_status": "rejected",
                    "reasons": reasons,
                }
            )

            continue

        # Approved and needs_review both continue into lifecycle.
        date_text = entry.get(
            "Date/Deadline",
            "",
        )

        lifecycle_status, lifecycle_reason = (
            classify_lifecycle(
                date_text,
                title=title,
                today=today,
            )
        )

        if lifecycle_status == "active":
            lifecycle_active += 1

            if validation_status == "approved":
                migrated.append(
                    entry
                )

                details.append(
                    {
                        "title": title,
                        "validation_status": validation_status,
                        "lifecycle_status": lifecycle_status,
                        "final_status": "migrated",
                        "reasons": [],
                    }
                )

            else:
                review.append(
                    entry
                )

                reasons = list(
                    validation[
                        "review_reasons"
                    ]
                )

                if lifecycle_reason:
                    reasons.append(
                        lifecycle_reason
                    )

                review_reasons[
                    title
                ] = reasons

                details.append(
                    {
                        "title": title,
                        "validation_status": validation_status,
                        "lifecycle_status": lifecycle_status,
                        "final_status": "review",
                        "reasons": reasons,
                    }
                )

        elif lifecycle_status == "expired":
            lifecycle_expired += 1

            expired.append(
                entry
            )

            reasons = []

            if validation_status == "needs_review":
                reasons.extend(
                    validation[
                        "review_reasons"
                    ]
                )

            if lifecycle_reason:
                reasons.append(
                    lifecycle_reason
                )

            expired_reasons[
                title
            ] = reasons

            details.append(
                {
                    "title": title,
                    "validation_status": validation_status,
                    "lifecycle_status": lifecycle_status,
                    "final_status": "expired",
                    "reasons": reasons,
                }
            )

        else:
            lifecycle_uncertain += 1

            review.append(
                entry
            )

            reasons = []

            if validation_status == "needs_review":
                reasons.extend(
                    validation[
                        "review_reasons"
                    ]
                )

            if lifecycle_reason:
                reasons.append(
                    lifecycle_reason
                )

            review_reasons[
                title
            ] = reasons

            details.append(
                {
                    "title": title,
                    "validation_status": validation_status,
                    "lifecycle_status": lifecycle_status,
                    "final_status": "review",
                    "reasons": reasons,
                }
            )

    write_entries(
        MIGRATED_BATCH,
        migrated,
    )

    write_entries(
        MIGRATION_REVIEW,
        review,
        extra_lines=review_reasons,
    )

    write_entries(
        MIGRATION_REJECTED,
        rejected,
        extra_lines=rejected_reasons,
    )

    write_entries(
        MIGRATION_EXPIRED,
        expired,
        extra_lines=expired_reasons,
    )

    STATUS_JSON.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    status = {
        "status": "success",
        "generated_at": datetime.now().isoformat(
            timespec="seconds"
        ),
        "source_batch": str(
            SOURCE_BATCH
        ),
        "backup_file": str(
            backup_file
        ),
        "migrated_batch": str(
            MIGRATED_BATCH
        ),
        "total_entries": len(
            blocks
        ),
        "validation": {
            "approved": validation_approved,
            "needs_review": validation_review,
            "rejected": validation_rejected,
        },
        "lifecycle": {
            "active": lifecycle_active,
            "uncertain": lifecycle_uncertain,
            "expired": lifecycle_expired,
        },
        "final": {
            "migrated": len(
                migrated
            ),
            "review": len(
                review
            ),
            "rejected": len(
                rejected
            ),
            "expired": len(
                expired
            ),
        },
        "details": details,
    }

    STATUS_JSON.write_text(
        json.dumps(
            status,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    text_status = "\n".join(
        [
            "Legacy batch migration completed successfully.",
            f"Source entries: {len(blocks)}",
            f"Validation approved: {validation_approved}",
            f"Validation review: {validation_review}",
            f"Validation rejected: {validation_rejected}",
            f"Lifecycle active: {lifecycle_active}",
            f"Lifecycle uncertain: {lifecycle_uncertain}",
            f"Lifecycle expired: {lifecycle_expired}",
            f"Final migrated: {len(migrated)}",
            f"Final review: {len(review)}",
            f"Final rejected: {len(rejected)}",
            f"Final expired: {len(expired)}",
            f"Backup: {backup_file}",
            f"Migrated batch: {MIGRATED_BATCH}",
        ]
    )

    STATUS_TXT.write_text(
        text_status,
        encoding="utf-8",
    )

    print(
        text_status
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )