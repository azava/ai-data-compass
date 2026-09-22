"""Asset selection and materialization for AI Data Compass."""

from __future__ import annotations

import json
import hashlib
import os
import re
import shutil
import stat
import sysconfig
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Set, Tuple

from . import __version__


BASE_ASSET = "base"
PACKAGE_NAME = "ai-data-compass"
AGENTS_ASSET = "agents.md"
ALL_SKILLS_ASSET = "skills"
COMPLETE_ASSET = "complete"
MANIFEST_RELATIVE_PATH = Path(".ai-data-compass") / "manifest.json"
MANIFEST_FORMAT = 2
SKILL_NAME_SUFFIX = "-ai-data-compass"
AGENTS_INSTRUCTIONS_PATH = Path("AGENTS.md")
CLAUDE_ADAPTER_PATH = Path("CLAUDE.md")
AGENTS_SUPPLEMENT_STEM = "AGENTS-ai-data-compass"
AGENTS_SUPPLEMENT_SUFFIX = ".md"

# Adapter paths live here so installation, validation, and CLI reporting share
# one registry. The bundled source and target relative paths are identical.
AGENT_ADAPTER_PATHS: Tuple[Path, ...] = (
    AGENTS_INSTRUCTIONS_PATH,
    CLAUDE_ADAPTER_PATH,
    Path("GEMINI.md"),
    Path(".cursor/rules/agents.mdc"),
    Path(".github/copilot-instructions.md"),
    Path(".windsurfrules"),
)
AGENT_ADAPTER_TARGETS = frozenset(AGENT_ADAPTER_PATHS)

SKILL_CATALOG_PATH = Path(__file__).with_name("skill_catalog.json")
SKILL_CATALOG = tuple(json.loads(SKILL_CATALOG_PATH.read_text(encoding="utf-8")))
SKILL_ASSETS: Dict[str, str] = {
    entry["asset"]: entry["directory"] for entry in SKILL_CATALOG
}
SKILL_DESCRIPTIONS: Dict[str, str] = {
    entry["asset"]: entry["description"] for entry in SKILL_CATALOG
}


def agents_supplement_filename(index: int = 1) -> str:
    """Return the canonical or numbered supplementary AGENTS filename."""

    if index < 1:
        raise ValueError("Supplement filename index must be positive")
    suffix = "" if index == 1 else f"-{index}"
    return f"{AGENTS_SUPPLEMENT_STEM}{suffix}{AGENTS_SUPPLEMENT_SUFFIX}"


def is_agents_supplement_filename(name: str) -> bool:
    """Return whether *name* follows the supplementary AGENTS naming rule."""

    pattern = (
        re.escape(AGENTS_SUPPLEMENT_STEM)
        + r"(?:-[2-9]|-[1-9][0-9]+)?"
        + re.escape(AGENTS_SUPPLEMENT_SUFFIX)
    )
    return re.fullmatch(pattern, name) is not None


@dataclass
class AssetInstallOutcome:
    """Describe the result of attempting to install one selected asset."""

    asset: str
    status: str
    installed: List[Path] = field(default_factory=list)
    identical: List[Path] = field(default_factory=list)
    conflicts: List[Path] = field(default_factory=list)
    message: Optional[str] = None


@dataclass
class InstallationResult:
    """Collect per-asset outcomes from one init operation."""

    outcomes: List[AssetInstallOutcome]
    skill_names: Dict[str, str] = field(default_factory=dict)

    @property
    def installed(self) -> List[Path]:
        paths: List[Path] = []
        for outcome in self.outcomes:
            for path in outcome.installed:
                if path not in paths:
                    paths.append(path)
        return paths

    @property
    def has_conflicts(self) -> bool:
        return any(outcome.status == "conflict" for outcome in self.outcomes)

ASSET_ALIASES = {
    "agents": AGENTS_ASSET,
    "all_skills": ALL_SKILLS_ASSET,
    "all": COMPLETE_ASSET,
    "full": COMPLETE_ASSET,
}
ASSET_ALIASES.update(
    {canonical_name: asset_name for asset_name, canonical_name in SKILL_ASSETS.items()}
)


def repository_root() -> Path:
    """Return the repository root containing the distributable source assets."""

    checkout_root = Path(__file__).resolve().parents[2]
    if (checkout_root / ".ai-data-compass" / "docs").is_dir():
        return checkout_root

    installed_root = (
        Path(sysconfig.get_path("data")) / "share" / "ai-data-compass" / "assets"
    )
    if (installed_root / ".ai-data-compass" / "docs").is_dir():
        return installed_root

    raise FileNotFoundError("Bundled AI Data Compass assets are not available")


def available_assets() -> List[str]:
    """Return the user-selectable asset names in display order."""

    return [COMPLETE_ASSET, AGENTS_ASSET] + sorted(SKILL_ASSETS) + [ALL_SKILLS_ASSET]


