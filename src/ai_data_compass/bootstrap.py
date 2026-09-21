"""Repository bootstrap operations."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Sequence

from .assets import install_assets, normalize_assets, planned_assets


def initialize(
    target: Path,
    asset_values: Sequence[str],
    *,
    dry_run: bool = False,
    asset_root: Optional[Path] = None,
) -> List[Path]:
    """Prepare *target* for AI Data Compass assets.

    This initial implementation targets clean repositories. Collision handling
    and merge behavior are intentionally deferred to a later iteration.
    """

    target = target.resolve()
    if not target.exists():
        raise FileNotFoundError(f"Target directory does not exist: {target}")
    if not target.is_dir():
        raise NotADirectoryError(f"Target is not a directory: {target}")

    selected = normalize_assets(asset_values)
    if dry_run:
        return planned_assets(selected, root=asset_root)
    return install_assets(target, selected, root=asset_root)
