import json
import sys
from datetime import datetime, UTC
from pathlib import Path

from actionable_queue import (
    build_actionable_queue,
    build_queue_summary,
)
from exporter import save_markdown_summary, save_to_csv, save_to_json
from opportunity_verifier import verify_opportunities
from parser import parse_opportunities
from ranking import (
    deduplicate_opportunities,
    generate_next_actions,
    generate_verification_actions,
    get_best_actionable_opportunity,
    get_top_unverified_opportunity,
    sort_opportunities,
)


USAGE = """
Usage:
    python src/cli.py [input_file] [json_output_file] [md_output_file]

Examples:
    python src/cli.py
    python src/cli.py input/opportunities.txt
    python src/cli.py input/opportunities.txt opportunities/result.json opportunities/result.md
""".strip()


def read_input_text(input_path: Path) -> str:
    if not input_path.exists():
        raise FileNotFoundError(
            f"Input file not found: {input_path.resolve()}"
        )

    return input_path.read_text(encoding="utf-8")


def get_paths_from_args() -> tuple[Path, Path, Path]:
    default_input = Path("input") / "opportunities.txt"

    default_json_output = (
        Path("opportunities")
        / "deduplicated_ranked_output.json"
    )

    default_md_output = (
        Path("opportunities")
        / "weekly_summary.md"
    )

    args = sys.argv[1:]

    if any(arg in {"-h", "--help"} for arg in args):
        print(USAGE)
        sys.exit(0)

    if len(args) > 3:
        print("Error: too many arguments.\n")
        print(USAGE)
        sys.exit(1)

    input_file = (
        Path(args[0])
        if len(args) >= 1
        else default_input
    )

    json_output_file = (
        Path(args[1])
        if len(args) >= 2
        else default_json_output
    )

    md_output_file = (
        Path(args[2])
        if len(args) >= 3
        else default_md_output
    )

    return (
        input_file,
        json_output_file,
        md_output_file,
    )


def build_history_paths(
    base_dir: Path,
    timestamp_label: str,
) -> tuple[Path, Path, Path]:

    history_dir = base_dir / "history"

    json_path = (
        history_dir
        / f"{timestamp_label}.json"
    )

    csv_path = (
        history_dir
        / f"{timestamp_label}.csv"
    )

    md_path = (
        history_dir
        / f"{timestamp_label}.md"
    )

    return (
        json_path,
        csv_path,
        md_path,
    )