def normalize_assets(values: Sequence[str]) -> List[str]:
    """Normalize comma-separated asset names and expand the skills bundle."""

    selected: List[str] = []
    for value in values:
        for raw_name in value.split(","):
            name = raw_name.strip().lower()
            name = ASSET_ALIASES.get(name, name)
            if not name:
                continue
            if name not in available_assets():
                valid = ", ".join(available_assets())
                raise ValueError(f"Unknown asset '{name}'. Choose from: {valid}")
            if name == COMPLETE_ASSET:
                expanded = [AGENTS_ASSET, ALL_SKILLS_ASSET]
            elif name == ALL_SKILLS_ASSET:
                expanded = [ALL_SKILLS_ASSET]
            else:
                expanded = [name]
            for expanded_name in expanded:
                if expanded_name == ALL_SKILLS_ASSET:
                    skill_names = sorted(SKILL_ASSETS)
                else:
                    skill_names = [expanded_name]
                for selected_name in skill_names:
                    if selected_name not in selected:
                        selected.append(selected_name)
    if not selected:
        raise ValueError("At least one asset must be selected")
    return selected


def _base_files(root: Path) -> List[Tuple[Path, Path]]:
    """Build source-to-target mappings for mandatory shared files."""
    files: List[Tuple[Path, Path]] = []

    # Documentation is a mandatory dependency of every installation.
    docs_root = root / ".ai-data-compass" / "docs"
    for source in sorted(docs_root.glob("*.md")):
        files.append((source, Path(".ai-data-compass") / "docs" / source.name))
    files.append(
        (root / ".ai-data-compass" / "LICENSE", Path(".ai-data-compass") / "LICENSE")
    )
    files.append(
        (
            root / ".ai-data-compass" / "THIRD-PARTY-NOTICES.md",
            Path(".ai-data-compass") / "THIRD-PARTY-NOTICES.md",
        )
    )

    return files


def _selected_asset_files(
    selected: Iterable[str], root: Path, skill_names: Optional[Dict[str, str]] = None,
    *, target: Optional[Path] = None, supplemental_agents: Optional[str] = None,
) -> List[Tuple[Path, Path]]:
    """Build source-to-target mappings for user-selected assets."""

    files: List[Tuple[Path, Path]] = []
    selected_set: Set[str] = set(selected)
    if AGENTS_ASSET in selected_set:
        agent_target = Path(supplemental_agents) if supplemental_agents else AGENTS_INSTRUCTIONS_PATH
        adapter_sources = [
            (root / path, agent_target if path == AGENTS_INSTRUCTIONS_PATH else path)
            for path in AGENT_ADAPTER_PATHS
        ]
        for source, relative in adapter_sources:
            if target is None or relative == agent_target or not (target / relative).exists():
                files.append((source, relative))
        if supplemental_agents:
            files.append((root / AGENTS_INSTRUCTIONS_PATH, AGENTS_INSTRUCTIONS_PATH))
            claude = CLAUDE_ADAPTER_PATH
            if target is not None and (target / claude).is_file():
                files.append((root / claude, claude))

    for asset_name, directory_name in SKILL_ASSETS.items():
        if asset_name not in selected_set:
            continue
        installed_name = (skill_names or {}).get(asset_name, directory_name)
        canonical_root = root / ".ai-data-compass" / "skills" / directory_name
        for source in sorted(canonical_root.rglob("*")):
            if source.is_file():
                relative = source.relative_to(root)
                parts = list(relative.parts)
                parts[2] = installed_name
                files.append((source, Path(*parts)))
        files.extend(
            [
                (
                    root / ".agents" / "skills" / directory_name / "SKILL.md",
                    Path(".agents") / "skills" / installed_name / "SKILL.md",
                ),
                (
                    root / ".claude" / "skills" / directory_name / "SKILL.md",
                    Path(".claude") / "skills" / installed_name / "SKILL.md",
                ),
            ]
        )

    return files


def _asset_files(
    selected: Iterable[str], root: Path, skill_names: Optional[Dict[str, str]] = None
) -> List[Tuple[Path, Path]]:
    """Build source-to-target mappings for shared and selected files."""

    return _base_files(root) + _selected_asset_files(selected, root, skill_names)


def _rendered_bytes(
    source: Path,
    destination: Path,
    root: Path,
    skill_names: Dict[str, str],
    agents_name: Optional[str] = None,
) -> Optional[bytes]:
    """Render resolved asset names in installed Markdown and shell assets."""

    if source.suffix.lower() not in {".md", ".sh"}:
        return None
    relative_source = source.relative_to(root)
    is_skill_file = (
        len(relative_source.parts) >= 3
        and relative_source.parts[:2]
        in {
            (".ai-data-compass", "skills"),
            (".agents", "skills"),
            (".claude", "skills"),
        }
        and relative_source.parts[2] in set(SKILL_ASSETS.values())
    )
    is_installed_markdown = (
        relative_source.parts[:2] == (".ai-data-compass", "docs")
        and source.suffix.lower() == ".md"
    )
    is_instruction_reference_doc = is_installed_markdown and source.name in {
        "README.md",
        "ai-agent-skills.md",
        "tests.md",
        "security-and-privacy.md",
    }
    if not is_skill_file and not is_installed_markdown:
        return None
    content = source.read_bytes()
    rendered = content
    if skill_names:
        for asset_name, canonical_name in SKILL_ASSETS.items():
            canonical = canonical_name.encode("utf-8")
            resolved = skill_names.get(asset_name, canonical_name).encode("utf-8")
            rendered = rendered.replace(canonical, resolved)
    if (
        agents_name
        and agents_name != AGENTS_INSTRUCTIONS_PATH.name
        and is_instruction_reference_doc
    ):
        rendered = rendered.replace(
            AGENTS_INSTRUCTIONS_PATH.name.encode("utf-8"),
            agents_name.encode("utf-8"),
        )
    return rendered if rendered != content else None


