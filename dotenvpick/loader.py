from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from pathlib import Path, PurePosixPath


def prepare() -> None:
    """Validate sources and write the requested sparse-checkout paths."""
    sources = json.loads(os.environ["SOURCES"])
    if not isinstance(sources, dict) or not sources:
        raise SystemExit("sources must be a nonempty JSON object")

    files: list[str] = []
    for name, source in sources.items():
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_-]*", name) or not isinstance(source, dict):
            raise SystemExit("Each source must have a name and an object containing file and keys")
        file = source.get("file")
        keys = source.get("keys")
        if not isinstance(file, str) or not re.fullmatch(r"[A-Za-z0-9_./-]+", file):
            raise SystemExit(f"Invalid repository-relative file path for source {name}")
        path = PurePosixPath(file)
        if path.is_absolute() or ".." in path.parts or not path.parts:
            raise SystemExit(f"File must be relative to the root for source {name}")
        if not isinstance(keys, list) or not keys or any(
            not isinstance(key, str) or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key)
            for key in keys
        ):
            raise SystemExit(f"keys must be a nonempty list of variable names for source {name}")
        if len(keys) != len(set(keys)):
            raise SystemExit(f"Duplicate keys requested for source {name}")
        files.append("/" + str(path))

    with Path(os.environ["GITHUB_OUTPUT"]).open("a") as output:
        output.write("files<<ENV_FILES\n" + "\n".join(dict.fromkeys(files)) + "\nENV_FILES\n")


def load() -> None:
    """Read the requested keys and write their grouped JSON output."""
    sources = json.loads(os.environ["SOURCES"])
    root = Path(".").resolve()
    values: dict[str, dict[str, str]] = {}
    for name, source in sources.items():
        file = (root / source["file"]).resolve()
        if not file.is_relative_to(root):
            raise SystemExit(f"File must remain inside the root for source {name}")
        lines = subprocess.check_output(
            ["./env-loader.sh", str(file), *source["keys"]], text=True
        ).splitlines()
        # Split at the first '=' so values can contain additional '=' characters.
        entries = dict(line.split("=", 1) for line in lines)
        if len(lines) != len(entries) or set(entries) != set(source["keys"]):
            raise SystemExit(f"Unexpected or duplicate variable names in source {name}")
        values[name] = entries

    with Path(os.environ["GITHUB_OUTPUT"]).open("a") as output:
        output.write("values=" + json.dumps(values, separators=(",", ":")) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Prepare environment file paths or load their values for GitHub Actions."
    )
    parser.add_argument("command", choices=("prepare", "load"))
    args = parser.parse_args()
    if args.command == "prepare":
        prepare()
    else:
        load()


if __name__ == "__main__":
    main()
