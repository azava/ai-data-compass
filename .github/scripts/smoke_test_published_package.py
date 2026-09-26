#!/usr/bin/env python3
"""Install an exact published version in isolation and smoke-test its CLI."""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import venv
from pathlib import Path


INSTALL_ATTEMPTS = 7
RETRY_DELAYS_SECONDS = (5, 10, 20, 30, 30, 30)


def toml_section(contents: str, name: str) -> str:
    heading = f"[{name}]"
    lines = contents.splitlines()
    try:
        start = lines.index(heading) + 1
    except ValueError as error:
        raise SystemExit(f"Could not find [{name}] in pyproject.toml") from error
    end = next(
        (index for index in range(start, len(lines)) if lines[index].startswith("[")),
        len(lines),
    )
    return "\n".join(lines[start:end])


def toml_string(section: str, key: str) -> str:
    match = re.search(
        rf"(?m)^{re.escape(key)}\s*=\s*\"([^\"]+)\"\s*(?:#.*)?$", section
    )
    if not match:
        raise SystemExit(f"Could not find a string value for {key!r} in pyproject.toml")
    return match.group(1)


def project_contract(project_file: Path) -> tuple[str, str, str, str]:
    contents = project_file.read_text(encoding="utf-8")
    project = toml_section(contents, "project")
    scripts = toml_section(contents, "project.scripts")
    distribution = toml_string(project, "name")
    version = toml_string(project, "version")
    command = distribution.replace("_", "-")
    try:
        entry_point = toml_string(scripts, command)
    except SystemExit:
        raise SystemExit(
            f"Expected a console script named {command!r} in project.scripts"
        ) from None
    module = entry_point.partition(":")[0]
    if not module:
        raise SystemExit(f"Could not determine the import module for {command!r}")
    return distribution, command, module, version


def run(command: list[str], *, env: dict[str, str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=False, capture_output=True, text=True, env=env, cwd=cwd)


def install_with_retries(
    python: Path,
    requirement: str,
    index_url: str,
    extra_index_urls: list[str],
    *,
    env: dict[str, str],
    cwd: Path,
) -> None:
    command = [
        str(python),
        "-m",
        "pip",
        "install",
        "--disable-pip-version-check",
        "--no-cache-dir",
        "--index-url",
        index_url,
    ]
    for extra_index_url in extra_index_urls:
        command.extend(("--extra-index-url", extra_index_url))
    command.append(requirement)

    for attempt in range(INSTALL_ATTEMPTS):
        result = run(command, env=env, cwd=cwd)
        if result.returncode == 0:
            return
        if attempt == INSTALL_ATTEMPTS - 1:
            sys.stderr.write(result.stdout)
            sys.stderr.write(result.stderr)
            raise SystemExit(
                f"Could not install {requirement} from {index_url} "
                f"after {INSTALL_ATTEMPTS} attempts"
            )
        delay = RETRY_DELAYS_SECONDS[attempt]
        print(
            f"Install attempt {attempt + 1}/{INSTALL_ATTEMPTS} failed; "
            f"retrying in {delay}s while the package index updates.",
            flush=True,
        )
        time.sleep(delay)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--local",
        action="store_true",
        help="Smoke-test the current source checkout without installing from an index",
    )
    parser.add_argument("--version", help="Exact published version to install")
    parser.add_argument("--index-url", help="Package index containing the release")
    parser.add_argument(
        "--extra-index-url",
        action="append",
        default=[],
        help="Additional index for resolving package dependencies; may be repeated",
    )
    args = parser.parse_args()

    if args.local:
        if args.version or args.index_url or args.extra_index_url:
            parser.error(
                "--local cannot be combined with published-version or index options"
            )
    else:
        if not args.version or not args.version.strip():
            parser.error("--version must be a non-empty exact package version")
        if not args.index_url:
            parser.error("--index-url is required unless --local is used")

    project_file = Path(__file__).resolve().parents[2] / "pyproject.toml"
    distribution, cli_command, module, expected_version = project_contract(project_file)
    if args.local:
        source_directory = project_file.parent / "src"
        local_env = os.environ.copy()
        local_env.pop("PYTHONHOME", None)
        local_env["PYTHONPATH"] = str(source_directory) + (
            os.pathsep + local_env["PYTHONPATH"] if local_env.get("PYTHONPATH") else ""
        )
        with tempfile.TemporaryDirectory(
            prefix="published-package-local-smoke-"
        ) as temporary_directory:
            root = Path(temporary_directory)
            probe = (
                "import importlib, sys; "
                "from ai_data_compass import __version__; "
                "expected, module = sys.argv[1:]; "
                    "__version__ == expected or sys.exit("
                    "f'loaded version {__version__}, expected {expected}'); "
                "importlib.import_module(module)"
            )
            result = run(
                [sys.executable, "-c", probe, expected_version, module],
                env=local_env,
                cwd=root,
            )
            if result.returncode != 0:
                sys.stderr.write(result.stderr)
                raise SystemExit("Local package metadata or import smoke test failed")
            for option in ("--version", "--help"):
                result = run(
                    [sys.executable, "-m", module, option], env=local_env, cwd=root
                )
                if result.returncode != 0:
                    sys.stderr.write(result.stdout)
                    sys.stderr.write(result.stderr)
                    raise SystemExit(f"Local command failed: {cli_command} {option}")
                if option == "--version" and expected_version not in result.stdout:
                    raise SystemExit(
                        f"{cli_command} --version did not report {expected_version}"
                    )
        print(f"Local package smoke test passed: {distribution} {expected_version}")
        return 0

    requirement = f"{distribution}=={args.version}"
    clean_env = os.environ.copy()
    clean_env.pop("PYTHONPATH", None)
    clean_env.pop("PYTHONHOME", None)

    with tempfile.TemporaryDirectory(prefix="published-package-smoke-") as temporary_directory:
        root = Path(temporary_directory)
        environment = root / "venv"
        venv.EnvBuilder(with_pip=True).create(environment)
        bin_directory = environment / ("Scripts" if os.name == "nt" else "bin")
        python = bin_directory / ("python.exe" if os.name == "nt" else "python")
        cli = bin_directory / (cli_command + (".exe" if os.name == "nt" else ""))

        install_with_retries(
            python,
            requirement,
            args.index_url,
            args.extra_index_url,
            env=clean_env,
            cwd=root,
        )

        if not cli.is_file() and shutil.which(cli_command, path=str(bin_directory)) is None:
            raise SystemExit(f"Installed console command was not created: {cli_command}")

        probe = (
            "import importlib, importlib.metadata, sys; "
            "dist, expected, module = sys.argv[1:]; "
            "actual = importlib.metadata.version(dist); "
            "actual == expected or sys.exit(f'installed {dist} {actual}, expected {expected}'); "
            "importlib.import_module(module)"
        )
        result = run(
            [str(python), "-c", probe, distribution, args.version, module],
            env=clean_env,
            cwd=root,
        )
        if result.returncode != 0:
            sys.stderr.write(result.stderr)
            raise SystemExit("Installed package metadata or import smoke test failed")

        for option in ("--version", "--help"):
            result = run([str(cli), option], env=clean_env, cwd=root)
            if result.returncode != 0:
                sys.stderr.write(result.stdout)
                sys.stderr.write(result.stderr)
                raise SystemExit(f"Installed command failed: {cli_command} {option}")
            if option == "--version" and args.version not in result.stdout:
                raise SystemExit(
                    f"{cli_command} --version did not report installed version {args.version}"
                )

    print(f"Published package smoke test passed: {requirement} from {args.index_url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
