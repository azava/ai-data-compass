# Asset Versioning

`src/ai_data_compass/asset_versions.json` is the repository's version-controlled source of truth for asset contents. It stores package snapshots; each snapshot associates an asset name and asset version with repository-relative source paths and SHA-256 hashes of their exact source bytes.

Apply these rules when maintaining the registry:

- Give each asset its own version, independent of the package version.
- Start a newly introduced asset at version `0.0.1`.
- Increment an existing asset's version when its files or contents change; keep its version when it does not change.
- Record an asset version in the package snapshot where that version is included.
- Include every asset in each package snapshot, including unchanged assets, so the snapshot represents the complete package state.
- Record the repository-relative path and SHA-256 hash for every source file in each asset snapshot.

Update the registry whenever a distributable asset changes or a package snapshot is prepared. Keep historical snapshots intact. Add each new asset version only in the package snapshot where it first applies; do not advance an asset version merely because the package version changed.

The registry hashes canonical source files before installer-specific rendering, such as resolving a skill directory name after a naming collision. The installed manifest records actual destination paths and hashes. A future `ai-data-compass update` implementation should use the registry to identify the packaged source version and the installed manifest to detect local file changes and resolved paths.

The registry is package metadata, not an installable asset, and is not included in its own file hashes. `pyproject.toml` includes it in built distributions alongside `skill_catalog.json`.
