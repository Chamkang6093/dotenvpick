from __future__ import annotations

import argparse
import json
from pathlib import Path

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
    arguments = parser.parse_args()
    sources = json.loads(arguments.sources)
    files = prepare(sources)
    if arguments.command == "prepare":
        print("\n".join(files))
    else:
        print(json.dumps(load(sources, arguments.root), separators=(",", ":")))


if __name__ == "__main__":
    main()
