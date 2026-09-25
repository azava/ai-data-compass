import errno
import hashlib
import json
import os
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from ai_data_compass import __version__
from ai_data_compass.assets import (
    AGENT_ADAPTER_PATHS,
    AGENT_ADAPTER_TARGETS,
    AGENTS_SUPPLEMENT_STEM,
    _asset_files,
    _selected_asset_files,
    agents_supplement_filename,
    is_agents_supplement_filename,
    install_assets,
    normalize_assets,
    planned_assets,
    validate_installation,
)
from ai_data_compass.cli import (
    AGENTS_ASSET,
    ALL_SKILLS_ASSET,
    COMPLETE_ASSET,
    SKILL_ASSETS,
    _asset_group,
    choose_assets,
    main,
)


class CliTests(unittest.TestCase):
    def test_adapter_paths_and_collision_names_share_the_registry(self) -> None:
        source_root = Path(__file__).resolve().parents[1]
        selected_paths = {
            destination
            for _, destination in _selected_asset_files(["agents.md"], source_root)
        }
        adapter_targets = set(AGENT_ADAPTER_PATHS)

        self.assertEqual(AGENT_ADAPTER_TARGETS, adapter_targets)
        self.assertEqual(adapter_targets, selected_paths)
        for adapter_path in adapter_targets:
            self.assertEqual("agents.md", _asset_group(adapter_path))

        self.assertEqual(f"{AGENTS_SUPPLEMENT_STEM}.md", agents_supplement_filename())
        self.assertEqual(
            f"{AGENTS_SUPPLEMENT_STEM}-2.md", agents_supplement_filename(2)
        )
        self.assertTrue(is_agents_supplement_filename(agents_supplement_filename()))
        self.assertTrue(is_agents_supplement_filename(agents_supplement_filename(2)))
        self.assertFalse(is_agents_supplement_filename(f"{AGENTS_SUPPLEMENT_STEM}-1.md"))

    def test_agents_collision_requires_consent_and_installs_supplement(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            existing_agents = target / "AGENTS.md"
            existing_agents.write_text("Project rules take precedence.\n", encoding="utf-8")
            for adapter in ["GEMINI.md", ".windsurfrules"]:
                path = target / adapter
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("custom adapter", encoding="utf-8")
            source_root = Path(__file__).resolve().parents[1]

            declined = install_assets(target, ["agents.md"], root=source_root)

            self.assertEqual("conflict", declined.outcomes[0].status)
            self.assertEqual("Project rules take precedence.\n", existing_agents.read_text())
            self.assertFalse((target / "AGENTS-ai-data-compass.md").exists())
            self.assertFalse((target / "CLAUDE.md").exists())

            accepted = install_assets(
                target, ["agents.md"], root=source_root,
                confirm_agents_adoption=lambda _: True,
            )

            self.assertEqual("installed", accepted.outcomes[0].status)
            self.assertTrue((target / "AGENTS-ai-data-compass.md").is_file())
            self.assertIn(
                "[AGENTS-ai-data-compass.md](AGENTS-ai-data-compass.md)",
                existing_agents.read_text(encoding="utf-8"),
            )
            instruction_lines = [
                line for line in existing_agents.read_text(encoding="utf-8").splitlines()
                if "Read and follow the AI Data Compass instructions" in line
            ]
            self.assertEqual(1, len(instruction_lines))
            self.assertIn("@AGENTS-ai-data-compass.md", (target / "CLAUDE.md").read_text())
            for document in [
                "README.md", "distribution.md", "security-and-privacy.md"
            ]:
                contents = (
                    target / ".ai-data-compass" / "docs" / document
                ).read_text(encoding="utf-8")
                self.assertIn("AGENTS-ai-data-compass.md", contents, document)
                self.assertNotIn("AGENTS.md", contents, document)
            self.assertEqual("custom adapter", (target / "GEMINI.md").read_text())
            self.assertEqual("custom adapter", (target / ".windsurfrules").read_text())
            self.assertEqual([], validate_installation(target))
            manifest = json.loads(
                (target / ".ai-data-compass/manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(
                "AGENTS-ai-data-compass.md", manifest["agent_instructions_file"]
            )

            occupied_skill = target / ".ai-data-compass/skills/security-audit/SKILL.md"
            occupied_skill.parent.mkdir(parents=True)
            occupied_skill.write_text("adopter-owned skill", encoding="utf-8")
            skill_result = install_assets(target, ["security_audit"], root=source_root)
            self.assertEqual("installed", skill_result.outcomes[0].status)
            combined_docs = (
                target / ".ai-data-compass/docs/distribution.md"
            ).read_text(encoding="utf-8")
            self.assertIn("AGENTS-ai-data-compass.md", combined_docs)
            self.assertIn("security-audit-ai-data-compass", combined_docs)
            self.assertNotIn("/skills/security-audit/", combined_docs)
            self.assertEqual([], validate_installation(target))

            repeated = install_assets(target, ["agents.md"], root=source_root)
            self.assertEqual("already_installed", repeated.outcomes[0].status)
            self.assertEqual(1, existing_agents.read_text().count("Read and follow the AI Data Compass"))
            self.assertEqual([], validate_installation(target))

    def test_cli_prompts_before_adopting_existing_agents(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            (target / "AGENTS.md").write_text("Local rules\n", encoding="utf-8")
            with patch("builtins.input", return_value="y"):
                result = main(["init", str(target), "--assets", "agents.md"])

            self.assertEqual(0, result)
            self.assertTrue((target / "AGENTS-ai-data-compass.md").is_file())

    def test_cli_declining_agents_adoption_leaves_asset_uninstalled(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            agents = target / "AGENTS.md"
            original = "Project instructions take precedence.\n"
            agents.write_text(original, encoding="utf-8")

            with patch("builtins.input", return_value="n"), patch("builtins.print"):
                result = main(["init", str(target), "--assets", "agents.md"])

            self.assertEqual(1, result)
            self.assertEqual(original, agents.read_text(encoding="utf-8"))
            self.assertFalse((target / "AGENTS-ai-data-compass.md").exists())
            self.assertFalse((target / "CLAUDE.md").exists())
            self.assertFalse((target / ".ai-data-compass/manifest.json").exists())

    def test_cli_verifies_numbered_agents_supplement_installation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            (target / "AGENTS.md").write_text("Local rules\n", encoding="utf-8")
            occupied = target / agents_supplement_filename()
            occupied.write_text("Adopter-owned file\n", encoding="utf-8")

            with patch("builtins.input", return_value="y"), patch("builtins.print"):
                install_result = main(["init", str(target), "--assets", "agents.md"])
                verify_result = main(["verify", str(target)])

            resolved = agents_supplement_filename(2)
            self.assertEqual(0, install_result)
            self.assertEqual(0, verify_result)
            self.assertTrue((target / resolved).is_file())
            self.assertEqual("Adopter-owned file\n", occupied.read_text(encoding="utf-8"))
            self.assertIn(resolved, (target / "AGENTS.md").read_text(encoding="utf-8"))

    def test_cli_verifies_skill_collision_installation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            occupied = target / ".ai-data-compass/skills/security-audit/SKILL.md"
            occupied.parent.mkdir(parents=True)
            occupied.write_text("Adopter-owned skill\n", encoding="utf-8")

            with patch("builtins.print"):
                install_result = main(
                    ["init", str(target), "--assets", "security_audit"]
                )
                verify_result = main(["verify", str(target)])

            resolved = "security-audit-ai-data-compass"
            self.assertEqual(0, install_result)
            self.assertEqual(0, verify_result)
            self.assertTrue(
                (target / ".ai-data-compass/skills" / resolved / "SKILL.md").is_file()
            )
            self.assertEqual("Adopter-owned skill\n", occupied.read_text(encoding="utf-8"))

    def test_agents_supplement_collision_uses_resolved_name_in_all_documents(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            (target / "AGENTS.md").write_text("Local rules\n", encoding="utf-8")
            existing_supplement = target / "AGENTS-ai-data-compass.md"
            existing_supplement.write_text("Adopter-owned file\n", encoding="utf-8")

            result = install_assets(
                target, ["agents.md"],
                confirm_agents_adoption=lambda _: True,
            )

            resolved = "AGENTS-ai-data-compass-2.md"
            self.assertEqual("installed", result.outcomes[0].status)
            self.assertTrue((target / resolved).is_file())
            self.assertEqual("Adopter-owned file\n", existing_supplement.read_text())
            self.assertIn(f"[{resolved}]({resolved})", (target / "AGENTS.md").read_text())
            self.assertIn(f"@{resolved}", (target / "CLAUDE.md").read_text())
            for document in [
                "README.md", "distribution.md", "security-and-privacy.md"
            ]:
                content = (target / ".ai-data-compass/docs" / document).read_text()
                self.assertIn(resolved, content)
                self.assertNotIn("AGENTS.md", content)
            self.assertEqual([], validate_installation(target))

    def test_existing_claude_adapter_is_extended_without_losing_its_content(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            (target / "AGENTS.md").write_text("Local rules\n", encoding="utf-8")
            claude = target / "CLAUDE.md"
            claude.write_text("# Project Claude settings\nKeep this text.\n", encoding="utf-8")

            result = install_assets(
                target, ["agents.md"],
                confirm_agents_adoption=lambda _: True,
            )

            self.assertEqual("installed", result.outcomes[0].status)
            claude_text = claude.read_text(encoding="utf-8")
            self.assertIn("Keep this text.", claude_text)
            self.assertEqual(1, claude_text.count("@AGENTS-ai-data-compass.md"))
            self.assertEqual([], validate_installation(target))

    def test_agents_adoption_rolls_back_appends_and_new_files_on_commit_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            agents = target / "AGENTS.md"
            original = b"Existing repository instructions.\n"
            agents.write_bytes(original)
            link = os.link

            def fail_manifest(source: str, destination: str, **kwargs) -> None:
                if Path(destination) == target / ".ai-data-compass/manifest.json":
                    raise OSError("synthetic manifest commit failure")
                link(source, destination, **kwargs)

            with patch("ai_data_compass.assets.os.link", side_effect=fail_manifest):
                with self.assertRaisesRegex(OSError, "synthetic manifest commit failure"):
                    install_assets(
                        target, ["agents.md"],
                        confirm_agents_adoption=lambda _: True,
                    )

            self.assertEqual(original, agents.read_bytes())
            self.assertFalse((target / "AGENTS-ai-data-compass.md").exists())
            self.assertFalse((target / "CLAUDE.md").exists())
            self.assertFalse((target / ".ai-data-compass/manifest.json").exists())

    def test_interactive_asset_descriptions_are_column_aligned(self) -> None:
        with patch("builtins.print") as print_mock, patch(
            "builtins.input", return_value="agents.md"
        ), patch.dict(os.environ, {"NO_COLOR": "1"}):
            selected = choose_assets()

        self.assertEqual(["agents.md"], selected)
        expected_options = {
            COMPLETE_ASSET,
            AGENTS_ASSET,
            ALL_SKILLS_ASSET,
            *SKILL_ASSETS,
        }
        option_calls = [
            call.args
            for call in print_mock.call_args_list
            if len(call.args) == 2
            and all(isinstance(argument, str) for argument in call.args)
            and call.args[0].strip().split(maxsplit=1)[0] in expected_options
        ]
        self.assertEqual(
            expected_options,
            {label.strip().split(maxsplit=1)[0] for label, _ in option_calls},
        )
        self.assertEqual(1, len({len(label) for label, _ in option_calls}))

    def test_interactive_menu_reads_skill_options_from_catalog_registry(self) -> None:
        with patch("ai_data_compass.cli.SKILL_ASSETS", {"demo_skill": "demo-skill"}), patch(
            "ai_data_compass.cli.SKILL_DESCRIPTIONS",
            {"demo_skill": "Demo skill and host adapters"},
        ), patch("builtins.print") as print_mock, patch(
            "builtins.input", return_value="demo_skill"
        ), patch.dict(os.environ, {"NO_COLOR": "1"}):
            selected = choose_assets()

        self.assertEqual(["demo_skill"], selected)
        self.assertTrue(
            any(
                len(call.args) == 2
                and call.args[0].strip() == "demo_skill"
                and call.args[1] == "Demo skill and host adapters"
                for call in print_mock.call_args_list
            )
        )

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
            self.assertFalse((target / "AGENTS-ai-data-compass.md").exists())
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
            self.assertEqual(manifest["version"], __version__)
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
            self.assertIn("base (", output)
            self.assertIn("agents.md (", output)
            self.assertIn("security_audit (", output)
            self.assertIn("  - AGENTS.md", output)
            self.assertIn("  - .ai-data-compass/docs/README.md", output)
            self.assertIn(
                "  - .ai-data-compass/skills/security-audit/SKILL.md", output
            )
            self.assertIn("  - .ai-data-compass/manifest.json", output)

    def test_installation_report_uses_resolved_skill_name_for_collisions(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            occupied = target / ".ai-data-compass/skills/security-audit/SKILL.md"
            occupied.parent.mkdir(parents=True)
            occupied.write_text("adopter-owned skill", encoding="utf-8")

            with patch("builtins.print") as print_mock, patch.dict(
                os.environ, {"NO_COLOR": "1"}
            ):
                exit_code = main(
                    ["init", str(target), "--assets", "security_audit"]
                )

            output = "\n".join(
                " ".join(str(argument) for argument in call.args)
                for call in print_mock.call_args_list
            )
            self.assertEqual(0, exit_code)
            self.assertIn("security-audit-ai-data-compass (", output)
            self.assertNotIn("other (", output)

    def test_init_accepts_all_skills_alias(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            exit_code = main(["init", str(target), "--assets", "skills"])

            self.assertEqual(exit_code, 0)
            self.assertTrue(
                (target / ".ai-data-compass" / "skills" / "security-audit" / "SKILL.md").is_file()
            )
            self.assertTrue(
                (
                    target
                    / ".ai-data-compass"
                    / "skills"
                    / "project-review"
                    / "SKILL.md"
                ).is_file()
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
            self.assertEqual(
                manifest["assets"],
                ["base", "agents.md", "documentation_validation", "project_review", "security_audit"],
            )

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

    def test_reinstall_reports_asset_as_already_installed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            source_root = Path(__file__).resolve().parents[1]
            install_assets(target, ["security_audit"], root=source_root)

            result = install_assets(target, ["security_audit"], root=source_root)

            self.assertEqual(["already_installed"], [item.status for item in result.outcomes])
            self.assertEqual([], result.installed)
            self.assertEqual([], validate_installation(target))

    def test_install_upgrades_manifest_from_an_older_package_version(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            source_root = Path(__file__).resolve().parents[1]
            install_assets(target, ["security_audit"], root=source_root)

            updated_version = f"{__version__}.post1"
            with patch("ai_data_compass.assets.__version__", updated_version):
                result = install_assets(target, ["agents.md"], root=source_root)
                manifest = json.loads(
                    (target / ".ai-data-compass/manifest.json").read_text(encoding="utf-8")
                )
                errors = validate_installation(target)

            self.assertEqual("installed", result.outcomes[0].status)
            self.assertEqual(updated_version, manifest["version"])
            self.assertIn("security_audit", manifest["assets"])
            self.assertEqual([], errors)

    def test_init_updates_manifest_version_when_assets_are_already_current(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            source_root = Path(__file__).resolve().parents[1]
            install_assets(target, ["security_audit"], root=source_root)

            updated_version = f"{__version__}.post1"
            with patch("ai_data_compass.assets.__version__", updated_version):
                result = install_assets(target, ["security_audit"], root=source_root)
                manifest = json.loads(
                    (target / ".ai-data-compass/manifest.json").read_text(encoding="utf-8")
                )

            self.assertEqual("installed", result.outcomes[0].status)
            self.assertEqual([Path(".ai-data-compass/manifest.json")], result.installed)
            self.assertEqual(updated_version, manifest["version"])

    def test_identical_script_with_wrong_executable_mode_is_a_conflict(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            source_root = Path(__file__).resolve().parents[1]
            source = (
                source_root
                / ".ai-data-compass/skills/security-audit/scripts/security-surface.sh"
            )
            destination = (
                target
                / ".ai-data-compass/skills/security-audit/scripts/security-surface.sh"
            )
            destination.parent.mkdir(parents=True)
            destination.write_bytes(source.read_bytes())
            destination.chmod(0o644)

            result = install_assets(target, ["security_audit"], root=source_root)

            self.assertEqual("conflict", result.outcomes[0].status)
            self.assertIn(Path(".ai-data-compass/skills/security-audit/scripts/security-surface.sh"),
                          result.outcomes[0].conflicts)
            self.assertFalse(destination.stat().st_mode & 0o111)
            self.assertFalse((target / ".ai-data-compass/manifest.json").exists())

    def test_reinstall_repairs_executable_mode_of_a_registered_script(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            source_root = Path(__file__).resolve().parents[1]
            install_assets(target, ["security_audit"], root=source_root)
            script = (
                target
                / ".ai-data-compass/skills/security-audit/scripts/security-surface.sh"
            )
            script.chmod(0o644)

            result = install_assets(target, ["security_audit"], root=source_root)

            self.assertEqual("installed", result.outcomes[0].status)
            self.assertTrue(script.stat().st_mode & 0o111)
            self.assertEqual([], validate_installation(target))

    def test_install_aborts_and_preserves_concurrent_document_edit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            source_root = Path(__file__).resolve().parents[1]
            install_assets(target, ["agents.md"], root=source_root)
            document = target / ".ai-data-compass/docs/distribution.md"
            original_manifest = (target / ".ai-data-compass/manifest.json").read_bytes()
            occupied = target / ".ai-data-compass/skills/security-audit/SKILL.md"
            occupied.parent.mkdir(parents=True)
            occupied.write_text("adopter-owned skill", encoding="utf-8")
            real_replace = os.replace
            changed = []

            def edit_before_backup(source: str, destination: str) -> None:
                if Path(source) == document and not changed:
                    document.write_bytes(document.read_bytes() + b"\nconcurrent edit\n")
                    changed.append(True)
                real_replace(source, destination)

            with patch("ai_data_compass.assets.os.replace", side_effect=edit_before_backup):
                with self.assertRaises(FileExistsError):
                    install_assets(target, ["security_audit"], root=source_root)

            self.assertEqual([True], changed)
            self.assertIn(b"concurrent edit", document.read_bytes())
            self.assertEqual(
                original_manifest,
                (target / ".ai-data-compass/manifest.json").read_bytes(),
            )
            self.assertEqual("adopter-owned skill", occupied.read_text(encoding="utf-8"))

    def test_install_does_not_replace_a_file_created_during_commit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            source_root = Path(__file__).resolve().parents[1]
            concurrent_file = target / ".ai-data-compass/docs/README.md"
            real_link = os.link
            created = []

            def create_before_link(source: str, destination: str, **kwargs) -> None:
                if Path(destination) == concurrent_file and not created:
                    concurrent_file.write_text("concurrent owner", encoding="utf-8")
                    created.append(True)
                real_link(source, destination, **kwargs)

            with patch("ai_data_compass.assets.os.link", side_effect=create_before_link):
                with self.assertRaises(FileExistsError):
                    install_assets(target, ["security_audit"], root=source_root)

            self.assertEqual([True], created)
            self.assertEqual("concurrent owner", concurrent_file.read_text(encoding="utf-8"))
            self.assertFalse((target / ".ai-data-compass/manifest.json").exists())

    def test_install_handles_cross_device_staging_without_replacing_destinations(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            source_root = Path(__file__).resolve().parents[1]
            real_link = os.link
            forced_cross_device = []

            def link_with_one_cross_device_error(source: str, destination: str, **kwargs) -> None:
                if not forced_cross_device:
                    forced_cross_device.append(True)
                    raise OSError(errno.EXDEV, "synthetic cross-device link")
                real_link(source, destination, **kwargs)

            with patch(
                "ai_data_compass.assets.os.link",
                side_effect=link_with_one_cross_device_error,
            ):
                result = install_assets(target, ["security_audit"], root=source_root)

            self.assertEqual("installed", result.outcomes[0].status)
            self.assertTrue(forced_cross_device)
            self.assertEqual([], validate_installation(target))

    def test_malformed_manifest_source_is_reported_as_conflict(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            source_root = Path(__file__).resolve().parents[1]
            install_assets(target, ["security_audit"], root=source_root)
            manifest_path = target / ".ai-data-compass/manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["files"][0]["source"] = None
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            malformed_manifest = manifest_path.read_bytes()
            validation_errors = validate_installation(target)

            result = install_assets(target, ["agents.md"], root=source_root)

            self.assertTrue(
                any("invalid source path" in error for error in validation_errors)
            )
            self.assertEqual("conflict", result.outcomes[0].status)
            self.assertIn(Path(".ai-data-compass/manifest.json"), result.outcomes[0].conflicts)
            self.assertEqual(malformed_manifest, manifest_path.read_bytes())
            self.assertFalse((target / "AGENTS.md").exists())

    def test_install_fills_missing_files_when_existing_content_matches(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            source_root = Path(__file__).resolve().parents[1]
            source = source_root / ".ai-data-compass" / "docs" / "README.md"
            destination = target / ".ai-data-compass" / "docs" / "README.md"
            destination.parent.mkdir(parents=True)
            destination.write_bytes(source.read_bytes())

            result = install_assets(target, ["security_audit"], root=source_root)

            self.assertEqual("installed", result.outcomes[0].status)
            self.assertIn(Path(".ai-data-compass/docs/README.md"), result.outcomes[0].identical)
            self.assertTrue(
                (target / ".ai-data-compass" / "skills" / "security-audit" / "SKILL.md").is_file()
            )
            self.assertEqual([], validate_installation(target))

    def test_identical_unregistered_asset_is_not_claimed_as_installed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            source_root = Path(__file__).resolve().parents[1]
            for source, relative in _asset_files(["security_audit"], source_root):
                destination = target / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(source.read_bytes())
                destination.chmod(source.stat().st_mode)

            result = install_assets(target, ["security_audit"], root=source_root)

            self.assertEqual("identical", result.outcomes[0].status)
            self.assertEqual([], result.installed)
            self.assertFalse((target / ".ai-data-compass" / "manifest.json").exists())

    def test_conflict_blocks_only_affected_asset(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            source_root = Path(__file__).resolve().parents[1]
            (target / "AGENTS.md").write_text("adopter-owned", encoding="utf-8")

            result = install_assets(
                target,
                ["agents.md", "security_audit"],
                root=source_root,
            )

            self.assertEqual(
                ["conflict", "installed"],
                [item.status for item in result.outcomes],
            )
            self.assertEqual("adopter-owned", (target / "AGENTS.md").read_text(encoding="utf-8"))
            self.assertTrue(
                (target / ".ai-data-compass" / "skills" / "security-audit" / "SKILL.md").is_file()
            )
            manifest = json.loads(
                (target / ".ai-data-compass" / "manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(["base", "security_audit"], manifest["assets"])

    def test_skill_name_collision_renders_markdown_without_changing_sources(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            source_root = Path(__file__).resolve().parents[1]
            occupied = target / ".ai-data-compass/skills/security-audit/SKILL.md"
            occupied.parent.mkdir(parents=True)
            occupied.write_text("adopter-owned skill", encoding="utf-8")
            source_doc = source_root / ".ai-data-compass/docs/distribution.md"
            original_doc = source_doc.read_bytes()

            result = install_assets(target, ["security_audit"], root=source_root)

            resolved_name = "security-audit-ai-data-compass"
            installed_skill = (
                target / ".ai-data-compass/skills" / resolved_name / "SKILL.md"
            )
            self.assertEqual("installed", result.outcomes[0].status)
            self.assertTrue(installed_skill.is_file())
            self.assertEqual("adopter-owned skill", occupied.read_text(encoding="utf-8"))
            self.assertIn(
                f"name: {resolved_name}", installed_skill.read_text(encoding="utf-8")
            )
            self.assertIn(
                f".ai-data-compass/skills/{resolved_name}/",
                (target / ".agents/skills" / resolved_name / "SKILL.md").read_text(
                    encoding="utf-8"
                ),
            )
            rendered_doc = (target / ".ai-data-compass/docs/distribution.md").read_text(
                encoding="utf-8"
            )
            self.assertIn(f".ai-data-compass/skills/{resolved_name}/", rendered_doc)
            for markdown in target.rglob("*.md"):
                content = markdown.read_text(encoding="utf-8")
                for stale_directory in [
                    "/skills/security-audit/",
                    "/security-audit/",
                ]:
                    self.assertNotIn(stale_directory, content, markdown.relative_to(target))
            self.assertIn(
                "security_audit",
                (target / ".ai-data-compass/docs/distribution.md").read_text(
                    encoding="utf-8"
                ),
            )
            self.assertEqual(original_doc, source_doc.read_bytes())

            manifest = json.loads(
                (target / ".ai-data-compass/manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(
                resolved_name, manifest["skill_names"]["security_audit"]
            )
            self.assertEqual([], validate_installation(target))

    def test_skill_collision_reuses_manifest_name_and_updates_managed_docs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            source_root = Path(__file__).resolve().parents[1]
            install_assets(target, ["agents.md"], root=source_root)
            existing_doc = target / ".ai-data-compass/docs/distribution.md"
            canonical_path = target / ".ai-data-compass/skills/security-audit/SKILL.md"
            canonical_path.parent.mkdir(parents=True)
            canonical_path.write_text("adopter-owned skill", encoding="utf-8")

            first = install_assets(target, ["security_audit"], root=source_root)
            resolved_name = "security-audit-ai-data-compass"
            rendered_doc = existing_doc.read_text(encoding="utf-8")
            self.assertIn(resolved_name, rendered_doc)
            self.assertEqual("installed", first.outcomes[0].status)

            second = install_assets(target, ["security_audit"], root=source_root)

            self.assertEqual("already_installed", second.outcomes[0].status)
            self.assertEqual(resolved_name, json.loads(
                (target / ".ai-data-compass/manifest.json").read_text(encoding="utf-8")
            )["skill_names"]["security_audit"])
            self.assertEqual([], validate_installation(target))

    def test_skill_collision_does_not_overwrite_adopter_modified_docs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            source_root = Path(__file__).resolve().parents[1]
            install_assets(target, ["agents.md"], root=source_root)
            doc = target / ".ai-data-compass/docs/distribution.md"
            doc.write_text("adopter-modified documentation", encoding="utf-8")
            occupied = target / ".ai-data-compass/skills/security-audit/SKILL.md"
            occupied.parent.mkdir(parents=True)
            occupied.write_text("adopter-owned skill", encoding="utf-8")

            result = install_assets(target, ["security_audit"], root=source_root)

            self.assertEqual("conflict", result.outcomes[0].status)
            self.assertEqual("adopter-modified documentation", doc.read_text(encoding="utf-8"))
            self.assertFalse(
                (target / ".ai-data-compass/skills/security-audit-ai-data-compass").exists()
            )
            self.assertFalse((target / ".agents/skills/security-audit-ai-data-compass").exists())

    def test_skill_collision_rolls_back_rendered_docs_if_manifest_commit_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            source_root = Path(__file__).resolve().parents[1]
            install_assets(target, ["agents.md"], root=source_root)
            docs = target / ".ai-data-compass/docs"
            original_docs = {
                path.relative_to(target): path.read_bytes()
                for path in docs.glob("*.md")
            }
            occupied = target / ".ai-data-compass/skills/security-audit/SKILL.md"
            occupied.parent.mkdir(parents=True)
            occupied.write_text("adopter-owned skill", encoding="utf-8")
            real_link = os.link
            failed_manifest_link = []

            def fail_manifest_replace(source: str, destination: str, **kwargs) -> None:
                if (
                    Path(destination) == target / ".ai-data-compass/manifest.json"
                    and not failed_manifest_link
                ):
                    failed_manifest_link.append(True)
                    raise OSError("synthetic manifest commit failure")
                real_link(source, destination, **kwargs)

            with patch(
                "ai_data_compass.assets.os.link", side_effect=fail_manifest_replace
            ):
                with self.assertRaisesRegex(OSError, "synthetic manifest commit failure"):
                    install_assets(target, ["security_audit"], root=source_root)

            self.assertEqual(
                original_docs,
                {path.relative_to(target): path.read_bytes() for path in docs.glob("*.md")},
            )
            self.assertFalse(
                (target / ".ai-data-compass/skills/security-audit-ai-data-compass").exists()
            )
            self.assertEqual("adopter-owned skill", occupied.read_text(encoding="utf-8"))

    def test_init_combines_agents_and_all_skills_in_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            main(["init", str(target), "--assets", "agents.md,skills"])

            manifest = json.loads(
                (target / ".ai-data-compass" / "manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(
                manifest["assets"],
                ["base", "agents.md", "documentation_validation", "project_review", "security_audit"],
            )

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
        self.assertEqual(
            ["documentation_validation", "project_review", "security_audit"],
            normalize_assets(["skills"]),
        )
        self.assertEqual(
            ["agents.md", "documentation_validation", "project_review", "security_audit"],
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

            result = install_assets(
                target,
                ["agents.md"],
                root=Path(__file__).resolve().parents[1],
            )

            self.assertEqual("conflict", result.outcomes[0].status)
            self.assertIn(Path(".ai-data-compass/LICENSE"), result.outcomes[0].conflicts)
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
            real_link = os.link
            calls = {"count": 0}

            def fail_on_second_link(source: str, destination: str, **kwargs) -> None:
                calls["count"] += 1
                if calls["count"] == 2:
                    raise OSError("synthetic commit failure")
                real_link(source, destination, **kwargs)

            with patch("ai_data_compass.assets.os.link", side_effect=fail_on_second_link):
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
            ("version", None, "Manifest version is invalid"),
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
            ("license_asset", [], "Unknown license asset"),
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
                exit_code = main(
                    ["init", str(target), "--assets", "security_audit", "--dry-run"]
                )

            output = [str(call.args[0]) for call in print_mock.call_args_list]
            reported_paths = {
                Path(line[2:]) for line in output if line.startswith("- ")
            }
            expected_paths = set(
                planned_assets(
                    normalize_assets(["security_audit"]),
                    root=Path(__file__).resolve().parents[1],
                )
            )
            self.assertEqual(0, exit_code)
            self.assertEqual(expected_paths, reported_paths)
            self.assertEqual([], list(target.iterdir()))

    def test_dry_run_reports_conflicts_without_changing_the_target(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            existing = target / "AGENTS.md"
            existing.write_text("adopter-owned", encoding="utf-8")
            with patch("builtins.print") as print_mock:
                exit_code = main(
                    ["init", str(target), "--assets", "agents.md", "--dry-run"]
                )

            output = "\n".join(str(call.args[0]) for call in print_mock.call_args_list)
            self.assertEqual(1, exit_code)
            self.assertIn("AGENTS.md", output)
            self.assertEqual([existing], list(target.iterdir()))
            self.assertEqual("adopter-owned", existing.read_text(encoding="utf-8"))

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
