from __future__ import annotations

import json
from pathlib import Path


def mask(values: dict[str, dict[str, str]], visible: list[str], output: Path) -> None:
    """Register GitHub log masks before writing the grouped values to its output file."""
    if not isinstance(visible, list) or any(not isinstance(field, str) for field in visible):
        raise SystemExit("visible must be a JSON list of SOURCE.KEY fields")
    fields = {f"{source}.{key}" for source, entries in values.items() for key in entries}
    unknown = set(visible) - fields
    if unknown:
        raise SystemExit("Unknown visible fields: " + ", ".join(sorted(unknown)))

    serialized = json.dumps(values, separators=(",", ":"))
    # Mask the complete payload as well as individual sensitive values.
    masks = [serialized]
    for source, entries in values.items():
        for key, value in entries.items():
            if f"{source}.{key}" not in visible and value:
                masks.append(value)
                masks.append(json.dumps(value)[1:-1])
    for value in dict.fromkeys(masks):
        escaped = value.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
        print("::add-mask::" + escaped, flush=True)

    # Register all masks before the runner processes this step's output file.
    with output.open("a", encoding="utf-8") as stream:
        stream.write("values=" + serialized + "\n")
