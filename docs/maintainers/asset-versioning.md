# Asset Versioning

`src/ai_data_compass/asset_versions.json` is the repository's version-controlled source of truth for asset contents. It stores package snapshots; each snapshot associates an asset name and asset version with repository-relative source paths and SHA-256 hashes of their exact source bytes. Package versions and asset versions are separate: a package release can contain assets whose versions did not change.

Apply these rules when maintaining the registry:

- Give each asset its own version, independent of the package version.
- Start a newly introduced asset at version `0.0.1`.
- Increment an existing asset's version only when preparing a new asset revision. Fixes made while preparing an unpublished package snapshot can remain in the current asset version; update that snapshot's file hashes to match the corrected source.
- Record an asset version in the package snapshot where that version is included.
- Include every asset in each package snapshot, including unchanged assets, so the snapshot represents the complete package state.
- Record the repository-relative path and SHA-256 hash for every source file in each asset snapshot.

Update the registry whenever a distributable asset changes or a package snapshot is prepared. A published package snapshot is immutable. An unpublished development snapshot may be updated before release, including its asset file hashes, while preserving the intended asset version. Keep published historical snapshots intact. Add each new asset version only in the package snapshot where it first applies; do not advance an asset version merely because the package version changed.

For example, package version `0.0.1` is published on PyPI, while package version `0.0.2` is a development snapshot. An asset at version `0.0.2` in the development snapshot does not imply that package version `0.0.2` has been published, and it does not change the asset version `0.0.1` recorded in the published package snapshot.

The registry hashes canonical source files before installer-specific rendering, such as resolving a skill directory name after a naming collision. The installed manifest records actual destination paths and hashes. A future `ai-data-compass update` implementation should use the registry to identify the packaged source version and the installed manifest to detect local file changes and resolved paths.

The registry is package metadata, not an installable asset, and is not included in its own file hashes. `pyproject.toml` includes it in built distributions alongside `skill_catalog.json`.