def _resolved_skill_names(
    target: Path, selected: Sequence[str], root: Path, manifest: Optional[dict]
) -> Dict[str, str]:
    """Choose an unused skill directory name, reusing the manifest choice."""

    result: Dict[str, str] = {}
    recorded = {} if manifest is None else manifest.get("skill_names", {})
    for asset, canonical in SKILL_ASSETS.items():
        if asset not in selected:
            continue
        prior = recorded.get(asset) if isinstance(recorded, dict) else None
        if isinstance(prior, str) and prior:
            result[asset] = prior
            continue
        candidates = [canonical, canonical + SKILL_NAME_SUFFIX, canonical + SKILL_NAME_SUFFIX + "-2"]
        for candidate in candidates:
            files = _selected_asset_files([asset], root, {asset: candidate})
            available = True
            for source, relative in files:
                try:
                    _validate_destination(target, relative)
                except ValueError:
                    available = False
                    break
                path = target / relative
                if path.is_symlink() or (path.exists() and not path.is_file()):
                    available = False
                    break
                if path.is_file():
                    content = _rendered_bytes(source, relative, root, {asset: candidate})
                    expected = content if content is not None else source.read_bytes()
                    if path.read_bytes() != expected:
                        available = False
                        break
            if available:
                result[asset] = candidate
                break
        else:
            # Continue deterministic suffix allocation if the first fallback is occupied.
            index = 3
            while True:
                candidate = f"{canonical}{SKILL_NAME_SUFFIX}-{index}"
                files = _selected_asset_files([asset], root, {asset: candidate})
                if not all(_destination_is_safe(target, relative) for _, relative in files):
                    result[asset] = canonical
                    break
                if all(
                    not (target / relative).exists()
                    and not (target / relative).is_symlink()
                    for _, relative in files
                ):
                    result[asset] = candidate
                    break
                index += 1
    return result


def _destination_is_safe(target: Path, relative: Path) -> bool:
    try:
        _validate_destination(target, relative)
    except ValueError:
        return False
    return True


def _license_asset(relative_path: Path) -> str:
    """Return the asset that licenses a materialized file."""

    for asset_name, directory_name in SKILL_ASSETS.items():
        if (len(relative_path.parts) > 2
                and relative_path.parts[:2] == (".ai-data-compass", "skills")
                and relative_path.parts[2].startswith(directory_name)):
            return asset_name
        if (len(relative_path.parts) > 2
                and relative_path.parts[:2] in {(".agents", "skills"), (".claude", "skills")}
                and relative_path.parts[2].startswith(directory_name)):
            return asset_name
    return BASE_ASSET


def _file_metadata(path: Path, contents: Optional[bytes] = None) -> Dict[str, object]:
    """Return stable integrity metadata for a file."""

    digest = hashlib.sha256()
    if contents is None:
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
    else:
        digest.update(contents)
    file_stat = path.stat()
    return {
        "sha256": digest.hexdigest(),
        "size": len(contents) if contents is not None else file_stat.st_size,
        "executable": bool(stat.S_IMODE(file_stat.st_mode) & 0o111),
    }


@contextmanager
def _installation_lock(target: Path):
    """Serialize installations targeting the same repository."""

    lock_id = hashlib.sha256(str(target).encode("utf-8")).hexdigest()[:20]
    lock_path = target.parent / f".ai-data-compass-lock-{lock_id}"
    if lock_path.is_symlink():
        raise OSError(f"Installation lock is a symlink: {lock_path}")
    if os.name == "nt":
        lock_file = lock_path.open("a+b")
    else:
        lock_flags = os.O_CREAT | os.O_RDWR
        if hasattr(os, "O_NOFOLLOW"):
            lock_flags |= os.O_NOFOLLOW
        lock_fd = os.open(lock_path, lock_flags, 0o600)
        lock_file = os.fdopen(lock_fd, "r+b")
    try:
        if os.name == "nt":
            import msvcrt

            lock_file.seek(0)
            lock_file.write(b"0")
            lock_file.flush()
            lock_file.seek(0)
            msvcrt.locking(lock_file.fileno(), msvcrt.LK_LOCK, 1)
        else:
            import fcntl

            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            if os.name == "nt":
                msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
    finally:
        lock_file.close()


def _validate_destination(target: Path, relative_target: Path) -> None:
    """Reject destination paths that traverse symlinks or leave the target."""

    if relative_target.is_absolute() or ".." in relative_target.parts:
        raise ValueError(f"Asset destination is outside target: {relative_target}")

    current = target
    for component in relative_target.parts[:-1]:
        current /= component
        if current.is_symlink():
            raise ValueError(f"Asset destination traverses a symlink: {relative_target}")

    try:
        (target / relative_target).parent.resolve().relative_to(target.resolve())
    except ValueError as error:
        raise ValueError(f"Asset destination is outside target: {relative_target}") from error


