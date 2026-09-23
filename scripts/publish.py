#!/usr/bin/env python3
"""Add a document to the library and rebuild the site."""

from __future__ import annotations

import argparse
import datetime as dt
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value or "document"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", nargs="?", type=Path)
    parser.add_argument("--text")
    parser.add_argument("--title", required=True)
    parser.add_argument("--description", default="")
    parser.add_argument("--slug")
    parser.add_argument("--date", default=dt.date.today().isoformat())
    parser.add_argument("--draft", action="store_true")
    parser.add_argument("--no-build", action="store_true")
    args = parser.parse_args()
    if bool(args.source) == bool(args.text is not None):
        parser.error("provide exactly one source file or --text")
    if args.source:
        if not args.source.exists():
            parser.error(f"file not found: {args.source}")
        suffix = args.source.suffix.lower()
        if suffix not in {".md", ".txt", ".html"}:
            parser.error("supported source types: .md, .txt, .html")
        body = args.source.read_text()
    else:
        suffix = ".md"
        body = args.text
    slug = args.slug or slugify(args.title)
    destination = ROOT / "content" / f"{slug}{suffix}"
    if destination.exists():
        parser.error(f"document already exists: {destination.relative_to(ROOT)}")
    description = args.description or f"{args.title}, published in Jordan's document library."
    front_matter = f'''---
title: {args.title}
description: {description}
date: {args.date}
slug: {slug}
draft: {'true' if args.draft else 'false'}
---

'''
    destination.write_text(front_matter + body.strip() + "\n")
    print(f"Added {destination.relative_to(ROOT)}")
    if not args.no_build:
        return subprocess.call([sys.executable, str(ROOT / "scripts" / "build.py")])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

