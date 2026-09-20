import json
import sys
from datetime import datetime, UTC
from pathlib import Path

from exporter import save_markdown_summary, save_to_csv, save_to_json
from parser import parse_opportunities
from ranking import (
    deduplicate_opportunities,
    generate_next_actions,
    get_best_opportunity,
    sort_opportunities,
)
from opportunity_verifier import verify_opportunities


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
        Path("opportunities") / "deduplicated_ranked_output.json"
    )
    default_md_output = (
        Path("opportunities") / "weekly_summary.md"
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

    return input_file, json_output_file, md_output_file


def build_history_paths(
    base_dir: Path,
    timestamp_label: str,
) -> tuple[Path, Path, Path]:

    history_dir = base_dir / "history"

    json_path = history_dir / f"{timestamp_label}.json"
    csv_path = history_dir / f"{timestamp_label}.csv"
    md_path = history_dir / f"{timestamp_label}.md"

    return json_path, csv_path, md_path


def main() -> None:
    try:
        input_file, json_output_file, md_output_file = (
            get_paths_from_args()
        )

        csv_output_file = (
            Path("opportunities") / "opportunities.csv"
        )

        text = read_input_text(input_file)

        # ---------------------------------------------------------
        # 1. Parse raw OpenClaw / discovery output
        # ---------------------------------------------------------
        parsed = parse_opportunities(text)

        # ---------------------------------------------------------
        # 2. Remove duplicate opportunities
        # ---------------------------------------------------------
        deduplicated = deduplicate_opportunities(parsed)

        # ---------------------------------------------------------
        # 3. Verify application/source status
        #
        # This enriches each opportunity with verification fields
        # such as:
        #
        # application_status
        # application_link_status
        # source_type
        # last_verified_at
        # verification_reason
        #
        # verify_opportunities() must not mutate the original list.
        # ---------------------------------------------------------
        verified = verify_opportunities(deduplicated)

        # ---------------------------------------------------------
        # 4. Rank verified opportunities
        # ---------------------------------------------------------
        ranked = sort_opportunities(verified)

        # ---------------------------------------------------------
        # 5. Select best opportunity and generate actions
        # ---------------------------------------------------------
        best = get_best_opportunity(ranked)
        actions = generate_next_actions(best)

        # ---------------------------------------------------------
        # 6. Build timestamp
        # ---------------------------------------------------------
        generated_at = datetime.now(UTC)
        generated_at_iso = generated_at.isoformat()
        timestamp_label = generated_at.strftime(
            "%Y-%m-%d_%H%M%S"
        )

        # ---------------------------------------------------------
        # 7. Build main JSON payload
        # ---------------------------------------------------------
        payload = {
            "generated_at": generated_at_iso,
            "count": len(ranked),
            "best_opportunity": best,
            "next_actions": actions,
            "opportunities": ranked,
        }

        # ---------------------------------------------------------
        # 8. Save current production outputs
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

        # ---------------------------------------------------------
        # 9. Save immutable history snapshot
        # ---------------------------------------------------------
        history_json, history_csv, history_md = (
            build_history_paths(
                Path("opportunities"),
                timestamp_label,
            )
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
        # 10. Console summary
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

        if best:
            print("Best opportunity:")
            print(
                json.dumps(
                    best,
                    indent=2,
                    ensure_ascii=False,
                )
            )

        print("Next 3 Actions:")

        for i, action in enumerate(
            actions,
            start=1,
        ):
            print(
                f"{i}. {action}"
            )

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
        print(f"Error: {e}")
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