def _manifest(
    selected: Sequence[str],
    files: Sequence[Tuple[Path, Path]],
    source_root: Path,
    skill_names: Optional[Dict[str, str]] = None,
    content_overrides: Optional[Dict[Path, bytes]] = None,
    agents_name: Optional[str] = None,
) -> dict:
    """Build a deterministic manifest for the installed assets."""

    entries = [
        {
            "path": relative_target.as_posix(),
            "license_asset": _license_asset(relative_target),
            "source": source.relative_to(source_root).as_posix(),
        **_file_metadata(
            source,
            (content_overrides or {}).get(
                relative_target,
                _rendered_bytes(
                    source, relative_target, source_root, skill_names or {}, agents_name
                ),
            ),
        ),
        }
                for source, relative_target in files
            ]
    licenses = [{"asset": BASE_ASSET, "path": ".ai-data-compass/LICENSE"}]
    notices = [
        {
            "asset": BASE_ASSET,
            "path": ".ai-data-compass/THIRD-PARTY-NOTICES.md",
        }
    ]
    for asset_name, directory_name in SKILL_ASSETS.items():
        if asset_name not in selected:
            continue
        licenses.append(
            {
                "asset": asset_name,
                "path": f".ai-data-compass/skills/{(skill_names or {}).get(asset_name, directory_name)}/LICENSE",
            }
        )
        notices.append(
            {
                "asset": asset_name,
                "path": f".ai-data-compass/skills/{(skill_names or {}).get(asset_name, directory_name)}/THIRD-PARTY-NOTICES.md",
            }
        )
    return {
        "format": MANIFEST_FORMAT,
        "package": PACKAGE_NAME,
        "version": __version__,
        "assets": [BASE_ASSET] + list(selected),
        "skill_names": skill_names or {},
        "agent_instructions_file": (
            (agents_name or AGENTS_INSTRUCTIONS_PATH.name)
            if AGENTS_ASSET in selected
            else None
        ),
        "files": entries,
        "licenses": licenses,
        "third_party_notices": notices,
    }


def validate_installation(target: Path) -> List[str]:
    """Validate an installed asset manifest and return metadata-only errors."""

    if not target.is_dir():
        return [f"Target directory does not exist: {target}"]
    manifest_path = target / MANIFEST_RELATIVE_PATH
    if not manifest_path.is_file():
        return [f"Manifest not found: {MANIFEST_RELATIVE_PATH}"]
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return ["Manifest could not be read as JSON"]
    if not isinstance(manifest, dict):
        return ["Manifest root must be a JSON object"]

    errors: List[str] = []
    if manifest.get("format") != MANIFEST_FORMAT:
        errors.append("Unsupported manifest format")
    if manifest.get("package") != PACKAGE_NAME:
        errors.append("Manifest package does not match this package")
    if manifest.get("version") != __version__:
        errors.append("Manifest version does not match this package")

    assets = manifest.get("assets")
    if not isinstance(assets, list) or not assets or assets[0] != BASE_ASSET:
        errors.append("Manifest assets entry is invalid")
        assets = []
    selected = [asset for asset in assets if asset != BASE_ASSET]
    known_assets = {AGENTS_ASSET} | set(SKILL_ASSETS)
    invalid_assets = [
        asset
        for asset in selected
        if not isinstance(asset, str) or asset not in known_assets
    ]
    if invalid_assets:
        errors.append("Manifest contains an unknown asset")
    if all(isinstance(asset, str) for asset in selected) and len(selected) != len(
        set(selected)
    ):
        errors.append("Manifest contains duplicate assets")
    selected = [asset for asset in selected if isinstance(asset, str) and asset in known_assets]
    skill_names = manifest.get("skill_names")
    if skill_names is None:
        skill_names = {asset: SKILL_ASSETS[asset] for asset in selected if asset in SKILL_ASSETS}
    if not isinstance(skill_names, dict):
        errors.append("Manifest skill_names entry is invalid")
        skill_names = {}
    expected_skill_assets = set(selected) & set(SKILL_ASSETS)
    if set(skill_names) != expected_skill_assets:
        errors.append("Manifest skill_names do not match selected skills")
    for asset_name, name in skill_names.items():
        canonical = SKILL_ASSETS.get(asset_name, "")
        if (
            not isinstance(name, str)
            or not name
            or Path(name).name != name
            or (name != canonical and not name.startswith(canonical + SKILL_NAME_SUFFIX))
        ):
            errors.append("Manifest contains an invalid resolved skill name")

    if not isinstance(manifest.get("files"), list):
        return errors + ["Manifest files entry is invalid"]

    entries_by_path: Dict[str, dict] = {}
    for entry in manifest["files"]:
        relative = entry.get("path") if isinstance(entry, dict) else None
        if not isinstance(relative, str):
            errors.append("Manifest contains a file entry without a path")
            continue
        if relative in entries_by_path:
            errors.append(f"Manifest contains a duplicate file entry: {relative}")
        entries_by_path[relative] = entry
        path = (target / relative).resolve()
        try:
            path.relative_to(target.resolve())
        except ValueError:
            errors.append(f"Manifest path escapes target: {relative}")
            continue
        if not path.is_file():
            errors.append(f"Installed file is missing: {relative}")
            continue
        metadata = _file_metadata(path)
        for key in ("sha256", "size", "executable"):
            if metadata[key] != entry.get(key):
                errors.append(f"Installed file metadata differs: {relative} ({key})")

        license_asset = entry.get("license_asset")
        if license_asset not in {BASE_ASSET} | set(selected):
            errors.append(f"Unknown license asset for file: {relative}")
        elif license_asset != _license_asset(Path(relative)):
            errors.append(f"License asset does not match file path: {relative}")

    try:
        source_root = repository_root()
        expected_files = {
            relative.as_posix()
            for _, relative in _base_files(source_root)
        }
        expected_files.update(
            relative.as_posix()
            for _, relative in _selected_asset_files(
                [asset for asset in selected if asset != AGENTS_ASSET],
                source_root,
                skill_names,
            )
        )
        actual_files = set(entries_by_path)
        agent_paths = {path.as_posix() for path in AGENT_ADAPTER_TARGETS}
        agent_paths.update(
            path for path in actual_files
            if is_agents_supplement_filename(path)
        )
        if AGENTS_ASSET in selected:
            present_agent_paths = actual_files & agent_paths
            agent_instruction_file = manifest.get(
                "agent_instructions_file", AGENTS_INSTRUCTIONS_PATH.name
            )
            if (
                not isinstance(agent_instruction_file, str)
                or not (
                    agent_instruction_file == AGENTS_INSTRUCTIONS_PATH.name
                    or is_agents_supplement_filename(agent_instruction_file)
                )
                or agent_instruction_file not in present_agent_paths
            ):
                errors.append("Manifest agent instruction file is missing")
            if (
                agent_instruction_file != AGENTS_INSTRUCTIONS_PATH.name
                and AGENTS_INSTRUCTIONS_PATH.as_posix() not in present_agent_paths
            ):
                errors.append(
                    f"Manifest host {AGENTS_INSTRUCTIONS_PATH.name} file is missing"
                )
            expected_files.update(actual_files & agent_paths)
        for relative in sorted(expected_files - actual_files):
            errors.append(f"Manifest file entry is missing: {relative}")
        for relative in sorted(actual_files - expected_files):
            errors.append(f"Manifest contains an unexpected file: {relative}")
    except FileNotFoundError as error:
        errors.append(str(error))

    expected_licenses = {
        BASE_ASSET: ".ai-data-compass/LICENSE",
    }
    expected_notices = {
        BASE_ASSET: ".ai-data-compass/THIRD-PARTY-NOTICES.md",
    }
    for asset_name, directory_name in SKILL_ASSETS.items():
        if asset_name in selected:
            directory_name = skill_names.get(asset_name, directory_name)
            expected_licenses[asset_name] = (
                f".ai-data-compass/skills/{directory_name}/LICENSE"
            )
            expected_notices[asset_name] = (
                f".ai-data-compass/skills/{directory_name}/THIRD-PARTY-NOTICES.md"
            )

    for collection in ("licenses", "third_party_notices"):
        values = manifest.get(collection)
        if not isinstance(values, list):
            errors.append(f"Manifest {collection} entry is invalid")
            continue
        expected = expected_licenses if collection == "licenses" else expected_notices
        actual: Dict[str, str] = {}
        for item in values:
            relative = item.get("path") if isinstance(item, dict) else None
            asset_name = item.get("asset") if isinstance(item, dict) else None
            if not isinstance(asset_name, str) or not isinstance(relative, str):
                errors.append(f"Manifest {collection} entry is invalid")
                continue
            if asset_name in actual:
                errors.append(f"Manifest {collection} contains a duplicate asset")
            actual[asset_name] = relative
            if not (target / relative).is_file():
                errors.append(f"Manifest {collection} file is missing: {relative}")
        if actual != expected:
            errors.append(f"Manifest {collection} entries do not match selected assets")

    for asset_name, relative in expected_licenses.items():
        for path, entry in entries_by_path.items():
            if entry.get("license_asset") == asset_name and path == relative:
                break
        else:
            errors.append(f"License file is not listed for asset: {asset_name}")
    return errors


