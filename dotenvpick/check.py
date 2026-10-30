from __future__ import annotations


def exist(values: dict[str, dict[str, str]], fields: list[str]) -> dict[str, bool]:
    """Report whether each SOURCE.KEY field contains a nonempty string."""
    present: dict[str, bool] = {}
    for field in fields:
        source, separator, key = field.partition(".")
        if not separator or not source or not key:
            raise SystemExit("Fields must use SOURCE.KEY")
        available = False
        if source in values and isinstance(values[source], dict) and key in values[source]:
            entry = values[source][key]
            available = isinstance(entry, str) and entry != ""
        present[field] = available
    return present


def value(values: dict[str, dict[str, str]], fields: list[str]) -> dict[str, str]:
    """Check all selected fields before returning their values for display."""
    for field, available in exist(values, fields).items():
        if not available:
            raise SystemExit(f"{field} is missing or empty")
    selected: dict[str, str] = {}
    for field in fields:
        source, _, key = field.partition(".")
        selected[field] = values[source][key]
    return selected
