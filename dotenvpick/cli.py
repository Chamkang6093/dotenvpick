from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from dotenvpick.check import exist, value
from dotenvpick.loader import load, prepare


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="dotenvpick",
        description="Select and group values from multiple dotenv files.",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    prepare_parser = commands.add_parser("prepare", help="print sparse-checkout paths")
    load_parser = commands.add_parser("load", help="print grouped values as JSON")
    for command in (prepare_parser, load_parser):
        command.add_argument(
            "--sources",
            required=True,
            help="JSON object mapping source names to file paths and key lists",
        )
    load_parser.add_argument(
        "--root",
        type=Path,
        default=Path("."),
        help="root directory containing the files; defaults to the current directory",
    )
    check_parser = commands.add_parser("check", help="check selected fields in grouped JSON")
    checks = check_parser.add_subparsers(dest="check_command", required=True)
    exist_parser = checks.add_parser("exist", help="check that fields exist and are nonempty")
    value_parser = checks.add_parser("value", help="print explicitly selected field values")
    for command in (exist_parser, value_parser):
        command.add_argument(
            "--env",
            default="VALUES",
            metavar="NAME",
            help="environment variable containing grouped JSON; defaults to VALUES",
        )
        command.add_argument("fields", nargs="+", metavar="SOURCE.KEY")

    arguments = parser.parse_args()
    if arguments.command == "check":
        if arguments.env not in os.environ:
            parser.error(f"Environment variable {arguments.env} is not set")
        values = json.loads(os.environ[arguments.env])
        if not isinstance(values, dict):
            parser.error("values must be a JSON object")
        if arguments.check_command == "exist":
            present = exist(values, arguments.fields)
            for field, available in present.items():
                print(f"{field}={str(available).lower()}")
            if not all(present.values()):
                raise SystemExit(1)
        else:
            for field, entry in value(values, arguments.fields).items():
                print(f"{field}={entry}")
        return

    sources = json.loads(arguments.sources)
    files = prepare(sources)
    if arguments.command == "prepare":
        print("\n".join(files))
    else:
        print(json.dumps(load(sources, arguments.root), separators=(",", ":")))


if __name__ == "__main__":
    main()