def install_assets(
    target: Path,
    selected: Sequence[str],
    *,
    root: Optional[Path] = None,
    confirm_agents_adoption: Optional[Callable[[Path], bool]] = None,
) -> InstallationResult:
    """Install selected assets independently, without overwriting conflicts."""

    target = target.resolve()
    with _installation_lock(target):
        return _install_assets(target, selected, root=root, confirm_agents_adoption=confirm_agents_adoption)


def _install_assets(
    target: Path,
    selected: Sequence[str],
    *,
    root: Optional[Path] = None,
    dry_run: bool = False,
    confirm_agents_adoption: Optional[Callable[[Path], bool]] = None,
) -> InstallationResult:
    """Install assets while the caller holds the per-target lock."""

    source_root = root or repository_root()
    all_files = _asset_files(selected, source_root)
    for source, _ in all_files:
        if not source.is_file():
            raise FileNotFoundError(f"Asset source file does not exist: {source}")
    try:
        _validate_destination(target, MANIFEST_RELATIVE_PATH)
    except ValueError:
        manifest, manifest_error = None, True
    else:
        manifest, manifest_error = _read_install_manifest(target)
    outcomes: List[AssetInstallOutcome] = []
    resolved_skill_names: Dict[str, str] = {}
    virtual_files: Dict[Path, str] = {}
    for asset in selected:
        skill_names = (
            dict(manifest.get("skill_names", {}))
            if manifest is not None and isinstance(manifest.get("skill_names", {}), dict)
            else {}
        )
        skill_names.update(_resolved_skill_names(target, [asset], source_root, manifest))
        resolved_skill_names.update(skill_names)
        supplemental_agents: Optional[str] = None
        overrides: Dict[Path, bytes] = {}
        if asset == AGENTS_ASSET and (target / AGENTS_INSTRUCTIONS_PATH).is_file():
            existing_agents = target / AGENTS_INSTRUCTIONS_PATH
            bundled_agents = source_root / AGENTS_INSTRUCTIONS_PATH
            if existing_agents.read_bytes() != bundled_agents.read_bytes():
                prior_paths = [
                    entry.get("path", "") for entry in (manifest or {}).get("files", [])
                    if isinstance(entry, dict)
                ]
                existing_content = existing_agents.read_bytes()
                prior_supplement = next(
                    (
                        path for path in prior_paths
                        if is_agents_supplement_filename(path)
                        and f"({path})".encode("utf-8") in existing_content
                    ),
                    None,
                )
                approved_before = prior_supplement in prior_paths
                approved = approved_before or bool(
                    confirm_agents_adoption and confirm_agents_adoption(existing_agents)
                )
                if not approved:
                    outcomes.append(AssetInstallOutcome(
                        asset=asset,
                        status="conflict",
                        conflicts=[AGENTS_INSTRUCTIONS_PATH],
                        message=(
                            "Dry run: user consent is required to append the instruction."
                            if dry_run else
                            "Appending the AI Data Compass instruction was declined or not authorized."
                        ),
                    ))
                    continue
                if approved_before and prior_supplement:
                    supplemental_agents = prior_supplement
                if supplemental_agents is None:
                    suffix = 1
                    supplemental_agents = agents_supplement_filename(suffix)
                    while (target / supplemental_agents).exists():
                        suffix += 1
                        supplemental_agents = agents_supplement_filename(suffix)
                directive = (
                    "\n\nRead and follow the AI Data Compass instructions in "
                    f"[{supplemental_agents}]({supplemental_agents}).\n"
                )
                if f"({supplemental_agents})".encode("utf-8") not in existing_content:
                    overrides[AGENTS_INSTRUCTIONS_PATH] = existing_content + directive.encode("utf-8")
                else:
                    overrides[AGENTS_INSTRUCTIONS_PATH] = existing_content
                claude = target / CLAUDE_ADAPTER_PATH
                if claude.is_file():
                    current = claude.read_bytes()
                    reference = f"\n@{supplemental_agents}\n".encode("utf-8")
                    if reference.strip() not in current:
                        overrides[CLAUDE_ADAPTER_PATH] = current.rstrip() + reference
                else:
                    claude_source = (source_root / CLAUDE_ADAPTER_PATH).read_bytes().rstrip()
                    overrides[CLAUDE_ADAPTER_PATH] = claude_source + f"\n@{supplemental_agents}\n".encode("utf-8")
        agents_name = supplemental_agents
        if agents_name is None and asset == AGENTS_ASSET:
            agents_name = AGENTS_INSTRUCTIONS_PATH.name
        if agents_name is None and manifest is not None and AGENTS_ASSET in manifest.get("assets", []):
            agents_name = manifest.get(
                "agent_instructions_file", AGENTS_INSTRUCTIONS_PATH.name
            )
        files = _base_files(source_root) + _selected_asset_files(
            [asset], source_root, skill_names, target=target,
            supplemental_agents=supplemental_agents,
        )
        if supplemental_agents and CLAUDE_ADAPTER_PATH not in overrides:
            files = [pair for pair in files if pair[1] != CLAUDE_ADAPTER_PATH]
        unsafe_destinations: List[Path] = []
        for _, relative_target in files:
            try:
                _validate_destination(target, relative_target)
            except ValueError:
                unsafe_destinations.append(relative_target)
        if unsafe_destinations:
            outcomes.append(
                AssetInstallOutcome(
                    asset=asset,
                    status="conflict",
                    conflicts=unsafe_destinations,
                )
            )
            continue

        if manifest_error:
            outcomes.append(
                AssetInstallOutcome(
                    asset=asset,
                    status="conflict",
                    conflicts=[MANIFEST_RELATIVE_PATH],
                )
            )
            continue

        outcome, manifest = _install_one_asset(
            target,
            asset,
            files,
            source_root,
            manifest,
            virtual_files,
            dry_run,
            skill_names,
            overrides,
            agents_name,
        )
        outcomes.append(outcome)
        if dry_run and outcome.status == "would_install":
            for source, relative_target in files:
                virtual_files[relative_target] = _file_metadata(
                    source,
                    _rendered_bytes(
                        source, relative_target, source_root, skill_names, agents_name
                    ),
                )["sha256"]
    return InstallationResult(outcomes, resolved_skill_names)


