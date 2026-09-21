import json
import hashlib
import os
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from ai_data_compass.assets import (
    _asset_files,
    install_assets,
    normalize_assets,
    planned_assets,
    validate_installation,
)
from ai_data_compass.cli import main


class CliTests(unittest.TestCase):
    def test_version(self) -> None:
        with self.assertRaises(SystemExit) as result:
            main(["--version"])

        self.assertEqual(result.exception.code, 0)

    def test_init_installs_agents_and_skill_assets(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            exit_code = main(
                [
                    "init",
                    str(target),
                    "--assets",
                    "agents.md,security_audit",
                ]
            )

            self.assertEqual(exit_code, 0)
            self.assertTrue((target / "AGENTS.md").is_file())
            for adapter in [
                "CLAUDE.md",
                "GEMINI.md",
                ".cursor/rules/agents.mdc",
                ".github/copilot-instructions.md",
                ".windsurfrules",
            ]:
                self.assertTrue((target / adapter).is_file(), adapter)
            self.assertTrue(
                (target / ".ai-data-compass" / "skills" / "security-audit" / "SKILL.md").is_file()
            )
            self.assertTrue(
                (target / ".agents" / "skills" / "security-audit" / "SKILL.md").is_file()
            )
            self.assertTrue(
                (target / ".claude" / "skills" / "security-audit" / "SKILL.md").is_file()
            )
            self.assertTrue((target / ".ai-data-compass" / "LICENSE").is_file())
            self.assertTrue(
                (target / ".ai-data-compass" / "skills" / "security-audit" / "LICENSE").is_file()
            )
            manifest = json.loads(
                (target / ".ai-data-compass" / "manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["version"], "0.0.1")
            self.assertEqual(manifest["assets"], ["base", "agents.md", "security_audit"])
            self.assertEqual(
                manifest["licenses"],
                [
                    {"asset": "base", "path": ".ai-data-compass/LICENSE"},
                    {
                        "asset": "security_audit",
                        "path": ".ai-data-compass/skills/security-audit/LICENSE",
                    },
                ],
            )
            file_licenses = {
                entry["path"]: entry["license_asset"]
                for entry in manifest["files"]
            }
            self.assertEqual(file_licenses["AGENTS.md"], "base")
            self.assertEqual(
                file_licenses[".agents/skills/security-audit/SKILL.md"],
                "security_audit",
            )
            self.assertEqual(
                file_licenses[".claude/skills/security-audit/SKILL.md"],
                "security_audit",
            )

    def test_installation_output_lists_files_grouped_by_asset(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            with patch("builtins.print") as print_mock, patch.dict(
                os.environ, {"NO_COLOR": "1"}
            ):
                main(["init", str(target), "--assets", "complete"])

            output = "\n".join(
                " ".join(str(argument) for argument in call.args)
                for call in print_mock.call_args_list
            )
            self.assertIn("Installation complete", output)
            self.assertIn("base (", output)
            self.assertIn("agents.md (", output)
            self.assertIn("security_audit (", output)
            self.assertIn("  - AGENTS.md", output)
            self.assertIn("  - .ai-data-compass/docs/README.md", output)
            self.assertIn(
                "  - .ai-data-compass/skills/security-audit/SKILL.md", output
            )
            self.assertIn("  - .ai-data-compass/manifest.json", output)
            self.assertIn("Total: 32 files installed.", output)

    def test_init_accepts_all_skills_alias(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            exit_code = main(["init", str(target), "--assets", "skills"])

            self.assertEqual(exit_code, 0)
            self.assertTrue(
                (target / ".ai-data-compass" / "skills" / "security-audit" / "SKILL.md").is_file()
            )
            self.assertFalse((target / "AGENTS.md").exists())

    def test_init_accepts_complete_asset(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            exit_code = main(["init", str(target), "--assets", "complete"])

            self.assertEqual(exit_code, 0)
            self.assertTrue((target / "AGENTS.md").is_file())
            self.assertTrue(
                (target / ".ai-data-compass" / "skills" / "security-audit" / "SKILL.md").is_file()
            )
            manifest = json.loads(
                (target / ".ai-data-compass" / "manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["assets"], ["base", "agents.md", "security_audit"])

    def test_agents_only_selection_does_not_install_skill_license_or_notice(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            main(["init", str(target), "--assets", "agents.md"])

            self.assertTrue((target / ".ai-data-compass" / "LICENSE").is_file())
            self.assertFalse(
                (target / ".ai-data-compass" / "skills" / "security-audit" / "LICENSE").exists()
            )
            self.assertFalse(
                (
                    target
                    / ".ai-data-compass"
                    / "skills"
                    / "security-audit"
                    / "THIRD-PARTY-NOTICES.md"
                ).exists()
            )

    def test_init_accepts_combined_assets_and_deduplicates_them(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            exit_code = main(
                ["init", str(target), "--assets", "agents.md,security_audit,agents"]
            )

            self.assertEqual(exit_code, 0)
            files = [path for path in target.rglob("*") if path.is_file()]
            self.assertEqual(len(files), len(set(files)))
            self.assertTrue((target / "AGENTS.md").is_file())
            self.assertTrue(
                (target / ".ai-data-compass" / "skills" / "security-audit" / "SKILL.md").is_file()
            )

    def test_init_combines_agents_and_all_skills_in_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            main(["init", str(target), "--assets", "agents.md,skills"])

            manifest = json.loads(
                (target / ".ai-data-compass" / "manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["assets"], ["base", "agents.md", "security_audit"])

    def test_init_rejects_nonexistent_target(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "missing"
            with self.assertRaises(SystemExit) as result:
                main(["init", str(target), "--assets", "agents.md"])

            self.assertEqual(result.exception.code, 2)

    def test_init_rejects_file_target(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "target-file"
            target.write_text("synthetic", encoding="utf-8")
            with self.assertRaises(SystemExit) as result:
                main(["init", str(target), "--assets", "agents.md"])

            self.assertEqual(result.exception.code, 2)

    def test_init_rejects_empty_asset_selection(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(SystemExit) as result:
                main(["init", directory, "--assets", ",,"])

            self.assertEqual(result.exception.code, 2)

    def test_every_selection_includes_documentation_and_base_license(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            main(["init", str(target), "--assets", "security_audit"])

            expected_docs = {
                path.name
                for path in (Path(__file__).resolve().parents[1] / ".ai-data-compass" / "docs").glob("*.md")
            }
            installed_docs = {
                path.name for path in (target / ".ai-data-compass" / "docs").glob("*.md")
            }
            self.assertEqual(expected_docs, installed_docs)
            self.assertTrue((target / ".ai-data-compass" / "LICENSE").is_file())
            self.assertTrue(
                (target / ".ai-data-compass" / "THIRD-PARTY-NOTICES.md").is_file()
            )
            self.assertFalse((target / "PENDING_FEATURES.md").exists())
            self.assertFalse((target / "README.md").exists())
            self.assertFalse((target / ".github" / "workflows").exists())

    def test_skill_selection_keeps_nested_paths_and_skill_license(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            main(["init", str(target), "--assets", "security_audit"])

            expected_paths = [
                target / ".ai-data-compass" / "skills" / "security-audit" / "references" / "detection-rules.md",
                target / ".ai-data-compass" / "skills" / "security-audit" / "scripts" / "security-surface.sh",
                target / ".ai-data-compass" / "skills" / "security-audit" / "tests" / "test_security_surface.sh",
                target / ".agents" / "skills" / "security-audit" / "SKILL.md",
                target / ".claude" / "skills" / "security-audit" / "SKILL.md",
                target / ".ai-data-compass" / "skills" / "security-audit" / "LICENSE",
            ]

            for path in expected_paths:
                self.assertTrue(path.is_file(), path)
            source_root = Path(__file__).resolve().parents[1]
            self.assertEqual(
                (target / ".ai-data-compass" / "LICENSE").read_text(encoding="utf-8"),
                (source_root / ".ai-data-compass" / "LICENSE").read_text(encoding="utf-8"),
            )
            self.assertEqual(
                (target / ".ai-data-compass" / "skills" / "security-audit" / "LICENSE").read_text(
                    encoding="utf-8"
                ),
                (
                    source_root
                    / ".ai-data-compass"
                    / "skills"
                    / "security-audit"
                    / "LICENSE"
                ).read_text(encoding="utf-8"),
            )

            self.assertEqual(
                (target / ".ai-data-compass" / "THIRD-PARTY-NOTICES.md").read_text(
                    encoding="utf-8"
                ),
                (source_root / ".ai-data-compass" / "THIRD-PARTY-NOTICES.md").read_text(
                    encoding="utf-8"
                ),
            )
            self.assertEqual(
                (
                    target
                    / ".ai-data-compass"
                    / "skills"
                    / "security-audit"
                    / "THIRD-PARTY-NOTICES.md"
                ).read_text(encoding="utf-8"),
                (
                    source_root
                    / ".ai-data-compass"
                    / "skills"
                    / "security-audit"
                    / "THIRD-PARTY-NOTICES.md"
                ).read_text(encoding="utf-8"),
            )

    def test_asset_plan_preserves_nested_destinations(self) -> None:
        root = Path(__file__).resolve().parents[1]
        destinations = {
            destination.as_posix()
            for _, destination in _asset_files(["security_audit"], root)
        }

        self.assertIn(
            ".ai-data-compass/skills/security-audit/references/detection-rules.md",
            destinations,
        )
        self.assertIn(
            ".ai-data-compass/skills/security-audit/scripts/security-surface.sh",
            destinations,
        )
        self.assertIn(".agents/skills/security-audit/SKILL.md", destinations)
        self.assertIn(".claude/skills/security-audit/SKILL.md", destinations)

    def test_asset_names_are_normalized_and_invalid_names_are_rejected(self) -> None:
        self.assertEqual(
            ["agents.md", "security_audit"],
            normalize_assets(["agents.md, security-audit"]),
        )
        self.assertEqual(["security_audit"], normalize_assets(["skills"]))
        self.assertEqual(
            ["agents.md", "security_audit"],
            normalize_assets(["complete"]),
        )

        with self.assertRaises(ValueError):
            normalize_assets(["unknown_asset"])

    def test_init_dry_run_does_not_change_target(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            with patch("builtins.print"):
                exit_code = main(
                    ["init", str(target), "--assets", "security_audit", "--dry-run"]
                )

            self.assertEqual(exit_code, 0)
            self.assertEqual([], list(target.iterdir()))

    def test_installation_rejects_symlinked_destination_directories(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            target = workspace / "target"
            external = workspace / "external"
            target.mkdir()
            external.mkdir()
            (target / ".ai-data-compass").symlink_to(external, target_is_directory=True)

            with self.assertRaises(ValueError):
                install_assets(
                    target,
                    ["agents.md"],
                    root=Path(__file__).resolve().parents[1],
                )

            self.assertEqual([], list(external.iterdir()))

    def test_installation_rejects_symlinked_lock_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            target = workspace / "target"
            external = workspace / "external-lock"
            target.mkdir()
            external.mkdir()
            lock_id = hashlib.sha256(str(target.resolve()).encode("utf-8")).hexdigest()[:20]
            (workspace / f".ai-data-compass-lock-{lock_id}").symlink_to(external)

            with self.assertRaises(OSError):
                install_assets(
                    target,
                    ["agents.md"],
                    root=Path(__file__).resolve().parents[1],
                )

            self.assertEqual([], list(external.iterdir()))

    def test_installations_for_one_target_are_serialized(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            first_entered = threading.Event()
            release_first = threading.Event()
            second_entered = threading.Event()
            calls = []

            def fake_install(*args, **kwargs):
                calls.append(threading.current_thread().name)
                if len(calls) == 1:
                    first_entered.set()
                    self.assertTrue(release_first.wait(timeout=5))
                else:
                    second_entered.set()
                return []

            with patch("ai_data_compass.assets._install_assets", side_effect=fake_install):
                first = threading.Thread(
                    target=install_assets,
                    args=(target, ["agents.md"]),
                    name="first-install",
                )
                second = threading.Thread(
                    target=install_assets,
                    args=(target, ["security_audit"]),
                    name="second-install",
                )
                first.start()
                self.assertTrue(first_entered.wait(timeout=5))
                second.start()
                time.sleep(0.1)
                self.assertFalse(second_entered.is_set())
                release_first.set()
                first.join(timeout=5)
                second.join(timeout=5)

            self.assertFalse(first.is_alive())
            self.assertFalse(second.is_alive())
            self.assertEqual(2, len(calls))

    def test_installation_is_unchanged_when_a_source_file_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "target"
            source_root = Path(directory) / "source"
            target.mkdir()
            source_root.mkdir()
            source_root.joinpath(".ai-data-compass", "docs").mkdir(parents=True)
            source_root.joinpath(".ai-data-compass", "docs", "README.md").write_text(
                "synthetic", encoding="utf-8"
            )
            source_root.joinpath(".ai-data-compass", "LICENSE").write_text(
                "license", encoding="utf-8"
            )
            source_root.joinpath(".ai-data-compass", "THIRD-PARTY-NOTICES.md").write_text(
                "notices", encoding="utf-8"
            )

            with self.assertRaises(FileNotFoundError):
                install_assets(target, ["security_audit"], root=source_root)

            self.assertEqual([], list(target.iterdir()))

    def test_installation_rolls_back_when_commit_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            real_replace = os.replace
            calls = {"count": 0}

            def fail_on_second_move(source: str, destination: str) -> None:
                calls["count"] += 1
                if calls["count"] == 2:
                    raise OSError("synthetic commit failure")
                real_replace(source, destination)

            with patch("ai_data_compass.assets.os.replace", side_effect=fail_on_second_move):
                with self.assertRaises(OSError):
                    install_assets(
                        target,
                        ["agents.md"],
                        root=Path(__file__).resolve().parents[1],
                    )

            self.assertEqual([], list(target.iterdir()))
            self.assertEqual([], list(target.parent.glob(".ai-data-compass-install-*")))

    def test_verify_accepts_untampered_installation_and_rejects_tampering(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            main(["init", str(target), "--assets", "security_audit"])

            self.assertEqual([], validate_installation(target))
            main(["verify", str(target)])

            document = target / ".ai-data-compass" / "docs" / "README.md"
            document.write_text(document.read_text(encoding="utf-8") + "\nchanged", encoding="utf-8")
            errors = validate_installation(target)
            self.assertTrue(any("metadata differs" in error for error in errors))
            with self.assertRaises(SystemExit) as result:
                main(["verify", str(target)])
            self.assertEqual(result.exception.code, 2)

    def test_verify_rejects_missing_manifest_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            main(["init", str(target), "--assets", "agents.md"])
            (target / "AGENTS.md").unlink()

            errors = validate_installation(target)
            self.assertTrue(any("Installed file is missing" in error for error in errors))

    def test_verify_rejects_invalid_manifest_metadata(self) -> None:
        mutations = [
            ("format", 99, "Unsupported manifest format"),
            ("package", "other-package", "Manifest package does not match"),
            ("version", "99.0.0", "Manifest version does not match"),
            ("assets", ["base", "unknown"], "Manifest contains an unknown asset"),
            ("assets", ["base", "complete"], "Manifest contains an unknown asset"),
            ("assets", ["base", "security_audit", "security_audit"], "duplicate assets"),
        ]
        for field, value, expected_error in mutations:
            with self.subTest(field=field):
                with tempfile.TemporaryDirectory() as directory:
                    target = Path(directory)
                    main(["init", str(target), "--assets", "security_audit"])
                    manifest_path = target / ".ai-data-compass" / "manifest.json"
                    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                    manifest[field] = value
                    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

                    errors = validate_installation(target)
                    self.assertTrue(any(expected_error in error for error in errors))

    def test_verify_rejects_invalid_paths_and_license_associations(self) -> None:
        mutations = [
            ("path", "../outside", "Manifest path escapes target"),
            ("license_asset", "unknown", "Unknown license asset"),
            ("license_asset", "security_audit", "License asset does not match file path"),
        ]
        for field, value, expected_error in mutations:
            with self.subTest(field=field):
                with tempfile.TemporaryDirectory() as directory:
                    target = Path(directory)
                    main(["init", str(target), "--assets", "security_audit"])
                    manifest_path = target / ".ai-data-compass" / "manifest.json"
                    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                    manifest["files"][0][field] = value
                    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

                    errors = validate_installation(target)
                    self.assertTrue(any(expected_error in error for error in errors))

    def test_verify_rejects_missing_or_unexpected_license_and_notice_entries(self) -> None:
        mutations = [
            ("licenses", [], "Manifest licenses entries do not match"),
            ("third_party_notices", [], "Manifest third_party_notices entries do not match"),
        ]
        for field, value, expected_error in mutations:
            with self.subTest(field=field):
                with tempfile.TemporaryDirectory() as directory:
                    target = Path(directory)
                    main(["init", str(target), "--assets", "security_audit"])
                    manifest_path = target / ".ai-data-compass" / "manifest.json"
                    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                    manifest[field] = value
                    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

                    errors = validate_installation(target)
                    self.assertTrue(any(expected_error in error for error in errors))

        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            main(["init", str(target), "--assets", "security_audit"])
            manifest_path = target / ".ai-data-compass" / "manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["files"].append(
                {
                    "path": ".ai-data-compass/extra.md",
                    "license_asset": "base",
                    "source": "extra.md",
                    "sha256": "0" * 64,
                    "size": 0,
                    "mode": 0o644,
                }
            )
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            errors = validate_installation(target)
            self.assertTrue(any("unexpected file" in error for error in errors))

    def test_verify_ignores_non_executable_permission_changes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            main(["init", str(target), "--assets", "security_audit"])
            document = target / ".ai-data-compass" / "docs" / "README.md"
            document.chmod(0o600)

            errors = validate_installation(target)
            self.assertFalse(any("metadata differs" in error for error in errors))

    def test_verify_rejects_executable_permission_changes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            main(["init", str(target), "--assets", "security_audit"])
            script = target / ".ai-data-compass" / "skills" / "security-audit" / "scripts" / "security-surface.sh"
            script.chmod(0o644)

            errors = validate_installation(target)
            self.assertTrue(
                any("metadata differs" in error and "executable" in error for error in errors)
            )

    def test_dry_run_output_lists_the_selected_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            with patch("builtins.print") as print_mock, patch.dict(
                os.environ, {"NO_COLOR": "1"}
            ):
                main(["init", str(target), "--assets", "security_audit", "--dry-run"])

            output = [str(call.args[0]) for call in print_mock.call_args_list]
            expected = ["Dry run: files that would be installed:"]
            expected.extend(
                f"- {path}"
                for path in planned_assets(
                    normalize_assets(["security_audit"]),
                    root=Path(__file__).resolve().parents[1],
                )
            )
            self.assertEqual(expected, output)

    def test_interactive_installer_rejects_invalid_selection(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with patch("builtins.input", return_value="not-an-asset"):
                with self.assertRaises(SystemExit) as result:
                    main(["init", directory])

            self.assertEqual(result.exception.code, 2)

    def test_interactive_installer_defaults_to_complete_selection(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            with patch("builtins.input", return_value=""):
                exit_code = main(["init", directory])

            self.assertEqual(exit_code, 0)
            self.assertTrue((target / "AGENTS.md").is_file())
            self.assertTrue(
                (target / ".ai-data-compass" / "skills" / "security-audit" / "SKILL.md").is_file()
            )

    def test_interactive_installer_accepts_complete_selection(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            with patch("builtins.input", return_value="complete"):
                exit_code = main(["init", directory])

            self.assertEqual(exit_code, 0)
            self.assertTrue((target / "AGENTS.md").is_file())
            self.assertTrue(
                (target / ".ai-data-compass" / "skills" / "security-audit" / "SKILL.md").is_file()
            )

    def test_interactive_installer_handles_eof_and_keyboard_interrupt(self) -> None:
        for input_side_effect in (EOFError, KeyboardInterrupt):
            with self.subTest(input_side_effect=input_side_effect):
                with tempfile.TemporaryDirectory() as directory:
                    with patch("builtins.input", side_effect=input_side_effect):
                        with self.assertRaises(SystemExit) as result:
                            main(["init", directory])

                    self.assertEqual(result.exception.code, 2)

    def test_init_without_assets_uses_interactive_installer(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            with patch("builtins.input", return_value="agents.md"):
                exit_code = main(["init", str(target)])

            self.assertEqual(exit_code, 0)
            self.assertTrue((target / "AGENTS.md").is_file())


if __name__ == "__main__":
    unittest.main()
