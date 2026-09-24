import ast
import csv
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

from ai_data_compass import __version__


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


class DistributionTests(unittest.TestCase):
    def _project_requires_python(self) -> str:
        pyproject = (REPOSITORY_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        match = re.search(r'(?m)^requires-python\s*=\s*"([^"]+)"$', pyproject)
        self.assertIsNotNone(match, "pyproject.toml must declare requires-python")
        assert match is not None
        return match.group(1)

    def _assert_markdown_links_resolve(self, root: Path, paths: list[Path]) -> None:
        link_pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
        for document in paths:
            content = document.read_text(encoding="utf-8")
            for link in link_pattern.findall(content):
                if link.startswith(("http://", "https://", "mailto:", "#")):
                    continue
                target = (document.parent / link.split("#", 1)[0]).resolve()
                with self.subTest(document=document, link=link):
                    self.assertTrue(target.is_file(), target)

    def test_repository_markdown_links_resolve(self) -> None:
        extensions = {".md", ".mdc", ".mdx", ".rst"}
        documents = [
            path
            for path in REPOSITORY_ROOT.rglob("*")
            if path.is_file()
            and path.suffix.lower() in extensions
            and ".git" not in path.parts
        ]
        self._assert_markdown_links_resolve(REPOSITORY_ROOT, documents)

    def test_installed_documentation_links_resolve(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            source = REPOSITORY_ROOT / "src"
            subprocess.run(
                [
                    sys.executable,
                    "-c",
                    "import sys; sys.path.insert(0, sys.argv[1]); from ai_data_compass.cli import main; raise SystemExit(main(sys.argv[2:]))",
                    str(source),
                    "init",
                    str(target),
                    "--assets",
                    "agents.md,security_audit",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            documents = [target / "AGENTS.md"]
            documents.extend((target / ".ai-data-compass" / "docs").glob("*.md"))
            documents.extend(
                [
                    target / "CLAUDE.md",
                    target / "GEMINI.md",
                    target / ".cursor" / "rules" / "agents.mdc",
                    target / ".github" / "copilot-instructions.md",
                ]
            )
            self._assert_markdown_links_resolve(target, documents)

    def test_installation_documentation_describes_both_installation_paths(self) -> None:
        readme = (REPOSITORY_ROOT / "README.md").read_text(encoding="utf-8")
        distribution = (
            REPOSITORY_ROOT / ".ai-data-compass" / "docs" / "distribution.md"
        ).read_text(encoding="utf-8")
        self.assertIn("python -m pip install ai-data-compass", readme)
        self.assertIn("ai-data-compass init --assets complete", readme)

        self.assertIn("python -m pip install .", distribution)
        self.assertIn("pipx install .", distribution)
        self.assertIn("python -m pip install ai-data-compass", distribution)
        self.assertIn("pipx install ai-data-compass", distribution)
    def test_python_requirement_and_compatibility_metadata(self) -> None:
        pyproject = (REPOSITORY_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        requires_python = self._project_requires_python()
        minimum_version = re.search(r">=\s*(\d+\.\d+)", requires_python)
        self.assertIsNotNone(minimum_version, "requires-python must declare a minimum")
        assert minimum_version is not None
        classifiers = set(
            re.findall(
                r'"Programming Language :: Python :: (\d+\.\d+)"', pyproject
            )
        )

        self.assertIn(minimum_version.group(1), classifiers)

        for source in (REPOSITORY_ROOT / "src").rglob("*.py"):
            ast.parse(source.read_text(encoding="utf-8"), filename=str(source))

    def test_asset_licenses_have_explicit_scopes(self) -> None:
        base_license = (
            REPOSITORY_ROOT / ".ai-data-compass" / "LICENSE"
        ).read_text(encoding="utf-8")
        skill_license = (
            REPOSITORY_ROOT
            / ".ai-data-compass"
            / "skills"
            / "security-audit"
            / "LICENSE"
        ).read_text(encoding="utf-8")

        self.assertIn("only to the files listed as part", base_license)
        self.assertIn("base asset", base_license)
        self.assertIn("only to the files distributed as part", skill_license)
        self.assertIn("`security_audit` skill", skill_license)

        distribution = (
            REPOSITORY_ROOT / ".ai-data-compass" / "docs" / "distribution.md"
        ).read_text(encoding="utf-8")
        self.assertIn("do not change the adopting repository's license", distribution)

    def test_source_assets_are_complete_and_internal_files_are_excluded(self) -> None:
        expected_skill_files = {
            "SKILL.md",
            "LICENSE",
            "THIRD-PARTY-NOTICES.md",
            "references/detection-rules.md",
            "references/report-format.md",
            "scripts/security-surface.sh",
            "tests/test_claude_projection.sh",
            "tests/test_codex_projection.sh",
            "tests/test_security_surface.sh",
            "tests/test_workflow_security_integration.sh",
        }

        actual_skill_files = {
            path.relative_to(REPOSITORY_ROOT / ".ai-data-compass" / "skills" / "security-audit").as_posix()
            for path in (REPOSITORY_ROOT / ".ai-data-compass" / "skills" / "security-audit").rglob("*")
            if path.is_file()
        }
        self.assertTrue(expected_skill_files <= actual_skill_files)

    def _copy_project(self, destination: Path) -> None:
        paths = [
            "pyproject.toml",
            "setup.py",
            "README.md",
            "LICENSE",
            "AGENTS.md",
            "CLAUDE.md",
            "GEMINI.md",
            ".windsurfrules",
            ".ai-data-compass",
            ".agents",
            ".claude",
            ".cursor",
            ".github",
            "src",
        ]
        for relative in paths:
            source = REPOSITORY_ROOT / relative
            target = destination / relative
            if source.is_dir():
                shutil.copytree(source, target)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)

    def _build_artifacts(self, project: Path, output: Path) -> None:
        try:
            import setuptools  # noqa: F401
        except ImportError:
            self.skipTest(
                "distribution artifact tests require setuptools; install the build dependency first"
            )

        subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "wheel",
                "--no-deps",
                "--no-build-isolation",
                str(project),
                "--wheel-dir",
                str(output),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            [
                sys.executable,
                "-c",
                "from setuptools.build_meta import build_sdist; import sys; build_sdist(sys.argv[1])",
                str(output),
            ],
            check=True,
            capture_output=True,
            text=True,
            cwd=project,
        )

    def test_wheel_and_sdist_include_required_assets(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            project = workspace / "project"
            artifacts = workspace / "artifacts"
            project.mkdir()
            artifacts.mkdir()
            self._copy_project(project)
            catalog_path = project / "src" / "ai_data_compass" / "skill_catalog.json"
            catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
            catalog.append(
                {
                    "asset": "demo_skill",
                    "directory": "demo-skill",
                    "description": "Demo skill and host adapters",
                }
            )
            catalog_path.write_text(json.dumps(catalog), encoding="utf-8")
            for relative in (
                ".ai-data-compass/skills/demo-skill/SKILL.md",
                ".agents/skills/demo-skill/SKILL.md",
                ".claude/skills/demo-skill/SKILL.md",
            ):
                file_path = project / relative
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text("# Demo skill\n", encoding="utf-8")
            self._build_artifacts(project, artifacts)

            wheel = next(artifacts.glob("*.whl"))
            with ZipFile(wheel) as archive:
                names = set(archive.namelist())
                metadata_name = next(
                    name for name in names if name.endswith(".dist-info/METADATA")
                )
                metadata = archive.read(metadata_name).decode("utf-8")
                self.assertIn("Name: ai-data-compass", metadata)
                self.assertIn(f"Version: {__version__}", metadata)
                self.assertIn(
                    f"Requires-Python: {self._project_requires_python()}", metadata
                )
                self.assertIn("Author: Alex Zava", metadata)
                self.assertIn(
                    "Project-URL: Repository, https://github.com/azava/ai-data-compass",
                    metadata,
                )
                self.assertIn(
                    "Project-URL: Documentation, https://github.com/azava/ai-data-compass/blob/main/.ai-data-compass/docs/README.md",
                    metadata,
                )
                self.assertIn("ai-data-compass = ai_data_compass.cli:main", archive.read(next(
                    name for name in names if name.endswith(".dist-info/entry_points.txt")
                )).decode("utf-8"))
                self.assertTrue(
                    any(name.endswith("assets/.cursor/rules/agents.mdc") for name in names)
                )
                self.assertTrue(
                    any(name.endswith("assets/.ai-data-compass/LICENSE") for name in names)
                )
                self.assertTrue(
                    any(
                        name.endswith("assets/.ai-data-compass/THIRD-PARTY-NOTICES.md")
                        for name in names
                    )
                )
                self.assertTrue(
                    any(
                        name.endswith(
                            "assets/.ai-data-compass/skills/security-audit/references/detection-rules.md"
                        )
                        for name in names
                    )
                )
                self.assertTrue(
                    any(
                        name.endswith("assets/.ai-data-compass/skills/demo-skill/SKILL.md")
                        for name in names
                    )
                )
                self.assertTrue(
                    any(name.endswith("assets/.agents/skills/demo-skill/SKILL.md") for name in names)
                )
                self.assertTrue(
                    any(name.endswith("assets/.claude/skills/demo-skill/SKILL.md") for name in names)
                )
                self.assertTrue(
                    any(name.endswith("assets/.ai-data-compass/skills/security-audit/LICENSE") for name in names)
                )
                self.assertTrue(
                    any(
                        name.endswith(
                            "assets/.ai-data-compass/skills/security-audit/THIRD-PARTY-NOTICES.md"
                        )
                        for name in names
                    )
                )
                self.assertFalse(any(name.endswith("PENDING_FEATURES.md") for name in names))

                record_name = next(name for name in names if name.endswith(".dist-info/RECORD"))
                records = list(csv.reader(archive.read(record_name).decode("utf-8").splitlines()))
                record_paths = {row[0] for row in records}
                self.assertTrue(
                    any(path.endswith(".ai-data-compass/docs/README.md") for path in record_paths)
                )
                self.assertTrue(
                    any(
                        path.endswith(".ai-data-compass/skills/security-audit/LICENSE")
                        for path in record_paths
                    )
                )

            sdist = next(artifacts.glob("*.tar.gz"))
            with tarfile.open(sdist) as archive:
                names = archive.getnames()
                self.assertTrue(any(name.endswith(".ai-data-compass/docs/README.md") for name in names))
                self.assertTrue(any(name.endswith(".ai-data-compass/LICENSE") for name in names))
                self.assertTrue(
                    any(name.endswith(".ai-data-compass/THIRD-PARTY-NOTICES.md") for name in names)
                )
                self.assertTrue(any(name.endswith(".cursor/rules/agents.mdc") for name in names))
                self.assertTrue(
                    any(
                        name.endswith(".ai-data-compass/skills/security-audit/THIRD-PARTY-NOTICES.md")
                        for name in names
                    )
                )
                self.assertFalse(any(name.endswith("PENDING_FEATURES.md") for name in names))

            rebuilt = workspace / "rebuilt"
            rebuilt.mkdir()
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "wheel",
                    "--no-deps",
                    "--no-build-isolation",
                    str(sdist),
                    "--wheel-dir",
                    str(rebuilt),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertEqual(1, len(list(rebuilt.glob("*.whl"))))

    def test_installed_wheel_exposes_cli_and_installs_assets(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            project = workspace / "project"
            artifacts = workspace / "artifacts"
            virtualenv = workspace / "venv"
            target = workspace / "target"
            project.mkdir()
            artifacts.mkdir()
            target.mkdir()
            self._copy_project(project)
            self._build_artifacts(project, artifacts)

            subprocess.run([sys.executable, "-m", "venv", str(virtualenv)], check=True)
            venv_python = virtualenv / "bin" / "python"
            wheel = next(artifacts.glob("*.whl"))
            subprocess.run(
                [str(venv_python), "-m", "pip", "install", "--no-index", "--no-deps", str(wheel)],
                check=True,
                capture_output=True,
                text=True,
            )
            entry_point = subprocess.run(
                [
                    str(venv_python),
                    "-c",
                    "import importlib.metadata as m; print(any(ep.name == 'ai-data-compass' for ep in m.distribution('ai-data-compass').entry_points))",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertEqual(entry_point.stdout.strip(), "True")
            cli = [str(venv_python), "-m", "ai_data_compass.cli"]
            version = subprocess.run(
                cli + ["--version"],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertEqual(version.stdout.strip(), __version__)
            subprocess.run(
                cli + ["init", str(target), "--assets", "security_audit"],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertTrue(
                (target / ".ai-data-compass" / "skills" / "security-audit" / "SKILL.md").is_file()
            )

            script = target / ".ai-data-compass" / "skills" / "security-audit" / "scripts" / "security-surface.sh"
            self.assertTrue(os.stat(script).st_mode & 0o111)


if __name__ == "__main__":
    unittest.main()
