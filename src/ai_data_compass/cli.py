"""Command-line interface for AI Data Compass."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import List, Optional

from . import __version__
from .assets import (
    AGENT_ADAPTER_TARGETS,
    AGENTS_ASSET,
    AGENTS_INSTRUCTIONS_PATH,
    ALL_SKILLS_ASSET,
    COMPLETE_ASSET,
    MANIFEST_RELATIVE_PATH,
    SKILL_ASSETS,
    SKILL_DESCRIPTIONS,
    agents_supplement_filename,
    is_agents_supplement_filename,
    InstallationResult,
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
    options = [
        (COMPLETE_ASSET, "Everything: agent instructions and all skills", "1;32"),
        (AGENTS_ASSET, f"{AGENTS_INSTRUCTIONS_PATH.name} and host adapters", "1;33"),
        *[
            (asset_name, SKILL_DESCRIPTIONS[asset_name], "1;33")
            for asset_name in sorted(SKILL_ASSETS)
        ],
        (ALL_SKILLS_ASSET, "All available skills", "1;33"),
    ]
    label_width = max(len(name) for name, _, _ in options)
    for name, description, color in options:
        print(_paint(f"  {name:<{label_width}}", color), description)
    print()
    print(_paint("You can combine options with commas (for example: agents.md,security_audit).", "2"))
    answer = input(_paint("Assets [complete]: ", "1;36"))
    if not answer.strip():
        answer = COMPLETE_ASSET
    return [answer]


def _asset_group(
    relative_path: Path, skill_names: Optional[dict] = None
) -> str:
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
    if relative_path in AGENT_ADAPTER_TARGETS:
        return AGENTS_ASSET
    if is_agents_supplement_filename(relative_path.name):
        return AGENTS_ASSET
    for asset_name, directory_name in SKILL_ASSETS.items():
        if (
            len(relative_path.parts) > 2
            and relative_path.parts[:2]
            in {
                (".ai-data-compass", "skills"),
                (".agents", "skills"),
                (".claude", "skills"),
            }
        ):
            resolved_name = (skill_names or {}).get(asset_name, directory_name)
            if relative_path.parts[2] == resolved_name:
                return resolved_name if resolved_name != directory_name else asset_name
    return "other"


def _print_installation_report(result: InstallationResult, target: Path) -> None:
    """Print every installed file grouped by the asset that provided it."""

    groups = {}
    for path in result.installed:
        groups.setdefault(_asset_group(path, result.skill_names), []).append(path)

    heading = (
        "Installation completed with conflicts"
        if result.has_conflicts
        else "Installation complete"
    )
    print(_paint(heading, "1;33" if result.has_conflicts else "1;32"))
    print(_paint(f"Target: {target.resolve()}", "2"))
    print()
    for outcome in result.outcomes:
        if outcome.status == "already_installed":
            print(f"{outcome.asset}: already installed; all files match the manifest.")
        elif outcome.status == "identical":
            print(
                f"{outcome.asset}: files already exist with identical content; "
                "no files were changed."
            )
        elif outcome.status == "conflict":
            print(f"Cannot install asset '{outcome.asset}': {outcome.message or 'conflicting files exist.'}")
            for path in outcome.conflicts:
                print(f"  - {path}")
        elif outcome.identical:
            print(
                f"{outcome.asset}: installed missing files; "
                f"{len(outcome.identical)} existing files already matched."
            )
    if result.outcomes:
        print()
    for group_name, paths in groups.items():
        print(_paint(f"{group_name} ({len(paths)} files)", "1;36"))
        for path in paths:
            print(f"  - {path}")
        print()
    print(_paint(f"Total: {len(result.installed)} files installed.", "1;32"))


def main(argv: Optional[List[str]] = None) -> int:
    """Run the command-line interface and return its exit status."""

    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "init":
        try:
            asset_values = [args.assets] if args.assets else choose_assets()
            result = initialize(
                args.target,
                asset_values,
                dry_run=args.dry_run,
                confirm_agents_adoption=(
                    None if args.dry_run else _confirm_agents_adoption
                ),
            )
        except (EOFError, KeyboardInterrupt):
            parser.error("Asset selection cancelled")
        except (OSError, ValueError) as error:
            parser.error(str(error))
        if args.dry_run:
            print(_paint("Dry run: files that would be installed:", "1;36"))
            for outcome in result.outcomes:
                if outcome.status == "would_install":
                    print(f"Would install asset '{outcome.asset}'.")
                elif outcome.status == "already_installed":
                    print(f"{outcome.asset}: already installed; all files match the manifest.")
                elif outcome.status == "identical":
                    print(
                        f"{outcome.asset}: files already exist with identical content; "
                        "no files would be changed."
                    )
                elif outcome.status == "conflict":
                    print(f"Cannot install asset '{outcome.asset}': {outcome.message or 'conflicting files exist.'}")
                    for path in outcome.conflicts:
                        print(f"  - {path}")
            for path in result.installed:
                print(f"- {path}")
        else:
            _print_installation_report(result, args.target)
        return 1 if result.has_conflicts else 0

    if args.command == "verify":
        errors = validate_installation(args.target)
        if errors:
            parser.error("; ".join(errors))
        print(_paint(f"Valid AI Data Compass installation: {args.target.resolve()}", "1;32"))
        return 0

    parser.print_help()
    return 0


def _confirm_agents_adoption(path: Path) -> bool:
    """Ask before appending the one-line AI Data Compass instruction."""

    print(
        f"An {AGENTS_INSTRUCTIONS_PATH.name} already exists at {path} with different content."
    )
    answer = input(
        "Append a single-line instruction and install "
        f"{agents_supplement_filename()} (or its available numeric suffix)? [y/N]: "
    )
    return answer.strip().lower() in {"y", "yes"}


if __name__ == "__main__":
    raise SystemExit(main())
