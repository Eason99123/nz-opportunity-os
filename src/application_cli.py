from datetime import date

from application_repository import (
    add_application,
    load_applications,
    replace_application,
)
from application_tracker import (
    create_application,
    update_application_status,
)


STATUS_OPTIONS = {
    "1": "APPLIED",
    "2": "ONLINE_ASSESSMENT",
    "3": "INTERVIEW",
    "4": "OFFER",
    "5": "REJECTED",
    "6": "WITHDRAWN",
}


def print_header():
    print()
    print("NZ Student Opportunity OS")
    print("Application Tracker")
    print("=" * 40)


def print_menu():
    print()
    print("1. Add application")
    print("2. View applications")
    print("3. Update application status")
    print("4. Application summary")
    print("5. Exit")
    print()


def display_applications(applications):
    if not applications:
        print("No applications recorded.")
        return

    print()
    print("Applications")
    print("=" * 70)

    for index, application in enumerate(applications, start=1):
        print(
            f"{index}. "
            f"{application.get('company', 'Unknown')} | "
            f"{application.get('title', 'Unknown')} | "
            f"{application.get('status', 'UNKNOWN')}"
        )

        print(
            f"   Applied: "
            f"{application.get('applied_at', 'Unknown')}"
        )

        print(
            f"   Link: "
            f"{application.get('source_link', '')}"
        )

        notes = application.get("notes", "")
        if notes:
            print(f"   Notes: {notes}")

        print()


def add_application_interactive():
    print()
    print("Add Application")
    print("=" * 40)

    company = input("Company: ").strip()
    title = input("Role title: ").strip()
    source_link = input("Source link: ").strip()

    applied_at = input(
        f"Applied date [{date.today().isoformat()}]: "
    ).strip()

    if not applied_at:
        applied_at = date.today().isoformat()

    notes = input("Notes (optional): ").strip()

    application = create_application(
        company=company,
        title=title,
        source_link=source_link,
        applied_at=applied_at,
        notes=notes,
    )

    add_application(application)

    print()
    print("Application saved successfully.")


def choose_status():
    print()
    print("Select new status:")

    for number, status in STATUS_OPTIONS.items():
        print(f"{number}. {status}")

    choice = input("Status: ").strip()

    if choice not in STATUS_OPTIONS:
        raise ValueError("Invalid status selection.")

    return STATUS_OPTIONS[choice]


def update_application_interactive():
    applications = load_applications()

    if not applications:
        print("No applications recorded.")
        return

    display_applications(applications)

    raw_choice = input("Select application: ").strip()

    try:
        index = int(raw_choice) - 1
    except ValueError as error:
        raise ValueError("Please enter a valid number.") from error

    if index < 0 or index >= len(applications):
        raise ValueError("Application selection out of range.")

    application = applications[index]

    new_status = choose_status()

    notes = input(
        "Update notes (leave blank to keep current notes): "
    ).strip()

    updated = update_application_status(
        application,
        status=new_status,
        last_updated_at=date.today().isoformat(),
        notes=notes or None,
    )

    replace_application(updated)

    print()
    print("Application updated successfully.")


def print_summary(applications):
    print()
    print("Application Summary")
    print("=" * 40)

    print(f"Total applications: {len(applications)}")

    counts = {}

    for application in applications:
        status = application.get("status", "UNKNOWN")
        counts[status] = counts.get(status, 0) + 1

    for status in sorted(counts):
        print(f"{status}: {counts[status]}")


def main():
    while True:
        print_header()
        print_menu()

        choice = input("Select option: ").strip()

        try:
            if choice == "1":
                add_application_interactive()

            elif choice == "2":
                display_applications(
                    load_applications()
                )

            elif choice == "3":
                update_application_interactive()

            elif choice == "4":
                print_summary(
                    load_applications()
                )

            elif choice == "5":
                print("Goodbye.")
                break

            else:
                print("Invalid option.")

        except (ValueError, OSError) as error:
            print(f"Error: {error}")


if __name__ == "__main__":
    main()