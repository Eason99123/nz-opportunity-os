from __future__ import annotations

import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent


TEXT_EXTENSIONS = {
    ".py",
    ".ps1",
    ".bat",
    ".html",
    ".css",
    ".js",
    ".json",
    ".md",
    ".txt",
    ".yml",
    ".yaml",
    ".toml",
    ".ini",
    ".cfg",
}


IGNORED_DIRS = {
    ".git",
    ".pytest_cache",
    "__pycache__",
    ".venv",
    "venv",
    "env",
    "logs",
    "archive",
    "history",
    "history_changes",
    "lifecycle_backups",
    "transaction_backups",
    "migration_backups",
}


IGNORED_FILES = {
    "openclaw_raw.txt",
    "openclaw_cleaned.txt",
    "openclaw_batch.txt",
    "openclaw_approved.txt",
    "openclaw_needs_review.txt",
    "openclaw_rejected.txt",
    "openclaw_active.txt",
    "openclaw_lifecycle_review.txt",
}


CHECKS: list[tuple[str, re.Pattern[str]]] = [
    (
        "Windows user path",
        re.compile(
            r"C:\\Users\\[^\\\r\n]+\\",
            re.IGNORECASE,
        ),
    ),
    (
        "Possible OpenAI API key",
        re.compile(
            r"\bsk-[A-Za-z0-9_-]{16,}\b",
        ),
    ),
    (
        "Possible Google API key",
        re.compile(
            r"\bAIza[A-Za-z0-9_-]{20,}\b",
        ),
    ),
    (
        "Possible bearer token",
        re.compile(
            r"Bearer\s+[A-Za-z0-9._~+/=-]{16,}",
            re.IGNORECASE,
        ),
    ),
    (
        "Possible API key assignment",
        re.compile(
            r"""(?ix)
            (api[_-]?key|secret|access[_-]?token)
            \s*
            [:=]
            \s*
            ["']
            [^"']{8,}
            ["']
            """
        ),
    ),
]


def should_ignore(path: Path) -> bool:
    relative = path.relative_to(PROJECT_ROOT)

    if any(
        part in IGNORED_DIRS
        for part in relative.parts
    ):
        return True

    if path.name in IGNORED_FILES:
        return True

    if "_pre_day" in path.name.lower():
        return True

    return False


def iter_public_text_files():
    for path in PROJECT_ROOT.rglob("*"):
        if not path.is_file():
            continue

        if should_ignore(path):
            continue

        if path.suffix.lower() not in TEXT_EXTENSIONS:
            continue

        yield path


def scan_file(
    path: Path,
) -> list[dict[str, object]]:
    try:
        content = path.read_text(
            encoding="utf-8"
        )
    except UnicodeDecodeError:
        try:
            content = path.read_text(
                encoding="utf-8-sig"
            )
        except UnicodeDecodeError:
            return []

    issues: list[dict[str, object]] = []

    lines = content.splitlines()

    for line_number, line in enumerate(
        lines,
        start=1,
    ):
        for check_name, pattern in CHECKS:
            if pattern.search(line):
                issues.append(
                    {
                        "file": str(
                            path.relative_to(
                                PROJECT_ROOT
                            )
                        ),
                        "line": line_number,
                        "check": check_name,
                        "content": line.strip()[:160],
                    }
                )

    return issues


def check_sensitive_files() -> list[str]:
    sensitive = []

    candidates = [
        PROJECT_ROOT / ".env",
        PROJECT_ROOT / "credentials.json",
        PROJECT_ROOT / "secrets.json",
        PROJECT_ROOT / "token.json",
    ]

    for path in candidates:
        if path.exists():
            sensitive.append(
                str(
                    path.relative_to(
                        PROJECT_ROOT
                    )
                )
            )

    return sensitive


def main() -> int:
    print(
        "NZ Student Opportunity OS "
        "Release Preflight"
    )
    print("=" * 50)

    scanned_files = 0
    findings: list[dict[str, object]] = []

    for path in iter_public_text_files():
        scanned_files += 1
        findings.extend(
            scan_file(path)
        )

    sensitive_files = (
        check_sensitive_files()
    )

    print(
        f"Scanned files: {scanned_files}"
    )

    print(
        f"Potential content issues: "
        f"{len(findings)}"
    )

    print(
        f"Sensitive files found: "
        f"{len(sensitive_files)}"
    )

    if findings:
        print()
        print(
            "Potential content issues:"
        )

        for issue in findings:
            print(
                f"  {issue['file']}:"
                f"{issue['line']}"
            )

            print(
                f"    {issue['check']}"
            )

            print(
                f"    {issue['content']}"
            )

    if sensitive_files:
        print()
        print(
            "Sensitive files:"
        )

        for file_name in sensitive_files:
            print(
                f"  {file_name}"
            )

    if findings or sensitive_files:
        print()
        print(
            "Release preflight FAILED."
        )

        print(
            "Review the findings before "
            "publishing this repository."
        )

        return 1

    print()
    print(
        "Release preflight PASSED."
    )

    print(
        "No obvious private paths, "
        "API keys, tokens, or sensitive "
        "files were detected."
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())