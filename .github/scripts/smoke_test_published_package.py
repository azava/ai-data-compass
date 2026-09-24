#!/usr/bin/env python3
"""Install an exact published version in isolation and smoke-test its CLI."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import time
import tomllib
import venv
from pathlib import Path


INSTALL_ATTEMPTS = 7
RETRY_DELAYS_SECONDS = (5, 10, 20, 30, 30, 30)


def project_contract(project_file: Path) -> tuple[str, str, str]:
    with project_file.open("rb") as file:
        project = tomllib.load(file)["project"]

    distribution = project["name"]
    command = distribution.replace("_", "-")
    entry_point = project.get("scripts", {}).get(command)
    if not entry_point:
        raise SystemExit(
            f"Expected a console script named {command!r} in project.scripts"
        )
    module = entry_point.partition(":")[0]
    if not module:
        raise SystemExit(f"Could not determine the import module for {command!r}")
    return distribution, command, module


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
    parser.add_argument("--version", required=True, help="Exact published version to install")
    parser.add_argument("--index-url", required=True, help="Package index containing the release")
    parser.add_argument(
        "--extra-index-url",
        action="append",
        default=[],
        help="Additional index for resolving package dependencies; may be repeated",
    )
    args = parser.parse_args()

    distribution, cli_command, module = project_contract(Path("pyproject.toml"))
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
