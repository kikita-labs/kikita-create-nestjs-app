#!/usr/bin/env python3
"""Structural check of plugin.json against the Agent Plugins 1.0.0 manifest rules."""
import json
import re
import sys
from pathlib import Path

ALLOWED_FIELDS = {
    "$schema",
    "name",
    "version",
    "description",
    "author",
    "homepage",
    "repository",
    "license",
    "keywords",
    "extensions",
}
EXPECTED_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
NAME_RE = re.compile(r"^[a-z0-9]([a-z0-9.-]{0,62}[a-z0-9])?$")


def main():
    manifest_path = Path("plugin.json")
    if not manifest_path.exists():
        print("ERROR: plugin.json not found at repo root.")
        sys.exit(1)

    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    errors = []

    unknown = set(data.keys()) - ALLOWED_FIELDS
    if unknown:
        errors.append(f"unknown top-level field(s): {sorted(unknown)}")

    if data.get("$schema") != EXPECTED_SCHEMA:
        errors.append(f"$schema must be exactly {EXPECTED_SCHEMA!r}")

    name = data.get("name", "")
    if not isinstance(name, str) or not NAME_RE.match(name) or "--" in name or ".." in name:
        errors.append(f"invalid name: {name!r}")

    if "$schema" not in data or "name" not in data:
        errors.append("missing required field(s): $schema and/or name")

    if errors:
        print("plugin.json is invalid:")
        for err in errors:
            print(f"  {err}")
        sys.exit(1)

    print("OK: plugin.json is valid.")


if __name__ == "__main__":
    main()
