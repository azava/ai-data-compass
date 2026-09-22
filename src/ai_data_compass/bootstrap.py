"""Repository bootstrap operations."""

from __future__ import annotations

from pathlib import Path
from typing import Callable, List, Optional, Sequence, Union

from .assets import (
    InstallationResult,
    install_assets,
    normalize_assets,
    plan_assets,
)


def initialize(
    target: Path,
    asset_values: Sequence[str],
    *,
    dry_run: bool = False,
    asset_root: Optional[Path] = None,
    confirm_agents_adoption: Optional[Callable[[Path], bool]] = None,
) -> Union[List[Path], InstallationResult]:
    """Prepare *target* for AI Data Compass assets.

    Existing files with different content block only the affected asset. Files
    with identical content are preserved, and missing files are installed.
    """

    target = target.resolve()
    if not target.exists():
        raise FileNotFoundError(f"Target directory does not exist: {target}")
    if not target.is_dir():
        raise NotADirectoryError(f"Target is not a directory: {target}")

    selected = normalize_assets(asset_values)
    if dry_run:
        return plan_assets(target, selected, root=asset_root)
    return install_assets(
        target, selected, root=asset_root,
        confirm_agents_adoption=confirm_agents_adoption,
    )