def main() -> None:
    try:
        (
            input_file,
            json_output_file,
            md_output_file,
        ) = get_paths_from_args()

        csv_output_file = (
            Path("opportunities")
            / "opportunities.csv"
        )

        actionable_queue_output = (
            Path("opportunities")
            / "actionable_queue.json"
        )

        text = read_input_text(input_file)

        # ---------------------------------------------------------
        # 1. Parse raw OpenClaw / discovery output
        # ---------------------------------------------------------
        parsed = parse_opportunities(text)

        # ---------------------------------------------------------
        # 2. Remove duplicate opportunities
        # ---------------------------------------------------------
        deduplicated = (
            deduplicate_opportunities(parsed)
        )

        # ---------------------------------------------------------
        # 3. Verify application/source status
        # ---------------------------------------------------------
        verified = verify_opportunities(
            deduplicated
        )

        # ---------------------------------------------------------
        # 4. Rank verified opportunities
        # ---------------------------------------------------------
        ranked = sort_opportunities(
            verified
        )

        # ---------------------------------------------------------
        # 5. Build actionable opportunity queue
        #
        # Only OPEN_VERIFIED opportunities are allowed through
        # this gate.
        # ---------------------------------------------------------
        actionable_queue = (
            build_actionable_queue(ranked)
        )

        queue_summary = (
            build_queue_summary(ranked)
        )

        # ---------------------------------------------------------
        # 6. Select verification-aware opportunities
        #
        # Best Actionable:
        #     Highest-ranked OPEN_VERIFIED opportunity.
        #
        # Top Unverified:
        #     Highest-ranked OPEN_UNVERIFIED opportunity that
        #     should be manually verified before action.
        # ---------------------------------------------------------
        best_actionable = (
            get_best_actionable_opportunity(
                ranked
            )
        )

        top_unverified = (
            get_top_unverified_opportunity(
                ranked
            )
        )

        # ---------------------------------------------------------
        # 7. Generate safe next actions
        #
        # Verified opportunities receive normal next actions.
        # If nothing is verified, the system generates
        # verification actions instead.
        # ---------------------------------------------------------
        if best_actionable:
            actions = generate_next_actions(
                best_actionable
            )
        else:
            actions = (
                generate_verification_actions(
                    top_unverified
                )
            )

        # ---------------------------------------------------------
        # 8. Build timestamp
        # ---------------------------------------------------------
        generated_at = datetime.now(UTC)

        generated_at_iso = (
            generated_at.isoformat()
        )

        timestamp_label = (
            generated_at.strftime(
                "%Y-%m-%d_%H%M%S"
            )
        )

        # ---------------------------------------------------------
        # 9. Build main JSON payload
        # ---------------------------------------------------------
        payload = {
            "generated_at": generated_at_iso,
            "count": len(ranked),
            "best_actionable_opportunity": (
                best_actionable
            ),
            "top_unverified_opportunity": (
                top_unverified
            ),
            "next_actions": actions,
            "opportunities": ranked,
        }

        # ---------------------------------------------------------
        # 10. Build actionable queue payload
        # ---------------------------------------------------------
        actionable_payload = {
            "generated_at": generated_at_iso,
            "summary": queue_summary,
            "opportunities": actionable_queue,
        }

        # ---------------------------------------------------------
        # 11. Save current production outputs
        # ---------------------------------------------------------
        save_to_json(
            payload,
            json_output_file,
        )

        save_to_csv(
            ranked,
            csv_output_file,
        )

        save_markdown_summary(
            ranked,
            actions,
            md_output_file,
        )

        save_to_json(
            actionable_payload,
            actionable_queue_output,
        )

        # ---------------------------------------------------------
        # 12. Save immutable history snapshot
        # ---------------------------------------------------------
        (
            history_json,
            history_csv,
            history_md,
        ) = build_history_paths(
            Path("opportunities"),
            timestamp_label,
        )

        save_to_json(
            payload,
            history_json,
        )

        save_to_csv(
            ranked,
            history_csv,
        )

        save_markdown_summary(
            ranked,
            actions,
            history_md,
        )

        # ---------------------------------------------------------
        # 13. Console pipeline summary
        # ---------------------------------------------------------
        print(
            f"Loaded input from: "
            f"{input_file.resolve()}"
        )

        print(
            f"Parsed opportunities: "
            f"{len(parsed)}"
        )

        print(
            f"After deduplication: "
            f"{len(deduplicated)}"
        )

        print(
            f"After verification: "
            f"{len(verified)}"
        )

        # ---------------------------------------------------------
        # 14. Actionable Queue summary
        # ---------------------------------------------------------
        print()
        print("Actionable Queue Summary")

        print(
            f"Total: "
            f"{queue_summary['total']}"
        )

        print(
            f"Actionable: "
            f"{queue_summary['actionable']}"
        )

        print(
            f"Needs verification: "
            f"{queue_summary['needs_verification']}"
        )

        print(
            f"Blocked: "
            f"{queue_summary['blocked']}"
        )

        # ---------------------------------------------------------
        # 15. Best actionable opportunity
        # ---------------------------------------------------------
        print()
        print(
            "Best Actionable Opportunity:"
        )

        if best_actionable:
            print(
                json.dumps(
                    best_actionable,
                    indent=2,
                    ensure_ascii=False,
                )
            )
        else:
            print("None")

        # ---------------------------------------------------------
        # 16. Top opportunity needing verification
        # ---------------------------------------------------------
        print()

        print(
            "Top Opportunity "
            "Needing Verification:"
        )

        if top_unverified:
            print(
                json.dumps(
                    top_unverified,
                    indent=2,
                    ensure_ascii=False,
                )
            )
        else:
            print("None")

        # ---------------------------------------------------------
        # 17. Recommended actions
        # ---------------------------------------------------------
        print()

        if best_actionable:
            print("Next 3 Actions:")
        elif top_unverified:
            print("Verification Actions:")
        else:
            print("Next Actions:")

        for i, action in enumerate(
            actions,
            start=1,
        ):
            print(
                f"{i}. {action}"
            )

        # ---------------------------------------------------------
        # 18. Saved output locations
        # ---------------------------------------------------------
        print()

        print(
            f"Saved ranked JSON to: "
            f"{json_output_file.resolve()}"
        )

        print(
            f"Saved CSV to: "
            f"{csv_output_file.resolve()}"
        )

        print(
            f"Saved markdown summary to: "
            f"{md_output_file.resolve()}"
        )

        print(
            f"Saved actionable queue to: "
            f"{actionable_queue_output.resolve()}"
        )

        print(
            f"Saved history JSON to: "
            f"{history_json.resolve()}"
        )

        print(
            f"Saved history CSV to: "
            f"{history_csv.resolve()}"
        )

        print(
            f"Saved history markdown to: "
            f"{history_md.resolve()}"
        )

    except FileNotFoundError as e:
        print(
            f"Error: {e}"
        )

        print()
        print(USAGE)

        sys.exit(1)

    except Exception as e:
        print(
            f"Unexpected error: {e}"
        )

        sys.exit(1)


if __name__ == "__main__":
    main()