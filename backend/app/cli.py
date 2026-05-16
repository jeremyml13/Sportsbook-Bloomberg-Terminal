import argparse

from app.db.session import SessionLocal
from app.services.seed_mock import seed_mock_data


def seed_mock() -> None:
    with SessionLocal() as db:
        counts = seed_mock_data(db)

    print("Seeded mock data: " + ", ".join(f"{name}={count}" for name, count in counts.items()))


def main() -> None:
    parser = argparse.ArgumentParser(description="Backend maintenance commands.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("seed-mock", help="Load the 5-game NBA mock board into Postgres.")
    args = parser.parse_args()

    if args.command == "seed-mock":
        seed_mock()


if __name__ == "__main__":
    main()
