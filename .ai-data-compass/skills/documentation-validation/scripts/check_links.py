#!/usr/bin/env python3
"""Check local Markdown link targets and section fragments in a repository."""

from __future__ import annotations

import argparse
import re
import sys
from html import unescape
from pathlib import Path
from urllib.parse import unquote, urlsplit


LINK_PATTERN = re.compile(r"!?\[[^\]]+\]\((<[^>]+>|[^)]*)\)")
MARKDOWN_SUFFIXES = {".md", ".mdx", ".markdown", ".mdc"}
DOCUMENT_SUFFIXES = MARKDOWN_SUFFIXES | {".rst"}


def markdown_anchors(content: str) -> set[str]:
    anchors = {
        value
        for _, _, value in re.findall(
            r"\b(id|name)\s*=\s*(['\"])(.*?)\2", content, re.IGNORECASE
        )
    }
    counts: dict[str, int] = {}
    for heading in re.findall(r"(?m)^\s{0,3}#{1,6}\s+(.+?)\s*#*\s*$", content):
        heading = unescape(heading)
        heading = re.sub(r"<[^>]+>", "", heading)
        heading = re.sub(r"`([^`]*)`", r"\1", heading)
        heading = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", heading)
        slug = re.sub(r"[^\w\- ]", "", heading.casefold()).strip()
        slug = re.sub(r"\s+", "-", slug)
        count = counts.get(slug, 0)
        counts[slug] = count + 1
        anchors.add(slug if count == 0 else f"{slug}-{count}")
    return anchors


def check_document(root: Path, document: Path) -> list[str]:
    content = document.read_text(encoding="utf-8")
    findings = []
    for match in LINK_PATTERN.finditer(content):
        link = match.group(1).strip()
        if link.startswith("<") and link.endswith(">"):
            link = link[1:-1]
        elif link:
            link = link.split(maxsplit=1)[0]
        parsed = urlsplit(link)
        if parsed.scheme or parsed.netloc:
            continue
        target_path = unquote(parsed.path)
        target = (
            root / target_path.lstrip("/")
            if target_path.startswith("/")
            else document.parent / target_path if target_path else document
        ).resolve()
        line = content.count("\n", 0, match.start()) + 1
        try:
            target.relative_to(root)
        except ValueError:
            findings.append(f"{document.relative_to(root)}:{line}: target outside repository")
            continue
        if not target.is_file() and not target.is_dir():
            findings.append(f"{document.relative_to(root)}:{line}: missing local target")
            continue
        fragment = unquote(parsed.fragment)
        if fragment and target.suffix.lower() in MARKDOWN_SUFFIXES and target.is_file():
            if fragment not in markdown_anchors(target.read_text(encoding="utf-8")):
                findings.append(f"{document.relative_to(root)}:{line}: missing target section")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="repository root (default: current directory)")
    args = parser.parse_args()
    root = args.root.resolve()
    if not root.is_dir():
        print("error: repository root is not a directory", file=sys.stderr)
        return 2

    try:
        documents = sorted(
            path for path in root.rglob("*")
            if path.is_file()
            and path.suffix.lower() in DOCUMENT_SUFFIXES
            and ".git" not in path.relative_to(root).parts
        )
        findings = [finding for document in documents for finding in check_document(root, document)]
    except (OSError, UnicodeError, ValueError):
        print("error: could not complete documentation link scan", file=sys.stderr)
        return 2

    if findings:
        print("\n".join(findings))
        return 1
    print(f"Checked local links in {len(documents)} documentation files; no broken targets found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