def plan_assets(
    target: Path,
    selected: Sequence[str],
    *,
    root: Optional[Path] = None,
) -> InstallationResult:
    """Inspect per-asset installation outcomes without writing to the target."""

    return _install_assets(target.resolve(), selected, root=root, dry_run=True)


def _read_install_manifest(target: Path) -> Tuple[Optional[dict], bool]:
    """Read a compatible manifest, returning a conflict flag for unsafe state."""

    path = target / MANIFEST_RELATIVE_PATH
    if not path.exists() and not path.is_symlink():
        return None, False
    if path.is_symlink() or not path.is_file():
        return None, True
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None, True
    if not isinstance(manifest, dict):
        return None, True
    if (
        manifest.get("format") != MANIFEST_FORMAT
        or manifest.get("package") != PACKAGE_NAME
        or manifest.get("version") != __version__
    ):
        return None, True
    assets = manifest.get("assets")
    entries = manifest.get("files")
    known_assets = {BASE_ASSET, AGENTS_ASSET} | set(SKILL_ASSETS)
    if (
        not isinstance(assets, list)
        or not assets
        or assets[0] != BASE_ASSET
        or any(not isinstance(asset, str) or asset not in known_assets for asset in assets)
        or len(assets) != len(set(assets))
        or not isinstance(entries, list)
        or not isinstance(manifest.get("skill_names", {}), dict)
    ):
        return None, True
    skill_names = manifest.get("skill_names")
    if skill_names is None:
        skill_names = {
            asset: SKILL_ASSETS[asset] for asset in assets if asset in SKILL_ASSETS
        }
        manifest["skill_names"] = skill_names
    selected_skills = set(assets) & set(SKILL_ASSETS)
    if set(skill_names) != selected_skills or any(
        not isinstance(name, str)
        or not name
        or Path(name).name != name
        or (
            name != SKILL_ASSETS[asset]
            and not name.startswith(SKILL_ASSETS[asset] + SKILL_NAME_SUFFIX)
        )
        for asset, name in skill_names.items()
        if asset in SKILL_ASSETS
    ):
        return None, True
    entry_paths: Set[str] = set()
    for entry in entries:
        if (
            not isinstance(entry, dict)
            or not isinstance(entry.get("path"), str)
            or not isinstance(entry.get("sha256"), str)
        ):
            return None, True
        if entry["path"] in entry_paths:
            return None, True
        entry_paths.add(entry["path"])
    return manifest, False


