#!/usr/bin/env python3
"""Verify every relative markdown link in the repo resolves to a real file."""
import re
import sys
from pathlib import Path

ROOT = Path(".").resolve()
LINK_RE = re.compile(r"\]\(([^)]+)\)")
SKIP_PREFIXES = ("http://", "https://", "mailto:")


def find_markdown_files():
    for path in ROOT.rglob("*.md"):
        if ".git" in path.parts:
            continue
        yield path


def check_file(md_path):
    errors = []
    text = md_path.read_text(encoding="utf-8")
    for match in LINK_RE.finditer(text):
        target = match.group(1).strip()
        if not target or target.startswith(SKIP_PREFIXES) or target.startswith("#"):
            continue
        target = target.split("#", 1)[0].strip()
        if not target:
            continue
        resolved = (md_path.parent / target).resolve()
        if not resolved.exists():
            rel = md_path.relative_to(ROOT)
            errors.append(f"{rel}: broken link -> {target}")
    return errors


def main():
    all_errors = []
    for md in find_markdown_files():
        all_errors.extend(check_file(md))

    if all_errors:
        print("Broken relative links found:")
        for err in all_errors:
            print(f"  {err}")
        sys.exit(1)

    print("OK: no broken relative markdown links.")


if __name__ == "__main__":
    main()
