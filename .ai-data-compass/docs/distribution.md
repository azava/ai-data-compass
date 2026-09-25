# Installation and Asset Selection

Install it in the Python environment used for your project:

```bash
python -m pip install ai-data-compass
ai-data-compass init --assets complete
```

For an isolated command-line installation, use `pipx install ai-data-compass`, then run `ai-data-compass init --assets complete` from the repository root.

The `complete` selection installs the agent instructions and available skills. Run `ai-data-compass init` without options to choose assets interactively. Use `ai-data-compass init --help` to see the available selections and options.

Each installation includes the base documentation, license, and third-party notices. A successful installation records the selected assets and installed files in `.ai-data-compass/manifest.json`.

The installer creates missing files and preserves existing files with matching content and required permissions. If an existing target differs, the installer reports a conflict for the affected asset instead of overwriting it; other selected assets can still be installed. Use `ai-data-compass init --dry-run` to preview the result without writing files.

When an existing `AGENTS.md` contains different instructions, the installer can place the AI Data Compass guidance in `AGENTS-ai-data-compass.md` and add a reference to it after consent. When a skill directory already contains different content, the installer uses an available name with the `-ai-data-compass` suffix and updates installed references to match. For example, the `security_audit` skill is normally stored under `.ai-data-compass/skills/security-audit/`.

The license files under `.ai-data-compass/` apply to the AI Data Compass assets they accompany. They do not change the adopting repository's license.
