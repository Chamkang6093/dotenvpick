from __future__ import annotations

import re
import subprocess
from pathlib import Path, PurePosixPath
from typing import Any


def prepare(sources: dict[str, Any]) -> list[str]:
    """Validate sources and return the requested sparse-checkout paths."""
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

    return list(dict.fromkeys(files))


def load(sources: dict[str, Any], root: Path) -> dict[str, dict[str, str]]:
    """Read the requested keys and return values grouped by source name."""
    root = root.resolve()
    values: dict[str, dict[str, str]] = {}
    for name, source in sources.items():
        file = (root / source["file"]).resolve()
        if not file.is_relative_to(root):
            raise SystemExit(f"File must remain inside the root for source {name}")
        lines = subprocess.check_output(
            ["bash", str(Path(__file__).with_name("env-loader.sh")), str(file), *source["keys"]],
            text=True,
        ).splitlines()
        # Split at the first '=' so values can contain additional '=' characters.
        entries = dict(line.split("=", 1) for line in lines)
        if len(lines) != len(entries) or set(entries) != set(source["keys"]):
            raise SystemExit(f"Unexpected or duplicate variable names in source {name}")
        values[name] = entries

    return values
