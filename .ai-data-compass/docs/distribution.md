# Distribution

AI Data Compass is distributed as the `ai-data-compass` Python package. Its CLI command has the same name: `ai-data-compass`.

The initial package supports Python 3.9 and newer. Compatibility should be verified across the supported interpreter matrix before each release.

Version `0.0.1` is published on PyPI. To install the current local source, run these commands from the repository root:

```bash
python -m pip install .
ai-data-compass --version
```

For a globally available CLI isolated from other Python environments, run `pipx install .` from the repository root. After a PyPI release, use either:

```bash
python -m pip install ai-data-compass
pipx install ai-data-compass
```

The package provides the CLI and installs the base documentation with every asset selection. `complete` installs the agent instructions and all available skills; `agents.md` installs `AGENTS.md` and its host adapters; each skill option installs that skill and its Codex and Claude projections; and `skills` installs all available skills. These values can be combined with commas.

Skills are registered in `src/ai_data_compass/skill_catalog.json`. To add a skill, add one catalog entry with its CLI asset name, canonical directory, and menu description, then add its canonical files under `.ai-data-compass/skills/<directory>/` and its Codex and Claude projections. Each skill also needs its own `LICENSE` and `THIRD-PARTY-NOTICES.md`. The CLI selection and packaged skill files are derived from the catalog.

The catalog itself is package data. Other distributable assets are currently installed under the platform data directory at `share/ai-data-compass/assets` by `setup.py`. Moving those assets inside the Python package and loading them as package resources remains a future improvement.

Running `init` without `--assets` opens the interactive installer. It presents the same options and uses `complete` when the selection is left empty. Terminal colors are used when supported and can be disabled with `NO_COLOR=1`.

A successful, non-dry-run `init` records `.ai-data-compass/manifest.json`. The manifest records the package version, selected assets, installed files, applicable license for each file, and the third-party notice files that apply to the selection.

The manifest format version is independent of the package version. `init` and `verify` accept manifests created by older package versions when their format is still supported; a successful installation updates the recorded package version. Changing the manifest format requires an explicit migration.

The package license describes the Python distribution. The license files installed under `.ai-data-compass/` apply only to the AI Data Compass assets listed in the manifest and do not change the adopting repository's license. Each skill has its own scoped license and third-party notice file.

The current base asset and `security_audit` skill contain no third-party material. Their notice files are included so future material can be recorded without changing the asset layout.

Stable releases are published to PyPI by `.github/workflows/publish-to-pypi.yml` when a stable `vMAJOR.MINOR.PATCH` tag is pushed. The workflow verifies that the tag matches the project version, builds and validates a wheel and source distribution, then publishes through the protected `pypi` GitHub environment using Trusted Publishing.

Pushes to the `dev` branch are published to TestPyPI by `.github/workflows/publish-to-testpypi.yml`. The workflow creates a unique `0.0.2.devN` version in its temporary runner checkout, where `N` is the GitHub Actions workflow run number; it does not change the committed `pyproject.toml`. Update `DEV_VERSION_BASE` in that workflow when development moves to a later stable release line. The TestPyPI publisher uses the separate `testpypi` GitHub environment and never publishes these builds to PyPI.

`init` checks each selected asset before writing files. It installs missing files, leaves files with matching content and executable status unchanged, repairs executable status on registered files, and refuses an asset if any of its existing files differ. A refused asset does not prevent other selected assets from being installed, and `init` exits with a nonzero status if any asset is refused. When files have matching content and executable status but are not recorded in the AI Data Compass manifest, the CLI reports them as identical existing files rather than claiming that the asset was already installed. `init --dry-run` applies the same checks and reports planned per-asset outcomes without writing files.

Each asset is staged and committed as a unit. If a handled error occurs while committing an asset, files created by that attempt are removed. Mandatory base documentation is included in each asset's preflight and installation unit. If a destination changes during commit, installation aborts, restores files committed by that attempt, and preserves the changed destination. The commit checks cover changes detected during the operation; they do not coordinate external editors that write after the final verification. This rollback covers errors reported during the running process; recovery after an abrupt termination or power loss is not provided.

When a destination already has a different `AGENTS.md`, the installer can add the AI Data Compass instructions in `AGENTS-ai-data-compass.md` (or an available numeric suffix) and append a single-line instruction to the existing `AGENTS.md` after user consent. If consent is declined, the `agents.md` asset is not installed. Claude receives a native `@` reference to the supplementary instructions. A missing `CLAUDE.md` is created with that reference. Other host adapter files are created only when absent; existing ones are preserved.

When a skill's canonical directory name is already occupied by different content, `init` selects an available name with the `-ai-data-compass` suffix (and a numeric suffix if needed). It records that name in the manifest and uses it consistently for the canonical skill directory, host adapters, and references in installed skill and documentation Markdown. If the base documentation was previously installed and is still unchanged from the manifest, it is updated in the same asset transaction. Adopter-modified base documentation remains a conflict.
