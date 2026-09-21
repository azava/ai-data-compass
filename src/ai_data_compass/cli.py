"""Command-line interface for AI Data Compass."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import List, Optional

from . import __version__
from .assets import (
    AGENTS_ASSET,
    ALL_SKILLS_ASSET,
    COMPLETE_ASSET,
    MANIFEST_RELATIVE_PATH,
    SKILL_ASSETS,
    available_assets,
    validate_installation,
)
from .bootstrap import initialize


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""

    parser = argparse.ArgumentParser(
        prog="ai-data-compass",
        description="Bootstrap AI Data Compass guidance in a repository.",
    )
    parser.add_argument("--version", action="version", version=__version__)

    subparsers = parser.add_subparsers(dest="command")
    init_parser = subparsers.add_parser(
        "init",
        help="Prepare a repository for AI Data Compass assets.",
    )
    init_parser.add_argument(
        "target",
        nargs="?",
        type=Path,
        default=Path("."),
        help="Repository directory to prepare (default: current directory).",
    )
    init_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Describe the operation without changing files.",
    )
    init_parser.add_argument(
        "--assets",
        help=(
            "Comma-separated assets: complete, agents.md, security_audit, or "
            "skills. Without this option, show the asset installer."
        ),
    )
    verify_parser = subparsers.add_parser(
        "verify",
        help="Validate an installed asset manifest.",
    )
    verify_parser.add_argument(
        "target",
        nargs="?",
        type=Path,
        default=Path("."),
        help="Installed repository to validate (default: current directory).",
    )
    return parser


def _supports_color() -> bool:
    """Return whether the current output supports ANSI colors."""

    return not os.environ.get("NO_COLOR") and bool(getattr(sys.stdout, "isatty", lambda: False)())


def _paint(text: str, color: str) -> str:
    """Apply a small, terminal-friendly color palette when appropriate."""

    if not _supports_color():
        return text
    return f"\033[{color}m{text}\033[0m"


def choose_assets() -> List[str]:
    """Prompt for a readable, comma-separated list of assets."""

    print(_paint("AI Data Compass", "1;36"))
    print(_paint("Choose what to install in this repository:", "1"))
    print()
    print(_paint(f"  {COMPLETE_ASSET:<13}", "1;32"), "Everything: agent instructions and all skills")
    print(_paint(f"  {AGENTS_ASSET:<13}", "1;33"), "AGENTS.md and host adapters")
    print(_paint(f"  security_audit", "1;33"), "Security audit skill and host adapters")
    print(_paint(f"  {ALL_SKILLS_ASSET:<13}", "1;33"), "All available skills")
    print()
    print(_paint("You can combine options with commas (for example: agents.md,security_audit).", "2"))
    answer = input(_paint("Assets [complete]: ", "1;36"))
    if not answer.strip():
        answer = COMPLETE_ASSET
    return [answer]


def _asset_group(relative_path: Path) -> str:
    """Return the human-facing asset group for an installed file."""

    if relative_path == MANIFEST_RELATIVE_PATH:
        return "base"
    if relative_path.parts[:2] == (".ai-data-compass", "docs"):
        return "base"
    if relative_path in {
        Path(".ai-data-compass") / "LICENSE",
        Path(".ai-data-compass") / "THIRD-PARTY-NOTICES.md",
    }:
        return "base"
    if relative_path in {
        Path("AGENTS.md"),
        Path("CLAUDE.md"),
        Path("GEMINI.md"),
        Path(".cursor") / "rules" / "agents.mdc",
        Path(".github") / "copilot-instructions.md",
        Path(".windsurfrules"),
    }:
        return AGENTS_ASSET
    for asset_name, directory_name in SKILL_ASSETS.items():
        if relative_path.parts[:3] in {
            (".ai-data-compass", "skills", directory_name),
            (".agents", "skills", directory_name),
            (".claude", "skills", directory_name),
        }:
            return asset_name
    return "other"


def _print_installation_report(installed: List[Path], target: Path) -> None:
    """Print every installed file grouped by the asset that provided it."""

    groups = {}
    for path in installed:
        groups.setdefault(_asset_group(path), []).append(path)

    print(_paint("Installation complete", "1;32"))
    print(_paint(f"Target: {target.resolve()}", "2"))
    print()
    for group_name, paths in groups.items():
        print(_paint(f"{group_name} ({len(paths)} files)", "1;36"))
        for path in paths:
            print(f"  - {path}")
        print()
    print(_paint(f"Total: {len(installed)} files installed.", "1;32"))


def main(argv: Optional[List[str]] = None) -> int:
    """Run the command-line interface and return its exit status."""

    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "init":
        try:
            asset_values = [args.assets] if args.assets else choose_assets()
            installed = initialize(
                args.target,
                asset_values,
                dry_run=args.dry_run,
            )
        except (EOFError, KeyboardInterrupt):
            parser.error("Asset selection cancelled")
        except (FileNotFoundError, NotADirectoryError, ValueError) as error:
            parser.error(str(error))
        if args.dry_run:
            print(_paint("Dry run: files that would be installed:", "1;36"))
            for path in installed:
                print(f"- {path}")
        else:
            _print_installation_report(installed, args.target)
        return 0

    if args.command == "verify":
        errors = validate_installation(args.target)
        if errors:
            parser.error("; ".join(errors))
        print(_paint(f"Valid AI Data Compass installation: {args.target.resolve()}", "1;32"))
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