def _manifest_entries(manifest: Optional[dict]) -> Dict[str, dict]:
    if manifest is None:
        return {}
    return {entry["path"]: entry for entry in manifest["files"]}


def _install_one_asset(
    target: Path,
    asset: str,
    files: Sequence[Tuple[Path, Path]],
    source_root: Path,
    previous_manifest: Optional[dict],
    virtual_files: Dict[Path, str],
    dry_run: bool,
    skill_names: Dict[str, str],
    overrides: Optional[Dict[Path, bytes]] = None,
    agents_name: Optional[str] = None,
) -> Tuple[AssetInstallOutcome, Optional[dict]]:
    """Preflight, stage, and commit one shared-base-plus-selected asset unit."""

    overrides = overrides or {}
    expected_hashes = {
        relative_target: _file_metadata(
            source,
            overrides.get(
                relative_target,
                _rendered_bytes(
                    source, relative_target, source_root, skill_names, agents_name
                ),
            ),
        )["sha256"]
        for source, relative_target in files
    }
    manifest_entries = _manifest_entries(previous_manifest)
    conflicts: List[Path] = []
    identical: List[Path] = []
    missing: List[Tuple[Path, Path]] = []
    replacements: List[Tuple[Path, Path]] = []

    for source, relative_target in files:
        destination = target / relative_target
        if relative_target in virtual_files:
            if virtual_files[relative_target] == expected_hashes[relative_target]:
                identical.append(relative_target)
            else:
                conflicts.append(relative_target)
        elif destination.is_symlink():
            conflicts.append(relative_target)
        elif not destination.exists():
            missing.append((source, relative_target))
        elif not destination.is_file():
            conflicts.append(relative_target)
        elif _file_metadata(destination)["sha256"] == expected_hashes[relative_target]:
            identical.append(relative_target)
        elif relative_target in overrides:
            replacements.append((source, relative_target))
        elif (
            relative_target.parts[:2] == (".ai-data-compass", "docs")
            and relative_target.as_posix() in manifest_entries
            and _file_metadata(destination)["sha256"]
            == manifest_entries[relative_target.as_posix()].get("sha256")
        ):
            replacements.append((source, relative_target))
        else:
            conflicts.append(relative_target)

    if conflicts:
        return (
            AssetInstallOutcome(
                asset,
                "conflict",
                identical=identical,
                conflicts=conflicts,
            ),
            previous_manifest,
        )

    was_registered = (
        previous_manifest is not None
        and asset in previous_manifest["assets"]
        and BASE_ASSET in previous_manifest["assets"]
        and all(
            relative.as_posix() in manifest_entries
            and manifest_entries[relative.as_posix()].get("sha256")
            == expected_hashes[relative]
            for _, relative in files
        )
    )
    if not missing and not replacements:
        status = "already_installed" if was_registered else "identical"
        return AssetInstallOutcome(asset, status, identical=identical), previous_manifest

    old_assets = (
        []
        if previous_manifest is None
        else [value for value in previous_manifest["assets"] if value != BASE_ASSET]
    )
    merged_assets = old_assets[:]
    if asset not in merged_assets:
        merged_assets.append(asset)
    merged_skill_names = {} if previous_manifest is None else dict(previous_manifest.get("skill_names", {}))
    merged_skill_names.update(skill_names)
    merged_by_path: Dict[Path, Path] = {}
    for entry in (previous_manifest or {}).get("files", []):
        relative = Path(entry["path"])
        source_relative = Path(entry.get("source", entry["path"]))
        source = (source_root / source_relative).resolve()
        try:
            source.relative_to(source_root.resolve())
        except ValueError:
            continue
        if not source_relative.is_absolute() and source.is_file():
            merged_by_path[relative] = source
    for source, relative in files:
        merged_by_path[relative] = source
    merged_files = [(source, relative) for relative, source in merged_by_path.items()]
    new_manifest = _manifest(
        merged_assets, merged_files, source_root, merged_skill_names, overrides,
        agents_name,
    )

    old_entries = _manifest_entries(previous_manifest)
    new_entries = {entry["path"]: entry for entry in new_manifest["files"]}
    generated_paths = set(new_entries)
    transaction_paths = {relative.as_posix() for _, relative in files}
    replacement_targets = {relative for _, relative in replacements}
    for relative in transaction_paths - {path.as_posix() for path in replacement_targets}:
        destination = target / relative
        if destination.is_file():
            new_entries[relative].update(_file_metadata(destination))
    for path, entry in old_entries.items():
        if path not in transaction_paths:
            new_entries[path] = entry
    ordered_paths = [entry["path"] for entry in new_manifest["files"]]
    ordered_paths.extend(path for path in old_entries if path not in generated_paths)
    new_manifest["files"] = [new_entries[path] for path in ordered_paths]

    if dry_run:
        return (
            AssetInstallOutcome(
                asset,
                "would_install",
                installed=[relative for _, relative in missing + replacements]
                + [MANIFEST_RELATIVE_PATH],
                identical=identical,
            ),
            new_manifest,
        )

    stage = Path(
        tempfile.mkdtemp(
            prefix=".ai-data-compass-install-",
            dir=str(target.parent),
        )
    )
    committed_paths: List[Path] = []
    created_directories: List[Path] = []
    try:
        for source, relative_target in missing + replacements:
            staged = stage / relative_target
            staged.parent.mkdir(parents=True, exist_ok=True)
            rendered = overrides.get(
                relative_target,
                _rendered_bytes(
                    source, relative_target, source_root, merged_skill_names, agents_name
                ),
            )
            if rendered is None:
                shutil.copy2(source, staged)
            else:
                staged.write_bytes(rendered)
                shutil.copystat(source, staged)

        staged_manifest = stage / MANIFEST_RELATIVE_PATH
        staged_manifest.parent.mkdir(parents=True, exist_ok=True)
        staged_manifest.write_text(
            json.dumps(new_manifest, indent=2) + "\n",
            encoding="utf-8",
        )

        backups: List[Tuple[Path, Path]] = []
        replacement_set = {relative for _, relative in replacements}
        for _, relative_target in missing + replacements:
            _validate_destination(target, relative_target)
            destination = target / relative_target
            if relative_target in replacement_set and destination.is_file() and not destination.is_symlink():
                backup = stage / "previous" / relative_target
                backup.parent.mkdir(parents=True, exist_ok=True)
                os.replace(destination, backup)
                backups.append((destination, backup))
            elif destination.exists() or destination.is_symlink():
                raise FileExistsError(
                    f"Asset destination changed during installation: {relative_target}"
                )
            _make_parent_directories(destination.parent, created_directories)
            os.replace(stage / relative_target, destination)
            committed_paths.append(destination)

        manifest_path = target / MANIFEST_RELATIVE_PATH
        if previous_manifest is None:
            if manifest_path.exists() or manifest_path.is_symlink():
                raise FileExistsError(
                    "Installation manifest changed during installation: "
                    f"{MANIFEST_RELATIVE_PATH}"
                )
        else:
            current_manifest, current_error = _read_install_manifest(target)
            if current_error or current_manifest != previous_manifest:
                raise FileExistsError(
                    "Installation manifest changed during installation: "
                    f"{MANIFEST_RELATIVE_PATH}"
                )
        _make_parent_directories(manifest_path.parent, created_directories)
        os.replace(staged_manifest, manifest_path)
    except Exception as install_error:
        rollback_failures: List[Path] = []
        for path in reversed(committed_paths):
            try:
                path.unlink()
            except OSError:
                rollback_failures.append(path)
        for destination, backup in reversed(locals().get("backups", [])):
            try:
                if backup.exists():
                    os.replace(backup, destination)
            except OSError:
                rollback_failures.append(destination)
        for directory in sorted(created_directories, key=lambda item: len(item.parts), reverse=True):
            try:
                directory.rmdir()
            except OSError:
                pass
        if rollback_failures:
            failed_paths = ", ".join(path.as_posix() for path in rollback_failures)
            raise OSError(
                "Asset installation failed and rollback could not remove: "
                f"{failed_paths}"
            ) from install_error
        raise
    finally:
        shutil.rmtree(stage, ignore_errors=True)

    return AssetInstallOutcome(
        asset,
        "installed",
        installed=[relative for _, relative in missing + replacements] + [MANIFEST_RELATIVE_PATH],
        identical=identical,
    ), new_manifest


def _make_parent_directories(parent: Path, created: List[Path]) -> None:
    """Create missing destination directories and record them for rollback."""

    if parent.exists():
        return
    missing: List[Path] = []
    current = parent
    while not current.exists():
        missing.append(current)
        current = current.parent
    parent.mkdir(parents=True, exist_ok=True)
    created.extend(missing)


def planned_assets(
    selected: Sequence[str],
    *,
    root: Optional[Path] = None,
) -> List[Path]:
    """Return target paths that would be installed for selected assets."""

    source_root = root or repository_root()
    planned = [relative_target for _, relative_target in _asset_files(selected, source_root)]
    planned.append(MANIFEST_RELATIVE_PATH)
    return planned
