"""Asset selection and materialization for AI Data Compass."""

from __future__ import annotations

import json
import hashlib
import os
import shutil
import stat
import sysconfig
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

from . import __version__


BASE_ASSET = "base"
PACKAGE_NAME = "ai-data-compass"
AGENTS_ASSET = "agents.md"
ALL_SKILLS_ASSET = "skills"
COMPLETE_ASSET = "complete"
MANIFEST_RELATIVE_PATH = Path(".ai-data-compass") / "manifest.json"
MANIFEST_FORMAT = 2

SKILL_ASSETS: Dict[str, str] = {
    "security_audit": "security-audit",
}

ASSET_ALIASES = {
    "agents": AGENTS_ASSET,
    "all_skills": ALL_SKILLS_ASSET,
    "security-audit": "security_audit",
    "all": COMPLETE_ASSET,
    "full": COMPLETE_ASSET,
}


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


def _asset_files(selected: Iterable[str], root: Path) -> List[Tuple[Path, Path]]:
    """Build source-to-target mappings for selected assets."""

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

    selected_set: Set[str] = set(selected)
    if AGENTS_ASSET in selected_set:
        files.extend(
            [
                (root / "AGENTS.md", Path("AGENTS.md")),
                (root / "CLAUDE.md", Path("CLAUDE.md")),
                (root / "GEMINI.md", Path("GEMINI.md")),
                (
                    root / ".cursor" / "rules" / "agents.mdc",
                    Path(".cursor") / "rules" / "agents.mdc",
                ),
                (
                    root / ".github" / "copilot-instructions.md",
                    Path(".github") / "copilot-instructions.md",
                ),
                (root / ".windsurfrules", Path(".windsurfrules")),
            ]
        )

    for asset_name, directory_name in SKILL_ASSETS.items():
        if asset_name not in selected_set:
            continue
        canonical_root = root / ".ai-data-compass" / "skills" / directory_name
        for source in sorted(canonical_root.rglob("*")):
            if source.is_file():
                relative = source.relative_to(root)
                files.append((source, relative))
        files.extend(
            [
                (
                    root / ".agents" / "skills" / directory_name / "SKILL.md",
                    Path(".agents") / "skills" / directory_name / "SKILL.md",
                ),
                (
                    root / ".claude" / "skills" / directory_name / "SKILL.md",
                    Path(".claude") / "skills" / directory_name / "SKILL.md",
                ),
            ]
        )

    return files


def _license_asset(relative_path: Path) -> str:
    """Return the asset that licenses a materialized file."""

    for asset_name, directory_name in SKILL_ASSETS.items():
        if relative_path.parts[:3] == (
            ".ai-data-compass",
            "skills",
            directory_name,
        ):
            return asset_name
        if relative_path.parts[:3] in {
            (".agents", "skills", directory_name),
            (".claude", "skills", directory_name),
        }:
            return asset_name
    return BASE_ASSET


def _file_metadata(path: Path) -> Dict[str, object]:
    """Return stable integrity metadata for a file."""

    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    file_stat = path.stat()
    return {
        "sha256": digest.hexdigest(),
        "size": file_stat.st_size,
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
) -> dict:
    """Build a deterministic manifest for the installed assets."""

    entries = [
        {
            "path": relative_target.as_posix(),
            "license_asset": _license_asset(relative_target),
            "source": source.relative_to(source_root).as_posix(),
            **_file_metadata(source),
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
                "path": f".ai-data-compass/skills/{directory_name}/LICENSE",
            }
        )
        notices.append(
            {
                "asset": asset_name,
                "path": f".ai-data-compass/skills/{directory_name}/THIRD-PARTY-NOTICES.md",
            }
        )
    return {
        "format": MANIFEST_FORMAT,
        "package": PACKAGE_NAME,
        "version": __version__,
        "assets": [BASE_ASSET] + list(selected),
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
        expected_files = {
            relative.as_posix()
            for _, relative in _asset_files(selected, repository_root())
        }
        actual_files = set(entries_by_path)
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
) -> List[Path]:
    """Install selected assets into a clean target repository."""

    target = target.resolve()
    with _installation_lock(target):
        return _install_assets(target, selected, root=root)


def _install_assets(
    target: Path,
    selected: Sequence[str],
    *,
    root: Optional[Path] = None,
) -> List[Path]:
    """Install assets while the caller holds the per-target lock."""

    source_root = root or repository_root()
    files = _asset_files(selected, source_root)
    for source, _ in files:
        if not source.is_file():
            raise FileNotFoundError(f"Asset source file does not exist: {source}")

    all_destinations = [relative_target for _, relative_target in files]
    all_destinations.append(MANIFEST_RELATIVE_PATH)
    for relative_target in all_destinations:
        _validate_destination(target, relative_target)

    stage = Path(tempfile.mkdtemp(prefix=".ai-data-compass-install-", dir=str(target.parent)))
    staged_paths: List[Path] = []
    committed_paths: List[Path] = []
    created_directories: List[Path] = []
    try:
        for source, relative_target in files:
            staged = stage / relative_target
            staged.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, staged)
            staged_paths.append(relative_target)

        manifest_path = stage / MANIFEST_RELATIVE_PATH
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(
            json.dumps(_manifest(selected, files, source_root), indent=2) + "\n",
            encoding="utf-8",
        )
        staged_paths.append(MANIFEST_RELATIVE_PATH)

        for relative_target in staged_paths:
            _validate_destination(target, relative_target)
            destination = target / relative_target
            if not destination.parent.exists():
                missing: List[Path] = []
                current = destination.parent
                while not current.exists():
                    missing.append(current)
                    current = current.parent
                destination.parent.mkdir(parents=True, exist_ok=True)
                created_directories.extend(missing)
            os.replace(stage / relative_target, destination)
            committed_paths.append(destination)
        return staged_paths
    except Exception:
        for path in reversed(committed_paths):
            if path.is_file():
                path.unlink()
        for directory in sorted(created_directories, key=lambda item: len(item.parts), reverse=True):
            try:
                directory.rmdir()
            except OSError:
                pass
        raise
    finally:
        shutil.rmtree(stage, ignore_errors=True)


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
