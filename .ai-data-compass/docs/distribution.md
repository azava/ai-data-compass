# Distribution

AI Data Compass is distributed as the `ai-data-compass` Python package. Its
CLI command has the same name: `ai-data-compass`.

The initial package supports Python 3.9 and newer. Compatibility should be
verified across the supported interpreter matrix before each release.

The supported installation paths are:

- `python -m pip install ai-data-compass` for the target Python environment,
  including a virtual environment or CI environment;
- `pipx install ai-data-compass` for a globally available CLI isolated from
  other Python environments.

pipx is an optional convenience and is not required to use the package.

The package provides the CLI and installs the base documentation with every
asset selection. `complete` installs the agent instructions and all available
skills; `agents.md` installs `AGENTS.md` and its host adapters;
`security_audit` installs the security-audit skill and its host adapters; and
`skills` installs all available skills. These values can be combined with
commas.

Running `init` without `--assets` opens the interactive installer. It presents
the same options and uses `complete` when the selection is left empty. Terminal
colors are used when supported and can be disabled with `NO_COLOR=1`.

Every installation writes `.ai-data-compass/manifest.json`. The manifest
records the package version, selected assets, installed files, applicable
license for each file, and the third-party notice files that apply to the
selection.

The package license describes the Python distribution. The license files
installed under `.ai-data-compass/` apply only to the AI Data Compass assets
listed in the manifest and do not change the adopting repository's license.
Each skill has its own scoped license and third-party notice file.

The current base asset and `security_audit` skill contain no third-party
material. Their notice files are included so future material can be recorded
without changing the asset layout.

The current bootstrap targets clean repositories. Conflict detection, merge
behavior, and preservation of existing project files will be implemented in a
later iteration.
